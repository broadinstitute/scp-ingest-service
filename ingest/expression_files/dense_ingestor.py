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
    from monitor import trace
    from connection import MongoConnection

except ImportError:
    # Used when importing as external package, e.g. imports in single_cell_portal code
    from .expression_files import GeneExpression
    sys.path.append("../ingest")
    from .ingest_files import IngestFiles
    from .monitor import trace


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
        for gene_docs, data_array_documents in self.transform():
            self.load_expression_file(
                gene_docs, data_array_documents)
        self.close()
        return 0

    def matches_file_type(file_type):
        return file_type == 'dense'

    def validate_unique_header(self):
        """Validates header has no duplicate values"""
        if len(set(self.header)) != len(self.header):
            self.error_logger.error(
                "Duplicated header values are not allowed", extra=self.extra_log_params
            )
            return False
        return True

    def validate_gene_keyword(self):
        """Validates that 'Gene' is the first value in header"""
        # File is an R formatted file
        if (self.header[-1] == '') and (self.header[0].upper() != 'GENE'):
            pass
        else:
            # If not R formatted file then first cell must be 'GENE'
            if self.header[0].upper() != 'GENE':
                self.error_logger.error(
                    f'First cell in header must be GENE not {self.header[0]}',
                    extra=self.extra_log_params,
                )
                return False
        return True

    # @trace
    # def preprocess(self):
    #     """Determines if file is R-formatted. Creates dataframe (df)"""
    #     csv_file, open_file_object = self.open_file(self.file_path)
    #     dtypes = {'GENE': object}
    #
    #     # # Remove white spaces and quotes
    #     header = [col_name.strip().strip('\"') for col_name in self.header]
    #     # See if R formatted file
    #     if (header[-1] == '') and (header[0].upper() != 'GENE'):
    #         header.insert(0, 'GENE')
    #         # Although the last column in the header is empty, python treats it
    #         # as an empty string,[ ..., ""]
    #         header = header[0:-1]
    #     else:
    #         header[0] = header[0].upper()
    #     # Set dtype for expression values to floats
    #     dtypes.update({cell_name: 'float' for cell_name in header[1:]})
    #     self.df = self.open_file(
    #         self.file_path,
    #         open_as='dataframe',
    #         names=header,
    #         skiprows=1,
    #         dtype=dtypes,
    #         # chunksize=100000, Save for when we chunk data
    #     )[0]
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
            numeric_scores = list(
                map(lambda x: round(float(x.strip().strip("\'")), 3), row[1:])
            )
            valid_expression_scores = []
            cells = []

            for idx, expression_score in enumerate(numeric_scores, 1):
                if expression_score != 0:
                    valid_expression_scores.append(expression_score)
                    cells.append(self.header[idx])
            gene = row[0]
            if gene in self.gene_names:
                raise ValueError(f'Duplicate gene: {gene}')
            self.gene_names[gene] = True
            print(f'Transforming gene :{gene}')
            formatted_gene_name = gene.strip().strip('\"')
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
                for gene_cell_model in self.set_data_array_gene_cell_names(gene, id, cells):
                    data_arrays.append(gene_cell_model)
                for gene_expression_values in self.set_data_array_gene_expression_values(gene, id, valid_expression_scores):
                    data_arrays.append(gene_expression_values)
                if len(gene_models) > 5:
                    num_processed += len(gene_models)
                    yield (gene_models, data_arrays)
                    print(f'Processed {num_processed} models, {str(datetime.datetime.now() - start_time)} elapsed')
                    self.error_logger.info(f'Processed {num_processed} models, {str(datetime.datetime.now() - start_time)} elapsed', extra=self.extra_log_params)
                    gene_models = []
                    data_arrays = []
        yield (gene_models, data_arrays)
        num_processed += len(gene_models)
        print(f'Processed {num_processed} models, {str(datetime.datetime.now() - start_time)}')
        gene_models = []
        data_arrays = []

    def validate_format(self):
        return all([self.validate_unique_header(), self.validate_gene_keyword()])

    def close(self):
        """Closes file

        Args:
            None

        Returns:
            None
        """
        self.csv_file.close()
