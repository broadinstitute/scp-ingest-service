"""Ingest Service for expression files and eventually metadata and cluster
files into firestore.

DESCRIPTION
This cli currently takes in extract and transform functions from different
file types then uploads them into Firestore.

PREREQUISITES
You must have Google Cloud Firestore installed, authenticated
 configured. Must have python 3.6 or higher.

EXAMPLES
# Takes expression file and stores it into firestore

#Ingest dense file
$python ingest.py ingest_expression --matrix-file ../tests/data/dense_matrix_19_genes_100k_cells.txt --matrix-file-type dense

#Ingest mtx files
$python ingest.py ingest_expression --matrix-file ../tests/data/matrix.mtx --matrix-file-type mtx --matrix-bundle ../tests/data/genes.tsv ../tests/data/barcodes.tsv
"""
import argparse
import os
import time
from typing import Dict, Generator, List, Tuple, Union

import numpy as np
from dense import Dense
from gene_data_model import Gene
from google.cloud import firestore
from mtx import Mtx

# Ingest file types
EXPRESSION_FILE_TYPES = ['dense', 'mtx']


class IngestService(object):
    def __init__(self, *, matrix_file: str, matrix_file_type: str,
                 matrix_bundle: List[str] = None):
        """Initializes variables in ingest service.

        Args:
            matrix_file: str,
                For expression files, the relative or Absolute path to the
                    matrix file
            matrix_file_type: str,
                The matrix file type
            matrix_bundle: List[str]
                Used for MTX files. The matrix bundle consister of the barcode
                    and gene files.

        Returns:
            Nothing
        """
        if not os.path.exists(matrix_file):
            raise IOError(f"File '{matrix_file}' not found")
        self.matrix_file_path = matrix_file
        self.matrix_file_type = matrix_file_type
        self.matrix_bundle = matrix_bundle
        self.matrix = self.initialize_file_connection()
        self.db = firestore.Client()

    def initialize_file_connection(self):
        """Initializes connection to file.

        Args:
            None
        Returns:
            File object.
        """
        # Mtx file types not included because class declaration is different
        file_connections = {
            'dense': Dense
        }
        if self.matrix_file_type == 'mtx':
            return Mtx(self.matrix_file_path, self.matrix_bundle)
        else:
            return(
                file_connections.get(self.matrix_file_type)(self.matrix_file_path))

    def close_matrix(self):
        """Closes connection to file.

        Args:
            None
        Returns:
            None
        """
        self.matrix.close()

    def load_expression_data(self, list_of_transformed_data: List[Gene]) -> None:
        """Loads expression data into firestore.

        Args:
            list_of_transformed_data : List[Gene]
                A list of object type Gene that's stored into Firestore

        Returns:
            None
        """

        # Subcollections that are defined in various datamodels
        firestore_subcollections = ['gene_expression', 'all_cells', '1000',
                                    '10000', '20000', '100000']
        batch = self.db.batch()

        for transformed_data in list_of_transformed_data:
            for collection, document in transformed_data.items():
                for gene, data in document.items():
                    doc_ref = self.db.collection(collection).document()
                    for subcollection in firestore_subcollections:
                        if subcollection in data:
                            data_subcollection = data.pop(subcollection)
                            doc_subcol_ref = doc_ref.collection(
                                subcollection).document()
            batch.set(doc_ref, data)
            batch.set(doc_subcol_ref, data_subcollection)
        batch.commit()

    def ingest_expression(self) -> None:
        """Ingests expression files. Calls file type's extract and transform
        functions. Then loads data into firestore.

        Args:
            None

        Returns:
            None
        """
        if self.matrix_bundle is not None:
            self.matrix.extract()
            transformed_data = self.matrix.transform_expression_data_by_gene()
        else:
            for data in self.matrix.extract():
                transformed_data = self.matrix.transform_expression_data_by_gene(
                    *data)
        self.load_expression_data(transformed_data)
        self.close_matrix()


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
    parser_ingest_xpression = subargs.add_parser('ingest_expression',
                                                 help='Indicates that expression'
                                                 ' files are being ingested')

    parser_ingest_xpression.add_argument('--matrix-file', required=True,
                                         help='Absolute or relative path to '
                                         'expression file.For 10x data this is '
                                         'the .mtx file')

    matrix_file_type_txt = 'Type of expression file that is ingested. If mtx \
        files are being ingested, .genes.tsv and .barcodes.tsv files must be \
        included using --matrix-bundle. See - -help for more information'

    parser_ingest_xpression.add_argument('--matrix-file-type',
                                         choices=EXPRESSION_FILE_TYPES,
                                         type=str.lower,
                                         required=True,
                                         help=matrix_file_type_txt
                                         )

    parser_ingest_xpression.add_argument('--matrix-bundle', default=None,
                                         nargs='+', help='Names of .genes.tsv '
                                         'and .barcodes.tsv files'
                                         )

    parsed_args = args.parse_args()
    if parsed_args.matrix_file_type == 'mtx' and parsed_args.matrix_bundle == None:
        if parsed_args.matrix_bundle == None:
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

    if hasattr(ingest, 'ingest_expression'):
        getattr(ingest, 'ingest_expression')()


if __name__ == "__main__":
    main()
