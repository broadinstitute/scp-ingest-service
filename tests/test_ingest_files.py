import unittest
import sys
import gzip
from unittest.mock import MagicMock

sys.path.append("../ingest")
from ingest_files import IngestFiles


def raise_error(*args):
    raise Exception


class TestIngestFiles(unittest.TestCase):
    def test_is_gzipped(self):
        zipped_path = "../tests/data/mtx/unsorted_mtx.txt.gz"
        self.assertTrue(IngestFiles.is_gzipped(zipped_path))
        gzip_extension = "../tests/data/mtx/unsorted_mtx.txt.gzip"
        self.assertTrue(IngestFiles.is_gzipped(gzip_extension))
        not_zipped = "../tests/data/expression_matrix_bad_duplicate_gene.txt"
        self.assertFalse(IngestFiles.is_gzipped(not_zipped))

        # Test exception
        gzip.open = MagicMock()
        gzip.open.side_effect = raise_error
        self.assertRaises(ValueError, IngestFiles.is_gzipped, zipped_path)