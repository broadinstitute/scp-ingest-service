import sys
import unittest
import json

from mock_data.annotation.cell_metadata.valid_array_v2_1_2 import (
    valid_array_v2_1_2_models,
)

sys.path.append("../ingest")
from cell_metadata import CellMetadata
from validation.validate_metadata import collect_jsonschema_errors
from ingest_pipeline import IngestPipeline
from ingest_files import IngestFiles


class TestCellMetadata(unittest.TestCase):
    def test_validate_header_for_coordinate_values_false(self):
        """Ensures validate_header_for_coordinate_values returns false when
        coordinate value is in metadata file
        Note: cluster has similar set of tests
         """
        cm = CellMetadata(
            "../tests/data/metadata_has_coordinate_header.txt",
            "5d276a50421aa9117c982845",
            "5dd5ae25421aa910a723a337",
            study_accession="SCP2",
            tracer=None,
        )
        self.assertFalse(cm.validate_header_for_coordinate_values())

    def test_validate_header_for_coordinate_values_true(self):
        """Ensures validate_header_for_coordinate_values returns true when
        coordinate value is not in metadata file
         """
        cm = CellMetadata(
            "../tests/data/metadata_example.txt",
            "5d276a50421aa9117c982845",
            "5dd5ae25421aa910a723a337",
            study_accession="SCP2",
            tracer=None,
        )
        cm.preprocess()
        self.assertTrue(cm.validate_header_for_coordinate_values())

    def test_metadata_type_inference(self):
        """Confirm consistency of type inference behavior
        in instantiated data frame
        """
        cm = CellMetadata(
            "../tests/data/metadata_NA.txt",
            "addedfeed000000000000000",
            "dec0dedfeed1111111111111",
            study_accession="SCPtest",
            tracer=None,
        )
        cm.preprocess()

        # integers, empty cell and string as inputs for numeric annotation
        assert isinstance(
            cm.file["NA_i_n_s__grp"]["group"][3], str
        ), "empty cell -> NaN, expect coercion to string"

        # integers and empty cell as inputs for numeric annotation
        assert isinstance(
            cm.file["NA_i_n_grp"]["group"][3], str
        ), "empty cell -> NaN, expect coercion to string"

        # floats, empty cell and string as inputs for numeric annotation
        assert isinstance(
            cm.file["NA_f_n_s__grp"]["group"][3], str
        ), "empty cell -> NaN, expect coercion to string"

        # floats and empty cell as inputs for numeric annotation
        assert isinstance(
            cm.file["NA_f_n_grp"]["group"][3], str
        ), "empty cell -> NaN, expect coercion to string"

        # integers, empty cell and string as inputs for group annotation
        assert isinstance(
            cm.file["NA_i_n_s__num"]["numeric"][3], float
        ), "empty cell -> NaN that remains float (not coerced)"

        # floats, empty cell and string as inputs for group annotation
        assert isinstance(
            cm.file["NA_f_n_s__num"]["numeric"][3], float
        ), "empty cell -> NaN that remains float (not coerced)"

    def test_transfrom(self):

        # Numeric columns that have array convention data are stored as a group in Mongo
        cm = CellMetadata(
            "../tests/data/metadata/valid_array_v2.1.2.txt",
            "5ea08bb17b2f150f29f4d952",
            "600f42bdb067340e777b1385",
            study_accession="SCP123",
            tracer=None,
        )
        cm.preprocess(is_metadata_convention=True)
        convention_file_object = IngestFiles(
            IngestPipeline.JSON_CONVENTION, ["application/json"]
        )
        json_file = convention_file_object.open_file(IngestPipeline.JSON_CONVENTION)
        convention = json.load(json_file)
        collect_jsonschema_errors(cm, convention)
        for metadata_model in cm.transform():
            model = metadata_model.metadata_model
            model_name = model["name"]
            self.assertEqual(
                model["name"],
                valid_array_v2_1_2_models["cell_metadata_models"][model_name],
            )
