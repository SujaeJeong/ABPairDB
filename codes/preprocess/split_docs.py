import os
import re
import uuid
import pandas as pd
import numpy as np
import sys

from collections import Counter
from bs4 import BeautifulSoup
from langgraph.graph import StateGraph, START, END
from langchain.docstore.document import Document
from collections import defaultdict
from itertools import chain

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
rag_dir = os.path.join(parent_dir, 'rag')

sys.path.append(parent_dir)
sys.path.append(rag_dir)

from state import DocState
from base import BaseNode
from .custom_splitter import HTMLCustomSplitter
from .script_converter import SubScriptConverter
from .table import build_table_preprocess_subgraph, ProcessTableChunkNode, TableMetadataNode

# Constants
ab_keys = ['VH','VL','HC','LC','scFv','MS','NB','nonAB']

ab_components = {
    "VH": "variable heavy chain domain",
    "VL": "variable light chain domain",
    "HC": "heavy chain",
    "LC": "light chain",
    "NB": "nanobody",
    "scFv": "single chain fragment variable",
    "MS": "Antibody Multimer",
    "FC": "Full-chain"
}

ab_complement = {
    "VH": "VL",
    "VL": "VH",
    "HC": "LC",
    "LC": "HC",
    "scFv": "scFv"
}

set_AA = 'ACDEFGHIKLMNPQRSTVWY '
list_AA3 = [
    'Ala','Cys','Asp','Glu','Phe','Gly','His','Ile','Lys',
    'Leu','Met','Asn','Pro','Gln','Arg','Ser','Thr','Val',
    'Trp','Tyr'
]
set_NT = 'ATGCU atgcu'

class LoadDocumentNode(BaseNode):
    """
    Split html using custom splitter
    """
    def __init__(self, **kwargs):
        self.name = "LoadDocumentNode"
        self.html_dir = kwargs.get('html')

        similarity_threshold = kwargs.get('similarity_threshold', 0.7)
        context_window = kwargs.get('context_window', 50)
        verbose=kwargs.get('verbose', False)
        print_level = kwargs.get('print_level', 1)
        self.converter = SubScriptConverter(
            context_window=context_window,
            similarity_threshold=similarity_threshold,
            verbose=verbose,
            print_level=print_level
        )
        self.ref_csv_path = kwargs.get("ref_csv_path", "")


    def get_title(self, keyword):
        ref_df = pd.read_csv(self.ref_csv_path)
        if 'B' in keyword:
            keyword = keyword.split('B')[0]
        cond = ref_df['Patent_ID'].str.contains(keyword)
        title = ref_df[cond]['GBReference_title'].iloc[0]

        return title


    def execute(self, state=DocState) -> DocState:
        content = self.converter.process_files(
            patent_id=state['patent_id'],
            input_dir=self.html_dir
        )
        title = self.get_title(state['patent_id'])

        return {
            "title": title,
            "full_html": content,
            }


