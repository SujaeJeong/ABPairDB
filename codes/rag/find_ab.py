import re
import itertools
import pandas as pd
import numpy as np
from functools import partial
from collections import defaultdict
from ..state import QAState
from .find_ag import PatentQANode
from .utils import format_docs, remove_duplicates_by_id


from langchain_core.output_parsers import StrOutputParser
from langchain_community.vectorstores.utils import maximal_marginal_relevance

# Constants
ab_components = {
    "VH": "heavy chain variable domain",
    "VL": "light chain variable domain",
    "HC": "heavy chain",
    "LC": "light chain",
    "NB": "nanobody",
    "scFv": "single chain fragment variable",
    "FC": "Full chain",
    "MS": "Antibody Multimer"
}

ab_complement = {
    "VH": "VL",
    "VL": "VH",
    "HC": "LC",
    "LC": "HC",
    "scFv": "scFv",
    "FC": "FC"
}


class AbNameNode(PatentQANode):
    def __init__(self, assistant, **kwargs) -> QAState:
        self.task = "ab_name"
        self.cols = {'seq_id_no': int, 'name': str, 'exclusion': bool}
        self.required = ['seq_id_no', 'exclusion']

        ag_name = kwargs.get('ag_name')
        self.max_group_size = kwargs.get('max_group_size', 7)
        self.mmr_out = kwargs.get('mmr_out', 5)
        self.batch_size = kwargs.get('batch_size', 6)

        self.assistant = assistant
        self.assistant.set_retriever(**kwargs)
        self.assistant.set_reranker(**kwargs)
        self.assistant.set_model(system_prompt_file="ab_name.yaml",
                    input_variables={'ag_name': ag_name})

    def create_retriever_queries(self, key, idx):
        queries = [
            f"TABLE antibody name or ID of {ab_components[key]} ({key}), SEQ ID NO {idx} ",
            f"FIG. antibody {ab_components[key]} ({key}) name of SEQ ID NO {idx}",
            f"antibody {ab_components[key]} ({key}) name of SEQ ID NO {idx} "
        ]
        return queries

    def ask_nb(self, ask_nb=False):
        if ask_nb:
            self.cols['is_nb'] = bool
            self.required.append('is_nb')
            nanobody_step = "  5. Identify if the query SEQ ID NO corresponds to **nanobody**."
            nanobody_output = f"""  - `is_nb`\n
    - `True` if antibody corresponds to nanobody\n
    - `False` if antibody does not corresponds to nanobody or it is not sure. """
        else:
            nanobody_step, nanobody_output = '', ''
        return nanobody_step, nanobody_output

    def _idx_in_doc(self, doc, idx):
        """
        Check if idx is in the document metadata or content.
        """
        return idx in doc.metadata.get('SEQ_ID_NO', [])

    def _idx_in_doc_pattern(self, doc, idx):
        """
        Check if idx is in the document content using regex.
        """
        return re.search(rf"(?!\d){re.escape(str(idx))}(?!\d)", doc.page_content) is not None

    def execute(self, state):
        ag_name = ', '.join(list(state['ag_detail']['name'].unique()))
        prompt = self.assistant.create_prompt(task=self.task, few_shot=4)
        prompt = prompt.partial(ag_name=ag_name)

        ab_keys = ['VL', 'HC', 'LC', 'scFv', 'FC', 'MS', 'VH']
        result = {}
        raw_result = {}
        for key in ab_keys:
            if state['idx_dict'][key] == []:
                result[key] = self.empty_df()
                continue
            ask_nb = (key == 'VH') and (state['entities']['nanobody'])
            nanobody_step, nanobody_output = self.ask_nb(ask_nb)

            # 1. cluster idx_list
            all_idx_list = state['idx_dict'][key]
            idx_groups = self.split_list(all_idx_list)

            # 2. Retrieve and rerank all chunks by corresponding SEQ ID NO

            dfs = []
            raw_responses = []
            for i in range(0, len(idx_groups), self.batch_size):
                batch_idx_groups = idx_groups[i: i+self.batch_size]
                batch_idx_list = list(itertools.chain.from_iterable(batch_idx_groups))

                list_queries = [self.create_retriever_queries(key, idx) for idx in batch_idx_list]

                dict_reranked_docs = {
                    idx: self.multi_query_retrieve(
                        queries=queries,
                        filter_fn=partial(self._idx_in_doc, idx=idx)
                        )
                    for queries, idx in zip(list_queries, batch_idx_list)
                }

                # 3. Make list of chunks by clustered idx_list
                list_reranked_docs = [
                    self.remove_duplicates_by_id(
                        docs=[doc for idx in idx_list for doc in dict_reranked_docs[idx]], sort=True
                    )
                    for idx_list in batch_idx_groups
                ]
                contexts = [format_docs(docs) for docs in list_reranked_docs]

                configs = [
                    {
                        'component': ab_components[key],
                        'key': key,
                        'context': context,
                        'idx_list': idx_list,
                        'ag_name': ag_name,
                        'nanobody_step': nanobody_step,
                        'nanobody_output': nanobody_output
                    } for context, idx_list in zip(contexts, batch_idx_groups)
                ]
                prompts = [prompt.format(**config) for config in configs]

                responses = self.assistant.model.batch(prompts)
                parsed_output = StrOutputParser().batch(responses)

                df_out = self.parse_answers_to_df(
                    parsed_output, filter_seq_id_no={'seq_id_no': batch_idx_groups}
                )
                dfs.append(df_out)

                configs = [{**config, "response": response} for config, response in zip(configs, parsed_output)]
                raw_responses.extend(configs)

            # Parse result
            df = pd.concat(dfs, ignore_index=True)
            result[key] = df
            raw_result[key] = raw_responses

            # Update Nanobody
            if ask_nb:
                df_valid = df[df['exclusion'] == False]
                nb_idxs = df_valid[df_valid['is_nb'] == True]['seq_id_no'].tolist()
                state['idx_dict']['VH'] = list(set(state['idx_dict']['VH']).difference(set(nb_idxs)))
                state['idx_dict']['NB'] = nb_idxs
            else:
                state['idx_dict']['NB'] = []

            # Update SEQ ID NO dictionary
            valid_idxs = df[df['exclusion'] == False]['seq_id_no'].tolist()
            state['idx_dict'][key] = sorted(list(set(valid_idxs)))

        return {self.task: result, f"{self.task}_raw": raw_result, 'idx_dict': state['idx_dict']}


