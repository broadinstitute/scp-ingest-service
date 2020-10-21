"""A base class for expression files.

DESCRIPTION
This base class provides functions to create dataArrays for gene expression
files.

PREREQUISITES
Must have python 3.6 or higher.
"""
import abc
import datetime
import ntpath
import copy
from dataclasses import dataclass
from typing import List, Dict, Generator  # noqa: F401

from bson.objectid import ObjectId
from mypy_extensions import TypedDict

try:
    from ingest_files import DataArray
    from monitor import setup_logger
    from mongo_connection import MongoConnection, graceful_auto_reconnect
except ImportError:
    # Used when importing as external package, e.g. imports in single_cell_portal code
    from ..ingest_files import DataArray
    from ..monitor import setup_logger
    from ..mongo_connection import MongoConnection, graceful_auto_reconnect


class GeneExpression:
    __metaclass__ = abc.ABCMeta
    COLLECTION_NAME = "genes"
    DATA_ARRAY_BATCH_SIZE = 1_000
    # Logger provides more details
    dev_logger = setup_logger(__name__, "log.txt", format="support_configs")

    @dataclass
    class Model(TypedDict):
        name: str
        # downcase version of 'name'
        searchable_name: str
        study_file_id: ObjectId
        study_id: ObjectId
        _id: ObjectId
        gene_id: str = None

    def __init__(self, file_path: str, study_id: str, study_file_id: str):
        self.study_id = ObjectId(study_id)
        self.study_file_id = ObjectId(study_file_id)
        head, tail = ntpath.split(file_path)
        self.cluster_name = tail or ntpath.basename(head)
        self.mongo_connection = MongoConnection()
        # Common data array kwargs
        self.data_array_kwargs = {
            "cluster_name": self.cluster_name,
            "study_file_id": self.study_file_id,
            "study_id": self.study_id,
        }

    @abc.abstractmethod
    def transform(self):
        """Abstract method for transforming expression data into data models."""

    @abc.abstractmethod
    def execute_ingest(self):
        """Abstract method for parsing expression data into MongoDB."""

    @staticmethod
    @abc.abstractmethod
    def check_valid():
        """Abstract method for validating expression matrices."""

    @staticmethod
    def create_gene_model(
        *ignore, name: str, study_file_id, study_id, _id: int, gene_id: str = None
    ):
        """Creates a gene model for a single gene.
            This function accepts keyword arguments only. An error will be raised
                if positional or additional keyword arguments are passed in.
        """
        if ignore:
            raise TypeError("Position arguments are not accepted.")
        return GeneExpression.Model(
            {
                "name": name,
                "searchable_name": name.lower(),
                "study_file_id": study_file_id,
                "study_id": study_id,
                "gene_id": gene_id,
                "_id": _id,
            }
        )

    @staticmethod
    def check_unique_cells(cell_names: List, study_id, study_file_id, client):
        """Checks cell names against database to confirm matrix contains unique
            cell names.

        Method acts as 'command center' for deciding what methods need to be called to check for cell uniquenes under
            given scenarios.

         Parameters:
            cell_names (List[str]): List of cell names in matrix
            study_id (ObjectId): The study id the cell names belong to
            study_file_id (ObjectId): The file id the cell names belong to
            client: MongoDB client
        """
        EXISITING_CELL_QUERY = {
            "$and": [
                {"linear_data_type": "Study"},
                {"array_type": "cells"},
                {"study_id": study_id},
            ],
            "$nor": [{"name": "All Cells"}],
        }
        # Returned fields from query results
        FIELD_NAMES = {"values": 1, "_id": 0}
        COLLECTION_NAME = "data_arrays"

        raw_count_query_results = GeneExpression.get_raw_count_study_file_ids(
            client, study_id
        )
        if raw_count_query_results:
            raw_count_query_fields: List[
                Dict
            ] = GeneExpression.get_raw_count_query_filters(
                study_file_id, raw_count_query_results, include_study_file_id=False
            )
            query_operator_value = "$and"
            operator_values = EXISITING_CELL_QUERY.get(query_operator_value, [])
            operator_values.append({"$or": raw_count_query_fields})
            EXISITING_CELL_QUERY[query_operator_value] = operator_values

        # Dict = {values_1: [<cell names>]... values_n:[<cell names>]}
        query_results: List[Dict] = list(
            client[COLLECTION_NAME].find(EXISITING_CELL_QUERY, FIELD_NAMES)
        )
        # Flatten query results
        existing_cells = [
            values
            for cell_values in query_results
            for values in cell_values.get("values")
        ]
        dupes = set(existing_cells) & set(cell_names)
        if len(dupes) > 0:
            error_string = (
                f"Expression file contains {len(dupes)} cells "
                "that also exist in another expression file."
            )

            # add the first 3 duplicates to the error message
            error_string += f'Duplicates include {", ".join(list(dupes)[:3])}'
            raise ValueError(error_string)
        return True

    @staticmethod
    def get_raw_count_query_filters(
        study_file_id, raw_count_study_file_ids: List[Dict], include_study_file_id=True
    ) -> List[Dict]:
        """Creates query filters for study files have are considered raw count matrices

            For every result in 'raw_id_query_results' is expected to have the id present. The current study file id
                is excluded from filters. This function can eventually expand to generically create filters for a
                given property.

        :parameter
            study_file_id (ObjectID) : Study file id for the current study
            raw_count_study_file_ids : Study file ids that need filters created ie. [{'id': <Study file id>}]
            include_study_file_id : Whether to include 'study_file_id' in filter
        """

        def generate_filters(raw_count_study_file_ids):
            return [
                {"study_file_id": result["_id"]} for result in raw_count_study_file_ids
            ]

        current_study_file_id = {"_id": ObjectId(study_file_id)}
        if not include_study_file_id:
            if (item == current_study_file_id.id for item in raw_count_study_file_ids):
                raw_count_study_file_ids.remove(current_study_file_id)
                # raw_count_study_file_ids has other study file
                if raw_count_study_file_ids:
                    # Builds study ids fields for query
                    return generate_filters(raw_count_study_file_ids)
                else:
                    return None
        else:
            return generate_filters(raw_count_study_file_ids)

    @staticmethod
    def get_raw_count_study_file_ids(client, study_id) -> List[Dict]:
        """Returns raw count study file ids that are apart of study"""

        COLLECTION_NAME = "study_files"

        raw_ids_query = {
            "$and": [
                {"study_id": study_id},
                {"file_type": "Expression Matrix"},
                {"expression_file_info.is_raw_counts": True},
            ]
        }
        # Returned fields from raw id query results
        field_names = {"_id": 1}
        raw_id_query_results = list(
            client[COLLECTION_NAME].find(raw_ids_query, field_names)
        )
        return raw_id_query_results

    @staticmethod
    def create_data_arrays(
        *ignore,
        # keyword arguments
        name: str,
        cluster_name: str,
        array_type: str,
        values: List,
        linear_data_type: str,
        linear_data_id,
        study_id,
        study_file_id,
    ) -> Generator:
        """
        Sets data array for expression data.
        This function accepts keyword arguments only. An error will be raised
                if positional or additional keyword arguments are passed in.
        """
        fn_kwargs = copy.copy(locals())
        # Positional arguments passed in
        if ignore:
            raise TypeError("Positional arguments are not accepted.")
        del fn_kwargs["ignore"]
        for model in DataArray(**fn_kwargs).get_data_arrays():
            yield model

    @staticmethod
    @graceful_auto_reconnect
    def insert(docs: List, collection_name: str, client):
        client[collection_name].insert_many(docs, ordered=False)

    def load(self, docs: List, collection_name: List):
        start_time = datetime.datetime.now()
        GeneExpression.insert(docs, collection_name, self.mongo_connection._client)
        GeneExpression.dev_logger.info(
            f"Time to load {len(docs)} models: {str(datetime.datetime.now() - start_time)}"
        )

    def create_models(
        self,
        exp_cells: List,
        exp_scores: List,
        gene: str,
        gene_id: str,
        gene_models: List,
        data_arrays: List,
        num_processed: int,
        force=False,
    ):
        """Creates models for a given gene and batches them for loading if
            necessary.

        After creating models, the amount of data arrays are checked to see if
        models should be loaded into the database. Data arrays and gene models
        will be loaded if the threshold, as specified in DATA_ARRAY_BATCH_SIZE,
        is met.

        Returns:
            data_arrays: List[str]
            gene_models: List[str]
            num_processed: int
                Amount of gene models created.
            """
        current_data_arrays = []
        start_time = datetime.datetime.now()
        model_id = ObjectId()

        GeneExpression.dev_logger.debug(f"Creating models for {gene}")
        if gene:
            gene_models.append(
                GeneExpression.create_gene_model(
                    name=gene,
                    study_file_id=self.study_file_id,
                    study_id=self.study_id,
                    gene_id=gene_id,
                    _id=model_id,
                )
            )
        # Make data array models for genes with expression data
        if len(exp_scores) > 0:
            # Data array model for cells
            for cell_data_array in GeneExpression.create_data_arrays(
                name=f"{gene} Cells",
                array_type="cells",
                values=exp_cells,
                linear_data_type="Gene",
                linear_data_id=model_id,
                **self.data_array_kwargs,
            ):
                current_data_arrays.append(cell_data_array)
            # Data array model for expression values
            for exp_value_data_array in GeneExpression.create_data_arrays(
                name=f"{gene} Expression",
                array_type="expression",
                values=exp_scores,
                linear_data_type="Gene",
                linear_data_id=model_id,
                **self.data_array_kwargs,
            ):
                current_data_arrays.append(exp_value_data_array)
        this_batch_size = len(data_arrays) + len(current_data_arrays)
        # Determine if models should be batched/loaded
        if this_batch_size >= GeneExpression.DATA_ARRAY_BATCH_SIZE or force:
            if force:
                # Add new data arrays
                data_arrays += current_data_arrays
                current_data_arrays.clear()
            if len(data_arrays) > 0:
                self.load(data_arrays, DataArray.COLLECTION_NAME)
            if len(gene_models) > 0:
                self.load(gene_models, GeneExpression.COLLECTION_NAME)
            num_processed += len(gene_models)
            GeneExpression.dev_logger.info(
                f"Processed {num_processed} genes. "
                f"{str(datetime.datetime.now() - start_time)} "
                f"elapsed"
            )
            gene_models.clear()
            data_arrays.clear()
        data_arrays += current_data_arrays

        return data_arrays, gene_models, num_processed
