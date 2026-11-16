from __future__ import annotations

import re
from lxml import html
import numpy as np
from bs4 import BeautifulSoup
from langchain_core.documents import Document
from langchain.text_splitter import RecursiveCharacterTextSplitter
from typing import Any, Dict, Iterable, List, Optional, Tuple, TypedDict, Literal, Union
from ..rag.utils import truncate_sequences

default_separators = [
    # body
    "<body",
    "<h1",
    "<h2",
    "<h3",
    "<h4",
    "<h5",
    "<h6",
    "<div",
    "<table",
    "<tables",
    "<p",
    "<br",
    "<span",
    "<header",
    "<footer",
    "<nav",
    # head
    "<head",
    "<style",
    "<script",
    "<meta",
    "<title",
    "",
]

set_AA = 'ACDEFGHIKLMNPQRSTVWY '
set_NT = 'ATGCU atgcu'

headers_to_split_on = [
    ("h3", "Heading 3"),
    ("h4", "Heading 4"),
    ("h5", "Heading 5")
]


class ElementType(TypedDict):
    """Element type as typed dict."""

    url: str
    xpath: str
    content: str
    metadata: Dict[str, str]

def replacer(match: re.Match) -> str:
    seq = match.group(0)
    return seq[:2] + seq[-2:]

