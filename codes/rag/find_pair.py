from collections import defaultdict
from ..state import QAState
from .find_ag import PatentQANode
import pandas as pd
import numpy as np
import re
import os
import itertools
from functools import partial
from bs4 import BeautifulSoup

from langchain_core.documents import Document
from langchain_core.messages import SystemMessage, HumanMessage
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_community.vectorstores.utils import maximal_marginal_relevance
from .utils import remove_duplicates_by_id, format_docs

# Constants
ab_components = {
    "VH": "variable heavy chain domain",
    "VL": "variable light chain domain",
    "HC": "heavy chain",
    "LC": "light chain",
    "scFv": "single chain Fragment variable",
    "FC": "Full length antibody",
    "NB": "Nanobody",
    "MS": "Multi-specific antibody"
}


class PairAbNameNode(PatentQANode):
    def __init__(self, assistant, **kwargs):
        self.task = "pair_ab_name"
        self.cols = {
            'ag_idx': int,
            'ab_name': str,
            'reference': str,
            'reason': str
        }
        self.required = ['ag_idx', 'ab_name', 'reference', 'reason']
        self.max_group_size = kwargs.get('max_group_size', 6)

        self.assistant = assistant
        system_prompt_file = kwargs.get("system_prompt_file", "system.yaml")
        if system_prompt_file != "system.yaml":
            self.assistant.set_model(system_prompt_file)
        self.top_n = kwargs.get('top_n', 8)
        self.mmr_out = kwargs.get('mmr_out', 5)
        assistant.set_retriever()
        assistant.set_reranker(top_n=self.top_n)

    def create_retriever_queries(self, ag_keyword, ag_name_alias, ab_name):
        ag_name = ag_name_alias[0]
        if len(ag_name_alias) > 1:
            ag_name += f"({', '.join(ag_name_alias[1:])})"
        queries = [
            f"Antibody {ab_name} binds with {ag_keyword}",
            f"Table shows that antibody {ab_name} bind with {ag_keyword}",
            f"TABLE binding affinity {ag_keyword} {ab_name}",
            f"FIG. shows that antibody {ab_name} bind with {ag_keyword}",
            f"antibody {ab_name} bind with {ag_keyword} as shown in FIG. ",
            f"{ag_name} specific antibody {ab_name}",
            f"{ag_name} targeting antibody {ab_name}",
            f"anti-{ag_name} antibody {ab_name}",
            f"result shows that antibody {ab_name} effective against {ag_keyword}",
            f"antibody {ab_name} assay on {ag_keyword} measuring KD, Kd, IC50, EC50"
        ]
        return queries

    def ab_in_doc(self, doc, ab_name):

        return re.search(rf"\b{re.escape(str(ab_name))}\b", doc.page_content)


    def retrieve_pair_documents(
            self,
            df_ag: pd.DataFrame,
            ab_name: str
        ) -> list[Document]:
        """
        Retrieve documents related to the binding of a specific antibody to antigens.
        """

        ag_keywords = self.create_antigen_keywords(df_ag)
        list_ag_name_alias = []
        for _, data in df_ag.iterrows():
            data = data.dropna()
            ag_name_alias = [data['name']]
            if 'abbreviation' in data:
                ag_name_alias.extend(data['abbreviation'].split(';'))
            list_ag_name_alias.append(ag_name_alias)

        query_list = [
            self.create_retriever_queries(ag_keyword, ag_name_alias, ab_name)
            for ag_name_alias, ag_keyword in zip(list_ag_name_alias, ag_keywords)
        ]

        reranked_docs = [
            self.multi_query_retrieve(queries=queries, filter_fn=partial(self.ab_in_doc, ab_name=ab_name))
            for queries in query_list
        ]
        flattened_docs = list(itertools.chain(*reranked_docs))
        unique_docs = remove_duplicates_by_id(flattened_docs)

        return unique_docs

    def create_ag_prompt(self, df_ag):
        ag_keywords = self.create_antigen_keywords(df_ag)
        prompt = "\n".join(ag_keywords)

        return prompt

    def create_ab_prompt(self, pair_key, df):
        keywords = []
        h_key, l_key = (pair_key.split('_') + [None])[:2]

        for ab_idx, series in df.iterrows():
            name_part = f"{ab_idx}. Name: '{series['name']}'"
            if l_key:  # Pair
                h_part = f"{ab_components[h_key]} ({h_key}) SEQ ID NO: {series['heavy_seq_id_no']}"
                l_part = f"{ab_components[l_key]} ({l_key}) SEQ ID NO: {series['light_seq_id_no']}"
                keywords.append(f"{name_part} {h_part}, {l_part}")
            else:  # Single
                seq_part = f"{ab_components[h_key]} ({h_key}) SEQ ID NO: {series['heavy_seq_id_no']}"
                keywords.append(f"{name_part} {seq_part}")

        return '\n'.join(keywords)

    def execute(self, state):
        pair_keys = ['VH_VL', 'HC_LC', 'scFv', 'FC', 'NB', 'MS']
        index_audits = []
        result = {pair_key: [] for pair_key in pair_keys}
        raw_result = {pair_key: [] for pair_key in pair_keys}
        prompt = self.assistant.create_prompt(self.task)

        df_ag = self.experiment_antigen_table(state)
        ag_prompt = self.create_ag_prompt(df_ag)

        for pair_key in pair_keys:
            df_ab_named = state['ab_pair_named'][pair_key]
            ab_names = list(df_ab_named['name'])

            if df_ab_named.empty:
                result[pair_key].append(self.empty_df())
                raw_result[pair_key].extend([{}])
                continue

            dict_reranked_docs = {
                ab_name: self.retrieve_pair_documents(df_ag, ab_name)
                for ab_name in ab_names
            }

            group_ab_idxs = self.flexible_split(range(len(ab_names)))
            group_ab_names = [[ab_names[i] for i in group] for group in group_ab_idxs]

            list_reranked_docs = [
                list({doc.page_content: doc
                    for ab_name in list_ab_name
                    for doc in dict_reranked_docs[ab_name]}.values())
                for list_ab_name in group_ab_names
            ]
            contexts = [format_docs(docs) for docs in list_reranked_docs]

            group_ab_prompts = [
                self.create_ab_prompt(pair_key, df_ab_named.iloc[ab_idxs])
                for ab_idxs in group_ab_idxs
            ]

            configs = [
                {'context': context, 'antigen': ag_prompt, 'antibody': ab_prompt}
                for context, ab_prompt in zip(contexts, group_ab_prompts)
            ]
            prompts = [prompt.format(**config) for config in configs]
            responses = self.assistant.model.batch(prompts)

            parsed_outputs = StrOutputParser().batch(responses)
            filter_seq_id_no = {'ab_name': group_ab_names}
            df, audits = self.parse_antigen_response(parsed_outputs, df_ag, filter_seq_id_no=filter_seq_id_no)
            index_audits.extend(audits)
            result[pair_key].append(df)

            configs = [{**config, "response": response} for config, response in zip(configs, parsed_outputs)]
            raw_result[pair_key].extend(configs)


        for pair_key, dfs in result.items():
            concat_df = pd.concat(dfs).reset_index(drop=True)
            result[pair_key] = concat_df

        return self.antigen_result(result, raw_result, index_audits)