class SplitDocumentNode(BaseNode):
    def __init__(self, **kwargs):
        self.name = "SplitDocumentNode"
        chunk_size = kwargs.get('chunk_size', 512)
        chunk_overlap = kwargs.get('chunk_overlap', 64)
        self.splitter = HTMLCustomSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )

    def is_small_single_col_table(self, soup, threshold=512):
        """
        Check if table satisfy following conditions:
        1. number of column <= 1
        2. Text length smaller than threshold
        3. has no index "TABLE" in table

        Parameters:
            table_tag (bs4.element.Tag): BeautifulSoup으로 파싱된 <table> 태그
            threshold (int): 텍스트 길이 기준 (default: 512)

        Returns:
            bool: 조건을 만족하면 True, 아니면 False
        """
        if isinstance(soup, str):
            soup = BeautifulSoup(soup, 'html.parser')

        # 1. column 수 확인
        tables = soup.find_all('table')
        num_cols = [int(table.get('cols', 0)) for table in tables]
        max_num_cols = max(num_cols)

        # 2. 텍스트 추출 및 조건 확인
        text = soup.get_text(strip=True)
        text_length = len(text)
        has_table_word = "TABLE" in text.upper()

        return max_num_cols <= 1 and text_length < threshold and not has_table_word

    def find_tables_to_del(self, tables):
        t_keys_to_del = []
        for t_key, t_dict in tables.items():
            if not self.is_small_single_col_table(t_dict['table_html']):
                t_keys_to_del.append(t_key)

        return t_keys_to_del

    def find_last_row(self, lines, table_html):

        words = table_html.text.split()[::-1]
        pattern = re.compile(rf"^[{set_NT}]+$")
        filtered_words = [word for word in words if not pattern.fullmatch(word)]

        pattern = re.compile(rf"^[{set_AA}]+$")
        filtered_words = [word for word in filtered_words if not pattern.fullmatch(word)]

        max_count = 0
        line_number_with_max = None
        line_with_max_keywords = ""

        for idx, line in enumerate(lines):
            count = sum(1 for word in filtered_words[:50] if word in line)
            if count >= max_count:
                max_count = count
                line_number_with_max = idx
                line_with_max_keywords = line

        return max_count, line_number_with_max, line_with_max_keywords

    def remove_lines(self, lines, t_key, i, j):
        if i > j:
            raise IndexError("Wrong row index")

        keyword_pos = lines[i].find('TABLE')
        lines[i] = lines[i][:keyword_pos] + t_key

        if i < j:
            for k in range(i+1, j+1):
                lines[k] = ''

        return lines


    def remove_tables(self, docs, tables_to_del):

        lines = docs.split('\n')
        for t_key, t_dict in tables_to_del.items():
            first_row = [idx for idx, line in enumerate(lines) if t_key in line]
            if len(first_row) == 0:
                if 'TABLE' in t_dict['index']:
                    first_row = [idx for idx, line in enumerate(lines) if re.search(rf"{t_dict['index']}\D", line)]
            if len(first_row) > 1:
                word_list = t_dict['summary'].title.split()
                num_words = []
                for idx in first_row:
                    num_words.append(len([word for word in word_list if word in lines[idx]]) / max(len(word_list), 1))
                if max(num_words) < 0.5:
                    continue
                first_row = [first_row[np.argmax(num_words).item()]]
            if len(first_row) != 1:
                continue
            first_row = first_row[0]
            _, last_row, _ = self.find_last_row(lines, t_dict['table_html'])

            if last_row - first_row > 20:
                for idx, line in enumerate(lines[first_row:last_row]):
                    if ('<h' in line) or ('<p>' in line):
                        last_row = idx + first_row - 1
                        break
                    if 'TABLE-US-' in line:
                        match = int(re.search(r'TABLE-US-(\d)+', line).group(1))
                        if match > int(t_key[-5:]):
                            last_row = idx + first_row -1
                            break
                    if ('\t' in lines[first_row]):
                        if (len(line) > 100) and ('\t' not in line):
                            last_row = idx + first_row - 1
                            break

            if last_row < first_row:
                for idx, line in enumerate(lines[first_row:]):
                    if ('<br' in line) or re.search(r'(\(\d+\)|\[\d+\])', line):
                        last_row = idx + first_row
                        break
            print(f'Removed {t_key}: {first_row} to {last_row}')
            lines = self.remove_lines(lines, t_key, first_row, last_row)

        lines = [line for line in lines if line != '']
        docs = '\n'.join(lines)

        return docs


    def execute(self, state=DocState) -> DocState:
        # Preprocess
        content = self.splitter.preprocess(state['full_html'], patent_id=state['patent_id'])
        t_keys_to_del = self.find_tables_to_del(state['tables'])
        tables_to_del = {k: v for k, v in state['tables'].items() if k in t_keys_to_del}
        content = self.remove_tables(content, tables_to_del)
        content = self.splitter._truncate_sequences(content)

        # Split chunk
        split_docs = self.splitter.split_text(content)
        split_docs = [
            doc for doc in split_docs if "Reference" not in doc.metadata.get("Heading 3", "")
        ]

        return {"split_docs": split_docs}


