"""Module for ingesting cell metadata files
DESCRIPTION
Module provides extract and transform functions for cell metadata files.
Text, CSV, and TSV files are supported.
PREREQUISITES
Must have python 3.6 or higher.
"""
from collections import defaultdict
from typing import Dict, Generator, List, Tuple, Union  # noqa: F401
from dataclasses import dataclass
from mypy_extensions import TypedDict
import ntpath
from annotations import Annotations
import collections
from ingest_files import DataArray


class CellMetadata(Annotations):
    ALLOWED_FILE_TYPES = ['text/csv', 'text/plain', 'text/tab-separated-values']
    COLLECTION_NAME = 'cell_metadata'

    def __init__(
        self, file_path: str, study_id: str, study_file_id: str, *args, **kwargs
    ):

        Annotations.__init__(self, file_path, self.ALLOWED_FILE_TYPES)
        self.file_path = file_path
        self.headers = self.file.columns.get_level_values(0)
        self.annot_types = self.file.columns.get_level_values(1)
        self.cell_names = []
        self.study_id = study_id
        self.study_file_id = study_file_id
        # lambda below initializes new key with nested dictionary as value and avoids KeyError
        self.issues = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        self.ontology = defaultdict(lambda: defaultdict(list))
        self.cells = []

    # This model pertains to columns from cell metadata files
    @dataclass
    class Model(TypedDict):
        # value from column header
        name: str
        annotation_type: str
        study_file_id: str
        study_id: str
        # unique values from "group" type annotations
        values: List

    def transform(self):
        """ Builds cell metadata model"""
        AnnotationModel = collections.namedtuple(
            'AnnotationModel', ['annot_header', 'model']
        )
        for annot_header in self.file.columns[:]:
            annot_name = annot_header[0]
            annot_type = annot_header[1]
            yield AnnotationModel(
                annot_header,
                self.Model(
                    {
                        'name': annot_name,
                        'annotation_type': annot_type,
                        # unique values from "group" type annotations else []
                        'values': list(self.file[annot_header].unique())
                        if annot_type == 'group'
                        else [],
                        'study_file_id': self.study_file_id,
                        'study_id': self.study_id,
                    }
                ),
            )

    def set_data_array(self, linear_data_id: str, annot_header: str):
        data_array_attrs = locals()
        del data_array_attrs['annot_header']
        del data_array_attrs['self']
        annot_name = annot_header[0]
        head, tail = ntpath.split(self.file_path)
        base_data_array_model = {
            'cluster_name': tail or ntpath.basename(head),
            'value': list(self.file[annot_header]),
            'study_file_id': self.study_file_id,
            'study_id': self.study_id,
        }
        # This is an array (or group of arrays) of every cell
        if annot_name.lower() == 'name':
            base_data_array_model.update(
                {
                    'name': 'All Cells',
                    'array_type': 'cells',
                    'linear_data_type': 'Study',
                }
            )
        # data from cell metadata file that correspond to a column of data
        else:
            base_data_array_model.update(
                {
                    'name': annot_name,
                    'array_type': 'annotations',
                    'linear_data_type': 'CellMetadatum',
                }
            )
        yield DataArray({**data_array_attrs, **base_data_array_model})

    def yield_by_row(self) -> None:
        """ Yield row from cell metadata file"""
        for row in self.file.itertuples(index=False):
            dict_row = row._asdict()
            yield dict_row.values()
