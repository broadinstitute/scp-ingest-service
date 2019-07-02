"""Module for ingesting dense matrix files

DESCRIPTION
Module provides extract and transforms function for gene expression data for
an dense matrix.

PREREQUISITES
Must have python 3.6 or higher.
"""
import argparse
import os
import sys
from itertools import islice
from typing import *

import numpy as np
from gene_data_model import Gene


class Dense():
    def __init__(self, file_path):
        self.file = open(file_path, 'r')
        self.cell_names = self.file.readline().replace('"', '').split(',')[1:]
        self.filetype = os.path.splitext(file_path)[1]
        self.file_name = file_path

    def extract(self, size: int = 500) -> List[str]:
        """Extracts lines from dense matrix.

        Args:
            size : int
                The amount of lines returned per chunk

        Returns:
                next_lines : List[str]
                    A list (chunk) of rows from a dense matrix.
        """
        while True:
            next_lines = list(islice(self.file, size))
            if not next_lines:
                break
            yield next_lines
            break

    def transform_expression_data_by_gene(self, *lines: List[str]) -> List[Gene]:
        """Transforms dense matrix into firestore data model for genes.

        Args:
            lines : List[str]
                Lines from dense matrix file

        Returns:
                transformed_data : List[Gene]
                A list of Gene objects
        """
        transformed_data = []
        for line in lines:
            compute = line.rstrip('\n').split(',')
            expression_scores = [float(x) for x in compute[1:]]
            gene_model = Gene(compute[0], self.file_name, self.filetype,
                              expression_scores=expression_scores,
                              cell_names=self.cell_names)
            transformed_data.append(gene_model)
        return transformed_data

    def close(self):
        self.file.close()

    def split_expression_data(self, expression_ref):
        amount_of_docs = self.determine_amount_of_doc(size_of_gene_doc)
