"""THIS IS A WORK IN PROGRESS
Command-line interface for ingesting Loom files into Firestore

DESCRIPTION
This CLI maps genes to expression values, cell ids, gene accesions from
a Loom file and puts them into Firestore.

PREREQUISITES
You must have google could firestore installed, authenticated
 configured.

EXAMPLES
# Takes Loom file and stores it into Firestore
$ python loom_ingest.py  200k_subsample_4k_PMBC.loom
"""


import sys

import loompy
from gene_data_model import Gene
import numpy as np

np.set_printoptions(precision=8, threshold=sys.maxsize, edgeitems=1e9)


class Loom:
    def __init__(self, file_path, file_id, study_accession, **kwargs):
        self.ds = loompy.connect(file_path)
        self.study_accession = study_accession
        self.file_id = file_id
        self.matrix_params = {k: v for k, v in kwargs.items() if v is not None}

    def extract(self):
        """Pythons iterator protocol. Reads though Loom file and extracts 512 rows at time

        Returns:
        ------
            view: < generator LoomView>
                    A generator of a view corresponding to the current chunk
        """
        for (ix, selection, view) in self.ds.scan(axis=0, batch_size=10):
            yield view

    def transform_expression_data_by_gene(self, view) -> Gene:
        """Transforms LoomView into Firestore data model
        Returns:
        ------
            transformed_data : List[Gene]
                A list of Gene objects
        """
        # TODO: Find way to utilize generators and interators for memory and CPU efficiency
        # Checkout https://www.datacamp.com/community/tutorials/python-iterator-tutorial
        gene_expression_models = []
        for gene in view.ra.Gene:
            gene_expression_models.append(
                Gene(
                    name=gene,
                    source_file_type="loom",
                    expression_scores=view[view.ra.Gene == gene, :][0],
                    cell_names=self.ds.ca.CellID.tolist(),
                    study_accession=self.study_accession,
                    file_id=self.file_id,
                    **self.matrix_params,
                )
            )
        return gene_expression_models
