"""Offline regression checks for names supplied to experiment extraction."""
import sys
import unittest
from pathlib import Path

import pandas as pd
from langchain_core.documents import Document

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from codes.rag.assistant import Assistant
from codes.rag.find_pair import PairAbNameExpNode

PROMPTS = ROOT / 'prompt'


class RecordingModel:
    def __init__(self):
        self.inputs = []

    def batch(self, messages):
        self.inputs.extend(messages)
        return ['[]'] * len(messages)


class ExperimentAntibodyNameTests(unittest.TestCase):
    def test_match_names_in_whole_context(self):
        node = object.__new__(PairAbNameExpNode)
        for label, context, names, expected in (
            ('single', 'MAB1 binds TARGET_B.', ['MAB1'], {'MAB1'}),
            ('case', 'mab1 binds TARGET_B.', ['MAB1'], {'mab1'}),
            ('repeated', 'MAB1 binds. MAB1 was tested.', ['MAB1'], {'MAB1'}),
            ('multiple', 'MAB1 and MAB2 were tested.', ['MAB1', 'MAB2', 'MAB3'], {'MAB1', 'MAB2'}),
            ('literal', 'AB(1)+ and AB.2; ABX2 is different.', ['AB(1)+', 'AB.2'], {'AB(1)+', 'AB.2'}),
            ('absent', 'Other antibodies were tested.', ['MAB1'], set()),
            ('empty-context', '', ['MAB1'], set()),
            ('no-candidates', 'MAB1 was tested.', [], set()),
        ):
            with self.subTest(case=label):
                result = node.mining_names(context, names)
                self.assertEqual(set(result), expected)
                self.assertEqual(len(result), len(expected))

    def test_existing_substring_and_case_preservation(self):
        node = object.__new__(PairAbNameExpNode)
        # This fix does not introduce word boundaries or canonicalize names.
        self.assertEqual(set(node.mining_names('preMAB1suffix mab1', ['MAB1'])),
                         {'MAB1', 'mab1'})

    def test_real_node_passes_context_specific_names_to_model(self):
        assistant = object.__new__(Assistant)
        assistant.dirs = {'prompt': str(PROMPTS), 'example': str(PROMPTS / 'example')}
        assistant.system_prompt = 'Offline fixture'
        assistant.model = RecordingModel()
        node = PairAbNameExpNode(assistant, prompt=str(PROMPTS), batch_size=2)
        state = {
            'ag_out': pd.DataFrame([{'name': 'TARGET_B', 'organism': 'human', 'seq_id_no': 20}]),
            'ab_pair_named': {'VH_VL': pd.DataFrame([
                {'name': 'MAB1; MAB2', 'heavy_seq_id_no': 10, 'light_seq_id_no': 11},
            ])},
        }
        texts = ['MAB1 binds TARGET_B. MAB1 was tested.',
                 'mab2 binds TARGET_B.', 'No candidate is mentioned.']
        docs = {'binding_exp_dict': {
            f'Example {i}': [Document(page_content=text)] for i, text in enumerate(texts, 1)
        }}
        result = node.execute(state, docs)
        expected_lists = ['-MAB1\n', '-mab2\n', '-\n']
        records = result['pair_ab_name_experiment_raw']
        self.assertEqual([record['antibody'] for record in records], expected_lists)
        self.assertEqual(len(assistant.model.inputs), 3)
        for messages, record, expected in zip(assistant.model.inputs, records, expected_lists):
            self.assertEqual([message.type for message in messages], ['system', 'human'])
            human = messages[1].content
            antibody_section = human.split('## Antibody List:')[-1].split('## Answer:')[0]
            self.assertEqual(antibody_section.strip(), expected.strip())
            self.assertIn(record['context'], human)
        self.assertEqual(result['pair_ab_name_experiment_antigen_index_source'], 'ag_out')


if __name__ == '__main__':
    unittest.main()