class AbNameDupNode(PatentQANode):
    def __init__(self, assistant, **kwargs):
        self.assistant = assistant
        self.assistant.set_reranker(**kwargs)
        self.task = "ab_name_duplicated"
        self.cols = {
            'seq_id_no': int,
            'name': str,
            'organism': str,
            'fragment': str,
            'isotype': str,
            'tag': str
        }
        self.required = ['seq_id_no', 'name']
        self.assistant.set_reranker(**kwargs)
        self.max_group_size = kwargs.get('max_group_size', 6)
        self.mmr_out = kwargs.get('mmr_out', 5)

    def create_retriever_queries(self, key, idx):
        queries = [
            f"antibody {ab_components[key]} ({key}) name of SEQ ID NO {idx} ",
            f"TABLE antibody name or ID of {ab_components[key]} ({key}), SEQ ID NO {idx} ",
            f"FIG. antibody {ab_components[key]} ({key}) name of SEQ ID NO {idx}"
        ]

        return queries

    def preprocess_ab_names(self, df):
        # Step 1: Split on ";"
        df['original_name'] = df['name']
        df['original_name'] = df['original_name'].str.split(';')
        df = df.explode('original_name')
        df['original_name'] = df['original_name'].str.strip()

        # Step 2: Extract names in parentheses
        def expand_bracket(name):
            match = re.match(r'^(.*?)[\(\[\{<](.*)[\)\]\}>](.*?)$', name)
            if match:
                return [name, (match.group(1) + match.group(3)).strip()]
            return [name]
        df['all_names'] = df['original_name'].apply(expand_bracket)
        df = df.explode('all_names')

        # Step 3: Clean suffixes from names
        clean = lambda s: re.sub(
            r'(-|_| )?(VL|LC|VK|KC|VH|HC)$|'
            r'(Heavy|Light|kappa|κ|lambda|λ)|'
            r'(humanized|murine|monoclonal|antibody|chain|variable|domain|region|fragment|chains)',
            '', s, flags=re.IGNORECASE).strip()
        df['cleaned_name'] = df['all_names'].apply(clean)
        df['name_lower'] = df['cleaned_name'].str.lower()
        df = self.clean_df(df, cols={'name': str, 'name_lower': str, 'cleaned_name': str})

        # Step 5: Merge original and cleaned names
        name_seq_count = df.groupby('name_lower')['seq_id_no'].nunique()
        unique_names = name_seq_count[name_seq_count == 1].index
        df_unique = df[df['name_lower'].isin(unique_names)]
        df_dup = df[~df['name_lower'].isin(unique_names)]


        return (
            df_unique[['seq_id_no', 'name', 'name_lower']].drop_duplicates(),
            df_dup[['seq_id_no', 'name', 'name_lower']].drop_duplicates()
        )

    def execute(self, state: QAState) -> QAState:
        prompt = self.assistant.create_prompt(task=self.task)
        result, unique_names, raw_responses = {}, {}, {}

        for key in ['VH', 'VL', 'HC', 'LC', 'scFv', 'FC', 'MS']:
            df = state['ab_name'][key]
            if df.empty:
                result[key] = self.empty_df()
                unique_names[key] = pd.DataFrame(columns={'seq_id_no': int, 'name': str, 'name_lower': str})
                continue

            # Preprocess name responses
            df = self.clean_df(df, cols={'name': str})
            if df.empty:
                result[key] = self.empty_df()
                unique_names[key] = pd.DataFrame(columns={'seq_id_no': int, 'name': str, 'name_lower': str})
                continue

            # Classify names into unique and duplicated
            df_no_dup, df_dup = self.preprocess_ab_names(df)
            unique_names[key] = df_no_dup
            if df_dup.empty:
                result[key] = self.empty_df()
                continue

            # If there are duplicated names, retrieve and rerank documents
            name_to_idx_list = df_dup.groupby('name')['seq_id_no'].apply(list).to_dict()
            dfs = []
            for ab_name, idx_list in name_to_idx_list.items():
                queries = [self.create_retriever_queries(key, idx) for idx in idx_list]
                idx_in_doc = partial(lambda doc, idx: idx in doc.metadata.get('SEQ_ID_NO', []))
                dict_reranked_docs = {
                    idx: self.multi_query_retrieve(queries=qs, filter_fn=partial(idx_in_doc, idx=idx))
                    for qs, idx in zip(queries, idx_list)
                }
                docs = [doc for idx in idx_list for doc in dict_reranked_docs[idx]]
                context = format_docs(self.remove_duplicates_by_id(docs, sort=True))
                config = {
                    'ab_key': key,
                    'ab_component': ab_components[key],
                    'context': context,
                    'idx_list': idx_list,
                    'ab_name': ab_name,
                }
                prompt_str = prompt.format(**config)
                response = self.assistant.model.invoke(prompt_str)
                parsed_output = StrOutputParser().invoke(response)

                filter_seq_id_no = {'seq_id_no': idx_list}
                df_out = self.parse_answers_to_df(parsed_output, filter_seq_id_no=filter_seq_id_no)
                dfs.append(df_out)

            df_dup_parsed = pd.concat(dfs, ignore_index=True)
            is_duplicated = df_dup_parsed.duplicated(subset=['name', 'organism', 'fragment', 'isotype', 'tag'], keep=False)
            result[key] = df_dup_parsed[~is_duplicated]

        return {self.task: result, 'unique_names': unique_names}


