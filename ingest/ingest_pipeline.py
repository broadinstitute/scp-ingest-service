"""Ingest Pipeline for ingesting expression, metadata and cluster
files into MongoDB.

DESCRIPTION
This CLI extracts and transforms different file types then writes them into
a remote MongoDB instance.

PREREQUISITES
See https://github.com/broadinstitute/scp-ingest-pipeline#prerequisites

EXAMPLES
# Takes expression file and stores it into MongoDB

# Ingest cluster file
python ingest_pipeline.py --study-id 5d276a50421aa9117c982845 --study-file-id 123abc ingest_cluster --cluster-file ../tests/data/test_1k_cluster_Data.csv --ingest-cluster --name cluster1 --domain-ranges "{'x':[-1, 1], 'y':[-1, 1], 'z':[-1, 1]}"

# Ingest Cell Metadata file
python ingest_pipeline.py --study-id 5d276a50421aa9117c982845 --study-accession 123abc --study-file-id 123abc ingest_cell_metadata --cell-metadata-file ../tests/data/valid_v1.1.1.tsv --ingest-cell-metadata

# Ingest Cell Metadata file against convention
!! Please note that you must have permission to the SCP bucket
python ingest_pipeline.py --study-id 5d276a50421aa9117c982845 --study-file-id 123abc ingest_cell_metadata --cell-metadata-file ../tests/data/valid_array_v1.1.3.tsv --ingest-cell-metadata --validate-convention

# Ingest dense file
python ingest_pipeline.py --study-id 5d276a50421aa9117c982845 --study-file-id 123abc ingest_expression --taxon-name 'Homo sapiens' --taxon-common-name human --ncbi-taxid 9606 --matrix-file ../tests/data/dense_matrix_19_genes_100k_cells.txt --matrix-file-type dense

# Ingest loom file
python ingest_pipeline.py  --study-id 5d276a50421aa9117c982845 --study-file-id 123abc ingest_expression --matrix-file ../tests/data/test_loom.loom  --matrix-file-type loom --taxon-name 'Homo Sapiens' --taxon-common-name humans

# Subsample cluster and metadata file
python ingest_pipeline.py --study-id 5d276a50421aa9117c982845 --study-file-id 123abc ingest_subsample --cluster-file ../tests/data/test_1k_cluster_Data.csv --name custer1 --cell-metadata-file ../tests/data/test_1k_metadata_Data.csv --subsample

# Ingest mtx files
python ingest_pipeline.py --study-id 5d276a50421aa9117c982845 --study-file-id 123abc ingest_expression --taxon-name 'Homo Sapiens' --taxon-common-name humans --matrix-file ../tests/data/matrix.mtx --matrix-file-type mtx --gene-file ../tests/data/genes.tsv --barcode-file ../tests/data/barcodes.tsv
"""
import argparse
from typing import Dict, Generator, List, Tuple, Union  # noqa: F401
import ast

import sys
import json
import os

from cell_metadata import CellMetadata
from clusters import Clusters
from dense import Dense
from pymongo import MongoClient
from mtx import Mtx

# from ingest_files import IngestFiles
from subsample import SubSample
from loom import Loom
from ingest_files import IngestFiles
from validation.validate_metadata import validate_input_metadata, report_issues

# Ingest file types
EXPRESSION_FILE_TYPES = ["dense", "mtx", "loom"]


