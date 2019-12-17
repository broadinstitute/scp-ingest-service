"""Test ingest_files.py
These tests verify:
    - Error is thrown for a missing file
PREREQUISITES
Spin up Python 3.6 virtualenv, install Python dependencies in requirements.txt
Note: When CI environment moves to Python 3.7, tests may break due to minor
differences in how the reference issues are serialized

# Run all tests in a manner that shows report_issues output
python3 test_ingest_files.py -s
"""


import sys
import unittest
import mimetypes
from unittest.mock import patch

sys.path.append("../ingest")
from ingest_files import IngestFiles


class TestIngestFiles(unittest.TestCase):
    csv_file_path = '../tests/data/test_1k_cluster_data.csv'
    csv_file_reader = open(csv_file_path, 'rt', encoding='utf-8-sig')
    tsv_file_path = '../tests/data/test_convention.tsv'
    tsv_file_reader = open(tsv_file_path, 'rt', encoding='utf-8-sig')

    def test_ingest_missing_file(self):
        """Should throw error for missing local file
        """
        with self.assertRaises(OSError):
            IngestFiles(
                '/this/file/does/not_exist.txt',
                ['text/csv', 'text/plain', 'text/tab-separated-values'],
            )

    def test_open_csv(self):
        ingest_file = IngestFiles(
            self.csv_file_path, ['text/csv', 'text/plain', 'text/tab-separated-values']
        )
        csv_reader = ingest_file.open_csv(self.csv_file_reader)
        self.assertEqual(
            csv_reader.dialect.delimiter,
            ',',
            'Function did not open file as comma delimited',
        )

    def test_open_tsv(self):
        ingest_file = IngestFiles(self.tsv_file_path, ['text/tab-separated-values'])
        tsv_reader = ingest_file.open_csv(self.tsv_file_reader)
        # Although we're checking for a comma, we opened the file up as a tsv
        # in the function. csv reader changed delimiter to a ','
        self.assertEqual(
            tsv_reader.dialect.delimiter,
            ',',
            'Function did not open file as tab delimited',
        )

    @patch('ingest_files.IngestFiles.open_tsv')
    def test_open_file_tsv(self, mock_open_tsv):
        """Tests if wrapper function calls open_tsv file successfully"""
        ingest_files = IngestFiles(
            '../tests/data/test_convention.tsv',
            ['text/csv', 'text/plain', 'text/tab-separated-values'],
        )
        tsv_file, open_file_object = ingest_files.open_file(ingest_files.file_path)
        mock_open_tsv.assert_called_with(open_file_object)

    @patch('ingest_files.IngestFiles.resolve_path')
    @patch('ingest_files.IngestFiles.open_csv')
    def test_open_file_csv(self, mock_open_csv, mock_resolve_path):
        "Checks to see if wrapper function opens csv file correctly"
        file_path = '../tests/data/test_1k_cluster_data.csv'
        reader = open(file_path, 'rt', encoding='utf-8-sig')
        mock_resolve_path.return_value = (reader, file_path)
        ingest_file = IngestFiles(
            file_path, ['text/csv', 'text/plain', 'text/tab-separated-values']
        )
        ingest_file.open_file(file_path)
        mock_resolve_path.assert_called_with(file_path)
        mock_open_csv.assert_called_with(reader)

    @patch('ingest_files.IngestFiles.resolve_path')
    @patch('ingest_files.IngestFiles.open_txt')
    def test_open_file_txt(self, mock_open_txt, mock_resolve_path):
        "Checks to see if wrapper function opens txt file correctly"
        file_path = '../tests/data/r_format_text.txt'
        reader = open(file_path, 'rt', encoding='utf-8-sig')
        mock_resolve_path.return_value = (reader, file_path)
        ingest_file = IngestFiles(
            file_path, ['text/csv', 'text/plain', 'text/tab-separated-values']
        )
        ingest_file.open_file(file_path)
        mock_resolve_path.assert_called_with(file_path)
        mock_open_txt.assert_called_with(reader)

    # def test_open_file_as_pandas_csv(self):
    #     """Checks to see if wrapper function opens csv file as a pandas dataframe
    #     correctly"""
    #
    # def test_open_file_as_pandas_txt(self):
    #
    # def test_open_file_as_pandas_tsv(self):