class AbPairNamed(PatentQANode):
    def __init__(self):
        self.task = "ab_pair_named"
        self.cols = {
            'heavy_seq_id_no': int,
            'light_seq_id_no': int,
            'name': str
        }
        self.required = ['heavy_seq_id_no', 'light_seq_id_no', 'name']

    def execute(self, state: QAState) -> QAState:
        # 1. post-process
        pair_result = {}
        unique_names = state['unique_names']
        dup_names = state['ab_name_duplicated']
        idx_dict = state['idx_dict']

        # 2. Enroll Antibody
        if 'NB' in idx_dict:
            nb_idxs = idx_dict['NB']
            df_NB = state['ab_name']['VH'].set_index('seq_id_no').loc[nb_idxs]
            df_p = pd.DataFrame({
                'name': df_NB['name'],
                'heavy_seq_id_no': nb_idxs,
                'light_seq_id_no': pd.NA
            }).reset_index(drop=True)
            df_p = df_p.dropna(subset='name')
            pair_result['NB'] = df_p
        else:
            pair_result['NB'] = self.empty_df()

        # Pair scFv
        for key in ['scFv', 'FC', 'MS']:
            df = pd.merge(state['unique_names'][key], state['ab_name'][key], how='left', on='seq_id_no')
            if not df.empty:
                df_p = pd.DataFrame({
                    'name': df['name_x'],
                    'heavy_seq_id_no': df['seq_id_no'],
                    'light_seq_id_no': df['seq_id_no']
                })
                pair_result[key] = df_p
            else:
                pair_result[key] = self.empty_df()

        # 4. Enroll VH-VL pair, HC-LC pair unique names
        for pair_key in ['VH_VL', 'HC_LC']:
            h_key, l_key = pair_key.split('_')
            df_h, df_l = unique_names[h_key], unique_names[l_key]
            if df_h.empty or df_l.empty:
                df_p = self.empty_df()
            else:
                df_p = pd.merge(df_h, df_l, on="name_lower", how="inner")

            if df_p.empty:
                pair_result[pair_key] = self.empty_df()
                continue

            df_p = df_p.rename(
                columns={"seq_id_no_x": "heavy_seq_id_no", "seq_id_no_y": "light_seq_id_no", "name_lower": "name"}
                )
            pair_result[pair_key] = df_p[self.required]

        # 5. Enroll VH-VL pair, HC-LC pair duplicated names
        for pair_key in ['VH_VL', 'HC_LC']:
            h_key, l_key = pair_key.split('_')
            df_h = dup_names[h_key].dropna(axis=1, how='all')
            df_l = dup_names[l_key].dropna(axis=1, how='all')
            if df_h.empty or df_l.empty:
                df_dup_p = self.empty_df()
            else:
                cols_to_merge = list(df_h.columns.intersection(df_l.columns).difference({'seq_id_no'}))
                df_dup_p = pd.merge(df_h, df_l, on=cols_to_merge, how='inner')
                df_dup_p = df_dup_p.rename(
                    columns={"seq_id_no_x": "heavy_seq_id_no", "seq_id_no_y": "light_seq_id_no", "name_lower": "name"}
                )[self.required]
                pair_result[pair_key] = pd.concat([pair_result[pair_key], df_dup_p], ignore_index=True)

        unpaired_idx_dict = {}
        for pair_key in ['VH_VL', 'HC_LC']:
            h_key, l_key = pair_key.split('_')

            heavy_idxs = set(state['idx_dict'].get(h_key, []))
            light_idxs = set(state['idx_dict'].get(l_key, []))

            paired_heavy_idxs = set(pair_result[pair_key]['heavy_seq_id_no'].tolist()).union(set(state['idx_dict'].get('NB', [])))
            paired_light_idxs = set(pair_result[pair_key]['light_seq_id_no'].tolist())

            unpaired_heavy_idxs = list(heavy_idxs.difference(paired_heavy_idxs))
            unpaired_light_idxs = list(light_idxs.difference(paired_light_idxs))

            unpaired_idx_dict[h_key] = sorted(unpaired_heavy_idxs)
            unpaired_idx_dict[l_key] = sorted(unpaired_light_idxs)

        idx_dict = state['idx_dict']
        idx_dict['unpaired'] = unpaired_idx_dict

        return {self.task: pair_result, "idx_dict": idx_dict}