class TextMetadataNode(BaseNode):
    def __init__(self, **kwargs):
        pass

    def add_seq_id_no_metadata(self, document, seq_id_no_list):
        """
        enroll SEQ ID NO candidates in the metadata
        """

        pattern = re.compile(
            r"SEQ[\.\s]*ID[\.\s]*NO[sS:;\.\s]+(?P<indexes>\d+(?:\s*(?:\([^)]+\))?\s*(?:,|and|or|/|;|\+|&|to|-|\s){,3}\s*\d+)*)",
            re.IGNORECASE
        )
        text = document.page_content
        matches = re.findall(pattern, text)

        all_seq_ids = []
        if matches:
            for match in matches:
                match = re.sub(r'\s*\([^)]+\)', '', match)
                idxs = re.sub(r'(\d+)(,|\s)*to(,|\s)*(\d+)', r'\1to\4', match)
                idxs = re.sub(r'(\d+)(,|\s)*-(,|\s)*(\d+)(?!-)', r'\1to\4', idxs)
                idxs = re.sub(r',|and|or|;|/|\s+|-|\+|&|AND|OR', ' ', idxs)
                idxs = re.sub(r'\s+', ' ', idxs)

                idxs = idxs.split(' ')
                seq_ids = [int(seq_id_no) for seq_id_no in idxs if 'to' not in seq_id_no]
                split_to_set = lambda s: tuple(int(x) for x in s.split("to"))
                seq_ranges = []
                for seq_id_range in idxs:
                    if seq_id_range.count('to') == 1:
                        try:
                            rng = split_to_set(seq_id_range)
                            seq_ranges.append(rng)
                        except Exception:
                            continue   # 에러 발생하면 건너뜀
                for seq_range in seq_ranges:
                    start, end = seq_range
                    seq_ids.extend(list(range(start, end+1)))
                all_seq_ids.extend(seq_ids)

            all_seq_ids = list(set(all_seq_ids).intersection(set(seq_id_no_list)))
            if all_seq_ids:
                document.metadata['SEQ_ID_NO'] = all_seq_ids

        return document


    def combine_metadata(self, document, idx_dict):
        """
        Combine document metadata into page_content in forms of HTML

        Parameters:
            document (Document): Langchain Document
            meta_keys (list, optional): metadata key lists to combine

        Returns:
            combined_text (str): text with metadata and page_content
        """
        meta = document.metadata

        metadata_html = f"Chunk info:\n\nHeadings:\n"
        metadata_html += f"  Heading 3: {meta['Heading 3']}\n"
        metadata_html += f"  Heading 4: {meta['Heading 4']}\n"
        metadata_html += f"  Heading 5: {meta['Heading 5']}\n"

        page_content = "\nPage_content:\n" + document.page_content

        combined_text = metadata_html + page_content

        return combined_text

    def execute(self, state=DocState) -> DocState:
        # seq id no list to filter
        seq_id_no_list = []
        for key, val in state['idx_dict'].items():
            if key != 'short':
                seq_id_no_list += val

        split_docs = [
            self.add_seq_id_no_metadata(docs, seq_id_no_list)
            for docs in state['split_docs']
        ]

        meta_docs = [
            Document(
                page_content=self.combine_metadata(docs, state['idx_dict']),
                metadata=docs.metadata
            ) for docs in split_docs
        ]

        return {
            'split_docs': split_docs,
            'meta_docs': meta_docs
            }


class CheckEntityNode(BaseNode):
    """
    Check entities to consider
    """
    def __init__(self, **kwargs):
        threshold = kwargs.get('threshold', 20)

        self.name = "CheckEntityNode"
        self.word_dict = {
            "strain": ['serotype', 'strain', 'surface protein', 'subtype', 'clade'],
            "nanobody": ['nanobody', 'domain antibody', 'sdAb', 'VHH']
        }
        self.threshold = threshold

    def count_entity(self, html, entity):
        word_list = self.word_dict[entity]
        counter = Counter()
        for word in word_list:
            counter[word] = html.count(word)
        word_count = sum([count for count in counter.values()])

        return word_count


    def execute(self, state=DocState) -> DocState:
        # strain
        ask_strain = self.count_entity(state['full_html'], 'strain') > self.threshold

        # nanobody
        ask_nanobody = self.count_entity(state['full_html'], 'nanobody') > self.threshold

        entities = {'strain': ask_strain, 'nanobody': ask_nanobody}

        return {'entities': entities}