class ExperimentSummary(PatentQANode):
    def __init__(self, assistant, **kwargs):
        self.assistant = assistant
        self.task = "experiment_summary"
        self.cols = {
            "experiment_summary": str,
            "antibody_format": str
        }
        self.required = ["experiment_summary"]

        system_prompt_file = f"pair_ab_name_experiment.yaml"
        self.assistant.set_model(system_prompt_file)
        antibody_info_f = os.path.join(kwargs.get('prompt'), 'patent_qa/assistant/antibody.md')
        with open(antibody_info_f, 'r') as rf:
            self.antibody_info = rf.read()
        self.batch_size = kwargs.get('batch_size', 4)


    def construct_context(self, binding_exp_dict):
        contexts = []
        for heading, docs in binding_exp_dict.items():
            text_docs = [doc for doc in docs if 'TABLE' not in doc.metadata.get('id', '')]
            table_docs = [doc for doc in docs if 'TABLE' in doc.metadata.get('id', '')]

            for table_doc in table_docs:
                tmp = text_docs + [table_doc]
                context = f'<h5>{heading}</h5>' + format_docs(tmp)
                contexts.append(context)
            if not table_docs:
                context = f'<h5>{heading}</h5>' + format_docs(text_docs)
                contexts.append(context)

        return contexts


    def execute(self, doc_state):
        result = []
        prompt = self.assistant.create_prompt(task=self.task)

        # Reconstruct
        binding_exp_dict = doc_state['binding_exp_dict']
        contexts = self.construct_context(binding_exp_dict)
        prompts = [prompt.format(context=context) for context in contexts]

        system_content = self.assistant.system_prompt + "\n\n" + self.antibody_info
        for i in range(0, len(prompts), self.batch_size):
            prompt_batch = prompts[i: i+self.batch_size]
            messages_batch = [
                [SystemMessage(content=system_content), HumanMessage(content=p)]
                for p in prompt_batch
            ]
            responses = self.assistant.model.batch(messages_batch)
            parsed_outputs = StrOutputParser().batch(responses)
            result.extend(parsed_outputs)

        if result:
            df_out = self.parse_answers_to_df(result, filter=False)
        else:
            df_out = self.empty_df()

        raw_out = {
            i: {"context": contexts[i], 'response': result[i]}
            for i in range(len(contexts))
        }

        return {self.task: df_out, f"{self.task}_raw": raw_out}


