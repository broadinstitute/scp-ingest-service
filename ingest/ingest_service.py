"""Ingest Service for ingesting expression, metadata and cluster
files into firestore.

DESCRIPTION
This cli currently takes in extract and transform functions from different
file types then uploads them into Firestore.

PREREQUISITES
You must have Google Cloud Firestore installed, authenticated
 configured. Must have python 3.6 or higher. Indexing must be turned off for
 all collections.

EXAMPLES
# Takes expression file and stores it into firestore

#Ingest cluster file
python ingest_service.py ingest_cluster --cluster-file ../tests/data/AB_toy_data_portal.cluster.txt

#Ingest Cell file
python ingest_service.py ingest_cell_metadata --cell-metadata-file ../tests/data/10k_cells_29k_genes.metadata.tsv

# Ingest dense file
$python ingest_service.py ingest_expression --matrix-file ../tests/data/dense_matrix_19_genes_100k_cells.txt --matrix-file-type dense

# Ingest mtx files
$python ingest_service.py ingest_expression --matrix-file ../tests/data/matrix.mtx --matrix-file-type mtx --gene-file ../tests/data/genes.tsv --barcode-file ../tests/data/barcodes.tsv
"""
import argparse
import os
import time
from typing import Dict, Generator, List, Tuple, Union

import numpy as np
from cell_metadata import CellMetadata
from clusters import Clusters
from dense import Dense
from gene_data_model import Gene
from google.api_core import exceptions
from google.cloud import firestore
from mtx import Mtx

# Ingest file types
EXPRESSION_FILE_TYPES = ['dense', 'mtx']


class IngestService(object):
    def __init__(self, *, matrix_file: str = None, matrix_file_type: str = None,
                 barcode_file: str = None, gene_file: str = None, cell_metadata_file: str = None,
                 cluster_file: str = None):
        """Initializes variables in ingest service."""

        self.matrix_file_path = matrix_file
        self.matrix_file_type = matrix_file_type
        self.gene_file = gene_file
        self.barcodes_file = barcode_file
        self.db = firestore.Client()
        if matrix_file is not None:
            self.matrix = self.initialize_file_connection(
                matrix_file_type, matrix_file)
        elif cell_metadata_file is not None:
            self.cell_metadata = self.initialize_file_connection(
                'cell_metadata', cell_metadata_file)
        elif cluster_file is not None:
            self.cluster = self.initialize_file_connection(
                'cluster', cluster_file)
        elif matrix_file is None:
            self.matrix = matrix_file
        elif cluster_file is None:
            self.cluster = cluster_file
        elif cell_metadata_file is None:
            self.cell_metadata = cell_metadata_file

    def initialize_file_connection(self, file_type, file_path):
        """Initializes connection to file.

        Args:
            None
        Returns:
            File object.
        """
        # Mtx file types not included because class declaration is different
        file_connections = {
            'dense': Dense,
            'cell_metadata': CellMetadata,
            'cluster': Clusters
        }

        if file_type == 'mtx':
            return Mtx(self.matrix_file_path, self.gene_file, self.barcodes_file)
        else:
            return file_connections.get(file_type)(file_path)

    def close_matrix(self):
        """Closes connection to file.

        Args:
            None
        Returns:
            None
        """
        self.matrix.close()

    def load_expression_data(self, list_of_expression_models: List[Gene]) -> None:
        """Loads expression data into firestore.

        Args:
            list_of_transformed_data : List[Gene]
                A list of object type Gene that's stored into Firestore

        Returns:
            None
        """

        # for expression_model in list_of_expression_models:
        for expression_model in list_of_expression_models:
            batch = self.db.batch()
            collection_name = expression_model.get_collection_name()
            doc_ref = self.db.collection(collection_name).document()
            doc_ref.set(expression_model.get_document())
            try:
                if expression_model.has_subcollection_data():
                    subcollection_name = expression_model.get_subcollection_name()
                    doc_ref_sub = doc_ref.collection(
                        subcollection_name).document()
                    doc_ref_sub.set(expression_model.get_subcollection())

            except exceptions.InvalidArgument as e:
                # Catches invalid argument exception, which error "Maximum
                # document size falls under
                print(f'{e}')
                batch = self.db.batch()
                for subdoc in expression_model.chunk_gene_expression_documents():

                    subcollection_name = expression_model.get_subcollection_name()
                    doc_ref_sub = doc_ref.collection(
                        subcollection_name).document()
                    batch.set(doc_ref_sub, subdoc)
                    # print(f'This is batch: {batch.__dict__}')

                batch.commit()

    # def load_cluster_files(self):
    #     """Loads cluster files into firestore."""
    #     collection_name = self.cluster.get_collection_name()
    #     doc_ref = self.db.collection(collection_name).document()
    #     doc_ref.set(self.cluster.top_level_doc)
    #     subcollection_name = self.cluster.get_subcollection_name()
    #     for annotation in self.cluster.annotation_subdocs.keys():
    #         batch = self.db.batch()
    #         doc_ref_sub = doc_ref.collection(
    #             subcollection_name).document()
    #         doc_ref_sub.set(self.cluster.annotation_subdocs[annotation])

    def load_cell_metadata(self):
        """Loads cell metadata files into firestore."""

        collection_name = self.cell_metadata.get_collection_name()
        subcollection_name = self.cell_metadata.get_subcollection_name()
        for annotation in self.cell_metadata.top_level_doc.keys():
            doc_ref = self.db.collection(collection_name).document()
            doc_ref.set(self.cell_metadata.top_level_doc[annotation])
            try:
                subcollection_doc = self.cell_metadata.data_subcollection[annotation]
                doc_ref_sub = doc_ref.collection(subcollection_name).document()
                doc_ref_sub.set(subcollection_doc)
            except exceptions.InvalidArgument as e:
                # Catches invalid argument exception, which error "Maximum
                # document size falls under
                print(e)

    def ingest_expression(self) -> None:
        """Ingests expression files. Calls file type's extract and transform
        functions. Then loads data into firestore.

        Args:
            None

        Returns:
            None
        """
        if self.gene_file is not None:
            self.matrix.extract()
            transformed_data = self.matrix.transform_expression_data_by_gene()
        else:
            for data in self.matrix.extract():
                transformed_data = self.matrix.transform_expression_data_by_gene(
                    *data)
        self.load_expression_data(transformed_data)
        self.close_matrix()

    def ingest_cell_metadata(self):
        """Ingests cell metadata files into firestore.
        """
        while True:
            row = self.cell_metadata.extract()
            if(row == None):
                break
            self.cell_metadata.transform(row)
        self.load_cell_metadata()

    # def ingest_cluster(self):
    #     """Ingests cluster files into firestore.
    #
    #     Args:
    #         None
    #
    #     Returns:
    #         None
    #     """
    #     for data in self.cluster.extract():
    #         self.cluster.transform(data)
    #     self.load_cluster_files()


