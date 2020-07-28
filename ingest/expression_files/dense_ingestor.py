"""Module for ingesting dense matrix files

DESCRIPTION
Module provides extract and transforms function for gene expression data for
an dense matrix.

PREREQUISITES
Must have python 3.6 or higher.
"""
import collections
import csv
import datetime
import sys
from typing import List  # noqa: F401

from bson.objectid import ObjectId

try:
    from .expression_files import GeneExpression
    sys.path.append("../ingest")
    from ingest_files import IngestFiles

except ImportError:
    # Used when importing as external package, e.g. imports in single_cell_portal code
    from .expression_files import GeneExpression
    sys.path.append("../ingest")
    from .ingest_files import IngestFiles


class DenseIngestor(GeneExpression, IngestFiles):
    ALLOWED_FILE_TYPES = ["text/csv",
                          "text/plain", "text/tab-separated-values"]

    def __init__(self, file_path, study_file_id, study_id, **kwargs):
        GeneExpression.__init__(self, file_path, study_file_id, study_id)
        IngestFiles.__init__(
            self, file_path, allowed_file_types=self.ALLOWED_FILE_TYPES
        )
        self.matrix_params = kwargs
        self.csv_file = self.open_file(self.file_path)[0]
        self.gene_names = {}
        self.header = next(self.csv_file)

    def execute_ingest(self):
        # import pdb; pdb.set_trace()
        for gene_docs, data_array_documents in self.transform():
            self.load(gene_docs, data_array_documents)

    def matches_file_type(file_type):
        return file_type == 'dense'

    def transform(self):
        """Transforms dense matrix into gene data model.
        """
        start_time = datetime.datetime.now()
        self.error_logger.info('Starting run at ' +
                               str(start_time), extra=self.extra_log_params)
        print('Starting run at ' + str(start_time))
        num_processed = 0
        gene_models = []
        data_arrays = []
        for all_cell_model in self.set_data_array_cells(
                self.header[1:], ObjectId()):
            data_arrays.append(all_cell_model)
        # Represents row as an ordered dictionary
        for row in self.csv_file:
            # import pdb
            # pdb.set_trace()
            numeric_scores = DenseIngestor.process_row(row)
            valid_expression_scores, cells = DenseIngestor.filter_expression_scores(
                numeric_scores)
            cells = []
            gene = row[0]
            if gene in self.gene_names:
                raise ValueError(f'Duplicate gene: {gene}')
            self.gene_names[gene] = True
            print(f'Transforming gene :{gene}')
            formatted_gene_name = DenseIngestor.format_gene_name(gene)
            id = ObjectId()
            gene_models.append(self.Model(
                {
                    'name': formatted_gene_name,
                    'searchable_name': formatted_gene_name.lower(),
                    'study_file_id': self.study_file_id,
                    'study_id': self.study_id,
                    '_id': id,
                    'gene_id': self.matrix_params['gene_id']
                    if 'gene_id' in self.matrix_params
                    else None,
                }
            )
            )
            if len(valid_expression_scores) > 0:
                print(valid_expression_scores)
                for gene_cell_model in self.set_data_array_gene_cell_names(gene, id, cells):
                    data_arrays.append(gene_cell_model)
                for gene_expression_values in self.set_data_array_gene_expression_values(gene, id, valid_expression_scores):
                    data_arrays.append(gene_expression_values)
                if len(gene_models) == 5:
                    num_processed += len(gene_models)
                    print(f'Processed {num_processed} models, {str(datetime.datetime.now() - start_time)} elapsed')
                    self.error_logger.info(f'Processed {num_processed} models, {str(datetime.datetime.now() - start_time)} elapsed', extra=self.extra_log_params)
                    yield (gene_models, data_arrays)
                    gene_models = []
                    data_arrays = []
        yield (gene_models, data_arrays)
        num_processed += len(gene_models)
        print(f'Processed {num_processed} models, {str(datetime.datetime.now() - start_time)}')
        gene_models = []
        data_arrays = []

    @staticmethod
    def format_gene_name(name):
        return gene.strip().strip('\"')

    @staticmethod
    def process_row(row: str):
        def convert_to_float(value: str):
            value = value.strip().strip("\'")
            return round(float(value), 3)
        result = map(convert_to_float, row[1:])
        return list(result)

    @staticmethod
    def filter_expression_scores(scores: List):
        valid_expression_scores = []
        associated_cells = []
        for idx, expression_score in enumerate(scores, 1):
            if expression_score != 0:
                valid_expression_scores.append(expression_score)
                associated_cells.append(self.header[idx])
        import pdb
        pdb.set_trace()
        print(valid_expression_scores)
        return valid_expression_scores, associated_cells