class PairAbNameExpNode(PatentQANode):
    def __init__(self, assistant, **kwargs):
        self.task = "pair_ab_name_experiment"
        self.cols = {
            'ag_idx': int,
            'ab_name': str,
            'measurement': str,
            'value': str,
            'unit': str,
            'approximate value': bool,
            'reference': int,
            'antibody_format': str,
            'experiment_summary': str
        }
        self.required = ['ag_idx', 'ab_name', 'measurement', 'value', 'approximate value', 'reference', 'antibody_format', 'experiment_summary']

        self.assistant = assistant
        measurement_info_f = os.path.join(kwargs.get('prompt'), 'patent_qa/assistant/measurement.md')
        patent_info_f = os.path.join(kwargs.get('prompt'), 'patent_qa/assistant/patent.md')
        with open(measurement_info_f, 'r') as rf:
            self.measurement_info = rf.read()
        with open(patent_info_f, 'r') as rf:
            self.patent_info = rf.read()
        self.batch_size = kwargs.get('batch_size', 4)

    def create_ag_prompt(self, df_ag):
        ag_keywords = self.create_antigen_keywords(df_ag)
        prompt = "\n".join(ag_keywords)

        return prompt

    def construct_context(self, binding_exp_dict):
        contexts = []
        for heading, docs in binding_exp_dict.items():
            text_docs = [doc for doc in docs if 'TABLE' not in doc.metadata.get('id', '')]
            table_docs = [doc for doc in docs if 'TABLE' in doc.metadata.get('id', '')]

            for table_doc in table_docs:
                tmp = text_docs + [table_doc]
                context = f'<h5>{heading}</h5>' + format_docs(tmp)
                contexts.append(context)
            if not table_docs:
                context = f'<h5>{heading}</h5>' + format_docs(text_docs)
                contexts.append(context)

        return contexts

    def mining_names(self, context: str, ab_names):
        if not ab_names:
            return []

        ab_name_p = r'(?:' + '|'.join(map(re.escape, ab_names)) + r')'
        matched_names = re.findall(ab_name_p, context, re.IGNORECASE)
        matched_names = list(set(matched_names))

        return matched_names


    def execute(self, state, doc_state) -> QAState:
        index_audits = []
        result = []
        raw_result = []
        prompt = self.assistant.create_prompt(task=self.task, few_shot=2)

        # Get Antigen prompt
        df_ag = self.experiment_antigen_table(state)
        ag_prompt = self.create_ag_prompt(df_ag)

        # Reconstruct
        df_ab = pd.concat(
            [
                df.assign(**{"pair_type": key})
                for key, df in state['ab_pair_named'].items()
            ], ignore_index=True
        ).dropna(subset='name')
        df_ab['name'] = df_ab['name'].str.split(';')
        df_ab = df_ab.explode('name')
        df_ab['name'] = df_ab['name'].str.strip()
        ab_names = list(set(df_ab['name']))
        if not ab_names:
            return self.antigen_result(self.empty_df(), {}, index_audits)

        binding_exp_dict = doc_state['binding_exp_dict']
        contexts = self.construct_context(binding_exp_dict)
        if ab_names:
            matched_abs = [self.mining_names(context, ab_names) for context in contexts]
        else:
            matched_abs = []
        configs = [
            {'context': context, 'antigen': ag_prompt, 'antibody': '-' + '\n-'.join(matched_ab) + '\n'}
            for context, matched_ab in zip(contexts, matched_abs)
        ]
        prompts = [prompt.format(**config) for config in configs]

        system_content = self.assistant.system_prompt + "\n\n" + self.measurement_info + "\n\n" + self.patent_info
        for i in range(0, len(prompts), self.batch_size):
            config_batch = configs[i:i+self.batch_size]
            prompt_batch = prompts[i:i+self.batch_size]
            messages_batch = [
                [SystemMessage(content=system_content), HumanMessage(content=p)]
                for p in prompt_batch
            ]
            responses = self.assistant.model.batch(messages_batch)
            parsed_outputs = StrOutputParser().batch(responses)
            result.extend(parsed_outputs)

            config_batch = [{**config, "response": response} for config, response in zip(config_batch, parsed_outputs)]
            raw_result.extend(config_batch)

        if result:
            df_out = []
            for i, response in enumerate(result):
                df, audits = self.parse_antigen_response(response, df_ag)
                index_audits.extend(audits)
                df['reference'] = i
                df_out.append(df)
            df_out = pd.concat(df_out, ignore_index=True)
        else:
            df_out = self.empty_df()

        return self.antigen_result(df_out, raw_result, index_audits)


