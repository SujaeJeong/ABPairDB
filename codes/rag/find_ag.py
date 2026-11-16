import itertools
import networkx as nx

from typing import Callable
import numpy as np
import re
import json
import os
from typing import Callable
import pandas as pd
from sklearn.cluster import DBSCAN
from functools import partial
from langchain_core.documents import Document

from langchain_community.vectorstores.utils import maximal_marginal_relevance
from langchain_core.output_parsers import StrOutputParser, JsonOutputParser
from langchain_core.runnables import RunnablePassthrough

from ..base import BaseNode
from ..state import QAState
from .utils import format_docs, remove_duplicates_by_id


class PatentQANode(BaseNode):
    def __init__(self, assistant, verbose=False, **kwargs):
        self.name = self.__class__.__name__
        self.verbose = verbose
        self.assistant = assistant

    def empty_df(self):
        return pd.DataFrame(columns=self.cols)

    def parse_json(self, text, pattern=r'```(?:json)?\n(.*?)```'):
        """
        Parse Json object from the GPT output.
        """
        # Strip <think>...</think> blocks (Qwen3 thinking mode leak)
        text = re.sub(r'<think>.*?</think>', '', text, flags=re.DOTALL).strip()

        matches = list(re.finditer(pattern, text, re.DOTALL | re.IGNORECASE))
        if matches:
            def score_match(match):
                content = match.group(1)
                return sum(1 for col in self.required if f'"{col}"' in content)
            best_match = max(matches, key=score_match)
            try:
                return json.loads(best_match.group(1))
            except (json.JSONDecodeError, AttributeError):
                pass

        # Fallback: raw JSON or bare {...} block (no markdown code fence)
        try:
            return json.loads(text.strip())
        except json.JSONDecodeError:
            pass
        raw_match = re.search(r'\{.*\}', text, re.DOTALL)
        if raw_match:
            try:
                return json.loads(raw_match.group())
            except json.JSONDecodeError:
                pass
        return None


    def parse_json_to_df(self, text, cols=None, pattern=r'```(?:json)?\n(.*?)```', filter=True, filter_seq_id_no=None):
        """
        Parse string to json, json to pandas DataFrame.
        """
        data = self.parse_json(text, pattern=pattern)
        if data is None:
            return self.empty_df()
        if isinstance(data, dict):
            df = pd.DataFrame([data])
        elif isinstance(data, list):
            df = pd.DataFrame(data)
        else:
            return self.empty_df()

        if filter:
            df = self.clean_df(df, cols=cols, filter_seq_id_no=filter_seq_id_no)

        return df

    def parse_answers_to_df(self, answer, cols=None, pattern=r'```(?:json)?\n(.*?)```', filter=True, filter_seq_id_no=None):
        """
        Parse the answer from the model and convert it to a DataFrame.
        This method handles both single string answers and lists of answers (batch responses).
        It extracts JSON data from the answer using a regex pattern and converts it to a DataFrame.
        It also filters the DataFrame based on required columns and optional sequence ID numbers.

        Parameters:
            - answer (str or list): The answer from the model, which can be a single string or a list of strings.
            - cols (dict): Column names and their corresponding data types.
            - pattern (str): Regex pattern to extract JSON from the answer.
            - filter (bool): Whether to filter the DataFrame based on required columns.
            - filter_seq_id_no (dict): Dictionary to filter by specific sequence IDs.
        Returns:
            - pd.DataFrame: The final DataFrame after parsing and filtering.
        """
        if isinstance(answer, list) and len(answer) > 0 and isinstance(answer[0], str):
            if filter_seq_id_no:
                filter_list = [dict(zip(filter_seq_id_no.keys(), values)) for values in zip(*filter_seq_id_no.values())]
                dfs = [
                    self.parse_json_to_df(a, cols=cols, pattern=pattern, filter=filter, filter_seq_id_no=f)
                    for a, f in zip(answer, filter_list)
                ]
            else:
                dfs = [
                    self.parse_json_to_df(a, cols=cols, pattern=pattern, filter=filter)
                    for a in answer
                ]
            final_df = pd.concat(dfs, ignore_index=True)
        elif isinstance(answer, str):
            final_df = self.parse_json_to_df(answer, cols=cols, pattern=pattern, filter=filter, filter_seq_id_no=filter_seq_id_no)
        elif answer is None:
            final_df = self.empty_df()
        else:
            raise ValueError("Unsupported type for 'answer'. Expected str or list of str.")

        return final_df


    def convert_dtype(self, df, cols):
        """
        Convert Dataframe dtype with predefined type.
        Extract Numbers from the answer.

        Parameters:
            df (pd.DataFrame): Raw DataFrame
            cols (Dict): column name to dtype

        Returns:
            pd.DataFrame: Revised DataFrame
        """

        def safe_cast(value, target_type):
            """
            if dtype is int, extract only integer part.
            for other dtypes, convert dtype to defined types.
            If failed, convert answer to np.nan
            """
            # bool must remain a JSON boolean; bool("false") would be True.
            if target_type == bool:
                if isinstance(value, (bool, np.bool_)):
                    return bool(value)
                text = str(value).strip().lower()
                if text == 'true':
                    return True
                if text == 'false':
                    return False
                return pd.NA

            # int 처리
            if target_type == int:
                text = str(value).strip()
                match = re.search(r'-?\d+', text)
                if match:
                    return int(match.group())
                else:
                    return pd.NA
            else:
                try:
                    if isinstance(value, target_type):
                        return value
                    return target_type(value)
                except (ValueError, TypeError):
                    return pd.NA

        for col, dtype in cols.items():
            if col not in df.columns:
                continue
            df[col] = df[col].apply(lambda x: safe_cast(x, dtype))

        return df

    def convert_NA(self, df, cols=None):
        """
        Convert NA like answers to pd.NA in the DataFrame
        """
        na_list = ['null', '', 'nan', 'None', 'N/A', 'none']
        if cols:
            subset_df = df[cols].replace(na_list, pd.NA)
            df[cols] = subset_df
            return df
        else:
            return df.replace(na_list, pd.NA)

    def clean_df(self, df, cols=None, filter_seq_id_no=None):
        """
        Filter DataFrame based on required columns, convert dtypes, and filter by sequence ID numbers.
        This method performs the following steps:
        1. Convert NA-like values to pd.NA.
        2. Filter the DataFrame based on required columns.
        3. Convert the DataFrame to the specified dtypes.
        4. Drop rows with NA in required columns.
        5. Drop duplicates based on required columns.
        6. Filter by sequence ID numbers if provided.

        Parameters:
            df (pd.DataFrame): The DataFrame to filter.
            cols (dict): Column names and their corresponding data types.
            filter_seq_id_no (dict): Dictionary to filter by specific sequence IDs.
        Returns:
            pd.DataFrame: The filtered DataFrame.
        """
        # 0. If DataFrame is empty, return an empty DataFrame
        if df.empty:
            return self.empty_df()

        # 1. If no columns are provided, use the required columns
        if cols is None:
            cols = {key: self.cols[key] for key in self.required if key in df.columns}

        # 2. Convert NA-like values to pd.NA
        current_required = list(set(cols.keys()).intersection(df.columns))

        df = self.convert_NA(df, cols=current_required)
        df = df.dropna(subset=current_required)

        df = self.convert_dtype(df, cols=cols)
        df = df.dropna(subset=current_required)
        df = df.drop_duplicates(subset=current_required)

        # 3. Filter by sequence ID numbers if provided
        # if filter_seq_id_no and not df.empty:
        #     for key, idx_list in filter_seq_id_no.items():
        #         df = df[df[key].isin(idx_list)]
        if filter_seq_id_no and not df.empty:
            for key, idx_list in filter_seq_id_no.items():
                df = df[df[key].astype(str).str.lower().isin([str(x).lower() for x in idx_list])]

        return df

    def load_examples(self):
        """
        Load examples for few-shot learning
        """
        input_dir = os.path.join(self.example_dir, self.task)
        examples = [a[:-5] for a in os.listdir(input_dir) if 'txt' in a]
        examples.sort()

        example_prompt = "---\n# Examples\n"
        for example in examples:
            context_path = os.path.join(input_dir, f'{example}.txt')
            with open(context_path, 'r') as rf:
                example_prompt += "\n\n" + rf.read()

        return {"example": example_prompt}


    def multi_query_retrieve(
        self,
        queries: list[str],
        filter_fn: Callable=None,
        filter_fn2: Callable=None,
        lambda_mult=0.75,
    ):
        """
        Retrieve based on multiple queries, rank documents, MMR, and remove duplicates.
        This method retrieves documents from the vector store, applies a filter function if provided,
        and then applies Maximal Marginal Relevance (MMR) to select the top documents.
        It also removes duplicates based on a specified key (default is 'id').

        Parameters:
            queries (List[str]): List of queries to retrieve documents.
            filter_fn (Callable, optional): Function to filter documents before MMR.
            filter_fn2 (Callable, optional): Secondary function to filter documents if the first returns no results.
            If provided, this function is applied to the documents after the first filter.
            lambda_mult (float): Lambda multiplier for MMR.
        Returns:
            List[Document]: List of documents after MMR and filtering.
        """

        all_docs = list(self.assistant.vectorstore.docstore._dict.values())
        filtered_docs = [doc for doc in all_docs if filter_fn(doc)]
        if len(filtered_docs) == 0 and filter_fn2:
            filtered_docs = [doc for doc in all_docs if filter_fn2(doc)]
        if len(filtered_docs) == 0:
            return []

        query = '\nOR '.join(queries)
        reranked_docs = self.assistant.reranker.base_compressor.compress_documents(
            documents=filtered_docs, query=query
        )
        reranked_texts = [doc.page_content for doc in reranked_docs]
        embeddings = self.assistant.vectorstore._embed_documents(reranked_texts)
        query_embeddings = self.assistant.vectorstore._embed_query(query)

        mmr_indices = maximal_marginal_relevance(
            np.array([query_embeddings], dtype=np.float32),
            embeddings,
            k=self.mmr_out, lambda_mult=lambda_mult
        )
        mmr_out_docs = [reranked_docs[i] for i in mmr_indices]

        return mmr_out_docs

    def create_antigen_keywords(self, df):
        """
        Write all characteristics related to antigen in a single line

        Parameters:
            df (pd.DataFrame): Antigen DataFrame

        Returns:
            keywords (List): List of antigen keyword line.
        """
        keywords = []
        cols = ['name', 'abbreviation', 'organism', 'seq_id_no', 'state', 'oligomer', 'subtype', 'strain', 'mutation']
        for ag_idx, data in df.iterrows():
            data = data.dropna()
            parts = [f'AG_IDX: {ag_idx}']

            # Name, organism, abbreviation
            attrs = {col: data[col] for col in cols if col in data}
            for key, val in attrs.items():
                if key == 'seq_id_no':
                    key = 'seq id no'
                parts.append(f"{key.upper()}: {val}")
            parts.append(f'END AG_IDX: {ag_idx}')

            keyword_str = " | ".join(parts)
            keywords.append(keyword_str)
        return keywords

    def flexible_split(self, numbers: list) -> list:
        """
        Splits a list into smaller groups aiming for a maximum group size,
        with flexibility for near-equal splitting.

        Args:
            numbers (List[int]): The list of items to split.
            max_group_size (int): The ideal maximum size for each group.

        Returns:
            List[List[int]]: A list of smaller groups.
        """
        n = len(numbers)

        if n <= self.max_group_size:
            # If the list is already smaller than the max size, return it as one group
            return [numbers]

        # Calculate the number of groups needed
        num_groups = max(1, (n + self.max_group_size - 1) // self.max_group_size)

        # Adjust group sizes to make them as equal as possible
        group_size = n // num_groups
        remainder = n % num_groups

        groups = []
        start = 0

        for i in range(num_groups):
            extra = 1 if i >= (num_groups - remainder) else 0
            end = start + group_size + extra
            groups.append(numbers[start:end])
            start = end

        return groups

    def cluster_numbers_dbscan(self, numbers, eps=10):
        # DBSCAN은 2차원 이상을 필요로 하므로 reshape
        numbers = np.array(numbers).reshape(-1, 1)

        # DBSCAN 적용
        clustering = DBSCAN(eps=eps, min_samples=1).fit(numbers)

        # 클러스터별로 숫자를 그룹화
        clusters = {}
        for number, label in zip(numbers, clustering.labels_):
            if label not in clusters:
                clusters[label] = []
            clusters[label].append(int(number))

        return list(clusters.values())


    def build_graph_from_chunks(self, docs, all_idx_list):
        """
        Construct graph only from seq_ids that are in all_idx_list.
        """
        G = nx.Graph()

        for doc in docs:
            seq_ids = [sid for sid in doc.metadata.get('SEQ_ID_NO', []) if sid in all_idx_list]
            for sid in seq_ids:
                G.add_node(sid)
            for a, b in itertools.combinations(seq_ids, 2):
                G.add_edge(a, b)

        return G

    def cluster_with_order_preserved(self, graph, max_group_size):
        """
        Cluster the graph while preserving the order of nodes.
        This method finds connected components in the graph and groups nodes into clusters
        of a specified maximum size. If the last cluster has fewer nodes than the maximum size,
        it is still included as a cluster.
        Args:
            graph (nx.Graph): The input graph.
            max_group_size (int): The maximum size of each cluster.
        Returns:
            List[List[int]]: A list of clusters, where each cluster is a list of node IDs.
        """
        clusters = []
        for component in nx.connected_components(graph):
            sorted_nodes = sorted(component)
            current_cluster = []
            for node in sorted_nodes:
                current_cluster.append(node)
                if len(current_cluster) == max_group_size:
                    clusters.append(current_cluster)
                    current_cluster = []
            if current_cluster:
                clusters.append(current_cluster)
        return clusters

    def split_list(self, all_idx_list):
        chunks = self.assistant.vectorstore.docstore._dict.values()
        G = self.build_graph_from_chunks(chunks, all_idx_list)

        clusters = self.cluster_with_order_preserved(G, self.max_group_size)

        included = [idx for cluster in clusters for idx in cluster]
        missing = [idx for idx in all_idx_list if idx not in included]

        for i in range(0, len(missing), self.max_group_size):
            clusters.append(missing[i: i+self.max_group_size])

        return clusters

    def get_chunk_idx(self, doc) -> int:
        """
        Parse chunk index
        """
        pattern = r'<chunk data-index=(\d+)>'
        match = re.search(pattern, doc.page_content)
        return int(match.group(1))

    def sort_docs_by_chunk_index(self, docs:list) -> list:
        """
        sort documents by chunk index order
        """
        return sorted(docs, key=lambda doc: self.get_chunk_idx(doc))

    def remove_duplicates_by_id(self, docs, sort=False):
        seen_indexes = set()
        unique_docs = []

        for doc in docs:
            chunk_idx = self.get_chunk_idx(doc)
            if chunk_idx not in seen_indexes:
                seen_indexes.add(chunk_idx)
                unique_docs.append(doc)
        if sort:
            unique_docs = self.sort_docs_by_chunk_index(unique_docs)

        return unique_docs

    def dict_to_string(self, d):
        return ", ".join(f"'{key}': '{value}'" for key, value in d.items())


class SummaryNode(PatentQANode):
    def __init__(self, assistant, **kwargs):
        self.task = "summary"
        self.assistant = assistant
        self.cols = {'summary': dict}
        self.required = ['summary']
        assistant.set_retriever(**kwargs)

    def execute(self, state: QAState) -> QAState:

        queries = [
            'Problems that researchers tried to solve',
            'New inventions (antibodies) that researchers developed',
            'New inventions (antibodies) that researchers claims',
            'Specific antigens that researchers targeted for antibody development',
            'How the new inventions (antibodies) solve the problem',
            'Purpose of the antibody',
            'Experimental validation provided in the patent that demonstrates the functionality of the new antibodies.'
        ]
        query = '\nOR '.join(queries)

        prompt = self.assistant.create_prompt(task=self.task)
        retrieved_docs = self.assistant.retriever.invoke(query)
        context = format_docs(retrieved_docs)
        prompt = prompt.format(context=context)
        response = self.assistant.model.invoke(prompt)
        parsed_output = StrOutputParser().invoke(response)
        answer = self.parse_json(parsed_output)

        return {"summary": answer}


class FindAgNode(PatentQANode):
    """
    Node to find antigens in the patent.
    This node retrieves antigens based on the summary provided by the SummaryNode.
    It uses the retriever to find relevant documents and then processes them to extract antigen information.
    """
    def __init__(self, assistant, **kwargs):
        self.task = "ag"
        self.cols = {
            "name": str,
            "abbreviation": str,
            "organism": str
        }
        self.required = ['name', 'organism']
        assistant.set_retriever(**kwargs)
        self.assistant = assistant

    def create_retreiver_query(self, ag_summary) -> str:
        """
        Create a query for the retriever based on the summary.
        This query will be used to retrieve documents related to antigens.
        """
        query = "Specific antigens that researchers targeted for antibody development\n"

        if isinstance(ag_summary, list):
            ag_list = ag_summary
            query += '\nOR '.join([self.dict_to_string(ag_dict) for ag_dict in ag_list])
        elif isinstance(ag_summary, dict):
            query += self.dict_to_string(ag_summary)
        elif isinstance(ag_summary, str):
            query += ag_summary
        else:
            raise ValueError("Unsupported type for 'Antigen' in summary. Expected list, dict, or str.")
        return query


    def execute(self, state: QAState) -> QAState:

        query = self.create_retreiver_query(state['summary']['Antigen'])
        retrieved_docs = self.assistant.retriever.invoke(query)
        context = format_docs(retrieved_docs)

        prompt = self.assistant.create_prompt(task=self.task).partial(summary=state['summary'])
        prompt = prompt.format(context=context)
        response = self.assistant.model.invoke(prompt)
        parsed_output = StrOutputParser().invoke(response)

        df = self.parse_answers_to_df(parsed_output, filter=False)
        df = self.convert_NA(df)
        df = pd.concat([df, self.empty_df()])

        return {self.task: df}


class AgDetailNode(PatentQANode):
    def __init__(self, assistant, **kwargs):

        self.task = "ag_detail"
        self.cols = {
            'name': str,
            'organism': str,
            'seq_id_no': int,
            'state': str,
            'mutation': str,
            'oligomer': str,
            'region': str
        }
        self.required = ['name', 'organism', 'seq_id_no']

        top_n = kwargs.get('top_n', 8)
        search_type=kwargs.get('search_type', 'similarity')
        search_kwargs=kwargs.get('search_kwargs', {'k': 16, 'fetch_k': 32})
        self.max_group_size = kwargs.get('max_group_size', 4)
        self.batch_size = kwargs.get('batch_size', 8)
        self.mmr_out = kwargs.get('mmr_out', 5)

        self.assistant = assistant
        self.assistant.set_retriever(search_type=search_type, search_kwargs=search_kwargs)
        self.assistant.set_reranker(top_n=top_n)


    def create_retriever_keywords(self, ag_keywords, idx):
        query = []
        ag_keywords = [f"{ag_keyword}, 'SEQ ID NO': {idx}" if idx != 0 else ag_keyword for ag_keyword in ag_keywords]

        for ag_keyword in ag_keywords:
            query.append(ag_keyword)
            query.append(f"{ag_keyword},'state': ?,")
            query.append(f"{ag_keyword}, 'mutation': ?")
            query.append(f"{ag_keyword}, 'oligomer (e.g., dimer, trimer)': ?")

            if self.strain != "":
                query.append(f"{ag_keyword} 'strain': ?")
                query.append(f"{ag_keyword} 'subtype': ?")

        return query


    def check_strain(self, state):
        if state['entities']['strain']:
            prompt_strain = self.assistant.create_prompt(task='strain')
            prompt_strain = prompt_strain.format()
            self.cols['strain'] = str
            self.cols['subtype'] = str
        else:
            prompt_strain = ""

        self.strain = prompt_strain

        return None

    def _idx_in_doc(self, doc, idx):
        """
        Check if the idx is in the document metadata.
        """
        return idx in doc.metadata.get('SEQ_ID_NO', [])

    def _idx_in_doc_pattern(self, doc, idx):
        """
        Check if the idx is in the document page content using regex.
        """
        pattern = re.compile(rf"(?!\d){re.escape(str(idx))}(?!\d)")
        return bool(pattern.search(doc.page_content))

    def execute(self, state: QAState) -> QAState:

        self.check_strain(state)
        prompt = self.assistant.create_prompt(task=self.task)
        ag_keywords = self.create_antigen_keywords(state['ag'])

        # 1. Cluster idx_list
        all_idx_list = state['idx_dict'].get('nonAB', [])
        if not all_idx_list:
            df_merged = pd.merge(
                self.empty_df(), state['ag'], how='right', on=['name', 'organism']
            )
            df_merged['seq_id_no'] = None
            return { self.task: df_merged }

        # 2. Retrieve and rerank all chunks by corresponding SEQ ID NO
        all_responses = []
        raw_responses = []
        idx_groups = self.split_list(all_idx_list)

        for i in range(0, len(idx_groups), self.batch_size):
            batch_idx_groups = idx_groups[i: i+self.batch_size]
            batch_idx_list = list(itertools.chain.from_iterable(batch_idx_groups))

            list_queries = [self.create_retriever_keywords(ag_keywords, idx) for idx in batch_idx_list]

            dict_reranked_docs = {
                idx: self.multi_query_retrieve(
                    queries,
                    filter_fn=partial(self._idx_in_doc, idx=idx),
                    filter_fn2=partial(self._idx_in_doc_pattern, idx=idx))
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
                    "context": context,
                    "idx_list": idx_list,
                    "ag_keyword": '\n'.join(str(ag_keywords)),
                    "strain": self.strain
                } for context, idx_list in zip(contexts, batch_idx_groups)
            ]

            prompts = [prompt.format(**config) for config in configs]
            responses = self.assistant.model.batch(prompts)
            parsed_output = StrOutputParser().batch(responses)

            filter_seq_id_no = {'seq_id_no': batch_idx_groups}
            df = self.parse_answers_to_df(parsed_output, filter_seq_id_no=filter_seq_id_no)
            all_responses.append(df)
            configs = [{**config, "response": response} for config, response in zip(configs, parsed_output)]
            raw_responses.extend(configs)

        df_out = pd.concat(all_responses, ignore_index=True)
        df_out = self.convert_dtype(df_out, cols=self.cols)
        if df_out.empty:
            df_merged = pd.merge(
                df_out, state['ag'], how='right', on=["name", "organism"]
            )
        else:
            df_merged = pd.merge(
                df_out, state['ag'], how='left', on=["name", "organism"]
            )

        return {self.task: df_merged, f"{self.task}_raw": raw_responses}