class AbPairUnnamedNode(PatentQANode):
    def __init__(self, assistant, **kwargs):
        self.task = "ab_pair_unnamed"
        self.cols = {
            'heavy_seq_id_no': int,
            'light_seq_id_no': int
        }
        self.required = ["heavy_seq_id_no", "light_seq_id_no"]
        self.top_n = kwargs.get('top_n', 8)
        self.max_group_size = kwargs.get('max_group_size', 4)
        self.batch_size = kwargs.get('batch_size', 6)
        self.mmr_out = kwargs.get('mmr_out', 6)

        self.assistant = assistant
        self.assistant.set_retriever(**kwargs)
        self.assistant.set_reranker(**kwargs)

    def _idxs_in_doc(self, doc, idx, comp_idxs):
        cond1 = idx in doc.metadata.get('SEQ_ID_NO', [])
        cond2 = any(comp_idx in doc.metadata.get('SEQ_ID_NO', []) for comp_idx in comp_idxs)
        return cond1 and cond2

    def _idxs_in_doc_pattern(self, doc, idx, comp_idxs):
        cond1 = re.search(rf"(?!\d){re.escape(str(idx))}(?!\d)", doc.page_content)
        cond2 = any(re.search(rf"(?!\d){re.escape(str(comp_idx))}(?!\d)", doc.page_content) for comp_idx in comp_idxs)
        return cond1 and cond2

    def _merge_names(self, tmp, h_key, l_key, state):
        """
        Find common names for heavy and light chains
        """
        # heavy
        name_h = state['ab_name'][h_key].copy(deep=True)
        name_h['name'] = name_h['name'].fillna('').str.split(';')
        name_h = name_h.explode('name')
        name_h['name'] = name_h['name'].str.strip()
        tmp = pd.merge(tmp, name_h, left_on='heavy_seq_id_no', right_on='seq_id_no', how='left')
        tmp = tmp.rename(columns={'name': 'heavy_name'})
        tmp['heavy_name_lower'] = tmp['heavy_name'].str.lower()
        # light
        name_l = state['ab_name'][l_key].copy(deep=True)
        name_l['name'] = name_l['name'].fillna('').str.split(';')
        name_l = name_l.explode('name')
        name_l['name'] = name_l['name'].str.strip()
        tmp = pd.merge(tmp, name_l, left_on='light_seq_id_no', right_on='seq_id_no', how='left')
        tmp = tmp.rename(columns={'name': 'light_name'})
        tmp['light_name_lower'] = tmp['light_name'].str.lower()
        # merge
        names = pd.concat([
            tmp['heavy_name'].where(tmp['heavy_name_lower'] == tmp['light_name_lower'], None),
            tmp['light_name'].where(tmp['heavy_name_lower'] == tmp['light_name_lower'], None)
        ], axis=1)
        tmp['name'] = names.apply(lambda row: list(set([item for item in [row['heavy_name'], row['light_name']] if item])), axis=1)
        tmp = tmp.explode('name')
        return tmp[self.required + ['name']]

    def _create_retriever_queries(self, key, idx, ag_name):
        """
        Generate multiple version of queries
        """
        queries = [
            f"TABLE anti-{ag_name} antibody SEQ ID NO {idx} {ab_components[key]} ({key}) {ab_components[ab_complement[key]]} ({ab_complement[key]})",
            f"Antibody {ab_components[key]} ({key}) of SEQ ID NO: {idx} and {ab_components[ab_complement[key]]} ({ab_complement[key]})"
        ]

        return queries


    def execute(self, state: QAState) -> QAState:
        prompt = self.assistant.create_prompt(task=self.task, few_shot=3)
        result = {}
        raw_result = {}
        ag_name = ','.join(list(state['ag_detail']['name'].unique()))

        for pair_key in ['VH_VL', 'HC_LC']:
            h_key, l_key = pair_key.split('_')
            h_idxs = state['idx_dict']['unpaired'][h_key]
            l_idxs = state['idx_dict']['unpaired'][l_key]

            if not h_idxs and not l_idxs:
                result[pair_key] = self.empty_df()
                continue

            q_key, c_key = (h_key, l_key) if len(h_idxs) >= len(l_idxs) else (l_key, h_key)
            q_comp, c_comp = ab_components[q_key], ab_components[c_key]
            all_idx_list = state['idx_dict']['unpaired'][q_key]
            comp_idxs = state['idx_dict']['unpaired'][c_key]
            idx_groups = self.split_list(all_idx_list)

            dfs, raw_responses = [], []
            for i in range(0, len(idx_groups), self.batch_size):
                batch_idx_groups = idx_groups[i: i+self.batch_size]
                batch_idx_list = list(itertools.chain.from_iterable(batch_idx_groups))

                list_queries = [self._create_retriever_queries(h_key, idx, ag_name) for idx in batch_idx_list]
                dict_reranked_docs = {
                    idx: self.multi_query_retrieve(
                        queries=queries,
                        filter_fn=partial(self._idxs_in_doc, idx=idx, comp_idxs=comp_idxs),
                        filter_fn2=partial(self._idxs_in_doc_pattern, idx=idx, comp_idxs=comp_idxs)
                    )
                    for queries, idx in zip(list_queries, batch_idx_list)
                }

                list_reranked_docs = [
                    self.remove_duplicates_by_id(
                        docs=[doc for idx in idx_list for doc in dict_reranked_docs[idx]], sort=True
                    )
                    for idx_list in batch_idx_groups
                ]
                contexts = [format_docs(docs) for docs in list_reranked_docs]

                # 4. Run GPT
                configs = [
                    {
                        "q_comp": q_comp, "c_comp": c_comp,
                        "q_key": q_key, "c_key": c_key,
                        "idx_list": idx_list,
                        "context": context,
                        "ag_name": ag_name.split(',')[0]
                    } for context, idx_list in zip(contexts, batch_idx_groups)
                ]
                prompts = [prompt.format(**config) for config in configs]
                responses = self.assistant.model.batch(prompts)
                parsed_outputs = StrOutputParser().batch(responses)
                configs = [{**config, "response": response} for config, response in zip(configs, parsed_outputs)]

                if 'H' in q_key:
                    filter_seq_id_no = {
                        'heavy_seq_id_no': batch_idx_groups,
                        'light_seq_id_no': [comp_idxs for _ in range(len(batch_idx_groups))]
                        }
                else:
                    filter_seq_id_no = {
                        'light_seq_id_no': batch_idx_groups,
                        'heavy_seq_id_no': [comp_idxs for _ in range(len(batch_idx_groups))]
                        }

                df_out = self.parse_answers_to_df(parsed_outputs, filter_seq_id_no=filter_seq_id_no)
                dfs.append(df_out)
                raw_responses.extend(configs)

            # Parse response
            parsed_df = pd.concat(dfs)
            df_out = self._merge_names(parsed_df, h_key, l_key, state)
            df_out = self.clean_df(df_out, cols=self.cols)

            # Remove named entities
            df_named = state['ab_pair_named'][pair_key][self.required]
            mask = df_out[self.required].apply(tuple, axis=1).isin(df_named.apply(tuple, axis=1))
            df_out = df_out[~mask].reset_index(drop=True)

            result[pair_key] = df_out
            raw_result[pair_key] = raw_responses

        for pair_key in ['scFv', 'FC', 'MS']:
            df = self.convert_NA(state['ab_name'][pair_key], cols=['name'])
            cond1 = df['exclusion'] == False
            cond2 = state['unique_names'][pair_key]['seq_id_no'].isin(state['unique_names'][pair_key]['seq_id_no'])
            df_filtered = df[cond1 & ~cond2]

            df_p = pd.DataFrame({
                'name': df_filtered['name'],
                'heavy_seq_id_no': df_filtered['seq_id_no'],
                'light_seq_id_no': df_filtered['seq_id_no']
            })
            result[pair_key] = df_p

        if state['entities']['nanobody']:
            cond = state['ab_name']['VH']['seq_id_no'].isin(state['idx_dict'].get('NB', []))
            df = state['ab_name']['VH'][cond]
            df_p = pd.DataFrame({
                'name': df['name'],
                'heavy_seq_id_no': df['seq_id_no'],
                'light_seq_id_no': pd.NA
            })
            result['NB'] = df_p
        else:
            result['NB'] = self.empty_df()

        return {self.task: result, f"{self.task}_raw": raw_result}