class PairNoNameExpNode(PatentQANode):
    def __init__(self, assistant, **kwargs):
        self.task = "pair_no_name_experiment"
        self.cols = {
            'ag_idx': int,
            'heavy_seq_id_no': int,
            'light_seq_id_no': int,
            'measurement': str,
            'value': str,
            'unit': str,
            'approximate value': bool,
            'reference': int,
            'antibody_format': str,
            'experiment_summary': str
        }
        self.required = ['ag_idx', 'heavy_seq_id_no', 'measurement', 'value', 'approximate value', 'reference', 'antibody_format', 'experiment_summary']

        self.assistant = assistant
        self.batch_size = kwargs.get('batch_size', 4)

    def create_ag_prompt(self, df_ag):
        ag_keywords = self.create_antigen_keywords(df_ag)
        prompt = "\n".join(ag_keywords)

        return prompt

    def construct_context(self, binding_exp_dict):
        contexts = []
        for heading, docs in binding_exp_dict.items():
            text_docs = [doc for doc in docs if 'TABLE' not in doc.metadata.get('id', '')]
            table_docs = [doc for doc in docs if 'TABLE' in doc.metadata.get('id', '')]

            for table_doc in table_docs:
                tmp = text_docs + [table_doc]
                context = f'<h5>{heading}</h5>' + format_docs(tmp)
                contexts.append(context)
            if not table_docs:
                context = f'<h5>{heading}</h5>' + format_docs(text_docs)
                contexts.append(context)

        return contexts

    def mining_names(self, docs, ab_names):

        ab_name_p = r'(?:' + '|'.join(map(re.escape, ab_names)) + r')'
        matched_names = []
        for doc in docs:
            matches = re.findall(ab_name_p, doc, re.IGNORECASE)
            matched_names.extend(matches)

        return matched_names


    def execute(self, state, doc_state) -> QAState:
        index_audits = []
        result = []
        raw_result = []
        prompt = self.assistant.create_prompt(task=self.task)

        # Get Antigen prompt
        df_ag = self.experiment_antigen_table(state)
        ag_prompt = self.create_ag_prompt(df_ag)

        binding_exp_dict = {
            heading: exp_docs for heading, exp_docs in doc_state['binding_exp_dict'].items()
            if any(doc.metadata.get('SEQ_ID_NO', []) for doc in exp_docs)
            }
        contexts = self.construct_context(binding_exp_dict)
        configs = [
            { 'context': context, 'antigen': ag_prompt }
            for context in zip(contexts)
        ]
        prompts = [prompt.format(**config) for config in configs]

        for i in range(0, len(prompts), self.batch_size):
            config_batch = configs[i:i+self.batch_size]
            prompt_batch = prompts[i:i+self.batch_size]

            responses = self.assistant.model.batch(prompt_batch)
            parsed_outputs = StrOutputParser().batch(responses)
            result.extend(parsed_outputs)

            config_batch = [{**config, "response": response} for config, response in zip(config_batch, parsed_outputs)]
            raw_result.extend(config_batch)

        if result:
            df_out = []
            for i, response in enumerate(result):
                df, audits = self.parse_antigen_response(response, df_ag)
                index_audits.extend(audits)
                df['reference'] = i
                df_out.append(df)
            df_out = pd.concat(df_out, ignore_index=True)
        else:
            df_out = self.empty_df()

        return self.antigen_result(df_out, raw_result, index_audits)


