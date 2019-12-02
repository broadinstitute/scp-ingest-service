from typing import Dict, Generator, List, Tuple, Union  # noqa: F401
from dataclasses import dataclass
from mypy_extensions import TypedDict
import logging

from ingest_files import DataArray
from annotations import Annotations
from monitor import log, setup_logger

# from ingest_pipeline import log


@dataclass
class DomainRanges(TypedDict):
    x: List
    y: List
    z: List = None


class Clusters(Annotations):
    ALLOWED_FILE_TYPES = ["text/csv", "text/plain", "text/tab-separated-values"]
    LINEAR_DATA_TYPE = 'ClusterGroup'
    COLLECTION_NAME = 'cluster_groups'
    errors_logger = setup_logger(
        __name__ + '_errors', 'errors.txt', level=logging.ERROR
    )
    # General logger for class
    info_logger = setup_logger(__name__, 'info.txt')

    my_debug_logger = log(errors_logger)

    @dataclass
    class Model(TypedDict):
        name: str
        # 3d or 2d cluster
        cluster_type: str
        # List of dictionaries that describe all extra "annotation" columns
        cell_annotations: List
        file_id: str
        study_id: str
        # Hash containing min/max arrays for each axis in the cluster plot
        domain_ranges: DomainRanges = None

    def __init__(
        self,
        file_path: str,
        study_id: str,
        study_file_id: str,
        name: str,
        *,
        domain_ranges: Dict = None,
    ):
        Annotations.__init__(
            self, file_path, self.ALLOWED_FILE_TYPES, study_id, study_file_id
        )
        self.determine_coordinates_and_cell_names()
        self.source_file_type = "cluster"
        self.cluster_type = (
            '3d'
            if (
                "z" in self.coordinates_and_cell_headers
                or "Z" in self.coordinates_and_cell_headers
            )
            else '2d'
        )
        self.name = name
        self.domain_ranges = domain_ranges

    @my_debug_logger()
    def transform(self):
        """ Builds cluster data model"""
        # Array of Hash objects that describe all extra "annotation" columns
        cell_annotations = []
        # Iterate through all extra "annotation" column headers
        # (I.E. column headers that are not coordinates or where TYPE !=NAME)
        for annot_headers in self.annot_column_headers:
            annot_name = annot_headers[0]
            annot_type = annot_headers[1]
            # column_type = annot[1]
            cell_annotations.append(
                {
                    'name': annot_name,
                    'type': annot_type,
                    'values': self.file[annot_headers].unique().tolist()
                    if annot_type == 'group'
                    else [],
                }
            )
        self.info_logger.info(f'Created model for {self.study_id}')
        return self.Model(
            name=self.name,
            cluster_type=self.cluster_type,
            cell_annotations=cell_annotations,
            study_file_id=self.study_file_id,
            study_id=self.study_id,
            domain_ranges=DomainRanges(**self.domain_ranges),
        )

    @my_debug_logger()
    def get_data_array_annot(self, linear_data_id):
        for annot_header in self.file.columns:
            self.info_logger.info(
                f'Creating data array for header {annot_header[0]} for {self.study_id}'
            )
            yield Clusters.set_data_array(
                annot_header[0],
                self.name,
                self.file[annot_header].tolist(),
                self.study_file_id,
                self.study_id,
                linear_data_id,
            )

    def can_subsample(self):
        # TODO: Add more subsample validations
        if self.has_z:
            return len(self.header) > 4
        else:
            return len(self.header) > 3

    @staticmethod
    def set_data_array(
        name: str,
        cluster_name: str,
        values: List,
        study_file_id: str,
        study_id: str,
        linear_data_id: str,
        array_index: int = 0,
        subsample_annotation: str = None,
        subsample_threshold: int = None,
    ):
        data_array_attr = locals()
        BASE_DICT = {'linear_data_type': Clusters.LINEAR_DATA_TYPE}

        def get_cluster_attr(annot_name):

            cluster_group_types = {
                'name': {'name': "text", 'array_type': "cells"},
                'coordinates': {
                    'name': annot_name.lower(),
                    'array_type': "coordinates",
                },
                'annot': {'name': annot_name, 'array_type': "annotations"},
            }

            if annot_name.lower() == "name":
                result = cluster_group_types.get('name')
                return result
            elif annot_name.lower() in ("x", "y", "z"):
                result = cluster_group_types.get('coordinates')
                return result
            else:
                result = cluster_group_types.get('annot')
                return result

        cluster_attr = get_cluster_attr(name)
        # Remove 'name' from function aruguments
        del data_array_attr['name']

        # Merge BASE_DICT, cluster_attr & data_array_attr and return DataArray model
        return DataArray(
            **data_array_attr, **cluster_attr, **BASE_DICT
        ).get_data_array()
