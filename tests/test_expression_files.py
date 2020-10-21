import sys
import unittest
from unittest.mock import patch, MagicMock
from bson.objectid import ObjectId

from pymongo.errors import AutoReconnect

# Dense models
from mock_data.expression.dense_matrices.nineteen_genes_100k_cell_models import (
    nineteen_genes_100k_cell_models,
)

# MTX models
from mock_data.expression.matrix_mtx.AB_toy_data_toy_models import (
    AB_toy_data_toy_data_models,
)
from mock_data.expression.matrix_mtx.one_column_feature_file_data_models import (
    one_column_feature_file_data_models,
)
from mock_data.expression.matrix_mtx.AB_toy_data_toy_unsorted_mtx_models import (
    AB_toy_data_toy_unsorted_mtx_models,
)

sys.path.append("../ingest")
from expression_files.expression_files import GeneExpression
from ingest_files import DataArray
from typing import Dict


def mock_load_genes_batched(documents, collection_name):
    """Enables overwriting of GeneExpression.load() with this placeholder.
    GeneExpression.load() is called multiple times. This method will verify
    data array documents are batched correctly everytime a call is made to
    GeneExpression.load()
    """
    # Assures transform function batches data array creation correctly
    if collection_name == DataArray.COLLECTION_NAME:
        assert GeneExpression.DATA_ARRAY_BATCH_SIZE >= len(documents)


def mock_expression_load(self, *args):
    """Enables overwriting of GeneExpression.load() with this placeholder.
    GeneExpression.load() is called multiple times. This method will verify
    models in the arguments have the expected values.
    """
    documents = args[0]
    collection_name = args[1]
    if not self.test_models:
        model_name = documents[0]["name"]
        if collection_name == GeneExpression.COLLECTION_NAME:
            if model_name in AB_toy_data_toy_data_models["gene_models"]:
                self.test_model = AB_toy_data_toy_data_models
            if model_name in AB_toy_data_toy_unsorted_mtx_models["gene_models"]:
                self.test_models = AB_toy_data_toy_unsorted_mtx_models
            if model_name in one_column_feature_file_data_models["gene_models"]:
                self.test_models = one_column_feature_file_data_models
            if model_name in nineteen_genes_100k_cell_models["gene_models"][model_name]:
                self.test_models = nineteen_genes_100k_cell_models
        if collection_name == DataArray.COLLECTION_NAME:
            if model_name in AB_toy_data_toy_data_models["data_arrays"]:
                self.test_models = AB_toy_data_toy_data_models
            if model_name in AB_toy_data_toy_unsorted_mtx_models["data_arrays"]:
                self.test_models = AB_toy_data_toy_unsorted_mtx_models
            if model_name in one_column_feature_file_data_models["data_arrays"]:
                self.test_models = one_column_feature_file_data_models
            if model_name in nineteen_genes_100k_cell_models["data_arrays"]:
                self.test_models = nineteen_genes_100k_cell_models
    # _id and linear_data_id are unique identifiers and can not be predicted
    # so we exclude it from the comparison
    for document in documents:
        model_name = document["name"]
        if collection_name == GeneExpression.COLLECTION_NAME:
            expected_model = self.test_models["gene_models"][model_name]
            del document["_id"]
            # Sometimes linear_data_id is not deleted in mock models in cases where mocked models are large
            if "linear_data_id" in expected_model:
                del expected_model["linear_data_id"]
            assert document == expected_model
        if collection_name == DataArray.COLLECTION_NAME:
            expected_model = self.test_models["data_arrays"][model_name]
            del document["linear_data_id"]
            # Sometimes linear_data_id is not deleted in mock models in cases where mocked models are large
            if "linear_data_id" in expected_model:
                del expected_model["linear_data_id"]
            assert document == expected_model
    self.models_processed += len(documents)


