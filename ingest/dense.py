"""Module for ingesting dense matrix files

DESCRIPTION
Module provides extract and transforms function for gene expression data for
an dense matrix.

PREREQUISITES
Must have python 3.6 or higher.
"""

import collections
from typing import List  # noqa: F401

from expression_files import GeneExpression


class Dense(GeneExpression):
    ALLOWED_FILE_TYPES = ["text/csv", "text/plain", "text/tab-separated-values"]

    def __init__(self, file_path, study_file_id, study_id, **kwargs):
        GeneExpression.__init__(
            self,
            file_path,
            study_file_id,
            study_id,
            allowed_file_types=self.ALLOWED_FILE_TYPES,
            open_as='dataframe',
        )
        # Remove from dictionary any keys that have value=None
        self.matrix_params = kwargs
        # Remove trailing white spaces, and quotes from column names
        self.file.rename(
            columns=lambda x: x.strip().strip('\"').strip('\'').strip('\"'),
            inplace=True,
        )

    def transform(self):
        """Transforms dense matrix into firestore data model for genes.
        """
        # Holds gene name and gene model for a single gene
        GeneModel = collections.namedtuple('Gene', ['gene_name', 'gene_model'])
        for gene in self.file['GENE']:
            # Remove white spaces and quotes
            formatted_gene_name = gene.strip().strip('\"').strip('\'').strip('\"')
            yield GeneModel(
                # Name of gene as observed in file
                gene,
                self.Model(
                    {
                        'name': formatted_gene_name,
                        'searchable_name': formatted_gene_name.lower(),
                        'study_file_id': self.study_file_id,
                        'study_id': self.study_id,
                        'gene_id': self.matrix_params['gene_id']
                        if 'gene_id' in self.matrix_params
                        else None,
                    }
                ),
            )

    def set_data_array(
        self,
        linear_data_id,
        unformatted_gene_name,
        gene_name,
        create_cell_data_array=False,
    ):
        """Creates data array for expression, gene, and cell values."""
        input_args = locals()
        gene_df = self.file[self.file['GENE'] == unformatted_gene_name]
        # Get list of cell names
        cells = self.file.columns.tolist()[1:]
        if create_cell_data_array:
            yield from self.set_data_array_cells(cells, linear_data_id)

        # Get row of expression values for gene
        # Round expression values to 3 decimal points
        # Insure data type of float for expression values
        cells_and_expression_vals = (
            gene_df[cells].round(3).astype(float).to_dict('records')[0]
        )
        # Filter out expression values = 0
        cells_and_expression_vals = dict(
            filter(lambda k_v: k_v[1] > 0, cells_and_expression_vals.items())
        )
        observed_cells = list(cells_and_expression_vals)
        observed_values = list(cells_and_expression_vals.values())

        # only return significant data (skip if no expression was observed)
        if len(observed_values) > 0:
            yield from self.set_data_array_gene_cell_names(
                unformatted_gene_name, linear_data_id, observed_cells
            )
            yield from self.set_data_array_gene_expression_values(
                unformatted_gene_name, linear_data_id, observed_values
            )

    def close(self):
        """Closes file

        Args:
            None

        Returns:
            None
        """
        self.file.close()
