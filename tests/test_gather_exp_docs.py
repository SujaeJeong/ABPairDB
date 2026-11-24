"""Offline regression checks for experiment body collection."""
import sys
import unittest
from pathlib import Path
from langchain_core.documents import Document

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from codes.preprocess.split_docs import GatherExpDocs

def body_chunk(content):
    return Document(
        page_content=f'<chunk data-index=0>\nPage_content:\n{content}\n</chunk>',
        metadata={'Heading 5': 'Example 1'},
    )

def collect_binding_groups(docs):
    node = GatherExpDocs()
    state = {'combined_docs': docs, 'idx_dict': {'VH': [10], 'VL': [11]}}
    return node.filter_exps(node.execute(state)['exp_dict'])

def assert_body_survives_collection(parts):
    groups = collect_binding_groups([body_chunk(part) for part in parts])

    assert list(groups) == ['Example 1']
    assert len(groups['Example 1']) == 1
    doc = groups['Example 1'][0]
    assert doc.page_content == 'MAB1 SEQ ID NO: 10 has KD = 5 nM.'
    assert doc.metadata['Heading 5'] == 'Example 1'
    assert doc.metadata['SEQ_ID_NO'] == [10]

class GatherExpDocsTests(unittest.TestCase):
    def test_single(self):
        assert_body_survives_collection(['<h5>Example 1</h5>MAB1 SEQ ID NO: 10 has KD = 5 nM.'])

    def test_two_overlapping(self):
        assert_body_survives_collection(['<h5>Example 1</h5>MAB1 SEQ ID NO: 10 has ', 'has KD = 5 nM.'])

    def test_three_overlapping(self):
        assert_body_survives_collection(['<h5>Example 1</h5>MAB1 SEQ ID NO: 10 has ', 'has KD = ', 'KD = 5 nM.'])

    def test_three_disjoint(self):
        assert_body_survives_collection(['<h5>Example 1</h5>MAB1 ', 'SEQ ID NO: 10 has ', 'KD = 5 nM.'])

    def test_no_experiment_body_has_no_binding_groups(self):
        docs = [Document(page_content='Background', metadata={'Heading 4': 'Background'})]
        assert collect_binding_groups(docs) == {}

    def test_table_only_retains_measurement_and_heading(self):
        table = body_chunk('MAB1 KD = 5 nM.')
        table.metadata.update({
            'id': 'TABLE-US-00001', 'index': '1', 'category': 'experiment result',
        })
        groups = collect_binding_groups([table])

        assert list(groups) == ['Example 1']
        assert len(groups['Example 1']) == 1
        assert 'MAB1 KD = 5 nM.' in groups['Example 1'][0].page_content

    def test_single_body_keeps_referenced_table_in_same_experiment(self):
        body = body_chunk('<h5>Example 1</h5>MAB1 KD values are in Table 1.')
        table = body_chunk('MAB1 KD = 5 nM.')
        table.metadata.update({
            'Heading 5': 'Results', 'id': 'TABLE-US-00001',
            'index': '1', 'category': 'experiment result',
        })
        groups = collect_binding_groups([body, table])

        assert list(groups) == ['Example 1']
        assert [doc.page_content for doc in groups['Example 1']] == [
            'MAB1 KD values are in Table 1.', table.page_content,
        ]
        assert all(doc.metadata['Heading 5'] == 'Example 1'
                   for doc in groups['Example 1'])

if __name__ == '__main__':
    unittest.main()
