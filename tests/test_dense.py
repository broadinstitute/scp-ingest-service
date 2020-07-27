import unittest
import sys
from unittest.mock import patch
from mock_data.dense_matrix_19_genes_100k_cells_txt.gene_models_0 import gene_models

sys.path.append("../ingest")
from expression_files.dense_ingestor import DenseIngestor


class TestDense(unittest.TestCase):
    def test_has_gene_keyword_false(self):
        "Validates validate_gene_keyword() returns false correctly"
        expression_matrix = DenseIngestor(
            '../tests/data/expression_matrix_bad_missing_keyword.txt',
            '5d276a50421aa9117c982845',
            '5dd5ae25421aa910a723a337',
            tracer=None,
        )
        self.assertFalse(expression_matrix.has_gene_keyword())

    def test_has_gene_keyword_true(self):
        "Validates validate_gene_keyword() returns true correctly"
        expression_matrix = DenseIngestor(
            '../tests/data/dense_expression_matrix.txt',
            '5d276a50421aa9117c982845',
            '5dd5ae25421aa910a723a337',
            tracer=None,
        )
        self.assertTrue(expression_matrix.has_gene_keyword())

    def test_has_unique_header_false(self):
        "Validates validate_unique_header() returns false correctly"
        expression_matrix = DenseIngestor(
            '../tests/data/expression_matrix_non_unique.txt',
            '5d276a50421aa9117c982845',
            '5dd5ae25421aa910a723a337',
            tracer=None,
        )
        self.assertFalse(expression_matrix.has_unique_header())

    def test_has_unique_header_true(self):
        "Validates validate_unique_header() returns true correctly"
        expression_matrix = DenseIngestor(
            '../tests/data/dense_expression_matrix.txt',
            '5d276a50421aa9117c982845',
            '5dd5ae25421aa910a723a337',
            tracer=None,
        )
        self.assertTrue(expression_matrix.has_unique_header())

    def test_duplicate_gene(self):
        expression_matrix = DenseIngestor(
            '../tests/data/expression_matrix_bad_duplicate_gene.txt',
            '5d276a50421aa9117c982845',
            '5dd5ae25421aa910a723a337',
            tracer=None,
        )
        with self.assertRaises(ValueError):
            for gene in expression_matrix.transform():
                pass

    def test_is_valid_format_false(self):
        expression_matrix = DenseIngestor(
            '../tests/data/expression_matrix_bad_missing_keyword.txt',
            '5d276a50421aa9117c982845',
            '5dd5ae25421aa910a723a337',
            tracer=None,
        )
        self.assertFalse(expression_matrix.is_valid_format())

    def test_is_valid_format_true(self):
        expression_matrix = DenseIngestor(
            '../tests/data/dense_expression_matrix.txt',
            '5d276a50421aa9117c982845',
            '5dd5ae25421aa910a723a337',
            tracer=None,
        )
        self.assertTrue(expression_matrix.is_valid_format())

    @patch('expression_files.expression_files.GeneExpression.load')
    @patch('expression_files.dense_ingestor.DenseIngestor.transform', return_value= [('foo1', 'foo2')])
    def test_execute_ingest(self, mock_load, mock_transform):
        "Validates functions in execute_ingest() are called "
        expression_matrix = DenseIngestor(
            '../tests/data/dense_matrix_19_genes_1000_cells.txt',
            '5d276a50421aa9117c982845',
            '5dd5ae25421aa910a723a337'
        )
        expression_matrix.execute_ingest()
        self.assertTrue(mock_transform.called)
        self.assertTrue(mock_load.called)

    def test_transform_fn(self):
        """ Tests to ensure transform function is creating
        gene data model correctly"""

        expression_matrix = DenseIngestor(
            '../tests/data/dense_matrix_19_genes_1000_cells.txt',
            '5d276a50421aa9117c982845',
            '5dd5ae25421aa910a723a337'
        )
        for actual_gene_models, actual_data_arrays in expression_matrix.transform():
            # _id is a unique identifier and can not be predicted
            # so we exclude it from the comparison
            for actual_gene_model in  actual_gene_models:
                del actual_gene_model['_id']
                gene_name = actual_gene_model['name']
                self.assertEqual(actual_gene_model, gene_models[gene_name])
