"""Exercise real experiment nodes offline with deliberately different antigen tables."""
import copy
import json
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace

import pandas as pd
from langchain_core.documents import Document
from langchain_core.prompts import PromptTemplate

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from codes.rag.find_pair import (
    PairAbNameExpNode, PairNoNameExpNode, PairAbNameNode, PairAbUnnamedNode,
)

PROMPTS = ROOT.parent / '03_configs/prompts' if ROOT.name == '02_code' else ROOT / 'prompt'


def antigen(name, seq):
    return dict(name=name, organism='human', abbreviation=name, seq_id_no=seq)


class FakeModel:
    def __init__(self, indices):
        self.inputs = []
        self.response = json.dumps([
            {'ag_idx': index, 'ab_name': 'MAB1', 'heavy_seq_id_no': 10,
             'light_seq_id_no': 11, 'measurement': 'KD', 'value': str(i + 1),
             'unit': 'nM', 'approximate value': False, 'reference': 0,
             'antibody_format': 'IgG', 'experiment_summary': 'binding assay'}
            for i, index in enumerate(indices)
        ])

    def batch(self, inputs):
        self.inputs.extend(inputs)
        return [self.response for _ in inputs]


class ExperimentAntigenIndexTests(unittest.TestCase):
    def state(self):
        return {
            'ag_detail': pd.DataFrame([antigen('A', 1), antigen('B', 2)], index=[4, 9]),
            'ag_out': pd.DataFrame([antigen('B', 2), antigen('A', 1), antigen('C', None)]),
            'ab_pair_named': {'VH_VL': pd.DataFrame([
                dict(name='MAB1', heavy_seq_id_no=10, light_seq_id_no=11)])},
        }

    def node(self, cls, indices):
        model = FakeModel(indices)
        assistant = SimpleNamespace(
            model=model, system_prompt='Offline fixture',
            create_prompt=lambda **kwargs: PromptTemplate.from_template('{antigen}\n{context}'),
        )
        return cls(assistant, prompt=str(PROMPTS)), model

    def docs(self):
        return {'binding_exp_dict': {'Example 1': [Document(
            page_content='MAB1 binds C with KD = 5 nM.', metadata={'SEQ_ID_NO': [10, 11]})]}}

    def test_real_nodes_present_ag_out_and_filter_invalid_labels(self):
        labels = [0, 1, 2, 3, -1, None, 0.5, True, 'not-an-index']
        for cls in (PairAbNameExpNode, PairNoNameExpNode):
            with self.subTest(node=cls.__name__):
                node, model = self.node(cls, labels)
                state = self.state()
                before = copy.deepcopy(state)
                result = node.execute(state, self.docs())
                frame = result[node.task]
                self.assertEqual(frame.ag_idx.tolist(), [0, 1, 2])
                self.assertEqual(result[node.task + '_antigen_index_source'], 'ag_out')
                audit = result[node.task + '_antigen_index_validation']
                self.assertEqual(audit['input_rows'], 9)
                self.assertEqual(audit['excluded_rows'], 6)
                self.assertIn('-1', audit['excluded_indices'])
                prompt = result[node.task + '_raw'][0]['antigen']
                self.assertIn('AG_IDX: 0 | NAME: B', prompt)
                self.assertIn('AG_IDX: 1 | NAME: A', prompt)
                self.assertIn('AG_IDX: 2 | NAME: C', prompt)
                self.assertNotIn('AG_IDX: 4', prompt)
                self.assertEqual(result[node.task + '_raw'][0]['response'], model.response)
                self.assertEqual(len(model.inputs), 1)
                pd.testing.assert_frame_equal(state['ag_detail'], before['ag_detail'])
                pd.testing.assert_frame_equal(state['ag_out'], before['ag_out'])

    def test_all_pair_prompt_builders_use_the_given_index_once(self):
        for cls in (PairAbNameExpNode, PairNoNameExpNode, PairAbNameNode, PairAbUnnamedNode):
            with self.subTest(node=cls.__name__):
                node = object.__new__(cls)
                prompt = node.create_ag_prompt(self.state()['ag_out'])
                self.assertEqual(len(prompt.splitlines()), 3)
                self.assertNotIn('ag_idx: **', prompt)
                self.assertIn('AG_IDX: 0 | NAME: B', prompt)

    def test_no_context_still_records_index_contract(self):
        for cls in (PairAbNameExpNode, PairNoNameExpNode):
            with self.subTest(node=cls.__name__):
                node, model = self.node(cls, [0])
                result = node.execute(self.state(), {'binding_exp_dict': {}})
                self.assertTrue(result[node.task].empty)
                self.assertEqual(result[node.task + '_antigen_index_source'], 'ag_out')
                self.assertEqual(result[node.task + '_antigen_index_validation']['excluded_rows'], 0)
                self.assertEqual(model.inputs, [])

    def test_no_named_antibodies_still_records_index_contract(self):
        node, model = self.node(PairAbNameExpNode, [0])
        state = self.state()
        state['ab_pair_named']['VH_VL'] = state['ab_pair_named']['VH_VL'].iloc[:0]
        result = node.execute(state, self.docs())
        self.assertEqual(result[node.task + '_antigen_index_source'], 'ag_out')
        self.assertTrue(result[node.task].empty)
        self.assertEqual(model.inputs, [])

    def test_noncontiguous_ag_out_is_rejected_before_model_call(self):
        for cls in (PairAbNameExpNode, PairNoNameExpNode):
            with self.subTest(node=cls.__name__):
                node, model = self.node(cls, [0])
                state = self.state()
                state['ag_out'].index = [2, 4, 6]
                with self.assertRaisesRegex(ValueError, 'ag_out'):
                    node.execute(state, self.docs())
                self.assertEqual(model.inputs, [])

    def test_empty_ag_out_filters_all_model_references(self):
        for cls in (PairAbNameExpNode, PairNoNameExpNode):
            with self.subTest(node=cls.__name__):
                node, _ = self.node(cls, [0, -1])
                state = self.state()
                state['ag_out'] = state['ag_out'].iloc[:0]
                result = node.execute(state, self.docs())
                self.assertTrue(result[node.task].empty)
                self.assertEqual(result[node.task + '_antigen_index_validation']['excluded_rows'], 2)

    def test_batch_parsing_preserves_per_response_candidate_filters(self):
        node, model = self.node(PairAbNameExpNode, [0, 3])
        frame, audits = node.parse_antigen_response(
            [model.response, model.response], self.state()['ag_out'],
            filter_seq_id_no={'ab_name': [['MAB1'], ['OTHER']]})
        self.assertEqual(frame.ag_idx.tolist(), [0])
        self.assertEqual(sum(a['input_rows'] for a in audits), 4)
        self.assertEqual(sum(a['excluded_rows'] for a in audits), 2)


if __name__ == '__main__':
    unittest.main()