class IngestPipeline(object):
    # File location for metadata json convention
    JSON_CONVENTION = 'gs://fc-bcc55e6c-bec3-4b2e-9fb2-5e1526ddfcd2/metadata_conventions/AMC_v1.1.3/AMC_v1.1.3.json'

    def __init__(
        self,
        study_id: str,
        study_file_id: str,
        matrix_file: str = None,
        matrix_file_type: str = None,
        cell_metadata_file: str = None,
        cluster_file: str = None,
        subsample=False,
        ingest_cell_metadata=False,
        ingest_cluster=False,
        **kwargs,
    ):
        """Initializes variables in ingest service."""
        self.study_id = study_id
        self.study_file_id = study_file_id
        self.matrix_file = matrix_file
        self.matrix_file_type = matrix_file_type
        if os.environ.get('DATABASE_HOST') is not None:
            # Needed to run tests in CircleCI.  TODO: add mock, remove this
            self.db = self.get_mongo_db()
        else:
            self.db = None
        self.cluster_file = cluster_file
        self.kwargs = kwargs
        self.cell_metadata_file = cell_metadata_file
        if matrix_file is not None:
            self.matrix = self.initialize_file_connection(matrix_file_type, matrix_file)
        elif ingest_cell_metadata:
            self.cell_metadata = self.initialize_file_connection(
                "cell_metadata", cell_metadata_file
            )
        elif ingest_cluster:
            self.cluster = self.initialize_file_connection("cluster", cluster_file)
        elif matrix_file is None:
            self.matrix = matrix_file

    def get_mongo_db(self):
        host = os.environ['DATABASE_HOST']
        user = os.environ['MONGODB_USERNAME']
        password = os.environ['MONGODB_PASSWORD']
        db_name = os.environ['DATABASE_NAME']

        client = MongoClient(
            host,
            username=user,
            password=password,
            authSource=db_name,
            authMechanism='SCRAM-SHA-1',
        )

        # TODO: Remove this block.
        # Uncomment and run `pytest -s` to manually verify your MongoDB set-up.
        # genes = client[db_name].genes
        # gene = {'gene': 'HBB'}
        # gene_mongo_id = genes.insert_one(gene).inserted_id
        # print(f'gene_mongo_id {gene_mongo_id}')

        return client[db_name]

    def initialize_file_connection(self, file_type, file_path):
        """Initializes connection to file.

            Returns:
                File object.
        """
        # Mtx file types not included because class declaration is different
        file_connections = {
            "dense": Dense,
            "cell_metadata": CellMetadata,
            "cluster": Clusters,
            "mtx": Mtx,
            "loom": Loom,
        }
        return file_connections.get(file_type)(
            file_path, self.study_id, self.study_file_id, **self.kwargs
        )

    def close_matrix(self):
        """Closes connection to file"""
        self.matrix.close()

    def load(
        self,
        model,
        set_data_array_fn,
        *set_data_array_fn_args,
        **set_data_array_fn_kwargs,
    ):
        try:

            print(model)
            # TODO: Get Linear_id from model
            for data_array_model in set_data_array_fn(
                'linear_id', *set_data_array_fn_args, **set_data_array_fn_kwargs
            ):
                print(data_array_model)
        except Exception as e:
            print(e)
            return 1
        return 0

    def load_subsample(self, subsampled_data, set_data_array_fn, scope):
        """Loads subsampled data into Firestore"""
        for key_value in subsampled_data[0].items():
            annot_name = subsampled_data[1][0]
            cluster_name = '?'
            annot_type = subsampled_data[1][1]
            sample_size = subsampled_data[2]
        try:
            # Either query mongo for linear_id from parent or have it passed in
            model = set_data_array_fn(
                (
                    key_value[0],
                    cluster_name,
                    key_value[1],
                    subsampled_data[1],
                    self.study_file_id,
                    self.study_id,
                    '123456789asdfg',
                ),
                {
                    'subsample_annotation': f"{annot_name}--{annot_type}--{scope}",
                    'subsample_threshold': sample_size,
                },
            )
            print(model)

        except Exception as e:
            # TODO: Log this error
            print(e)
            return 1
        return 0

    def has_valid_metadata_convention(self):
        """ Determines if cell metadata file follows metadata convention"""
        with open(self.JSON_CONVENTION, 'r') as f:
            json_file = IngestFiles(self.JSON_CONVENTION, ['application/json'])
            convention = json.load(json_file.file)
            validate_input_metadata(self.cell_metadata, convention)

        f.close()
        return not report_issues(self.cell_metadata)

    def ingest_expression(self) -> None:
        """Ingests expression files.
        """
        print('expression')
        if self.kwargs["gene_file"] is not None:
            self.matrix.extract()
        for idx, gene in enumerate(self.matrix.transform()):
            if idx == 0:
                self.load(
                    gene.gene_model,
                    self.matrix.set_data_array,
                    gene.gene_name,
                    gene.gene_model['searchable_name'],
                    {'create_cell_DataArray': True},
                )
            else:
                self.load(
                    gene.gene_model,
                    self.matrix.set_data_array,
                    gene.gene_name,
                    gene.gene_model['searchable_name'],
                )

    def ingest_cell_metadata(self):
        """Ingests cell metadata files into Firestore."""
        # TODO: Add self.has_valid_metadata_convention() to if statement
        if self.cell_metadata.validate_format():
            # Check to see file needs to be check against metadata convention
            if self.kwargs['validate_convention'] is not None:
                if self.kwargs['validate_convention']:
                    if self.has_valid_metadata_convention():
                        pass
                    else:
                        return 1
            self.cell_metadata.reset_file(2, open_as="dataframe")
            self.cell_metadata.preproccess()
            for metadataModel in self.cell_metadata.transform():
                # This is where to load Top-level ClusterGroup document
                # TODO: 'Linear_id' will need to change to MongoDB ObjectId
                status = self.load(
                    metadataModel.model,
                    self.cell_metadata.set_data_array,
                    metadataModel.annot_header,
                )
                if status != 0:
                    return status
            return status

    def ingest_cluster(self):
        """Ingests cluster files."""
        if self.cluster.validate_format():
            annotation_model = self.cluster.transform()
            return self.load(annotation_model, self.cluster.get_data_array_annot)

    def subsample(self):
        """Method for subsampling cluster and metadata files"""

        subsample = SubSample(
            cluster_file=self.cluster_file, cell_metadata_file=self.cell_metadata_file
        )

        for data in subsample.subsample():
            load_status = self.load_subsample(data, subsample.set_data_array, 'cluster')
            if load_status != 0:
                return load_status

        if self.cell_metadata_file is not None:
            subsample.prepare_cell_metadata()
            for doc in subsample.subsample():
                load_status = load_status = self.load_subsample(
                    data, subsample.set_data_array, 'study'
                )
                if load_status != 0:
                    return load_status
        return 0