class CombineChunkNode(BaseNode):
    def __init__(self):
        self.table_list = []
        self.docs = []
        self.doc_idx = 0

    def add_docs(self, doc):
        header = f"<chunk data-index={self.doc_idx}>\n"
        doc.page_content = header + doc.page_content + '\n</chunk>'
        self.docs.append(doc)
        self.doc_idx += 1

    def execute(self, state):

        for doc in state['meta_docs']:
            # Add split tables
            if 'TABLE-US-' in doc.page_content:
                # HTML text chunk refering table
                self.add_docs(doc)
                table_ids = [table_id for table_id in state['tables'].keys()
                             if table_id in doc.page_content
                             if table_id not in self.table_list]
                for table_id in table_ids:
                    split_tables = [t for t in state['meta_tables'] if t.metadata['id'] == table_id]
                    for split_table in split_tables:
                        # Add HTML table
                        self.add_docs(split_table)
                    self.table_list.append(table_id)

            else:
                self.add_docs(doc)

        state['combined_docs'] = self.docs
        del state['tables']
        del state['split_tables']
        del state['split_docs']
        del state['meta_docs']
        del state['meta_tables']
        del state['full_html']

        return state


class GatherExpDocs(BaseNode):
    def __init__(self, **kwargs):
        self.name = "GatherExpDocs"
        chunk_size = kwargs.get('chunk_size', 512)
        chunk_overlap = kwargs.get('chunk_overlap', 64)
        self.splitter = HTMLCustomSplitter(
            chunk_size=chunk_size, chunk_overlap=chunk_overlap
        )
        self.table_merge_threshold = kwargs.get('table_merge_threshold', 50000)

    def filter_sequence(self, context):
        context = context.replace('\u200c', '')
        aa3 = [
            'Ala','Cys','Asp','Glu','Phe','Gly','His','Ile','Lys',
            'Leu','Met','Asn','Pro','Gln','Arg','Ser','Thr','Val',
            'Trp','Tyr','PRT', 'NT SEQ', 'AA SEQ', 'Xaa'
        ]
        # 반드시 re.escape 처리해서 메타문자 문제도 방지
        escaped_codes = '|'.join(map(re.escape, aa3))
        pattern = re.compile(
            rf'(?:{escaped_codes}|\d|\s){{30,}}',
            re.IGNORECASE
        )

        # 매치된 블록을 전부 ''로 대체
        cleaned_content = pattern.sub('', context)

        return cleaned_content

    def get_chunk_idx(self, doc):
        pattern = r'<chunk data-index=(\d+)>'
        match = re.search(pattern, doc.page_content)

        return int(match.group(1)) if match else 0

    def find_max_overlap(self, s1, s2, min_overlap=1):
        """
        s1의 suffix와 s2의 prefix가 겹치는 최대 길이(overlap)와 해당 substring 반환
        min_overlap: 최소 겹침 허용 길이 (기본값 1)
        """
        max_overlap = 0
        overlap_str = ""
        max_len = min(len(s1), len(s2))
        for i in range(min_overlap, max_len+1):
            if s1[-i:] == s2[:i]:
                max_overlap = i
                overlap_str = s1[-i:]
        return max_overlap, overlap_str

    def convert_h4_to_h5(self, text):
        # 콜론이 없는 <h4>만 변환: 첫 <h4>에 콜론 있으면 skip
        pattern = r'<h4>([^<]*)</h4><br/><h4>([^<]*)</h4>'
        def repl(match):
            h1 = match.group(1).strip()
            h2 = match.group(2).strip()
            return f'<h5>{h1}: {h2}</h5>'
        return re.sub(pattern, repl, text, flags=re.DOTALL)

    def merge_tables(self, table_docs, threshold=None):
        """
        같은 metadata['index']를 가진 테이블들을 threshold를 넘지 않을 경우 병합
        병합 시 find_max_overlap을 사용해 중복 부분 제거
        """
        threshold = threshold or self.table_merge_threshold
        grouped = defaultdict(list)
        for doc in table_docs:
            idx = doc.metadata.get('index')
            grouped[idx].append(doc)

        merged_list = []
        for idx, docs in grouped.items():
            if len(docs) == 1:
                merged_list.extend(docs)
                continue

            # 정렬된 순서대로 merge
            docs_sorted = sorted(docs, key=self.get_chunk_idx)
            merged_content = None
            for d in docs_sorted:
                content = d.page_content.replace('\n</chunk>', '').split('Page_content:\n')[1]
                if merged_content is None:
                    merged_content = content
                else:
                    overlap, _ = self.find_max_overlap(merged_content, content)
                    merged_content += content[overlap:]

            # threshold 비교
            if len(merged_content) <= threshold:
                new_doc = Document(merged_content)
                # 첫 doc의 메타데이터 복사
                new_doc.metadata = docs_sorted[0].metadata.copy()
                new_doc.metadata['merged_index'] = idx
                merged_list.append(new_doc)
            else:
                merged_list.extend(docs_sorted)

        return merged_list

    def get_exp_part(self, all_docs):

        exp_docs, exp_tables = [], []
        collect = False
        for doc in all_docs:
            if (re.search(r'(Example|Experiment)s?', doc.metadata.get('Heading 4', ''), re.IGNORECASE) \
                or re.search(r'(Example|Experiment)s?', doc.metadata.get('Heading 5', ''), re.IGNORECASE)):
                collect = True
            if re.search(r'claim', doc.metadata.get('Heading 3', ''), re.IGNORECASE) \
                or re.search(r'reference', doc.metadata.get('Heading 4', ''), re.IGNORECASE) \
                or re.search(r'SEQUENCE LISTING', doc.page_content):
                collect = False
            if collect:
                if 'TABLE-US' in doc.metadata.get('id', ''):
                    if doc.metadata.get('category', '') == 'experiment result':
                        exp_tables.append(doc)
                else:
                    exp_docs.append(doc)
        if not exp_docs:
            if (re.search(r'(METHODS)', doc.metadata.get('Heading 4', ''), re.IGNORECASE) \
                or re.search(r'(METHODS)', doc.metadata.get('Heading 5', ''), re.IGNORECASE)):
                collect = True
            if re.search(r'claim', doc.metadata.get('Heading 3', ''), re.IGNORECASE) \
                or re.search(r'reference', doc.metadata.get('Heading 4', ''), re.IGNORECASE) \
                or re.search(r'SEQUENCE LISTING', doc.page_content):
                collect = False
            if collect:
                if 'TABLE-US' in doc.metadata.get('id', ''):
                    if doc.metadata.get('category', '') == 'experiment result':
                        exp_tables.append(doc)
                else:
                    exp_docs.append(doc)

        exp_tables = self.merge_tables(exp_tables)

        # collect experiment part of content
        exp_content = ''
        for prev_doc, doc in zip(exp_docs[:-1], exp_docs[1:]):

            prev_content = prev_doc.page_content.replace('\n</chunk>', '').split('Page_content:\n')[1]
            page_content = doc.page_content.replace('\n</chunk>', '').split('Page_content:\n')[1]

            max_overlap, overlap_str = self.find_max_overlap(prev_content, page_content)

            if exp_content == '':
                exp_content += prev_content
            exp_content += page_content[max_overlap:]

        exp_content = self.convert_h4_to_h5(exp_content)
        exp_content = self.filter_sequence(exp_content)

        # Collect by heading
        exp_docs = []
        for split_content in exp_content.split('<h5>'):
            if '</h5' in split_content:
                heading, page_content = split_content.split('</h5>')
                doc = Document(page_content)
                doc.metadata['Heading 5'] = heading
                exp_docs.append(doc)
                for t_idx in re.findall(r'TABLE-US-\d{5}', page_content):
                    table_docs = [doc for doc in exp_tables if doc.metadata.get('id', '') == t_idx]
                    for table_doc in table_docs:
                        table_doc.metadata['Heading 5'] = heading
                        # exp_docs.append(table_doc)
            else:
                doc = Document(split_content)
                doc.metadata['Heading 5'] = ''
                exp_docs.append(doc)

        # generate experiment dictionary
        exp_dict = defaultdict(list)
        for doc in exp_docs:
            heading = doc.metadata.get('Heading 5')
            doc = self.add_seq_id_no_metadata(doc)
            exp_dict[heading].append(doc)

        # Table 할당하기
        table_idx_to_headings = defaultdict(set)
        table_id_to_idx = {
            doc.metadata.get('id'): doc.metadata.get('index', '')
            for doc in exp_tables
        }
        exp_table_idx = [a for a in table_id_to_idx.values() if a != '']

        table_index_pattern = r'\b(?:' + '|'.join(map(re.escape, exp_table_idx)) + r')\b'

        for key, docs in exp_dict.items():
            for doc in docs:
                # exp_table_idx 추출 (예: 정규표현식 사용)
                matches = re.findall(table_index_pattern, doc.page_content, re.IGNORECASE)
                for idx in matches:
                    table_idx_to_headings[idx.upper()].add(key)

        unique_table_idx = {idx for idx, keys in table_idx_to_headings.items() if len(keys) == 1}
        duplicated_table_idx = {idx for idx, keys in table_idx_to_headings.items() if len(keys) > 1}
        mentioned_idx = {
            key for key, val in table_id_to_idx.items()
            if val in unique_table_idx
        }
        unmentioned_idx = set(table_id_to_idx.keys()).difference(mentioned_idx)

        for t_idx in unique_table_idx:
            t_set = table_idx_to_headings[t_idx]
            heading = next(iter(t_set))
            table_docs = [doc for doc in exp_tables if doc.metadata.get('index', '') == t_idx]
            for doc in table_docs:
                doc.metadata['Heading 5'] = heading
                exp_dict[heading].append(doc)

        for t_id in (duplicated_table_idx | unmentioned_idx):
            table_docs = [doc for doc in exp_tables if doc.metadata.get('id', '') == t_id]
            for doc in table_docs:
                heading = doc.metadata.get('Heading 5', '')
                exp_dict[heading].append(doc)

        return exp_dict

    def add_seq_id_no_metadata(self, document):
        """
        enroll SEQ ID NO candidates in the metadata
        """

        pattern = re.compile(
            r"SEQ[\.\s]*ID[\.\s]*NO[sS:;\.\s]+(?P<indexes>\d+(?:\s*(?:\([^)]+\))?\s*(?:,|and|or|/|;|\+|&|to|-|\s){,3}\s*\d+)*)",
            re.IGNORECASE
        )
        text = document.page_content
        matches = re.findall(pattern, text)

        all_seq_ids = []
        if matches:
            for match in matches:
                match = re.sub(r'\s*\([^)]+\)', '', match)
                idxs = re.sub(r'(\d+)(,|\s)*to(,|\s)*(\d+)', r'\1to\4', match)
                idxs = re.sub(r'(\d+)(,|\s)*-(,|\s)*(\d+)(?!-)', r'\1to\4', idxs)
                idxs = re.sub(r',|and|or|;|/|\s+|-|\+|&|AND|OR', ' ', idxs)
                idxs = re.sub(r'\s+', ' ', idxs)

                idxs = idxs.split(' ')
                seq_ids = [int(seq_id_no) for seq_id_no in idxs if 'to' not in seq_id_no]
                split_to_set = lambda s: tuple(int(x) for x in s.split("to"))
                seq_ranges = []
                for seq_id_range in idxs:
                    if seq_id_range.count('to') == 1:
                        try:
                            rng = split_to_set(seq_id_range)
                            seq_ranges.append(rng)
                        except Exception:
                            continue   # 에러 발생하면 건너뜀
                for seq_range in seq_ranges:
                    start, end = seq_range
                    seq_ids.extend(list(range(start, end+1)))
                all_seq_ids.extend(seq_ids)

            all_seq_ids = list(set(all_seq_ids).intersection(set(self.all_idx_list)))
            if all_seq_ids:
                document.metadata['SEQ_ID_NO'] = all_seq_ids

        return document


    def filter_exps(self, exp_split_dict):
        exp_keywords = [
            'KD', 'Dissociation constant', 'K<sub>D</sub>', 'K_D',
            'IC50', "50% inhibition", 'IC<sub>50</sub>', 'IC_50',  'inhibition concentration',
            'EC50', 'EC_50', 'EC<sub>50</sub>',
            'ka', 'kd', 'k_on', 'k_off', 'off-rate',
            't½', 'T1/2',
            'binding affinity', 'binding kinetics', "binding activity", "binding constant", "affinity value"]
        exp_p = r'\b(?:' + '|'.join(map(re.escape, exp_keywords)) + r')\b'

        filtered_dict = {}
        for heading, docs in exp_split_dict.items():
            contain_ba = any(re.search(exp_p, doc.page_content, re.IGNORECASE) for doc in docs)

            if contain_ba:
                filtered_dict[heading] = docs

        return filtered_dict


    def execute(self, state):

        all_idx_list = [val for key, val in state['idx_dict'].items() if key in ab_components]
        self.all_idx_list = set(chain.from_iterable(all_idx_list))
        exp_dict = self.get_exp_part(state['combined_docs'])

        return {'exp_dict': exp_dict}


