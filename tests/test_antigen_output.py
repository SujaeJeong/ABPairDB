"""Offline checks for antigen preservation and public JSON references."""
import copy
import sys
import unittest
from pathlib import Path

import pandas as pd

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from codes.rag.find_ag import AgMainNode
from scripts.run_extraction import _antigen_output, _measurement_records, build_public_output


def antigen(name, seq):
    return dict(name=name, organism='human', abbreviation=name, seq_id_no=seq)


class AntigenOutputTests(unittest.TestCase):
    def setUp(self):
        self.node = object.__new__(AgMainNode)
        self.detail = pd.DataFrame([antigen('A', 10), antigen('B', 20)])

    def merge(self, detail, main):
        return _antigen_output({'ag_detail': detail, 'ag_main': main, 'ag': main}, self.node)

    def export(self, detail, main, indices):
        qa = {'ag_detail': detail.copy(deep=True), 'ag_main': main.copy(deep=True),
              'ag': main.copy(deep=True), 'ab_merged': {}}
        qa['ag_out'] = _antigen_output(qa, self.node)
        for key in ('pair_ab_name_experiment', 'pair_no_name_experiment'):
            qa[key] = pd.DataFrame([{'ag_idx': idx, 'measurement': 'KD', 'value': 5}
                                    for idx in indices])
            qa[key + '_antigen_index_source'] = 'ag_out'
        before = copy.deepcopy(qa)
        config = {'qa': {'assistant': {'model': {'model_name': 'offline'},
                                      'embedding': {'embedding_model_name': 'offline'}}}}
        output = build_public_output('TEST', {'title': 'Test', 'source_url': ''},
                                     {'qa': qa}, ROOT / 'config/release.yaml', config)
        for key, value in before.items():
            if isinstance(value, pd.DataFrame):
                pd.testing.assert_frame_equal(qa[key], value)
        return output

    def test_selected_or_reordered_main_does_not_drop_or_reorder_details(self):
        for main in (self.detail.iloc[[1]], self.detail.iloc[::-1]):
            with self.subTest(indices=main.index.tolist()):
                result = self.merge(self.detail, main)
                self.assertEqual(result.name.tolist(), ['A', 'B'])
                self.assertEqual(result.seq_id_no.tolist(), [10, 20])

    def test_unnumbered_main_keeps_numbered_details_and_attributes(self):
        detail = self.detail.assign(mutation=['variant-a', 'variant-b'])
        main = pd.DataFrame([antigen('A', None), antigen('B', None)])
        before = detail.copy(deep=True)
        result = self.merge(detail, main)
        self.assertEqual(result.seq_id_no.tolist(), [10, 20])
        self.assertEqual(result.mutation.tolist(), ['variant-a', 'variant-b'])
        pd.testing.assert_frame_equal(detail, before)

    def test_missing_main_and_missing_detail_sequence_keep_details(self):
        detail = pd.DataFrame([antigen('A', None), antigen('B', 20)])
        result = self.merge(detail, self.detail.iloc[:0])
        self.assertEqual(result.name.tolist(), ['A', 'B'])
        self.assertTrue(pd.isna(result.seq_id_no.iloc[0]))

    def test_same_name_distinct_or_repeated_details_are_preserved(self):
        detail = pd.DataFrame([antigen('A', 10), antigen('A', 20), antigen('A', 20)])
        result = self.merge(detail, pd.DataFrame([antigen('A', None)]))
        self.assertEqual(result.seq_id_no.tolist(), [10, 20, 20])

    def test_only_unmatched_unnumbered_main_is_appended(self):
        main = pd.DataFrame([antigen('A', None), antigen('C', None), antigen('D', 40)])
        result = self.merge(self.detail, main)
        self.assertEqual(result.name.tolist(), ['A', 'B', 'C'])
        self.assertTrue(pd.isna(result.seq_id_no.iloc[2]))

    def test_empty_details_allow_unnumbered_supplement(self):
        result = self.merge(self.detail.iloc[:0], pd.DataFrame([antigen('C', None)]))
        self.assertEqual(result.name.tolist(), ['C'])

    def test_json_references_both_measurement_sources_after_sparse_indices(self):
        detail = self.detail.set_axis([4, 9])
        output = self.export(detail, self.detail.iloc[::-1], [1, 0])
        self.assertEqual([m['ag_idx'] for m in output['measurements']], [1, 0, 1, 0])
        self.assertEqual([output['antigens'][m['ag_idx']]['name']
                          for m in output['measurements']], ['B', 'A', 'B', 'A'])
        self.assertEqual({m['antibody_reference'] for m in output['measurements']},
                         {'named_antibody', 'sequence_pair'})

    def test_contiguous_indices_and_zero_sequence_are_not_shifted(self):
        detail = pd.DataFrame([antigen('A', 0), antigen('B', 20)])
        output = self.export(detail, detail, [0, 1])
        self.assertEqual([m['ag_idx'] for m in output['measurements']], [0, 1, 0, 1])
        self.assertEqual(output['antigens'][0]['seq_id_no'], 0)

    def test_unknown_model_reference_is_filtered_and_counted(self):
        output = self.export(self.detail, self.detail, [3])
        self.assertEqual(output['measurements'], [])
        for source in ('named_antibody', 'sequence_pair'):
            self.assertEqual(output['measurement_index_validation'][source]['export']['excluded_rows'], 1)

    def test_legacy_nonempty_measurements_are_not_reinterpreted(self):
        for source in (None, 'ag_detail', 'unknown'):
            with self.subTest(source=source):
                qa = {'ag_out': self.detail, 'pair_ab_name_experiment': pd.DataFrame([{'ag_idx': 0}])}
                if source is not None:
                    qa['pair_ab_name_experiment_antigen_index_source'] = source
                with self.assertRaisesRegex(ValueError, 'legacy or unknown'):
                    _measurement_records(qa)

    def test_export_uses_ag_out_order_without_detail_remapping(self):
        qa = {
            'ag_detail': self.detail.set_axis([4, 9]),
            'ag_out': self.detail.iloc[::-1].reset_index(drop=True),
            'pair_ab_name_experiment': pd.DataFrame([{'ag_idx': 0}, {'ag_idx': 1}]),
            'pair_ab_name_experiment_antigen_index_source': 'ag_out',
        }
        records, _ = _measurement_records(qa)
        self.assertEqual([qa['ag_out'].iloc[row['ag_idx']]['name'] for row in records], ['B', 'A'])

    def test_real_nodes_to_json_keep_supplement_and_rejection_audit(self):
        from test_experiment_antigen_indices import ExperimentAntigenIndexTests
        from codes.rag.find_pair import PairAbNameExpNode, PairNoNameExpNode
        fixture = ExperimentAntigenIndexTests()
        qa = fixture.state()
        qa['ab_merged'] = {}
        for cls in (PairAbNameExpNode, PairNoNameExpNode):
            node, _ = fixture.node(cls, [2, 3, -1, None])
            qa.update(node.execute(qa, fixture.docs()))
        config = {'qa': {'assistant': {'model': {'model_name': 'offline'},
                                      'embedding': {'embedding_model_name': 'offline'}}}}
        output = build_public_output('TEST', {'title': 'Test', 'source_url': ''},
                                     {'qa': qa}, ROOT / 'config/release.yaml', config)
        self.assertEqual([m['ag_idx'] for m in output['measurements']], [2, 2])
        self.assertEqual(output['antigens'][2]['name'], 'C')
        for audit in output['measurement_index_validation'].values():
            self.assertEqual(audit['extraction']['excluded_rows'], 3)
            self.assertEqual(audit['export']['excluded_rows'], 0)

    def test_export_rejects_noncontiguous_ag_out_instead_of_renumbering(self):
        with self.assertRaisesRegex(ValueError, 'ag_out'):
            _measurement_records({'ag_out': self.detail.set_axis([4, 9])})


if __name__ == '__main__':
    unittest.main()