class AgMainNode(PatentQANode):
    def __init__(self, assistant, **kwargs):
        self.task = "ag_main"
        self.cols = {
            'name': str,
            'organism': str,
            'seq_id_no': int,
            'abbreviation': str
        }
        self.required = ['name', 'organism']
        assistant.set_retriever(**kwargs)
        self.assistant = assistant

    def create_ag_prompt(self, df_ag):
        ag_keyword = []
        for ag_idx, data in df_ag.iterrows():
            data = data.dropna()
            parts = [f"{ag_idx}. "]
            for key, val in data.to_dict().items():
                if key == 'name':
                    parts.append(f"Name: {val}")
                elif key == 'organism':
                    parts.append(f"Organism: {val}")
                elif key == 'abbreviation':
                    parts.append(f"Abbreviation: {val}")
                elif key == 'seq_id_no':
                    parts.append(f"**SEQ_ID_NO: {int(val)}**")
                else:
                    parts.append(f"{key.capitalize()}: {val}")
            ag_keyword.append(", ".join(parts))

        ag_keyword = '\n'.join(ag_keyword)

        return ag_keyword

    def execute(self, state: QAState) -> QAState:

        prompt = self.assistant.create_prompt(task=self.task)
        df_ag = pd.merge(state['ag'], state['ag_detail'], on=['name', 'organism', 'abbreviation'], how='outer')
        ag_keyword = self.create_ag_prompt(df_ag)

        question = f"""Read the abstract, summary, and claim part of the patent again.
        Among the antigen candidates, which are the major targets of the antibodies that patent claims?

        # Antigen candidates
        {ag_keyword}
        """
        parser = StrOutputParser()
        prompt = prompt.partial(
            num_ag=len(state['ag_detail']), ag_detail=ag_keyword
        )
        chain = (
            {
                "context": self.assistant.reranker | format_docs,
                "question": RunnablePassthrough()
            }
            | prompt
            | self.assistant.model
            | parser
        )

        response = chain.invoke(question)
        df = self.parse_answers_to_df(response)

        return {self.task: df}