class TestExpressionFiles(unittest.TestCase):
    def test_check_unique_cells(self):
        client_mock = MagicMock()

        client_mock["data_arrays"].find.return_value = [
            {"values": ["foo3", "foo4", "foo5"]},
            {"values": ["foo6", "foo7", "foo8"]},
        ]

        """Following tests are for matrices that aren't raw counts"""

        with patch(
            "expression_files.expression_files.GeneExpression.get_raw_count_study_file_ids",
            side_effect=None,
            return_value=[],
        ), self.assertRaises(ValueError) as cm:
            header = ["GENE", "foo", "foo2", "foo3"]
            GeneExpression.check_unique_cells(
                header, ObjectId(), ObjectId(), client_mock
            )
            self.assertTrue("contains 1 cells" in str(cm.exception))
            self.assertTrue("foo3" in str(cm.exception))

        # Duplicate header but duplicate values don't appear in same order
        header = ["GENE", "foo", "foo3", "foo2", "foo6"]
        with patch(
            "expression_files.expression_files.GeneExpression.get_raw_count_study_file_ids",
            side_effect=None,
            return_value=None,
        ), self.assertRaises(ValueError) as cm:
            GeneExpression.check_unique_cells(
                header, ObjectId(), ObjectId(), client_mock
            )
        self.assertTrue("contains 2 cells" in str(cm.exception))
        self.assertTrue("foo3" in str(cm.exception))
        self.assertTrue("foo6" in str(cm.exception))

        with patch(
            "expression_files.expression_files.GeneExpression.get_raw_count_study_file_ids",
            side_effect=None,
            return_value=None,
        ):
            header = ["GENE", "foo", "foo2"]
            self.assertTrue(
                GeneExpression.check_unique_cells(
                    header, ObjectId(), ObjectId(), client_mock
                )
            )

        """Following tests are for matrices that are raw counts"""

        with patch(
            "expression_files.expression_files.GeneExpression.get_raw_count_study_file_ids",
            side_effect=None,
            return_value=[
                {"_id": ObjectId("5dd5ae25421aa910a723a337")},
                {"_id": ObjectId("5d276a50421aa9117c982845")},
                {"_id": ObjectId("5f70abd6771a5b0de0cea0f0")},
            ],
        ), self.assertRaises(ValueError) as cm:
            header = ["GENE", "foo", "foo3", "foo2", "foo6"]
            study_id = ObjectId()
            study_file_id = ObjectId("5dd5ae25421aa910a723a337")
            GeneExpression.check_unique_cells(
                header, study_id, study_file_id, client_mock
            )
            client_mock["data_arrays"].find.assert_called_with(
                {
                    "$and": [
                        {"linear_data_type": "Study"},
                        {"array_type": "cells"},
                        {"study_id": study_id},
                        {
                            "$or": [
                                {"study_file_id": ObjectId("5d276a50421aa9117c982845")},
                                {"study_file_id": ObjectId("5f70abd6771a5b0de0cea0f0")},
                            ]
                        },
                    ],
                    "$nor": [{"name": "All Cells"}],
                },
                {"values": 1, "_id": 0},
            )
            self.assertTrue("contains 2 cells" in str(cm.exception))
            self.assertTrue("foo3" in str(cm.exception))
            self.assertTrue("foo6" in str(cm.exception))

        # When no cells are returned from the query
        client_mock["data_arrays"].find.return_value = []
        self.assertTrue(
            GeneExpression.check_unique_cells(
                header, ObjectId(), ObjectId(), client_mock
            )
        )

    def test_get_raw_count_query_filters(self):

        # Tests when there are results outside of current raw counts study file
        query_results = [
            {"_id": ObjectId("5dd5ae25421aa910a723a337")},
            {"_id": ObjectId("5d276a50421aa9117c982845")},
            {"_id": ObjectId("5f70abd6771a5b0de0cea0f0")},
        ]
        expected_results = [
            {"study_file_id": ObjectId("5d276a50421aa9117c982845")},
            {"study_file_id": ObjectId("5f70abd6771a5b0de0cea0f0")},
        ]
        current_study_id = ObjectId("5dd5ae25421aa910a723a337")
        results = GeneExpression.get_raw_count_query_filters(
            current_study_id, query_results, include_study_file_id=False
        )
        self.assertEqual(expected_results, results)

        # Tests when there are not results outside of current raw counts study file
        query_results = [{"_id": ObjectId("5dd5ae25421aa910a723a337")}]
        current_study_id = ObjectId("5dd5ae25421aa910a723a337")
        results = GeneExpression.get_raw_count_query_filters(
            current_study_id, query_results, include_study_file_id=False
        )
        self.assertEqual(None, results)

    def test_create_data_arrays(self):
        _id = ObjectId()
        study_id = ObjectId()
        study_file_id = ObjectId()
        kwargs = {
            "name": "foo",
            "cluster_name": "foo_name",
            "array_type": "foo_type",
            "values": [1, 2, 3, 4, 5],
            "linear_data_type": "data_dtype",
            "linear_data_id": _id,
            "study_id": study_id,
            "study_file_id": study_file_id,
        }

        self.assertRaises(
            TypeError, [GeneExpression.create_data_arrays], "bad_position_arg", **kwargs
        )
        self.assertRaises(
            TypeError, [GeneExpression.create_data_arrays], hi="bad_kwarg", **kwargs
        )
        actual_data_array: Dict = next(GeneExpression.create_data_arrays(**kwargs))
        self.assertEqual(DataArray(**kwargs).__dict__, actual_data_array)

    def test_create_gene_model(self):
        _id = ObjectId()
        study_id = ObjectId()
        study_file_id = ObjectId()
        kwargs = {
            "name": "foo",
            "study_file_id": study_file_id,
            "study_id": study_id,
            "_id": _id,
        }
        self.assertRaises(
            TypeError, [GeneExpression.create_gene_model], "bad_position_arg", **kwargs
        )
        self.assertRaises(
            TypeError, [GeneExpression.create_gene_model], hi="bad_kwarg", **kwargs
        )
        actual_gene_model = GeneExpression.create_gene_model(**kwargs)
        expected_gene_model = GeneExpression.Model(
            searchable_name="foo", gene_id=None, **kwargs
        )
        self.assertEqual(actual_gene_model, expected_gene_model)

    def test_insert(self):

        client_mock = MagicMock()

        docs = [
            {"values": ["foo3", "foo4", "foo5"]},
            {"values": ["foo6", "foo7", "foo8"]},
        ]
        GeneExpression.insert(docs, "collection", client_mock)
        client_mock["collection"].insert_many.assert_called_with(docs, ordered=False)

        client_mock["collection"].insert_many.side_effect = ValueError("Foo")
        self.assertRaises(
            Exception, GeneExpression.insert, docs, "collection", client_mock
        )

        # Test exponential back off
        client_mock["collection"].insert_many.side_effect = AutoReconnect
        self.assertRaises(
            Exception, GeneExpression.insert, docs, "collection", client_mock
        )

        # client_mock["collection"].insert_many called twice before scenario
        self.assertEqual(client_mock["collection"].insert_many.call_count - 2, 5)