class AbMergeNode(PatentQANode):
    def __init__(self):
        self.task = 'ab_merged'
        self.cols = {
            'heavy_seq_id_no': int,
            'light_seq_id_no': int,
            'name': str
        }
        self.required = ['heavy_seq_id_no', 'light_seq_id_no', 'name']

    def execute(self, state: QAState) -> QAState:
        result = {}
        for pair_key in ['VH_VL', 'HC_LC', 'scFv', 'FC', 'MS']:
            df_pair_named = state['ab_pair_named'][pair_key][self.required]
            if '_' in pair_key:
                df_pair_unnamed = state['ab_pair_unnamed'][pair_key]
                df_merged = pd.concat([df_pair_named, df_pair_unnamed])
            else:
                df_merged = df_pair_named

            df_out = df_merged.groupby(['heavy_seq_id_no', 'light_seq_id_no'])['name'].agg(lambda x: list(set(x.dropna())) if len(x.dropna()) > 0 else []).reset_index()

            if len(df_out) > 1:
                df_out = df_out.sort_values(by=['heavy_seq_id_no', 'light_seq_id_no']).reset_index(drop=True)

            result[pair_key] = df_out

        if state['entities']['nanobody']:
            pair_key = 'NB'
            df_pair_named = state['ab_pair_named'][pair_key].astype(str)
            df_pair_unnamed = state['ab_pair_unnamed'][pair_key][['heavy_seq_id_no', 'light_seq_id_no']].astype(str)

            df_merged = pd.merge(
                df_pair_named, df_pair_unnamed,
                how='outer', on=['heavy_seq_id_no', 'light_seq_id_no']
            )
            if 'name' not in df_merged:
                df_merged['name'] = pd.NA
            df_out = df_merged \
                .groupby(['heavy_seq_id_no'])['name'] \
                .agg(lambda x: list(set(x.dropna())) if len(x.dropna()) > 0 else []) \
                .reset_index()
            df_out['light_seq_id_no'] = pd.NA

            if len(df_out) > 1:
                df_out = df_out.sort_values(by=['heavy_seq_id_no']).reset_index(drop=True)
            result[pair_key] = df_out
        else:
            result['NB'] = self.empty_df()

        return {self.task: result}