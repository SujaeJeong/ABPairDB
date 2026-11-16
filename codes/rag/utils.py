from sklearn.cluster import DBSCAN
import numpy as np
from typing import List
import re

set_AA = 'ACDEFGHIKLMNPQRSTVWY '
set_NT = 'ATGCU atgcu'

def create_message(system_prompt, user_prompt):

    messages = [
        {
            "role": "system",
            "content": system_prompt
        },
        {
            "role": "user",
            "content": [
                {
                    "type": "text",
                    "text": user_prompt
                }
            ]
        }
    ]

    return messages


def format_docs(docs):

    def extract_headings(doc):
        headings = []
        for heading_idx in ['Heading 3', 'Heading 4', 'Heading 5']:
            h_num = heading_idx[-1]
            if heading_idx not in doc.metadata:
                continue
            title = doc.metadata[heading_idx]
            if title != "":
                heading = f"    <h{h_num}>{title}</h{h_num}>"
                headings.append(heading)
        return '\n'.join(headings)

    return "\n\n---\n\n".join(
        [ f"""{doc.page_content}""" for doc in docs ]
    )


def flexible_split(numbers: list, max_group_size: int = 15) -> list:
    """
    Splits a list into smaller groups aiming for a maximum group size, with flexibility for near-equal splitting.

    Args:
        numbers (List[int]): The list of items to split.
        max_group_size (int): The ideal maximum size for each group.

    Returns:
        List[List[int]]: A list of smaller groups.
    """
    n = len(numbers)

    if n <= max_group_size:
        # If the list is already smaller than the max size, return it as one group
        return [numbers]

    # Calculate the number of groups needed
    num_groups = max(1, (n + max_group_size - 1) // max_group_size)

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

def cluster_numbers_dbscan(numbers, eps=10):
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


def split_list(all_idx_list, eps=10, max_group_size=13):
    idx_group = []

    if len(all_idx_list) < max_group_size:
        idx_group = [all_idx_list]
        return idx_group
    else:
        cluster_list = cluster_numbers_dbscan(all_idx_list, eps=eps)
        for idx_list in cluster_list:
            if len(idx_list) < max_group_size:
                idx_group.append(idx_list)
            else:
                idx_group += flexible_split(idx_list, max_group_size=max_group_size)

    return idx_group


def remove_duplicates_by_id(docs):
    r"""
    Remove duplicate documents based on the value of <chunk data-index=(\d+)>
    found in doc.page_content.

    If multiple docs have the same chunk data-index value,
    only the first doc is kept and the rest are discarded.
    """
    unique_docs = []
    seen_indexes = set()

    pattern = re.compile(r'<chunk data-index=(\d+)>')

    for doc in docs:
        match = pattern.search(doc.page_content)
        chunk_index = match.group(1)
        if chunk_index not in seen_indexes:
            unique_docs.append(doc)
            seen_indexes.add(chunk_index)

    return unique_docs


def extract_seq_numbers(text):
    """
    Extract number or range from text.
    Expand range to discrete numbers, return list of sequences
    """

    pattern = r'\b\d+(?:\s*-\s*\d+)?\b'
    matches = re.findall(pattern, text)
    numbers = []
    for match in matches:
        if '-' in match:
            try:
                lower, upper = [int(n.strip()) for n in match.split('-')]
#                numbers.extend(range(lower, upper + 1))
            except Exception:
                continue
        else:
            try:
                numbers.append(int(match))
            except Exception:
                continue
    return sorted(set(numbers))


def convert_dtype(df, cols):
    """
    DataFrame의 컬럼별 데이터 타입을 검사하여:
    1. 타입이 cols에서 지정한 dtype과 일치하면 유지
    2. 변환 가능하면 해당 dtype으로 변환
    3. 변환 불가능하면 NaN으로 변경하여 필터링

    Parameters:
        df (pd.DataFrame): 원본 데이터프레임
        cols (dict): {컬럼명: 기대하는 데이터 타입} 형태의 딕셔너리

    Returns:
        pd.DataFrame: 정제된 데이터프레임
    """
    def safe_cast(value, target_type):
        """
        값이 target_type으로 변환 가능하면 변환하고, 불가능하면 NaN 반환
        """
        try:
            if isinstance(value, target_type):  # 이미 올바른 타입이면 그대로 반환
                return value
            return target_type(value)  # 변환 가능하면 변환
        except (ValueError, TypeError):  # 변환 불가능하면 NaN
            return np.nan

    for col, dtype in cols.items():
        df[col] = df[col].apply(lambda x: safe_cast(x, dtype))

    return df


def truncate_sequences(text: str, seq_type='AA', n = 20, remainder=2) -> str:
    """
    Finds any stretch of amino acid / nucleic acid characters >= n in length.
    Then retains only the first 2 and last 2 characters of that stretch.
    """
    blocklist = ['DESCRIP', 'DETAIL', 'INVENT', 'RELATE', 'APPLI', 'TECHNI', 'FIELD', 'CHARACTER']
    if seq_type == 'NT':
        residues = set_NT
    elif seq_type == 'AA':
        residues = set_AA
    pattern = rf"[{residues}]{{{n},}}"

    if n < 2 * remainder:
        raise ValueError(f"`n` must be at least twice the `remainder` (got n={n}, remainder={remainder})")

    def replacer(match: re.Match) -> str:
        seq = match.group(0)
        for word in blocklist:
            if word in seq:
                return seq
        return seq_type + ' SEQ'

    return re.sub(pattern, replacer, text)