def create_parser():
    """Creates parser for input arguments.

    Structuring the argument parsing code like this eases automated testing.

    Args:
        None

    Returns:
        parser: ArgumentParser object
    """
    parser = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        "--study-file-id",
        required=True,
        help="Single study accession associated with ingest files",
    )
    parser.add_argument("--study-id", required=True, help="MongoDB identifier")

    subparsers = parser.add_subparsers()

    # Ingest expression files subparsers
    parser_ingest_expression = subparsers.add_parser(
        "ingest_expression",
        help="Indicates that expression" " files are being ingested",
    )

    parser_ingest_expression.add_argument(
        "--matrix-file",
        required=True,
        help="Absolute or relative path to "
        "expression file. For 10x data this is "
        "the .mtx file",
    )

    matrix_file_type_txt = "Type of expression file that is ingested. If mtx \
        files are being ingested, .genes.tsv and .barcodes.tsv files must be \
        included using --barcode-file <barcode file path> and --gene-file \
        <gene file path>. See --help for more information"

    parser_ingest_expression.add_argument(
        "--taxon-name",
        help="Scientific name of taxon associated with file.  E.g. 'Homo sapiens'",
    )
    parser_ingest_expression.add_argument(
        "--taxon-common-name",
        help="Common name of taxon associated with file.  E.g. 'human'",
    )
    parser_ingest_expression.add_argument(
        "--ncbi-taxid",
        help="NCBI Taxonomy ID of taxon associated with file.  E.g. 9606",
    )
    parser_ingest_expression.add_argument(
        "--genome-assembly-accession",
        help="Genome assembly accession for file.  E.g. 'GCA_000001405.15'",
    )
    parser_ingest_expression.add_argument(
        "--genome-annotation",
        help="Genomic annotation for expression files.  E.g. 'Ensembl 94'",
    )

    parser_ingest_expression.add_argument(
        "--matrix-file-type",
        choices=EXPRESSION_FILE_TYPES,
        type=str.lower,
        required=True,
        help=matrix_file_type_txt,
    )

    # Gene and Barcode arguments for MTX bundle
    parser_ingest_expression.add_argument(
        "--barcode-file", help="Path to .barcodes.tsv files"
    )
    parser_ingest_expression.add_argument("--gene-file", help="Path to .genes.tsv file")

    # Parser ingesting cell metadata files
    parser_cell_metadata = subparsers.add_parser(
        "ingest_cell_metadata",
        help="Indicates that cell metadata files are being " "ingested",
    )
    parser_cell_metadata.add_argument(
        "--cell-metadata-file",
        required=True,
        help="Absolute or relative path to cell metadata file.",
    )
    parser_cell_metadata.add_argument(
        "--study-accession",
        required=True,
        help="Single study accession associated with ingest files.",
    )
    parser_cell_metadata.add_argument(
        "--ingest-cell-metadata",
        required=True,
        action="store_true",
        help="Indicates that ingest of cell metadata should be invoked",
    )
    parser_cell_metadata.add_argument(
        "--validate-convention",
        action="store_true",
        help="Indicates that metadata file should be validated against convention",
    )

    # Parser ingesting cluster files
    parser_cluster = subparsers.add_parser(
        "ingest_cluster", help="Indicates that cluster file is being ingested"
    )
    parser_cluster.add_argument(
        "--cluster-file",
        required=True,
        help="Absolute or relative path to cluster file.",
    )
    parser_cluster.add_argument(
        "--ingest-cluster",
        required=True,
        action="store_true",
        help="Indicates that ingest of cluster file should be invoked",
    )
    parser_cluster.add_argument(
        "--name", required=True, help="Name of cluster from input form"
    )
    parser_cluster.add_argument(
        "--domain-ranges",
        type=ast.literal_eval,
        help="Optional paramater taken from UI",
    )

    # Parser ingesting cluster files
    parser_subsample = subparsers.add_parser(
        "ingest_subsample", help="Indicates that subsampling will be initialized"
    )
    parser_subsample.add_argument(
        "--subsample",
        required=True,
        action="store_true",
        help="Indicates that subsampliing functionality should be invoked",
    )
    parser_subsample.add_argument(
        "--name", required=True, help="Name of cluster from input form"
    )
    parser_subsample.add_argument(
        "--cluster-file",
        required=True,
        help="Absolute or relative path to cluster file.",
    )
    parser_subsample.add_argument(
        "--cell-metadata-file", help="Absolute or relative path to cell metadata file."
    )

    return parser


