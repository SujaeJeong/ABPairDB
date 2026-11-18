"""Offline checks for rejecting prepared inputs with no sequences."""
import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from scripts import run_extraction as runner
from codes.preprocess.categorize_protein import ANARCIINode


class PreparedInputTests(unittest.TestCase):
    def setUp(self):
        temporary = tempfile.TemporaryDirectory(prefix='prepared-input-test-')
        self.addCleanup(temporary.cleanup)
        self.root = Path(temporary.name)
        (self.root / 'html').mkdir()
        (self.root / 'anarcii').mkdir()
        (self.root / 'html/TEST.html').write_text('<html>Offline input</html>')
        (self.root / 'patent_metadata.csv').write_text(
            'Patent_ID,GBReference_title\nTEST,Offline input\n')
        self.sequence_path = self.root / 'anarcii/TEST.json'
        self.write_sequences({})
        self.args = ['--patent-id', 'TEST', '--input-dir', str(self.root),
                     '--config', str(ROOT / 'config/release.yaml')]

    def write_sequences(self, sequences):
        self.sequence_path.write_text(json.dumps({'sequences': sequences}))

    def test_empty_sequences_rejected_with_input_path(self):
        with self.assertRaisesRegex(ValueError, 'sequences is empty') as error:
            runner.validate_prepared_input(self.root, 'TEST')
        self.assertIn(str(self.sequence_path), str(error.exception))

    def test_both_modes_stop_before_runtime_or_output(self):
        output = self.root / 'output.json'
        work = self.root / 'work'
        for mode in (['--validate-input'], ['--output', str(output), '--work-dir', str(work)]):
            with self.subTest(mode=mode), patch.object(runner, '_run_pipeline') as pipeline, \
                    patch.object(runner, '_load_runtime_config') as config:
                with self.assertRaisesRegex(ValueError, 'sequences is empty'):
                    runner.main(self.args + mode)
                pipeline.assert_not_called()
                config.assert_not_called()
                self.assertFalse(output.exists())
                self.assertFalse(work.exists())

    def test_cli_returns_failure_for_empty_sequences(self):
        for mode in (['--validate-input'], ['--output', str(self.root / 'output.json')]):
            with self.subTest(mode=mode):
                result = subprocess.run(
                    [sys.executable, str(ROOT / 'scripts/run_extraction.py'), *self.args, *mode],
                    capture_output=True, text=True, check=False)
                self.assertNotEqual(result.returncode, 0)
                self.assertIn('sequences is empty', result.stderr)
                self.assertEqual(result.stdout, '')
                self.assertFalse((self.root / 'output.json').exists())

    def test_one_sequence_still_validates_and_loads(self):
        self.write_sequences({'1': {'sequence': 'EVQL', 'category': 'VH'}})
        info = runner.validate_prepared_input(self.root, 'TEST')
        self.assertEqual(info['n_sequences'], 1)
        result = ANARCIINode(str(self.root / 'anarcii')).execute({'patent_id': 'TEST'})
        self.assertEqual(result['idx_dict']['VH'], [1])

    def test_existing_structure_and_field_checks_remain(self):
        for sequences, message in (
            ([], 'must contain a sequences object'),
            ({'1': {'sequence': '', 'category': 'VH'}}, 'missing sequence'),
            ({'1': {'sequence': 'EVQL'}}, 'missing category'),
        ):
            with self.subTest(sequences=sequences):
                self.write_sequences(sequences)
                with self.assertRaisesRegex(ValueError, message):
                    runner.validate_prepared_input(self.root, 'TEST')


if __name__ == '__main__':
    unittest.main()