def parse_arguments():
    """Parses and validates input arguments.

    Args:
        None

    Returns:
        parsed_args: Namespace
            Validated input arguments
    """
    args = argparse.ArgumentParser(
        prog='ingest.py',
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter)

    subargs = args.add_subparsers()

    # Ingest expression files subparser
    parser_ingest_expression = subargs.add_parser('ingest_expression',
                                                  help='Indicates that expression'
                                                  ' files are being ingested')

    parser_ingest_expression.add_argument('--matrix-file', required=True,
                                          help='Absolute or relative path to '
                                          'expression file.For 10x data this is '
                                          'the .mtx file')

    matrix_file_type_txt = 'Type of expression file that is ingested. If mtx \
        files are being ingested, .genes.tsv and .barcodes.tsv files must be \
        included using --barcode-file <barcode file path> and --gene-file \
        <gene file path>. See --help for more information'

    parser_ingest_expression.add_argument('--matrix-file-type',
                                          choices=EXPRESSION_FILE_TYPES,
                                          type=str.lower,
                                          required=True,
                                          help=matrix_file_type_txt
                                          )

    # Gene and Barcode arguments for MTX bundle
    parser_ingest_expression.add_argument('--barcode-file', type=str,
                                          help='Names of .barcodes.tsv files')
    parser_ingest_expression.add_argument('--gene-file', type=str,
                                          help='Names of .genes.tsv file')

    # Parser ingesting cell metadata files
    parser_cell_metadata = subargs.add_parser('ingest_cell_metadata',
                                              help='Indicates that cell '
                                              ' metadata files are being '
                                              'ingested')
    parser_cell_metadata.add_argument('--cell-metadata-file', required=True,
                                      help='Absolute or relative path to '
                                      'cell metadata file.')

    # Parser ingesting cluster files
    parser_cluster = subargs.add_parser('ingest_cluster',
                                        help='Indicates that cluster '
                                        'file is being ingested')
    parser_cluster.add_argument('--cluster-file', required=True,
                                help='Absolute or relative path to '
                                'cluster file.')

    parsed_args = args.parse_args()
    if hasattr(parsed_args, 'ingest_expression'):
        if parsed_args.matrix_file_type == 'mtx' and (parsed_args.gene_file == None
                                                      or parsed_args.barcode_file == None):
            raise ValueError(
                ' Missing argument: --matrix-bundle. Mtx files must include '
                '.genes.tsv, and .barcodes.tsv files. See --help for more '
                'information')
    return parsed_args


def main() -> None:
    """This function handles the actual logic of this script.

    Args:
        None

    Returns:
        None
    """
    arguments = vars(parse_arguments())
    ingest = IngestService(**arguments)

    if 'matrix_file' in arguments:
        getattr(ingest, 'ingest_expression')()
    elif 'cell_metadata_file' in arguments:
        getattr(ingest, 'ingest_cell_metadata')()
    # elif 'cluster_file' in arguments:
    #     getattr(ingest, 'ingest_cluster')()


if __name__ == "__main__":
    main()