class AliasMappingNode(PatentQANode):
    def __init__(self, assistant, **kwargs):
        self.assistant = assistant
        self.task = "alias_mapping"
        self.threshold = kwargs.get("threshold", 30)
        self.window_size = kwargs.get("window_size", 100)
        self.batch_size = kwargs.get("batch_size", 16)

        self.cols = {
            'query': str,
            'matched_antibody': str,
            'justification': str
        }
        self.required = ['query', 'matched_antibody', 'justification']


    def filter_docs(self, query, ab_names):

        def name_in_doc(doc, query, cands):
            cond1_pattern = r'(?:' + '|'.join(map(re.escape, cands)) + r')'
            cond1 = re.findall(cond1_pattern, doc.page_content, re.IGNORECASE)
            cond2 = re.findall(query, doc.page_content, re.IGNORECASE)
            return cond1 and cond2
        all_docs = list(self.assistant.vectorstore.docstore._dict.values())
        both_name_in_doc = partial(name_in_doc, cands=ab_names)
        filtered_docs = [doc for doc in all_docs if both_name_in_doc(doc=doc, query=query)]

        return filtered_docs

    def get_ab_names(self, ab_pair_named):
        df_ab = pd.concat(
            [
                df.assign(**{"pair_type": key})
                for key, df in ab_pair_named.items()
            ], ignore_index=True
        )
        df_ab['name'] = df_ab['name'].str.split(';')
        df_ab = df_ab.explode('name')
        df_ab['name'] = df_ab['name'].str.strip()
        ab_names = set(df_ab['name'])

        return ab_names

    def compose_context(self, query, unmatched_names, html_text):
        """
        Build a context string that contains text windows where the query IgG name
        (e.g., “AM4405”) appears within `self.threshold` characters of any name
        in `unmatched_names`.  If several unmatched names share the exact same
        query position, the window is included only once.
        """
        # 1) 태그 제거 → 순수 텍스트
        soup = BeautifulSoup(html_text, "html.parser")
        plain_text = soup.get_text(separator=" ", strip=True)

        # 2) 정규식 패턴 (word-boundary 권장)
        cond1_pattern = r'(?:' + '|'.join(map(re.escape, unmatched_names)) + r')'
        cond2_pattern = re.escape(query)

        matches1 = [(m.group(), m.start()) for m in re.finditer(cond1_pattern, plain_text, re.IGNORECASE)]
        matches2 = [(m.group(), m.start()) for m in re.finditer(cond2_pattern, plain_text, re.IGNORECASE)]

        # 3) 동일 query 위치(pos2)가 중복될 경우 한 번만 수집
        seen_query_pos = set()
        candidate_set = set()
        contexts = []

        for name1, pos1 in matches1:
            for _, pos2 in matches2:
                if abs(pos1 - pos2) <= self.threshold and pos2 not in seen_query_pos:
                    start = max(0, min(pos1, pos2) - self.window_size)
                    end   = min(max(pos1, pos2) + self.window_size, len(plain_text))
                    contexts.append(plain_text[start:end])
                    candidate_set.add(name1)      # 실제 근접 매치된 name1 저장
                    seen_query_pos.add(pos2)

        # query 자체가 candidate_set 에 들어갔을 경우 제거(대소문자 무시)
        candidate_set = {n for n in candidate_set if n.lower() != query.lower()}

        # 4) 여러 창을 줄바꿈으로 이어붙여 반환
        return '\n'.join(contexts), candidate_set

    def execute(self, state, doc_state):

        ab_names   = self.get_ab_names(state['ab_pair_named'])
        exp_names  = set(state['pair_ab_name_experiment']['ab_name'].dropna().unique())

        unknown_names   = list(exp_names.difference(ab_names))
        matched_names   = exp_names.intersection(ab_names)
        unmatched_names = ab_names.difference(matched_names)

        html_text = doc_state['full_html']

        # compose_context 가 (context, candidate_set) 튜플을 반환
        ctx_cand_pairs = [
            self.compose_context(query, unmatched_names, html_text)
            for query in unknown_names
        ]

        configs = []
        for (context_str, cand_set), query in zip(ctx_cand_pairs, unknown_names):
            # bullet 형식으로 정렬하여 프롬프트에 넣기
            if cand_set:
                name_prompt = '- ' + '\n- '.join(sorted(cand_set, key=str.lower))
            else:
                name_prompt = ''  # 근접 매치가 없으면 빈 후보 목록
            configs.append(
                {
                    'context': context_str,
                    'query': query,
                    'candidate_list': name_prompt
                }
            )

        prompt_template = self.assistant.create_prompt(task=self.task)
        prompts = [prompt_template.format(**cfg) for cfg in configs]

        result_frames = []
        raw_result    = []

        for i in range(0, len(prompts), self.batch_size):
            cfg_batch    = configs[i:i + self.batch_size]
            prompt_batch = prompts[i:i + self.batch_size]

            responses       = self.assistant.model.batch(prompt_batch)
            parsed_outputs  = StrOutputParser().batch(responses)
            df_batch        = self.parse_answers_to_df(parsed_outputs, filter=False)
            result_frames.append(df_batch)

            raw_result.extend(
                [{**cfg, "response": resp} for cfg, resp in zip(cfg_batch, parsed_outputs)]
            )
        if len(result_frames) > 0:
            df_out = pd.concat(result_frames).reset_index(drop=True)
        else:
            df_out = self.empty_df()
        return {self.task: df_out, f"{self.task}_raw": raw_result}