class AgAccessionNode(PatentQANode):
    def __init__(self, assistant, **kwargs):
        self.task = "ag_accession"
        self.cols = {
            'name': str,
            'organism': str,
            'database': str,
            'accession_number': str
        }
        self.required = ['name', 'organism', 'database', 'accession_number']
        self.max_group_size = kwargs.get('max_group_size', 3)
        assistant.set_retriever(**kwargs)
        assistant.set_reranker(**kwargs)
        self.assistant = assistant


    def execute(self, state: QAState) -> QAState:

        df_no_id = state['ag_detail'][state['ag_detail']['seq_id_no'].isna()]
        if len(df_no_id) == 0:
            df = self.empty_df()
        else:
            prompt = self.assistant.create_prompt(task=self.task)
            keywords = list(df_no_id.T.to_dict().values())
            keyword_groups = self.flexible_split(keywords)

            all_dfs = []
            for keyword_group in keyword_groups:
                queries = [f"{keyword} database" for keyword in keyword_group]
                reranked_docs = [self.assistant.reranker.invoke(query) for query in queries]
                contexts = [format_docs(docs) for docs in reranked_docs]

                config = {
                    "antigen": '\n'.join([str(keyword) for keyword in keyword_group]),
                    "context": '\n\n===\n\n'.join(contexts)
                }

                group_prompt = prompt.format(**config)
                response = self.assistant.model.invoke(group_prompt)
                group_df = self.parse_answers_to_df(response.content, filter=False)
                all_dfs.append(group_df)

            df = pd.concat(all_dfs, ignore_index=True) if all_dfs else self.empty_df()

            if len(df) == 0:
                df = self.empty_df()

        return {'ag_accession': df}