def build_combine_chunks_subgraph(config):
    # Define graph
    workflow = StateGraph(DocState)

    # Define nodes
    text_metadata_node = TextMetadataNode()
    process_table_chunk_node = ProcessTableChunkNode()
    table_metadata_node = TableMetadataNode()
    combine_chunk_node = CombineChunkNode()
    check_entity_node = CheckEntityNode(**config['check_entity'])

    # Set nodes
    workflow.add_node("text_metadata", text_metadata_node)
    workflow.add_node("process_table_chunk", process_table_chunk_node)
    workflow.add_node('table_metadata', table_metadata_node)
    workflow.add_node('combine_chunk', combine_chunk_node)
    workflow.add_node('check_entity', check_entity_node)

    # Set edges
    workflow.add_edge(START, 'text_metadata')
    workflow.add_edge('text_metadata', 'process_table_chunk')
    workflow.add_edge('process_table_chunk', 'table_metadata')
    workflow.add_edge('table_metadata', 'combine_chunk')
    workflow.add_edge('combine_chunk', 'check_entity')
    workflow.add_edge('check_entity', END)

    # Compile graph
    subgraph = workflow.compile()

    return subgraph


def build_document_proprecessing_graph(config):

    graph_builder = StateGraph(DocState)

    load_doc_node = LoadDocumentNode(
        ref_csv_path=config['io']['ref_csv_path'],
        html=config['io']['html'],
        **config['preprocess']['load_document'])
    subgraph_preprocess_table = build_table_preprocess_subgraph(config=config)
    split_doc_node = SplitDocumentNode(
        html=config['io']['html'],
        **config['preprocess']['split_docs'])
    subgraph_combine_chunks = build_combine_chunks_subgraph(config=config['preprocess'])

    graph_builder.add_node("load_documents", load_doc_node)
    graph_builder.add_node("table_preprocess", subgraph_preprocess_table)
    graph_builder.add_node("split_document", split_doc_node)
    graph_builder.add_node("combine_chunks", subgraph_combine_chunks)

    graph_builder.add_edge(START, 'load_documents')
    graph_builder.add_edge('load_documents', 'table_preprocess')
    graph_builder.add_edge('table_preprocess', 'split_document')
    graph_builder.add_edge('split_document', 'combine_chunks')
    graph_builder.add_edge('combine_chunks', END)

    graph = graph_builder.compile()

    return graph
