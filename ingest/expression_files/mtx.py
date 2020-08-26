"""
Module for ingesting MTX files

DESCRIPTION
This module provides extract and transforms function for an MTX file bundle. An
MTX file bundle consists of A) an .mtx file in Matrix
Market matrix coordinate format, B) a genes.tsv file, and a barcodes.tsv file.
These are commonly provided from 10x Genomics v2.

"""


from typing import Dict, Generator, List, Tuple  # noqa: F401
import sys


sys.path.append("..")
try:
    from expression_files import GeneExpression
    from ingest_files import IngestFiles
except ImportError:
    # Used when importing as external package, e.g. imports in
    # single_cell_portal code
    from .expression_files import GeneExpression
    from ..ingest_files import IngestFiles


class MTXIngestor(GeneExpression):
    ALLOWED_FILE_TYPES = ["text/tab-separated-values"]

    @staticmethod
    def matches_file_type(file_type):
        return "mtx" == file_type

    def __init__(self, mtx_path: str, study_file_id: str, study_id: str, **kwargs):
        GeneExpression.__init__(self, mtx_path, study_file_id, study_id)

        mtx_ingest_file = IngestFiles(mtx_path, self.ALLOWED_FILE_TYPES)
        self.mtx_file = mtx_ingest_file.resolve_path(mtx_path)[0]

        genes_path = kwargs.pop("gene_file")
        genes_ingest_file = IngestFiles(genes_path, self.ALLOWED_FILE_TYPES)
        self.genes_file = genes_ingest_file.resolve_path(genes_path)[0]

        barcodes_path = kwargs.pop("barcode_file")
        barcodes_ingest_file = IngestFiles(barcodes_path, self.ALLOWED_FILE_TYPES)
        self.barcodes_file = barcodes_ingest_file.resolve_path(barcodes_path)[0]

        # A list ['N', 'K', 'M'] that represents a gene-barcode matrix where N
        # is the gene index, M is the barcode index, and K is the expression
        # score for the given gene index
        self.mtx_dimensions: List[int] = MTXIngestor.get_mtx_dimensions(self.mtx_file)

    @staticmethod
    def check_valid(
        barcodes: List[str], genes: List[str], mtx_dimensions, query_params
    ):
        error_messages = []

        try:
            MTXIngestor.check_bundle(barcodes, genes, mtx_dimensions)
        except ValueError as v:
            error_messages.append(str(v))
        try:
            MTXIngestor.check_duplicates(genes, "gene")
        except ValueError as v:
            error_messages.append(str(v))
        try:
            MTXIngestor.check_duplicates(barcodes, "barcode")
        except ValueError as v:
            error_messages.append(str(v))
        try:
            GeneExpression.check_unique_cells(barcodes, *query_params)
        except ValueError as v:
            error_messages.append(str(v))

        if len(error_messages) > 0:
            raise ValueError("; ".join(error_messages))
        return True

    @staticmethod
    def check_bundle(barcodes, genes, mtx_dimensions):
        """Confirms barcode and gene files have expected length of values"""
        expected_genes = mtx_dimensions[0]
        actual_genes = len(genes)

        expected_barcodes = mtx_dimensions[1]
        actual_barcodes = len(barcodes)

        if (actual_barcodes == expected_barcodes) and (actual_genes == expected_genes):

            return True
        else:
            msg = (
                f"Expected {expected_barcodes} cells and {expected_genes} genes. "
                f"Got {actual_barcodes} cells and {actual_genes} genes."
            )
            raise ValueError(msg)

    @staticmethod
    def check_duplicates(names: List, file_type: str):
        """Checks for duplicate values.
        Barcode and gene files cannot contain duplicate values within the file

        Parameters
        ----------
        names - Gene or cell values

        file_type: Barcode or gene files. Used in error message
        """
        unique_names: List[str] = set(names)
        if len(names) > len(unique_names):
            amount_of_duplicates = abs(len(unique_names) - len(names))
            msg = (
                "Duplicate values are not allowed. "
                f"There are {amount_of_duplicates} duplicates "
                f"in the {file_type} file"
            )
            raise ValueError(msg)
        return True

    @staticmethod
    def get_mtx_dimensions(file_handler) -> List:
        for line in file_handler:
            if not line.startswith("%"):
                mtx_dimensions: List[str] = line.strip().split()
                # Convert values in mtx_dimensions to int
                return list(map(int, mtx_dimensions))

    def execute_ingest(self):
        """Parses MTX files"""
        self.extract_feature_barcode_matrices()
        MTXIngestor.check_valid(
            self.cells,
            self.genes,
            self.mtx_dimensions,
            query_params=(self.study_id, self.mongo_connection._client),
        )
        self.transform()

    def extract_feature_barcode_matrices(self):
        """
        Sets relevant iterables for the gene and barcode file of the MTX bundle
        """
        self.genes: List[str] = [
            g.strip().strip('"') for g in self.genes_file.readlines()
        ]
        self.cells: List[str] = [
            c.strip().strip('"') for c in self.barcodes_file.readlines()
        ]

    def transform(self):
        num_processed = 0
        prev_idx = 0
        gene_models = []
        data_arrays = []
        exp_cells = []
        exp_scores = []

        # All observed cells
        for data_array in GeneExpression.create_data_arrays(
            name=f"{self.cluster_name} Cells",
            array_type="cells",
            values=self.cells,
            linear_data_type="Study",
            linear_data_id=self.study_file_id,
            **self.data_array_kwargs,
        ):
            data_arrays.append(data_array)
        for row in self.mtx_file:
            raw_gene_idx, raw_barcode_idx, raw_exp_score = row.split()
            current_idx = int(raw_gene_idx)
            if current_idx != prev_idx:
                if not current_idx == prev_idx + 1:
                    raise ValueError("MTX file must be sorted")
                else:
                    if prev_idx != 0:
                        # Expressed cells and scores are associated with prior gene
                        prev_gene_id, prev_gene = self.genes[prev_idx - 1].split("\t")
                        # Ff the previous gene exists, load its models
                        data_arrays, gene_models, num_processed = self.load_data_arrays(
                            exp_cells,
                            exp_scores,
                            prev_gene,
                            prev_gene_id,
                            gene_models,
                            data_arrays,
                            num_processed,
                            False,
                        )
                        exp_cells = []
                        exp_scores = []
                    prev_idx = current_idx
            exp_cell = self.cells[int(raw_barcode_idx) - 1]
            exp_score = round(float(raw_exp_score), 3)
            exp_cells.append(exp_cell)
            exp_scores.append(exp_score)
        # Create data array for last row
        current_gene_id, current_gene = self.genes[prev_idx - 1].split("\t")
        self.load_data_arrays(
            exp_cells,
            exp_scores,
            current_gene,
            current_gene_id,
            gene_models,
            data_arrays,
            num_processed,
            True,
        )