def validate_arguments(parsed_args):
    """Verify parsed input arguments

    Args:
        parsed_args: Parsed input arguments

    Returns:
        None
    """

    if ("matrix_file" in parsed_args and parsed_args.matrix_file_type == "mtx") and (
        parsed_args.gene_file is None or parsed_args.barcode_file is None
    ):
        raise ValueError(
            " Missing arguments: --gene-file and --barcode-file. Mtx files "
            "must include .genes.tsv, and .barcodes.tsv files. See --help for "
            "more information"
        )


def main() -> None:
    """This function handles the actual logic of this script.

    Args:
        None

    Returns:
        None
    """
    status = []
    parsed_args = create_parser().parse_args()
    validate_arguments(parsed_args)
    arguments = vars(parsed_args)
    ingest = IngestPipeline(**arguments)
    # TODO: Add validation for gene and cluster file types
    if "matrix_file" in arguments:
        status.append(ingest.ingest_expression())
    elif "ingest_cell_metadata" in arguments:
        if arguments["ingest_cell_metadata"]:
            status_cell_metadata = ingest.ingest_cell_metadata()
            status.append(status_cell_metadata)
    elif "ingest_cluster" in arguments:
        if arguments["ingest_cluster"]:
            status.append(ingest.ingest_cluster())
    elif "subsample" in arguments:
        if arguments["subsample"]:
            status_subsample = ingest.subsample()
            status.append(status_subsample)

    if all(i < 1 for i in status) or len(status) == 0:
        sys.exit(os.EX_OK)
    else:
        sys.exit(os.EX_DATAERR)


if __name__ == "__main__":
    main()
