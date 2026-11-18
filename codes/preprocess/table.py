# Langchain Module
from langchain_openai import ChatOpenAI
from langchain_core.runnables import chain
from langgraph.graph import StateGraph, START, END
from langchain_core.prompts import PromptTemplate, load_prompt
from langchain.docstore.document import Document

import itertools
import numpy as np
import pandas as pd
import re
import os
import random
import uuid
from bs4 import BeautifulSoup  # type: ignore

# Custom Module
from ..state import DocState, TableSummary, AbNameLocation
from ..base import BaseNode
from ..rag.utils import create_message, truncate_sequences
from .custom_splitter import HTMLCustomSplitter


# Constants
set_AA = 'ACDEFGHIKLMNPQRSTVWY '
set_NT = 'ATGCU atgcu'

ab_components = {
    "VH": "variable heavy chain domain",
    "VL": "variable light chain domain",
    "HC": "heavy chain",
    "LC": "light chain",
    "NB": "nanobody",
    "scFv": "single chain fragment variable",
    "MS": "Antibody Multimer",
    "nonAB": "Proteins"
}

ab_complement = {
    "VH": "VL",
    "VL": "VH",
    "HC": "LC",
    "LC": "HC",
    "scFv": "scFv"
}

ab_keys = ['VH', 'VL', 'HC', 'LC', 'scFv', 'MS', 'NB', 'nonAB']
ab_type_dict = {0: 'VH', 1: 'VL', 2: 'HC', 3: 'LC', 4: 'scFv', 5: 'MS', 6: 'NB', 7: 'nonAB'}


