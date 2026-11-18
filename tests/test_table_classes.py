"""Offline regression checks for table class cleanup in both input paths."""
import sys
import unittest
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

from bs4 import BeautifulSoup

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from codes.preprocess import table as table_module


class TableClassTests(unittest.TestCase):
    def collect(self, html):
        state = {'patent_id': 'OFFLINE', 'full_html': html}
        if hasattr(table_module, 'requests'):
            with patch.object(table_module.requests, 'get', return_value=SimpleNamespace(text=html)):
                return table_module.TableCrawlNode().execute(state)['tables']
        return table_module.TableCrawlNode().execute(state)['tables']

    def test_class_cleanup_preserves_other_classes_and_contents(self):
        for tag_name, removable in (
            ('tables', 'description-table'), ('tr', 'description-tr'), ('td', 'description-td'),
        ):
            for label, classes, expected in (
                ('absent', None, None),
                ('empty', [], None),
                ('target-only', [removable], None),
                ('other-only', ['custom'], ['custom']),
                ('mixed', ['before', removable, 'after'], ['before', 'after']),
                ('repeated-target', [removable, 'custom', removable], ['custom']),
                ('similar-name', [removable + '-custom'], [removable + '-custom']),
            ):
                with self.subTest(tag=tag_name, case=label):
                    soup = BeautifulSoup(
                        '<tables id="TABLE-US-00001"><table><tr><td colspan="2">'
                        'MAB1 KD = 5 nM.</td></tr></table></tables>', 'html.parser')
                    if classes is not None:
                        soup.find(tag_name)['class'] = classes
                    tables = self.collect(str(soup))
                    self.assertEqual(list(tables), ['TABLE-US-00001'])
                    output = tables['TABLE-US-00001']['table_html']
                    self.assertEqual(output.find(tag_name).get('class') if tag_name != 'tables'
                                     else output.get('class'), expected)
                    self.assertEqual(output.get_text(), 'MAB1 KD = 5 nM.')
                    self.assertEqual(output.td['colspan'], '2')
                    self.assertEqual(len(output.find_all('tr')), 1)
                    self.assertEqual(len(output.find_all('td')), 1)

    def test_docbook_conversion_cleans_all_three_classes(self):
        tables = self.collect(
            '<tables id="TABLE-US-00001" class="description-table keep-table">'
            '<tgroup><row class="description-tr keep-row">'
            '<entry class="description-td keep-cell">KD = 5 nM.</entry>'
            '</row></tgroup></tables>')
        output = tables['TABLE-US-00001']['table_html']
        self.assertEqual(output['class'], ['keep-table'])
        self.assertEqual(output.tr['class'], ['keep-row'])
        self.assertEqual(output.td['class'], ['keep-cell'])
        self.assertEqual(output.get_text(), 'KD = 5 nM.')
        self.assertIsNone(output.find('row'))
        self.assertIsNone(output.find('entry'))


if __name__ == '__main__':
    unittest.main()