class PairAbUnnamedNode(PatentQANode):
    def __init__(self, assistant, **kwargs):
        self.task = "pair_ab_unnamed"
        self.cols = {
            'heavy_seq_id_no': int,
            'light_seq_id_no': int,
            'ag_idx': int,
            'reference': str,
            'reason': str
            }
        self.required = ['heavy_seq_id_no', 'light_seq_id_no', 'ag_idx', 'references']
        self.assistant = assistant
        self.mmr_out = kwargs.get('mmr_out', 5)
        self.max_group_size = kwargs.get('max_group_size', 4)

        system_prompt_file = kwargs.get("system_prompt_file", "system.yaml")
        if system_prompt_file != "system.yaml":
            self.assistant.set_model(system_prompt_file)
        assistant.set_reranker(**kwargs)

    def create_retriever_queries(self, ag_keyword, ag_name_alias, ab_idx):
        ag_name = ag_name_alias[0]
        if len(ag_name_alias) > 1:
            ag_name += f"({', '.join(ag_name_alias[1:])})"
        h_idx, l_idx = ab_idx
        queries = [
            f"anti-{ag_name} antibody composed of SEQ ID NO {h_idx} and SEQ ID NO {l_idx}",
            f"Antibody composed of SEQ ID NO {h_idx} and SEQ ID NO {l_idx} bind with {ag_keyword}"
            f"Antibody consist of SEQ ID NO {h_idx} and SEQ ID NO {l_idx} targeting {ag_keyword}"
            f"TABLE anti-{ag_name} antibody SEQ ID NO {h_idx}, SEQ ID NO {l_idx}"
        ]
        return queries

    def _idx_in_doc(self, doc, ab_idx):
        """
        Check if both heavy and light chain SEQ ID NO are present in the document metadata.
        """
        h_idx, l_idx = ab_idx
        idx_list = doc.metadata.get('SEQ_ID_NO', [])
        cond1 = h_idx in idx_list
        if pd.isna(l_idx):
            cond2 = False
        else:
            cond2 = l_idx in idx_list

        return cond1 or cond2

    def retrieve_pair_documents(self, df_ag, ab_idx):
        ag_keywords = self.create_antigen_keywords(df_ag)
        list_ag_name_alias = []
        for _, data in df_ag.iterrows():
            data = data.dropna()
            ag_name_alias = [data['name']]
            if 'abbreviation' in data:
                ag_name_alias.extend(data['abbreviation'].split(';'))
            list_ag_name_alias.append(ag_name_alias)

        query_list = [
            self.create_retriever_queries(ag_keyword, ag_name_alias, ab_idx)
            for ag_keyword, ag_name_alias in zip(ag_keywords, list_ag_name_alias)
        ]

        reranked_docs = [
            self.multi_query_retrieve(
                queries=queries,
                filter_fn=partial(self._idx_in_doc, ab_idx=ab_idx)
            )
            for queries in query_list
        ]
        flattened_docs = list(itertools.chain(*reranked_docs))
        unique_docs = remove_duplicates_by_id(flattened_docs)

        return unique_docs

    def create_ag_prompt(self, df_ag):
        ag_keywords = self.create_antigen_keywords(df_ag)
        prompt = "\n".join(ag_keywords)

        return prompt

    def create_ab_prompt(self, pair_key, df):

        keywords = []
        if '_' in pair_key:
            h_key, l_key = pair_key.split('_')
            for idx, data in df.iterrows():
                keyword = f"{idx}. Antibody composed of {ab_components[h_key]} ({h_key}) SEQ ID NO: {data['heavy_seq_id_no']}, "
                keyword+= f"{ab_components[l_key]} ({l_key}) SEQ ID NO: {data['light_seq_id_no']}"
                keywords.append(keyword)
        else:
            for idx, data in df.iterrows():
                keyword = f"{idx+1}. {ab_components[pair_key]} ({pair_key}) "
                keyword+= f"SEQ ID NO: {data['heavy_seq_id_no']}"
                keywords.append(keyword)

        prompt = '\n'.join(keywords)

        return prompt

    def execute(self, state: QAState) -> QAState:
        pair_keys = ['VH_VL', 'HC_LC', 'scFv', 'FC', 'NB', 'MS']
        index_audits = []
        result = {pair_key: [] for pair_key in pair_keys}
        raw_result = {pair_key: [] for pair_key in pair_keys}
        prompt = self.assistant.create_prompt(task=self.task)

        df_ag = self.experiment_antigen_table(state)
        ag_prompt = self.create_ag_prompt(df_ag)

        for pair_key in pair_keys:
            df_ab_unnamed = state['ab_pair_unnamed'][pair_key]
            if df_ab_unnamed.empty:
                result[pair_key].append(self.empty_df())
                raw_result[pair_key].extend([])
                continue

            all_ab_idxs = list(df_ab_unnamed[['heavy_seq_id_no', 'light_seq_id_no']].itertuples(index=False, name=None))
            dict_reranked_docs = {
                ab_idx: self.retrieve_pair_documents(df_ag=df_ag, ab_idx=ab_idx)
                for ab_idx in all_ab_idxs
            }

            group_idxs = self.flexible_split(range(len(df_ab_unnamed)))
            group_ab_idxs = [[all_ab_idxs[i] for i in group] for group in group_idxs]

            list_reranked_docs = [
                self.remove_duplicates_by_id(
                    docs = [doc for ab_idx in list_ab_idx for doc in dict_reranked_docs[ab_idx]],
                )
                for list_ab_idx in group_ab_idxs
            ]
            contexts = [format_docs(docs) for docs in list_reranked_docs]

            group_ab_prompts = [
                self.create_ab_prompt(pair_key, df_ab_unnamed.iloc[idx])
                for idx in group_idxs
            ]

            configs = [
                {'context': context, 'antigen': ag_prompt, 'antibody': ab_prompt}
                for context, ab_prompt in zip(contexts, group_ab_prompts)
            ]
            prompts = [prompt.format(**config) for config in configs]
            responses = self.assistant.model.batch(prompts)

            parsed_outputs = StrOutputParser().batch(responses)
            df, audits = self.parse_antigen_response(parsed_outputs, df_ag)
            index_audits.extend(audits)

            result[pair_key].append(df)
            configs = [{**config, "response": response} for config, response in zip(configs, parsed_outputs)]
            raw_result[pair_key].extend(configs)

        for pair_key, data in result.items():
            df = pd.concat(data)
            result[pair_key] = df

        return self.antigen_result(result, raw_result, index_audits)