class TableCrawlNode(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "TableCrawlNode"

    def convert_docbook_table_to_html(self, soup) -> str:

        # 1. <tgroup> → <table>
        for tgroup in soup.find_all("tgroup"):
            tgroup.name = "table"

        # 2. <row> → <tr>
        for row in soup.find_all("row"):
            row.name = "tr"

        # 3. <entry> → <td>
        for entry in soup.find_all("entry"):
            entry.name = "td"

        # 4. <colspec> → <col>
        for colspec in soup.find_all("colspec"):
            colspec.name = "col"

        return soup

    def unwrap_tags(self, soup):
        table_tags = {'patent-tables', 'table', 'thead', 'tbody', 'tr', 'td', 'th'}
        highlight_tags = {'u', 'b', 'i'}
        script_tags = {'sub', 'sup', 'sup2'}
        attachment_tags = {'img', 'a', 'attachment', 'attachments'}
        codebook_tags = {'entry', 'tgroup', 'row', 'colspec'}
        ref_tags = {'figure-callout', 'div', 'chemistry', 'figref'}
        math_tags = {'maths', 'math', 'mspace', 'mtable', 'mstyle',
            'mo', 'msub', 'msup', 'mi', 'mn', 'mrow', 'mtd', 'mtr', 'mfrac'}
        etc = {'o'}
        to_unwrap = highlight_tags | attachment_tags | ref_tags

        for tag in soup.find_all(to_unwrap):
            tag.unwrap()

        return soup


    def execute(self, state=DocState) -> DocState:
        # Use the frozen prepared input rather than a mutable live web page.
        text = state['full_html'].replace('\u2003', ' ')
        text = text.replace('\u2009', ' ')
        text = text.replace('\u200c', '')

        soup = BeautifulSoup(text, "html.parser")
        tables = soup.find_all('tables')

        # Trim tables
        for table in tables:
            # 1. convert docbook_table_to_html
            table = self.convert_docbook_table_to_html(table)
            # Remove only the designated class; preserve all other classes.
            for tr in table.find_all('tr'):
                if tr.has_attr('class'):
                    tr['class'] = [name for name in tr['class'] if name != 'description-tr']
                    if not tr.get('class', []):
                        del tr['class']
            for td in table.find_all('td'):
                if td.has_attr('class'):
                    td['class'] = [name for name in td['class'] if name != 'description-td']
                    if not td.get('class', []):
                        del td['class']
            if table.has_attr('class'):
                table['class'] = [name for name in table['class'] if name != 'description-table']
                if not table.get('class', []):
                    del table['class']

        for table in tables:
            self.unwrap_tags(table)

        table_dict = {
            table['id']: {
                'id': table['id'],
                'table_html': table
            }
            for table in tables
            if table.get_text().count('ATOM') <= 100
        }

        for _, t_dict in table_dict.items():
            p = re.compile(r'TABLE \S{,8}[^\n]')
            m_index = p.search(t_dict['table_html'].text)
            if m_index is None:
                t_dict['index'] = ''
            else:
                t_dict['index'] = m_index.group()

        return {"tables": table_dict}

class TableRelatedTextNode(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "TabelRelatedTextNode"

    def execute(self, state=DocState) -> DocState:
        # split full text -> sentences
        sentences = re.split(r'\n|<br>|\. |<br/>|</p>', state['full_html'])
        proc_sentences = []
        for sentence in sentences:
            if len(sentence) > 500:
                split_sentences = [sentence[i: i+100] for i in range(0, len(sentence), 100)]
                proc_sentences.extend(split_sentences)
            else:
                proc_sentences.append(sentence)
        proc_sentences = [sentence for sentence in proc_sentences if sentence.strip() != '']

        table_dicts = state['tables']

        for t_key, t_dict in table_dicts.items():
            # gather lines referring table index
            if 'TABLE' in t_dict['index']:
                pattern = rf"{t_dict['index']}\D"
                table_mentioned_sentences = [
                    sentence for sentence in proc_sentences
                    if re.search(pattern, sentence, flags=re.IGNORECASE) and (t_key not in sentence)
                ]

                if table_mentioned_sentences == 0:
                    table_mentioned_sentences = f"No sentences mentioning {t_dict['index']}."
                elif len(table_mentioned_sentences) > 3:
                    table_mentioned_sentences = random.sample(table_mentioned_sentences, 3)
                    table_mentioned_sentences = '. \n'.join(table_mentioned_sentences)
                else:
                    table_mentioned_sentences = '. \n'.join(table_mentioned_sentences)
            else:
                table_mentioned_sentences = f"No sentences mentioning {t_dict['index']}."


            table_line_idxs = [idx for idx, line in enumerate(proc_sentences) if t_key in line]
            if len(table_line_idxs) == 1:
                line_idx = table_line_idxs[0]
                prev_sentences = '. '.join(proc_sentences[line_idx-3:line_idx])
            else:
                prev_sentences = f'The table is unspecified.'

            t_dict['table_mentioned_sentences'] = table_mentioned_sentences
            t_dict['prev_sentences'] = prev_sentences

        return {'tables': table_dicts}

class TableSummaryNode(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "TableSummaryNode"

        self.prompt_dir = kwargs.get('prompt_dir')
        self.example_dir = kwargs.get('example_dir')
        self.few_shot = kwargs.get('few_shot', 1)
        model_name = kwargs.get('model_name', 'gpt-4.1')
        temperature = kwargs.get('temperature', 0.0)
        self.batch_size = kwargs.get('batch_size', 3)
        base_url = kwargs.get('base_url')
        api_key = kwargs.get('api_key')
        extra_body = {"chat_template_kwargs": {"enable_thinking": False}} if kwargs.get('enable_thinking') is False else None

        model = ChatOpenAI(model_name=model_name, temperature=temperature,
                           base_url=base_url, api_key=api_key, extra_body=extra_body)
        so_method = "json_schema" if base_url else "function_calling"
        self.structured_llm = model.with_structured_output(TableSummary, method=so_method)
        self.wrap_rows_node = WrapRowsNode()

    def _format_example_prompt(self):

        examples = {}
        example_files = [os.path.join(self.example_dir, a) for a in os.listdir(self.example_dir) if '.txt' in a]

        for example_f in example_files[:self.few_shot]:
            name = os.path.basename(example_f).split('.')[0]
            with open(example_f, 'r') as rf:
                content = rf.read()
            examples[name] = content
        examples = dict(sorted(examples.items()))

        example_prompt = "\n".join(examples.values())
        return example_prompt

    def format_chunk(self, t_dict):

        table_html = t_dict['table_html'].prettify()
        split_lines = table_html.split('\n')
        i = 50
        table_chunk = f'<chunk pos="first">\n' + '\n'.join(split_lines[:50]) + '\n'
        while (len(table_chunk) < 5120) and (len(table_chunk) < len(table_html)//2):
            table_chunk += '\n'.join(split_lines[i: i+10]) + '\n'
            i += 10
        if (len(table_html) > 5120) and (len(split_lines) > 50):
            table_chunk += f'</chunk>\n<chunk pos="last">\n' + '\n'.join(split_lines[-i:]) + '\n</chunk>'

        return table_chunk

    def _table_hint(self, t_dict):
        count_trs, bool_results, blank_cols = self.wrap_rows_node.extract_table_numbers(t_dict['table_html'])
        table_chunk = self.format_chunk(t_dict)
        np_ab_category, np_content = self.wrap_rows_node.extract_ab_idxs(t_dict['table_html'])
        ab_col_dict = self.wrap_rows_node.get_ab_cols(np_ab_category, np_content)

        values, counts = np.unique(count_trs[:, 2], return_counts=True)
        col_count = np.max(counts)
        num_cols = values[counts == col_count].max().item()
        num_pads = blank_cols.count(True)

        hint = f"""## Hint from text-mining:
        This table has maximum {num_cols} columns in each rows.
        And there are {len(ab_col_dict)} types of antibody components in the table.
        """
        if num_pads > 0:
            hint += "There is {num_pads} blank column that serves as padding in the table. When reporting on table columns, ignore this column."

        if ab_col_dict != {}:
            for key_idx, col_num in ab_col_dict.items():
                ab_key = ab_keys[key_idx]
                hint+= f"- {ab_components[ab_key]} ({ab_key}) SEQ ID NO column located in column {col_num+1}.\n"

        return hint

    def _format_prompt(self, t_dict):
        system_prompt_path = os.path.join(self.prompt_dir, 'preprocess/system/table_summary.yaml')
        user_prompt_path = os.path.join(self.prompt_dir, 'preprocess/user/table_summary.yaml')

        system_prompt = load_prompt(system_prompt_path).format()
        user_template = load_prompt(user_prompt_path)
        example_prompt = self._format_example_prompt()

        # concatenate input chunks
        table_chunk = self.format_chunk(t_dict)
        hint = self._table_hint(t_dict)

        combined_prompt = user_template.format(
            index=t_dict['index'] if t_dict['index'] else 'No index',
            examples=example_prompt,
            input=table_chunk,
            hint=hint,
            prev_sentences=t_dict['prev_sentences'],
            table_mentioned_sentences=t_dict['table_mentioned_sentences']
        )

        prompt = create_message(
            system_prompt=system_prompt,
            user_prompt=combined_prompt
        )

        return prompt


    def execute(self, state=DocState) -> DocState:
        self.wrap_rows_node.get_ab_idxs(state)
        table_list = list(state['tables'].values())
        batch_size = self.batch_size

        # process data in batch size
        for i in range(0, len(table_list), batch_size):
            batch = table_list[i: i+batch_size]
            messages = [self._format_prompt(t_dict) for t_dict in batch]
            answers = self.structured_llm.batch(messages)

            for j, result in enumerate(answers):
                t_dict = batch[j].copy()
                id = t_dict['id']
                state['tables'][id]['summary'] = result

        return {'tables': state['tables']}

class WrapRowsNode(BaseNode):
    def __init__(self):
        pass

    def get_ab_idxs(self, state):
        ab_idxs = [state['idx_dict'].get(ab_key, []) for ab_key in ab_keys]
        self.ab_idxs = list(itertools.chain.from_iterable(ab_idxs))

        idx_to_key = {}
        for key, idx_list in state['idx_dict'].items():
            for idx in idx_list:
                idx_to_key[idx] = key
        self.idx_to_key = idx_to_key

    def find_col_w_SEQIDNO(self, soup):
        SEQIDNO_in_table = [[], [], []]
        blank_tds_in_rows = []
        for i, tr in enumerate(soup.find_all('tr')):
            tds = tr.find_all('td')
            content = [td.get_text(strip=True) for td in tds]
            is_blank = [cell == '' for cell in content]
            blank_tds_in_rows.append(is_blank)

            SEQIDNO_in_row = [
                ['SEQ' in a for a in content],
                ['ID' in a for a in content],
                ['NO' in a.upper() for a in content]
            ]
            SEQIDNO_in_table = [
                [x + y for x, y in itertools.zip_longest(res_list, lst, fillvalue=0)]
                for res_list, lst in zip(SEQIDNO_in_table, SEQIDNO_in_row)
            ]
        max_td = len(SEQIDNO_in_table[0])
        blank_tds_in_rows = [
            row + [True] * (max_td - len(row)) for row in blank_tds_in_rows
        ]
        blank_cols = [
            all(row[col_idx] for row in blank_tds_in_rows) for col_idx in range(max_td)
        ]
        cols_w_SEQIDNO = np.array(SEQIDNO_in_table).min(0)

        return cols_w_SEQIDNO, blank_cols


    def extract_table_numbers(self, soup):

        cols_w_SEQIDNO, blank_cols = self.find_col_w_SEQIDNO(soup)
        threshold = 1

        count_trs = []
        idx_lists = []
        bool_results = []
        for i, tr in enumerate(soup.find_all('tr')):
            tds = tr.find_all('td')
            not_blank = np.array([td.get_text(strip=True) != '' for td in tds])

            idx_list = []
            for col_idx, td in enumerate(tds):
                if cols_w_SEQIDNO[col_idx] == 0:
                    idxs = []
                elif cols_w_SEQIDNO[col_idx] <= threshold:
                    idxs = re.findall(r'^\d+$', td.get_text(strip=True))
                    idx_range = re.match(r"^(\d+)-(\d+)$", td.get_text(strip=True))
                    if idx_range:
                        start, end = int(idx_range.group(1)), int(idx_range.group(2))
                        idxs.extend(list(range(start, end+1)))
                elif cols_w_SEQIDNO[col_idx] > threshold:
                    idxs = re.findall(r'SEQ ID NO:\s*(\d+)', td.get_text(strip=True), flags=re.IGNORECASE)
                idxs = [int(num) for num in idxs if int(num) in self.ab_idxs]
                idx_list.append(idxs)

            flattened_idxs = list(itertools.chain.from_iterable(idx_list))
            idx_lists.append(flattened_idxs)
            contains_seqidno = [a != [] for a in idx_list]

            tr_result = np.vstack([not_blank, contains_seqidno])
            count_tr = np.sum(tr_result, 1)
            count_tr = np.concatenate([count_tr, np.array([len(tds)])])
            count_trs.append(count_tr)

            if i == 0:
                bool_results = [np.array([0, 0, 0, 0])]
                continue
            prev_tr = count_trs[-2]

            bool_prev_blank_tr = int((prev_tr[0] == 0) and (count_tr[0] > 0)) # 이전 row는 모두 blank 이번 row에는 data 있음
            bool_increase_td = int(count_tr[2] > prev_tr[2])                  # column 개수 증가
            bool_decrease_blank = int(count_tr[0] > prev_tr[0])               # blank cell 감소
            bool_contain_int = int(count_tr[1] > 0)                           # 관심 SEQ ID NO 포함
            bool_result = np.array([bool_prev_blank_tr, bool_increase_td, bool_decrease_blank, bool_contain_int])
            bool_results.append(bool_result)

        count_trs = np.stack(count_trs)
        bool_results = np.stack(bool_results)

        return count_trs, bool_results, blank_cols

    def extract_ab_idxs(self, soup, max_td=None, cols_w_SEQIDNO=None, threshold=1):
        if cols_w_SEQIDNO is None:
            cols_w_SEQIDNO, blank_cols = self.find_col_w_SEQIDNO(soup)
            max_td = len(cols_w_SEQIDNO)
            force = False
        else:
            force = True

        idx_lists = []
        ab_categories = []
        for tr in soup.find_all('tr'):
            tds = tr.find_all('td')
            idx_list = []
            for col_idx, td in enumerate(tds[:max_td]):
                td_text = td.get_text(strip=True)
                idxs = []

                if cols_w_SEQIDNO[col_idx] == 0:
                    pass
                # SEQ ID NO referred less frequently
                elif cols_w_SEQIDNO[col_idx] <= 10:
                    # extract number
                    if re.fullmatch(r'\d+', td_text):
                        idxs = [int(td_text)]
                    # extract range
                    elif re.fullmatch(r'\d+\s*-\s*\d+', td_text):
                        start, end = map(int, re.findall(r'\d+', td_text))
                        idxs = list(range(start, end + 1))
                idxs = [int(num) for num in idxs if int(num) in self.ab_idxs]
                # SEQ ID NO가 여러 번 언급되는 경우
                if cols_w_SEQIDNO[col_idx] > 1:
                    add_idxs = re.findall(r'SEQ ID NO:\s*(\d+)', td_text, flags=re.IGNORECASE)
                    add_idxs = [int(num) for num in idxs if int(num) in self.ab_idxs]
                    idxs += add_idxs

                if len(idxs) == 0 and force == True:
                    matches = re.findall(r'(?<!\w)\d+(?!\w)', td_text)
                    for match in matches:
                        idx = int(re.search(r'\d+', match).group(0))
                        if idx in self.ab_idxs:
                            idxs.append(idx)

                idx_list.append(idxs)

            if len(idx_list) < max_td:
                idx_list.extend([[] for _ in range(max_td - len(idx_list))])

            ab_category = [[self.idx_to_key.get(x) for x in sublist] for sublist in idx_list]
            ab_categories.append(ab_category)
            idx_lists.append(idx_list)

        df = pd.DataFrame(ab_categories).applymap(lambda x: ','.join(map(str, x)))
        vh_mask = df.astype(str).applymap(lambda x: 'VH' in x).to_numpy(dtype=bool)
        vl_mask = df.astype(str).applymap(lambda x: 'VL' in x).to_numpy(dtype=bool)
        hc_mask = df.astype(str).applymap(lambda x: 'HC' in x).to_numpy(dtype=bool)
        lc_mask = df.astype(str).applymap(lambda x: 'LC' in x).to_numpy(dtype=bool)
        fv_mask = df.astype(str).applymap(lambda x: 'scFv' in x).to_numpy(dtype=bool)
        ms_mask = df.astype(str).applymap(lambda x: 'MS' in x).to_numpy(dtype=bool)
        nb_mask = df.astype(str).applymap(lambda x: 'NB' in x).to_numpy(dtype=bool)
        nonAB_mask = df.astype(str).applymap(lambda x: 'nonAB' in x).to_numpy(dtype=bool)
        np_ab_category = np.stack([vh_mask, vl_mask, hc_mask, lc_mask, fv_mask, ms_mask, nb_mask, nonAB_mask])

        df = pd.DataFrame(idx_lists)
        df_content = df.applymap(lambda x: ','.join(map(str, x)) if isinstance(x, list) and len(x) > 0 else None)
        np_content = df_content.to_numpy()
        np_content = np.expand_dims(np_content, axis=0)

        return np_ab_category, np_content

    def get_ab_cols(self, np_ab_category, np_content, threshold=2):
        counter = [
            len(np.unique(np.where(np_ab_category, np_content, 0)[idx].nonzero()[0]))
            for idx in range(len(np_ab_category))
            ]
        counter = np.array(counter)
        ab_type_idxs = np.where(counter >= threshold)[0]
        ab_col_dict = {int(idx): int(np_ab_category[idx].sum(0).argmax()) for idx in ab_type_idxs}

        return ab_col_dict

    def table_get_separators(self, bool_results, np_ab_category, ab_col_dict):
        separator = np.where(bool_results[:, 0] | bool_results[:, 2])[0]
        ab_counts = []
        for i in range(len(separator)):
            if i == 0:
                start, end = 0, separator[i]
            else:
                start, end = separator[i-1], separator[i]
            ab_count = [int(np_ab_category[key, start:end, col].sum()) for key, col in ab_col_dict.items()]
            ab_count = np.array(ab_count)
            ab_counts.append(ab_count)
        if ab_counts == []:
            return []

        ab_counts = np.stack(ab_counts)

        list_separators = []
        values, counts = np.unique(ab_counts.sum(1), return_counts=True)
        nonzero_filter = values != 0
        nonzero_values = values[nonzero_filter]
        nonzero_counts = counts[nonzero_filter]
        if nonzero_counts.sum() == 0:
            return []
        max_count = nonzero_counts.max()
        mode_values = nonzero_values[nonzero_counts == max_count]
        mode_frequencies = nonzero_counts[nonzero_counts == max_count].max()

        if (mode_frequencies / nonzero_counts.sum()).item() > 0.7:
            for i in range(len(separator)):
                if i == 0:
                    start, end = 0, separator[i]
                else:
                    start, end = separator[i-1].item(), separator[i].item()
                ab_count = [int(np_ab_category[key, start:end, col].sum()) for key, col in ab_col_dict.items()]
                ab_count = np.array(ab_count).sum().item()

                if (ab_count in mode_values.tolist()) and (ab_count != 0):
                    list_separators.append((start, end))

        return list_separators

    def wrap_row_entries(self, soup, list_separators):

        for start, end in sorted(list_separators, key=lambda x: x[0], reverse=True):
            # DOM이 변경될 수 있으므로 매번 현재의 모든 <tr> 태그(flattened)를 가져옵니다.
            current_trs = soup.find_all('tr')
            # 대상 범위의 <tr> 태그들 (start부터 end까지)
            target_trs = current_trs[start:end]

            # 대상이 없는 경우 건너뜁니다.
            if not target_trs:
                continue

            # 대상 범위의 첫 번째 <tr> 태그와 그 부모 컨테이너를 가져옵니다.
            first_tr = target_trs[0]
            parent = first_tr.parent

            # 부모의 .contents 목록에서 첫 번째 대상 태그가 위치하는 인덱스를 찾습니다.
            insertion_index = None
            for idx, child in enumerate(parent.contents):
                if child is first_tr:
                    insertion_index = idx
                    break
            if insertion_index is None:
                insertion_index = 0

            # 새로운 <entry> 태그 생성
            entry_tag = soup.new_tag("entry")

            # 대상 범위의 모든 <tr> 태그를 추출하여 <entry> 태그 안에 추가합니다.
            for tr in target_trs:
                entry_tag.append(tr.extract())

            # 부모 컨테이너의 정확한 위치(첫 번째 대상 태그가 있던 자리)에 <entry> 태그 삽입
            parent.insert(insertion_index, entry_tag)

        return soup

    def trim_table(self, soup):
        for element in soup.find_all(string=True):
            if element.isspace():
                element.replace_with('')
            else:
                stripped_text = re.sub(r'\s+', ' ', element.strip())
                element.replace_with(stripped_text)

        processed_html = str(soup)

        return processed_html

    def execute(self, state):
        # antibody index list
        self.get_ab_idxs(state)

        for t_key, table in state['tables'].items():
            soup = BeautifulSoup(str(table['table_html']), 'html.parser')
            if table['summary'].category == 'sequence description':
                count_trs, bool_results, blank_cols = self.extract_table_numbers(soup)
                np_ab_category, np_content = self.extract_ab_idxs(soup)
                ab_col_dict = self.get_ab_cols(np_ab_category, np_content)
                list_separators = self.table_get_separators(bool_results, np_ab_category, ab_col_dict)
                wrapped_soup = self.wrap_row_entries(soup, list_separators)
                trimmed_soup = self.trim_table(wrapped_soup)
            else:
                trimmed_soup = self.trim_table(soup)
            state['tables'][t_key]['wrapped_soup'] = trimmed_soup

        return state

class AbNameLocNode(BaseNode):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.name = "AbNameLocNode"
        model_name = kwargs.get('model_name', 'gpt-4.1')
        temperature = kwargs.get('temperature', 0.0)
        self.prompt_dir = kwargs.get('prompt_dir', '')
        self.batch_size = kwargs.get('batch_size', 3)
        base_url = kwargs.get('base_url')
        api_key = kwargs.get('api_key')
        extra_body = {"chat_template_kwargs": {"enable_thinking": False}} if kwargs.get('enable_thinking') is False else None

        model = ChatOpenAI(model_name=model_name, temperature=temperature,
                           base_url=base_url, api_key=api_key, extra_body=extra_body)
        so_method = "json_schema" if base_url else "function_calling"
        self.structured_llm = model.with_structured_output(AbNameLocation, method=so_method)

    def format_chunk(self, t_dict):

        table_chunk = f"=== {t_dict['index']} {t_dict['summary'].title} ===\n\n"

        table_chunk += "Column structure:\n"
        for col_idx, col in enumerate(t_dict['summary'].columns):
            table_chunk += f"  Column {col_idx+1}: {col.column_header}\n"
            for elem_idx, element in enumerate(col.elements):
                table_chunk += f"  - Element {elem_idx+1}: {element.element_name} ({element.value_type})\n"
                if element.includes_seq_id_no:
                    table_chunk += "    - includes SEQ ID NO\n"

        table_html = t_dict['table_html'].prettify()
        split_lines = table_html.split('\n')
        i = 50
        table_chunk += "\n---\nHTML TABLE_content:\n"
        table_chunk += f'<chunk pos="first">\n' + '\n'.join(split_lines[:50]) + '\n'
        while (len(table_chunk) < 10000) and (len(table_chunk) < len(table_html)//2):
            table_chunk += '\n'.join(split_lines[i: i+10]) + '\n'
            i += 10

        return table_chunk

    def _format_prompt(self, t_dict):
        system_prompt_path = os.path.join(self.prompt_dir, 'preprocess/system/table_ab_name_location.yaml')
        user_prompt_path = os.path.join(self.prompt_dir, 'preprocess/user/table_ab_name_location.yaml')

        system_prompt = load_prompt(system_prompt_path).format()
        user_template = load_prompt(user_prompt_path)
        table_chunk = self.format_chunk(t_dict)

        user_prompt = user_template.format(
            table_chunk=table_chunk
        )
        prompt = create_message(
            system_prompt=system_prompt,
            user_prompt=user_prompt
        )

        return prompt

    def execute(self, state):
        table_list = [
            t_dict for t_dict in state['tables'].values()
            if t_dict['summary'].category == 'sequence description'
            ]


        for i in range(0, len(table_list), self.batch_size):
            batch = table_list[i: i+self.batch_size]
            messages = [self._format_prompt(t_dict) for t_dict in batch]
            answers = self.structured_llm.batch(messages)

            for j, result in enumerate(answers):
                t_dict = batch[j].copy()
                id = t_dict['id']
                state['tables'][id]['ab_location'] = result

        return {'tables': state['tables']}


class TableChunkNode(BaseNode):
    def __init__(self, **kwargs):
        self.splitter = HTMLCustomSplitter(**kwargs)
        self.wrap_rows_node = WrapRowsNode()

    def remove_seq_rows(self, table_str):
        soup = BeautifulSoup(table_str)
        for tr in soup.find_all('tr'):
            text = tr.get_text(separator=" ", strip=True)
            if text == 'AA SEQ':
                tr.decompose()

        return str(soup)

    def execute(self, state=DocState) -> DocState:
        self.wrap_rows_node.get_ab_idxs(state)
        tables = state['tables']
        for t_key, table in tables.items():

            table_str = str(table['wrapped_soup'])
            table_str = self.splitter._replace_script(table_str)
            table_str = truncate_sequences(table_str, 'AA', 15)
            table_str = truncate_sequences(table_str, 'NT', 15)
            table_str = self.remove_seq_rows(table_str)
            chunks = self.splitter.split_text(table_str)

            table['split_docs'] = chunks

        return {'tables': tables}


class ProcessTableChunkNode(BaseNode):
    def __init__(self, **kwargs):
        self.name = "ProcessTableChunkNode"
        self.wrap_rows_node = WrapRowsNode()

    def extract_seq_id_no(self, split_doc, cols_w_SEQIDNO, max_td):
        soup = BeautifulSoup(split_doc.page_content, 'html.parser')
        _, np_content = self.wrap_rows_node.extract_ab_idxs(
            soup,
            cols_w_SEQIDNO=cols_w_SEQIDNO,
            max_td=max_td
            )

        np_nums = [np_content[0, :, idx] for idx, val in enumerate(cols_w_SEQIDNO) if val > 0]
        if len(np_nums) > 0:
            np_nums = np.concatenate(np_nums)
            seq_id_nos = np.array([x for x in np_nums if x is not None]).tolist()
            seq_id_nos = [int(num.strip()) for x in seq_id_nos for num in x.split(',')]
        else:
            return []

        return seq_id_nos

    def find_heading(self, t_key, docs):

        headings = {}
        heading_list = ["Heading 3", "Heading 4", "Heading 5"]
        for doc in docs:
            if t_key in doc.page_content:
                headings = {key: doc.metadata.get(key) for key in heading_list}

        return headings


    def execute(self, state=DocState) -> DocState:
        self.wrap_rows_node.get_ab_idxs(state)

        split_tables = []
        t_dicts = state['tables']
        for t_key, t_dict in t_dicts.items():
            cols_w_SEQIDNO, blank_cols = self.wrap_rows_node.find_col_w_SEQIDNO(t_dict['table_html'])
            np_ab_category, np_content = self.wrap_rows_node.extract_ab_idxs(t_dict['table_html'])
            ab_col_dict = self.wrap_rows_node.get_ab_cols(np_ab_category, np_content)
            max_td = len(blank_cols)

            if blank_cols.count(False) == len(t_dict['summary'].columns):
                non_blank_indices = [i for i, is_blank in enumerate(blank_cols) if not is_blank]
                for col_idx, col in enumerate(t_dict['summary'].columns):
                    if any(element.includes_seq_id_no for element in col.elements):
                        actual_idx = non_blank_indices[col_idx]
                        if actual_idx in ab_col_dict.values():
                            cols_w_SEQIDNO[actual_idx] = max(cols_w_SEQIDNO[actual_idx], 1)
                        else:
                            cols_w_SEQIDNO[actual_idx] = 1
            else:
                cols_w_SEQIDNO = np.array([
                    val if col_idx in ab_col_dict.values() else 0
                    for col_idx, val in enumerate(cols_w_SEQIDNO)
                ])

            for split_doc in t_dict['split_docs']:
                # Extract SEQ ID NO from
                if cols_w_SEQIDNO.sum() > 0:
                    seq_id_nos = self.extract_seq_id_no(split_doc=split_doc, cols_w_SEQIDNO=cols_w_SEQIDNO, max_td=max_td)
                else:
                    seq_id_nos = []
                seq_id_nos = list(set(seq_id_nos))

                summary = t_dict.get('summary', None)
                metadata = {
                    'index': t_dict['index'] if t_dict['index'] else '',
                    'title': summary.title if summary and hasattr(summary, 'title') else '',
                    'id': t_key,
                    'category': summary.category if summary and hasattr(summary, 'category') else 'No category',
                    'footnotes': summary.footnotes,
                    'SEQ_ID_NO': seq_id_nos,
                    'columns': summary.columns if summary and hasattr(summary, 'columns') else [],
                    'prev_sentences': t_dict['prev_sentences'],
                    'table_mentioned_sentences': t_dict['table_mentioned_sentences']
                }
                if 'ab_location' in t_dict:
                    metadata['ab_location'] = t_dict['ab_location']

                # Match table id with document
                headings = self.find_heading(t_key=t_key, docs=state['split_docs'])
                metadata = metadata | headings

                split_doc.metadata = metadata
                split_tables.append(split_doc)

        return {'split_tables': split_tables}


class TableMetadataNode(BaseNode):
    def __init__(self, **kwargs):
        pass

    def combine_metadata(self, document):

        meta = document.metadata
        metadata_html = ""
        if meta['index'] != 'No index found':
            metadata_html += f"=== {meta['index']} {meta['title']} ===\n\n"

        if 'Heading 3' in meta:
            metadata_html += f"Headings:\n"
            metadata_html += f"  Heading 3: {meta['Heading 3']}\n"
        if 'Heading 4' in meta:
            metadata_html += f"  Heading 4: {meta['Heading 4']}\n"
        if 'Heading 5' in meta:
            if meta['Heading 5'] != '':
                metadata_html += f"  Heading 5: {meta['Heading 5']}\n"

        metadata_html += "\nColumn structure:\n"
        for col_idx, col in enumerate(meta['columns']):
            metadata_html += f"  Column {col_idx+1}: {col.column_header}\n"
            for elem_idx, element in enumerate(col.elements):
                metadata_html += f"  - Element {elem_idx+1}: {element.element_name} ({element.value_type})\n"
                if element.includes_seq_id_no:
                    metadata_html += "    - includes SEQ ID NO\n"

        if 'SEQ_ID_NO' in meta:
            seq_ids_in_meta = meta['SEQ_ID_NO']
            metadata_html+= f"\nSEQ ID NO LIST:\n"
            for ab_key in ab_keys:
                ab_type_seq_list = set(self.idx_dict.get(ab_key, []))
                matched = ab_type_seq_list.intersection(seq_ids_in_meta)
                if matched:
                    matched_str = f"- {ab_components[ab_key]} ({ab_key}): "
                    matched_str+= ", ".join([f'SEQ ID NO: {seq_id_no}' for seq_id_no in matched])
                    metadata_html += matched_str + '\n'

        if 'ab_location' in meta:
            ab_location = document.metadata.get('ab_location')
            name_loc = ab_location.name_location
            rel_loc = ab_location.relative_location
            metadata_html += "\n\nNotes:\n"
            if name_loc == 'header':
                metadata_html += "- Antibody or antigen name located in the header\n"
            if 'column' in name_loc:
                metadata_html += f"- Antibody or Antigen name in {name_loc}\n"

        metadata_html += "\n\nSentences referring the table:\n" + document.metadata.get('table_mentioned_sentences') + '\n'
        metadata_html += "\n\nSentences before the table:\n" + document.metadata.get('prev_sentences') + '\n'

        page_content = "\nPage_content:\n" + document.page_content

        footnote_html = ""
        if 'category' in meta:
            if meta['category'] == 'experiment result':
                footnotes = meta['footnotes']
                if len(footnotes) > 0:
                    footnote_html+= 'Footnotes: \n'
                    for footnote in footnotes:
                        footnote_html+= f'- {footnote}\n'

        combined_text = metadata_html + footnote_html + page_content

        return combined_text


    def execute(self, state=DocState) -> DocState:
        self.idx_dict = state['idx_dict']
        meta_tables = [
            Document(
                page_content=self.combine_metadata(docs),
                metadata = docs.metadata
            ) for split_idx, docs in enumerate(state['split_tables'])
        ]

        return {'meta_tables': meta_tables}


def build_table_preprocess_subgraph(config):
    # Define Graph
    graph_builder = StateGraph(DocState)

    # Define nodes
    table_crawl_node = TableCrawlNode()
    table_related_text_node = TableRelatedTextNode()
    table_summary_node = TableSummaryNode(
        prompt_dir=config['io']['prompt'],
        example_dir=config['io']['example'],
        **config['preprocess']['table_summary'])
    ab_name_loc_node = AbNameLocNode(
        prompt_dir=config['io']['prompt'],
        **config['preprocess']['ab_name_location'])
    wrap_rows_node = WrapRowsNode()
    table_chunk_node = TableChunkNode(**config['preprocess']['table_chunk'])

    # Add Nodes
    graph_builder.add_node("table_crawl", table_crawl_node)
    graph_builder.add_node("table_related_text", table_related_text_node)
    graph_builder.add_node("table_summary", table_summary_node)
    graph_builder.add_node("ab_name_location", ab_name_loc_node)
    graph_builder.add_node("wrap_rows", wrap_rows_node)
    graph_builder.add_node("table_chunk", table_chunk_node)

    # Connect Edges
    graph_builder.add_edge(START, 'table_crawl')
    graph_builder.add_edge('table_crawl', 'table_related_text')
    graph_builder.add_edge('table_related_text', 'table_summary')
    graph_builder.add_edge('table_summary', 'ab_name_location')
    graph_builder.add_edge('ab_name_location', 'wrap_rows')
    graph_builder.add_edge('wrap_rows', 'table_chunk')
    graph_builder.add_edge('table_chunk', END)

    # Compile Graph
    sub_graph = graph_builder.compile()

    return sub_graph