class HTMLCustomSplitter(RecursiveCharacterTextSplitter):
    """
    Custom HTML splitter for patent html containing outdated xml tags.
    """
    def __init__(
            self,
            separator: Optional[List[str]] = None,
            keep_separator: Union[bool, Literal["start", "end"]] = True,
            is_separator_regex: bool = False,
            headers_to_split_on: List[Tuple[str, str]] = headers_to_split_on,
            **kwargs: Any,
    ) -> None:
        """Create a new text splitter"""
        super().__init__(**kwargs)
        self._separator = separator or default_separators
        self._is_separator_regex = is_separator_regex
        self.headers_to_split_on = headers_to_split_on
        self.new_headings = {}
        self._chunk_size = kwargs.get('chunk_size')
        self._chunk_overlap = kwargs.get('chunk_overlap')


    def preprocess(self, content, patent_id):
        """Preprocessing HTML text"""
        content = self._remove_tags(content)
        content = self._add_headings(content, patent_id)
        #content = self._replace_script(content)    # deleted because of 10.sup.-10 -> 10<sup>-1</sub>0
        #content = self._add_h5_heading_experiment(content)
        #content = self._add_h5_heading_roman_indexed(content)
        #content = self._remove_tables(content)
        #content = self._truncate_sequences(content)

        return content


    def from_file(self, input_path: str) -> str:
        """
        Open html file
        """
        with open(input_path, "r", encoding="utf-8") as rf:
            content = rf.read()

        return content


    def _replace_script(self, content:str) -> str:
        sub_pattern = r"\.sub\.(.)"
        sub_converted = r"<sub>\1</sub>"
        content = re.sub(sub_pattern, sub_converted, content)

        sup_pattern = r"\.sup\.(.)"
        sup_converted = r"<sup>\1</sup>"
        content = re.sub(sup_pattern, sup_converted, content)

        return content


    # def _add_h4_heading_uppercase(self, content: str) -> str:
    #     """
    #     Add <h4> or <h5> tags depending on uppercase headings.
    #     - "DEFINITIONS" → <h5> and added to self.new_headings['h5']
    #     - Other headings → <h4> and added to self.new_headings['h4']
    #     """

    #     # 준비: headings 리스트 초기화
    #     if 'h4' not in self.new_headings:
    #         self.new_headings['h4'] = []
    #     if 'h5' not in self.new_headings:
    #         self.new_headings['h5'] = []


    #     # pattern = r'(?P<indent>\s*)(<br\s*/?>)\s*\n(?P=indent)(?P<heading>[A-Z][A-Z \-/]{10,})\s*\n(?P=indent)(<br\s*/?>)'
    #     pattern = r'(?P<indent1>\s*)(?P<first_tag><p>|<br\s*/?>)\s*\n(?P<indent2>\s*)(?:(\(\d+\)|\[\d+\])\s*)?(?P<heading>[A-Z][A-Z \-/]{7,})\s*\n(?P<indent3>\s*)(?P<last_tag><br\s*/?>)'

    #     def heading_replacer(match: re.Match) -> str:

    #         heading = match.group('heading').strip()

    #         self.new_headings['h4'].append(heading)
    #         return (
    #             f"{match.group('indent1')}{match.group('first_tag')}\n"
    #             f"{match.group('indent2')}<h4>{heading}</h4>\n"
    #             f"{match.group('indent3')}{match.group('last_tag')}"
    #         )

    #     # Replace pattern
    #     content = re.sub(pattern, heading_replacer, content)

    #     return content


    def _remove_tags(self, content: str) -> str:

        """
        Remove tags
        """
        # Multiple \s\n\t -> single \s
        content = re.sub(r'\s*<(b|i|u)>\s*', r' <\1>', content)
        content = re.sub(r'\s*<(figref)(^>)*>\s*', r' <figref>', content)
        content = re.sub(r'\s*</(b|i|u)>\s*', r'</\1> ', content)
        content = re.sub(r'\s*</figref>\s*', r' <figref>', content)

        # Parse html
        soup = BeautifulSoup(content, "html.parser")

        # remove tags
        for tag in soup.find_all(['img']):
            tag.decompose()

        for tag in soup.find_all(['b', 'i', 'figref', 'u', 'a', 'figure-callout']):
            tag.unwrap()

        content = str(soup)
        content = content.replace('<br/>', '<br>')
        content = content.replace('<br />', '<br>')

        return content

    def _get_headings(self, content) -> list:
        """Read heading labels from the prepared HTML itself."""
        soup = BeautifulSoup(content, "html.parser")
        heading_tags = soup.find_all('heading')
        headings = [heading.text.strip() for heading in heading_tags]

        return headings


    def _add_headings(self, content:str, patent_id:str) -> str:

        headings = self._get_headings(content)
        lines = content.splitlines()
        newlines = []

        if 'h4' not in self.new_headings:
            self.new_headings['h4'] = []
        if 'h5' not in self.new_headings:
            self.new_headings['h5'] = []


        for i, line in enumerate(lines):
            pattern = r'^(?P<indent>\s*)(?P<line_idx>(\(\d+\)|\[\d+\])\s*)?(?P<title>.*)'
            match = re.fullmatch(pattern, line)
            title = match.group('title')
            line_idx = match.group('line_idx')
            indent = match.group('indent')
            if line_idx is None:
                line_idx = ''

            if title in headings:
                if re.search(r'(Example|Experiment)s?', title, re.IGNORECASE):
                    if re.search(r'\d', title):
                        t_idx = headings.index(title)
                        next_match = re.match(pattern, lines[i+2]).group('title')
                        if title == headings[-1]:
                            newline = f'{indent}{line_idx}<h5>{title}</h5>'
                            self.new_headings['h5'].append(f'{title}')
                        elif headings[t_idx+1] == next_match:
                            subtitle = next_match
                            headings.remove(subtitle)
                            newline = f'{indent}{line_idx}<h5>{title}: {subtitle}</h5>'
                            self.new_headings['h5'].append(f'{title}: {subtitle}')
                        else:
                            newline = f'{indent}{line_idx}<h5>{title}</h5>'
                            self.new_headings['h5'].append(f'{title}')
                    else:
                        newline = f'{indent}{line_idx}<h4>{title}</h4>'
                        self.new_headings['h4'].append(f'{title}')
                else:
                    newline = f'{indent}{line_idx}<h4>{title}</h4>'
                    self.new_headings['h4'].append(f'{title}')
                newlines.append(newline)
            else:
                newlines.append(line)

        content = '\n'.join(newlines)

        return content


    def _remove_tables(self, content:str) -> str:
        """
        Remove table from
        """
        new_lines = []
        is_table = False
        for line in content.split('\n'):
            if 'TABLE-US-' in line:
                pos = line.find('TABLE-US-')
                newline = line[:pos] + line[pos:pos+15]
                new_lines.append(newline)
                is_table = True
            if is_table:
                if ('<br/>' in line) or ('<br>' in line):
                    new_lines.append(line)
                elif 'TABLE-US' not in line and line.count('\t') < 5:
                    is_table = False
                    new_lines.append(line)
                # 'TABLE-US' in line or many '\t' in line
                else:
                    pass
            else:
                new_lines.append(line)

        new_content = '\n'.join(new_lines)

        return new_content

    def split_chunks(self, table, min_td_count=3, min_char_threshold=2000):
        if isinstance(table, str):
            soup = BeautifulSoup(table, 'html.parser')
        else:
            soup = table

        lines = soup.prettify().split('\n')
        num_tds = [line.count('</td>') for line in lines]
        table_ends = [line.count('</table>') for line in lines]
        table_starts = [line.count('<table') for line in lines]

        np_table_ends = np.array(table_ends)
        indices = np.where(np_table_ends == 1)[0]

        # <table> 블록 범위 (start, end 포함)
        table_line_ranges = []
        start = 0
        for end in indices:
            table_line_ranges.append((start, end + 1))
            start = end + 1

        # 각 <table>에 대한 정보
        td_counts_per_table = []
        char_counts_per_table = []
        table_col_is_one = []

        table_start_indices = [i for i, count in enumerate(table_starts) if count > 0]

        for idx, (s, e) in enumerate(table_line_ranges):
            td_count = sum(num_tds[s:e])
            char_count = sum(len(line) for line in lines[s:e])
            td_counts_per_table.append(td_count)
            char_counts_per_table.append(char_count)

            # 시작줄 기준으로 "cols=1" 포함 여부 판단
            first_line = next((line for line in lines[s:e] if '<table' in line), "")
            has_cols_1 = bool(re.search(r'cols\s*=\s*["\']?1["\']?', first_line, re.IGNORECASE))
            table_col_is_one.append(has_cols_1)

        # chunk split points 결정
        chunk_boundaries = []
        accumulated_chars = 0

        for i, (td_count, char_count, col_is_one) in enumerate(zip(td_counts_per_table, char_counts_per_table, table_col_is_one)):
            is_potential_header = td_count <= min_td_count and col_is_one
            contains_seq_id_no = any("SEQ ID NO" in lines[j] for j in range(*table_line_ranges[i]))

            if is_potential_header and not contains_seq_id_no:
                if accumulated_chars >= min_char_threshold:
                    chunk_boundaries.append(i)
                    accumulated_chars = 0
            else:
                accumulated_chars += char_count

        # chunk 나누기
        if not chunk_boundaries:
            return [''.join(line.strip() for line in lines)]

        chunks = []
        start_table_idx = 0
        for boundary_table_idx in chunk_boundaries:
            chunk_lines = []
            for i in range(start_table_idx, boundary_table_idx):
                s, e = table_line_ranges[i]
                chunk_lines.extend(lines[s:e])
            chunks.append(chunk_lines)
            start_table_idx = boundary_table_idx

        # 마지막 chunk 추가
        chunk_lines = []
        for i in range(start_table_idx, len(table_line_ranges)):
            s, e = table_line_ranges[i]
            chunk_lines.extend(lines[s:e])
        chunks.append(chunk_lines)

        chunks = [''.join(line.strip() for line in chunk) for chunk in chunks]

        return chunks


    def split_text(self, text:str) -> List[str]:
        """
        Split text and add heading to metadata
        """
        final_chunks = []
        chunks = self.split_chunks(text)
        for chunk in chunks:
            if len(chunk) < self._chunk_size:
                final_chunks.append(chunk)
            else:
                splits = self._split_text(chunk, self._separator)
                final_chunks.extend(splits)

        documents = []
        heading_mapping = dict(self.headers_to_split_on)
        headers = {key: "" for key in heading_mapping.keys()}

        for chunk in final_chunks:
            headers = self._extract_headers(chunk, headers)
            metadata = {heading_mapping[key]: value for key, value in headers.items()}
            doc = Document(page_content=chunk,
                           metadata=metadata)
            documents.append(doc)

        return documents

    def _truncate_sequences(self, content, n=20) -> str:
        """
        Truncated amino acid / nuclotide sequences.
        - content: text
        - n: number of repeat
        """

        content = truncate_sequences(content, 'AA', n=20, remainder=2)
        content = truncate_sequences(content, 'NT', n=15, remainder=2)

        return content


    def _extract_headers(self,
                         text: str,
                         previous_headings: Dict[str, str]) -> Dict[str, str]:
        """
        Extract headers from text.
        Compare headers between previous headers and updated headers.
        Choose the headers in the current text.
        """
        # Parse the HTML content
        tree = html.fromstring(text)

        # Initialize current headings
        current_headings = {key: '' for key in previous_headings.keys()}
        headers_sorted = sorted(list(current_headings.keys()))

        # Extract headings
        for level in headers_sorted:
            # Find all headings of this level
            headings = tree.xpath(f'//{level}')
            if headings:
                # If multiple headings are found, we take the first one
                current_headings[level] = headings[0].text_content().strip()

        # Build the metadata dictionary based on the inheritance rules
        metadata = {}

        # Flags to indicate if a higher-level heading has changed
        changed = {key: False for key in headers_sorted}

        # Process h1
        for h_idx, header in enumerate(headers_sorted):
            if current_headings[header]:
                if current_headings[header] != previous_headings[header]:
                    changed[header] = True
                    metadata[header] = current_headings[header]

                    # Reset lower-level headings
                    for low_lev_header in headers_sorted[h_idx+1:]:
                        metadata[low_lev_header] = ''
                else:
                    metadata[header] = previous_headings[header]
            else:
                is_changed = [False] + [changed[key] for key in headers_sorted[:h_idx]]
                if True in is_changed:
                    metadata[header] = ''
                else:
                    metadata[header] = previous_headings[header]


        return metadata
