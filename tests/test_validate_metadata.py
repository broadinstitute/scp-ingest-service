"""Tests for metadata validation

These tests verify that metadata files are checked against metadata convention,
ontology terms are validated against an external source, and tsv metadata files
conform to SCP metadata file format requirements.

PREREQUISITES
Spin up Python 3.6 virtualenv, install Python dependencies in requirements.txt
and Firestore emulator must be running, see PR26 for instructions
(https://github.com/broadinstitute/scp-ingest-pipeline/pull/26)

# Run all tests in a manner that shows report_issues output
python3 test_validate_metadata.py

"""

import sys
import unittest
import json
import os
from bson.objectid import ObjectId
import requests
from unittest.mock import patch
import io
import numpy as np

sys.path.append("../ingest")
sys.path.append("../ingest/validation")

from validate_metadata import (
    create_parser,
    report_issues,
    collect_jsonschema_errors,
    validate_schema,
    CellMetadata,
    validate_collected_ontology_data,
    collect_cell_for_ontology,
    validate_input_metadata,
    request_json_with_backoff,
    MAX_HTTP_ATTEMPTS,
    is_empty_string,
    is_label_or_synonym
)


# do not attempt a request, but instead throw a request exception
def mocked_requests_get(*args, **kwargs):
    raise requests.exceptions.RequestException


class TestValidateMetadata(unittest.TestCase):
    def setup_metadata(self, args):
        args_list = args.split(" ")
        args = create_parser().parse_args(args_list)
        with open(args.convention) as f:
            convention = json.load(f)
        filetsv = args.input_metadata
        # set ObjectIDs to be recognizably artificial
        artificial_study_file_id = "addedfeed000000000000000"
        metadata = CellMetadata(
            filetsv,
            ObjectId("dec0dedfeed1111111111111"),
            ObjectId(artificial_study_file_id),
            "SCPtest",
            study_accession="SCPtest",
        )
        metadata.preprocess(is_metadata_convention=True)
        # The following line should become metadata.validate() as part of bugfix SCP-2756
        metadata.validate_format()
        print(f"Format is correct {metadata.validate_format()}")
        return (metadata, convention)

    def teardown_metadata(self, metadata):
        metadata.file_handle.close()
        try:
            os.remove("scp_validation_errors.txt")
            os.remove("scp_validation_warnings.txt")
            os.remove("errors.txt")
            os.remove("info.txt")
        except OSError:
            print("no file to remove")

    def test_comma_delimited_array(self):
        args = (
            "--convention ../schema/alexandria_convention/alexandria_convention_schema.json "
            "../tests/data/annotation/metadata/convention/has_commas_in_arrays.csv"
        )
        metadata, convention = self.setup_metadata(args)
        self.assertTrue(
            metadata.validate_format(), "Valid metadata headers should not elicit error"
        )
        collect_jsonschema_errors(metadata, convention)
        validate_collected_ontology_data(metadata, convention)
        report_issues(metadata)

        reference_file = open(
            "mock_data/annotation/metadata/convention/has_commas_in_arrays.json"
        )
        reference_issues = json.load(reference_file)
        reference_file.close()
        self.assertEqual(
            metadata.issues,
            reference_issues,
            "Metadata validation issues do not match reference issues",
        )
        self.teardown_metadata(metadata)

    def test_convention_content(self):
        """Metadata convention should be valid jsonschema
        """

        args = "--convention ../tests/data/AMC_invalid.json ../tests/data/annotation/metadata/convention/valid_no_array_v2.0.0.txt"
        metadata, convention = self.setup_metadata(args)
        self.assertIsNone(
            validate_schema(convention, metadata),
            "Invalid metadata schema should be detected",
        )
        self.teardown_metadata(metadata)

    def test_auto_filling_missing_labels(self):
        # note that the filename provided here is irrelevant -- we will be specifying row data ourselves
        args = (
            "--convention ../schema/alexandria_convention/alexandria_convention_schema.json "
            "../tests/data/annotation/metadata/convention/valid_no_array_v2.0.0.txt"
        )
        metadata, convention = self.setup_metadata(args)

        # handle empty string ontology label for required array metadata
        input_row = {
            "CellID": "test1",
            "disease": ["MONDO_0005015"],
            "disease__ontology_label": "",
        }
        expected_row = {
            "CellID": "test1",
            "disease": ["MONDO_0005015"],
            "disease__ontology_label": [],
        }
        updated_row = collect_cell_for_ontology(
            "disease", input_row, metadata, convention, True, True
        )
        self.assertEqual(
            expected_row,
            updated_row,
            "Row should not be altered if label for required ontology is missing",
        )
        self.assertEqual(
            metadata.issues["error"]["ontology"],
            {
                'disease: required column "disease__ontology_label" missing data': [
                    "test1"
                ]
            },
            "unexpected error reporting",
        )

        # handle missing ontology label column for required array metadata
        metadata, convention = self.setup_metadata(args)
        row = {"CellID": "test1", "disease": ["MONDO_0005015"]}
        updated_row = collect_cell_for_ontology(
            "disease", row, metadata, convention, True, True
        )
        self.assertEqual(
            {
                "CellID": "test1",
                "disease": ["MONDO_0005015"],
                "disease__ontology_label": [],
            },
            updated_row,
            "Row should have column ontology_label added with value of empty array",
        )
        self.assertEqual(
            metadata.issues["error"]["ontology"],
            {
                'disease: required column "disease__ontology_label" missing data': [
                    "test1"
                ]
            },
            "unexpected error reporting",
        )

        # handles nan ontology label for required array metadata
        metadata, convention = self.setup_metadata(args)
        row = {
            "CellID": "test1",
            "disease": ["MONDO_0005015"],
            "disease__ontology_label": np.nan,
        }
        updated_row = collect_cell_for_ontology(
            "disease", row, metadata, convention, True, True
        )
        self.assertEqual(
            {
                "CellID": "test1",
                "disease": ["MONDO_0005015"],
                "disease__ontology_label": [],
            },
            updated_row,
            "nan should be converted to empty array",
        )
        self.assertEqual(
            metadata.issues["error"]["ontology"],
            {
                'disease: required column "disease__ontology_label" missing data': [
                    "test1"
                ]
            },
            "unexpected error reporting",
        )

        # handle empty string ontology label for required non-array metadata
        metadata, convention = self.setup_metadata(args)
        row = {
            "CellID": "test1",
            "organ": "UBERON_0001913",
            "organ__ontology_label": "",
        }
        updated_row = collect_cell_for_ontology(
            "organ", row, metadata, convention, False, True
        )
        self.assertEqual(
            row,
            updated_row,
            "Row should not be altered if label for required ontology is missing",
        )
        self.assertEqual(
            metadata.issues["error"]["ontology"],
            {'organ: required column "organ__ontology_label" missing data': ["test1"]},
            "unexpected error reporting",
        )

        # handle missing ontology label column for required non-array metadata
        metadata, convention = self.setup_metadata(args)
        row = {"CellID": "test1", "organ": "UBERON_0001913"}
        updated_row = collect_cell_for_ontology(
            "organ", row, metadata, convention, False, True
        )
        self.assertEqual(
            {"CellID": "test1", "organ": "UBERON_0001913", "organ__ontology_label": ""},
            updated_row,
            "Row should have column ontology_label added with value of empty string",
        )
        self.assertEqual(
            metadata.issues["error"]["ontology"],
            {'organ: required column "organ__ontology_label" missing data': ["test1"]},
            "unexpected error reporting",
        )

        # handles nan ontology label for required non-array metadata
        metadata, convention = self.setup_metadata(args)
        row = {
            "CellID": "test1",
            "organ": "UBERON_0001913",
            "organ__ontology_label": np.nan,
        }
        updated_row = collect_cell_for_ontology(
            "organ", row, metadata, convention, False, True
        )
        self.assertEqual(
            {"CellID": "test1", "organ": "UBERON_0001913", "organ__ontology_label": ""},
            updated_row,
            "nan should be converted to empty string",
        )
        self.assertEqual(
            metadata.issues["error"]["ontology"],
            {'organ: required column "organ__ontology_label" missing data': ["test1"]},
            "unexpected error reporting",
        )

        # handle empty string ontology label for optional array metadata
        row = {
            "CellID": "test1",
            "ethnicity": ["HANCESTRO_0005"],
            "ethnicity__ontology_label": "",
        }
        updated_row = collect_cell_for_ontology(
            "ethnicity", row, metadata, convention, True, False
        )
        self.assertEqual(
            {
                "CellID": "test1",
                "ethnicity": ["HANCESTRO_0005"],
                "ethnicity__ontology_label": ["European"],
            },
            updated_row,
            "Row should be updated to inject missing ontology label as array",
        )
        self.assertEqual(
            metadata.issues["warn"]["ontology"],
            {
                'ethnicity: missing ontology label "HANCESTRO_0005" - using "European" per EBI OLS lookup': [
                    "test1"
                ]
            },
            "unexpected error reporting",
        )

        # handle missing ontology label column for optional array metadata
        metadata, convention = self.setup_metadata(args)
        row = {"CellID": "test1", "ethnicity": ["HANCESTRO_0005"]}
        updated_row = collect_cell_for_ontology(
            "ethnicity", row, metadata, convention, True, False
        )
        self.assertEqual(
            {
                "CellID": "test1",
                "ethnicity": ["HANCESTRO_0005"],
                "ethnicity__ontology_label": ["European"],
            },
            updated_row,
            "Row should be updated to inject missing ontology label as array",
        )
        self.assertEqual(
            metadata.issues["warn"]["ontology"],
            {
                'ethnicity: missing ontology label "HANCESTRO_0005" - using "European" per EBI OLS lookup': [
                    "test1"
                ]
            },
            "unexpected error reporting",
        )

        # handles nan ontology label for optional array metadata
        metadata, convention = self.setup_metadata(args)
        row = {
            "CellID": "test1",
            "ethnicity": ["HANCESTRO_0005"],
            "ethnicity__ontology_label": np.nan,
        }
        updated_row = collect_cell_for_ontology(
            "ethnicity", row, metadata, convention, True, False
        )
        self.assertEqual(
            {
                "CellID": "test1",
                "ethnicity": ["HANCESTRO_0005"],
                "ethnicity__ontology_label": ["European"],
            },
            updated_row,
            "Row should be updated to inject missing ontology label as array",
        )
        self.assertEqual(
            metadata.issues["warn"]["ontology"],
            {
                'ethnicity: missing ontology label "HANCESTRO_0005" - using "European" per EBI OLS lookup': [
                    "test1"
                ]
            },
            "unexpected error reporting",
        )

        # handle empty string ontology label for optional non-array metadata
        metadata, convention = self.setup_metadata(args)
        row = {
            "CellID": "test1",
            "cell_type": "CL_0000066",
            "cell_type__ontology_label": "",
        }
        updated_row = collect_cell_for_ontology(
            "cell_type", row, metadata, convention, False, False
        )
        self.assertEqual(
            {
                "CellID": "test1",
                "cell_type": "CL_0000066",
                "cell_type__ontology_label": "epithelial cell",
            },
            updated_row,
            "Row should be updated to inject missing ontology label as non-array",
        )
        self.assertEqual(
            metadata.issues["warn"]["ontology"],
            {
                'cell_type: missing ontology label "CL_0000066" - using "epithelial cell" per EBI OLS lookup': [
                    "test1"
                ]
            },
            "unexpected error reporting",
        )

        # handle missing ontology label column for optional non-array metadata
        metadata, convention = self.setup_metadata(args)
        row = {"CellID": "test1", "cell_type": "CL_0000066"}
        updated_row = collect_cell_for_ontology(
            "cell_type", row, metadata, convention, False, False
        )
        self.assertEqual(
            {
                "CellID": "test1",
                "cell_type": "CL_0000066",
                "cell_type__ontology_label": "epithelial cell",
            },
            updated_row,
            "Row should be updated to inject missing ontology label as non-array",
        )
        self.assertEqual(
            metadata.issues["warn"]["ontology"],
            {
                'cell_type: missing ontology label "CL_0000066" - using "epithelial cell" per EBI OLS lookup': [
                    "test1"
                ]
            },
            "unexpected error reporting",
        )

        # handles nan ontology label for optional non-array metadata
        metadata, convention = self.setup_metadata(args)
        row = {
            "CellID": "test1",
            "cell_type": "CL_0000066",
            "cell_type__ontology_label": np.nan,
        }
        updated_row = collect_cell_for_ontology(
            "cell_type", row, metadata, convention, False, False
        )
        self.assertEqual(
            {
                "CellID": "test1",
                "cell_type": "CL_0000066",
                "cell_type__ontology_label": "epithelial cell",
            },
            updated_row,
            "Row should be updated to inject missing ontology label as non-array",
        )
        self.assertEqual(
            metadata.issues["warn"]["ontology"],
            {
                'cell_type: missing ontology label "CL_0000066" - using "epithelial cell" per EBI OLS lookup': [
                    "test1"
                ]
            },
            "unexpected error reporting",
        )

        # handles mismatch in item #s for optional array metadata and its label
        metadata, convention = self.setup_metadata(args)
        row = {
            "CellID": "test1",
            "ethnicity": ["HANCESTRO_0005", "HANCESTRO_0462"],
            "ethnicity__ontology_label": ["British"],
        }
        updated_row = collect_cell_for_ontology(
            "ethnicity", row, metadata, convention, True, False
        )
        self.assertEqual(
            row,
            updated_row,
            "Row should not be altered if mismatch in item #s for between array metadata and its label",
        )
        self.assertEqual(
            metadata.issues["error"]["ontology"],
            {
                "ethnicity: mismatched # of ethnicity and ethnicity__ontology_label values": [
                    "test1"
                ]
            },
            "unexpected error reporting",
        )

    def test_valid_nonontology_content(self):
        """Non-ontology metadata should conform to convention requirements
        """
        # def set
        # Note: this input metadata file does not have array-based metadata
        args = (
            "--convention ../schema/alexandria_convention/alexandria_convention_schema.json "
            "../tests/data/annotation/metadata/convention/valid_no_array_v2.0.0.txt"
        )
        metadata, convention = self.setup_metadata(args)
        self.assertTrue(
            metadata.validate_format(), "Valid metadata headers should not elicit error"
        )
        collect_jsonschema_errors(metadata, convention)
        self.assertFalse(
            report_issues(metadata), "Valid metadata content should not elicit error"
        )
        self.teardown_metadata(metadata)

        # invalid non-ontology content
        args = (
            "--convention ../schema/alexandria_convention/alexandria_convention_schema.json "
            "../tests/data/annotation/metadata/invalid_metadata_v2.0.0.tsv"
        )
        metadata, convention = self.setup_metadata(args)
        self.maxDiff = None
        self.assertTrue(
            metadata.validate_format(), "Valid metadata headers should not elicit error"
        )
        collect_jsonschema_errors(metadata, convention)
        self.assertTrue(
            report_issues(metadata), "Valid metadata content should not elicit error"
        )
        validate_collected_ontology_data(metadata, convention)
        # reference errors tests for:
        #   missing required property 'sex'
        #   missing dependency for non-required property 'ethinicity'
        #   missing value for non-required property 'is_living'
        #   value provided not a number for 'organism_age'
        reference_file = open(
            "mock_data/annotation/metadata/convention/issues_metadata_v2.0.0.json"
        )
        reference_issues = json.load(reference_file)
        reference_file.close()
        self.assertEqual(
            metadata.issues,
            reference_issues,
            "Metadata validation issues do not match reference issues",
        )
        self.teardown_metadata(metadata)

    def test_valid_ontology_content(self):
        """Ontology metadata should conform to convention requirements
        """
        # Note: this input metadata file does not have array-based metadata
        args = (
            "--convention ../schema/alexandria_convention/alexandria_convention_schema.json "
            "../tests/data/annotation/metadata/convention/valid_no_array_v2.0.0.txt"
        )
        metadata, convention = self.setup_metadata(args)
        self.assertTrue(
            metadata.validate_format(), "Valid metadata headers should not elicit error"
        )
        validate_input_metadata(metadata, convention)
        self.assertFalse(
            report_issues(metadata), "Valid ontology content should not elicit error"
        )
        self.teardown_metadata(metadata)

    def test_valid_multiple_ontologies_content(self):
        """Ontology metadata should conform to convention requirements
           Specifically tests that a term can be found in one of two accepted ontologies (e.g. disease in MONDO or PATO)
        """
        # Note: this input metadata file does not have array-based metadata
        args = (
            "--convention ../schema/alexandria_convention/alexandria_convention_schema.json "
            "../tests/data/annotation/metadata/convention/valid_no_array_v2.0.0.txt"
        )
        metadata, convention = self.setup_metadata(args)
        self.assertTrue(
            metadata.validate_format(), "Valid metadata headers should not elicit error"
        )
        validate_input_metadata(metadata, convention)
        self.assertFalse(
            report_issues(metadata), "Valid ontology content should not elicit error"
        )
        self.teardown_metadata(metadata)

    def test_invalid_ontology_content(self):
        """Ontology metadata should conform to convention requirements
        """
        # Note: this input metadata file does not have array-based metadata
        args = "--convention ../schema/alexandria_convention/alexandria_convention_schema.json ../tests/data/invalid_ontology_v2.0.0.tsv"
        metadata, convention = self.setup_metadata(args)
        self.maxDiff = None
        self.assertTrue(
            metadata.validate_format(), "Valid metadata headers should not elicit error"
        )
        validate_input_metadata(metadata, convention)
        # reference errors tests for:
        #   empty cell for cell_type entry (convention and ontology errors)
        #   empty cell for entry of geographical_region and its label
        #       (convention and ontology errors)
        #   improper syntax (lack of _ or :) for EFO0008919
        #       (convention and ontology errors)
        #   invalid ontology shortname CELL for cell_type
        #   invalid ontology label 'homo sapien' for species__ontology_label
        #     with species ontologyID of 'NCBITaxon_9606'
        #   invalid ontologyID of 'NCBITaxon_9606' for geographical_region
        #   invalid ontologyID UBERON_1000331 for organ__ontology_label
        reference_file = open(
            "mock_data/annotation/metadata/convention/issues_ontology_v2.0.0.json"
        )
        reference_issues = json.load(reference_file)
        self.assertEqual(
            metadata.issues,
            reference_issues,
            "Ontology validation issues do not match reference issues",
        )
        reference_file.close()
        self.teardown_metadata(metadata)

    def test_content(self):
        """Array-based metadata should conform to convention requirements
        """

        def set_up_test(test_file_name, ref_file_name):
            test_file_path = "data/annotation/metadata/convention/" + test_file_name
            ref_file_path = "mock_data/annotation/metadata/convention/" + ref_file_name
            args = "--convention ../schema/alexandria_convention/alexandria_convention_schema.json "
            metadata, convention = self.setup_metadata(args + test_file_path)
            validate_input_metadata(metadata, convention)

            reference_file = open(ref_file_path)
            reference_issues = json.load(reference_file)
            reference_file.close()
            self.assertEqual(
                reference_issues,
                metadata.issues,
                "Metadata validation issues do not match reference issues",
            )
            return metadata

        # valid array data emits one warning message for disease__time_since_onset__unit
        # because no ontology label supplied in metadata file for the unit ontology
        metadata = set_up_test("valid_array_v2.1.2.txt", "issues_warn_v2.1.2.json")
        self.assertTrue(
            metadata.validate_format(), "Valid metadata headers should not elicit error"
        )
        self.assertFalse(
            report_issues(metadata), "Valid ontology content should not elicit error"
        )
        self.teardown_metadata(metadata)

        # Negative test cases

        # reference errors tests for:
        # conflict between convention type and input metadata type annotation
        #     group instead of numeric: organism_age
        #     numeric instead of group: biosample_type
        # invalid array-based metadata type: disease__time_since_onset
        # invalid boolean value: disease__treated
        # non-uniform unit values: organism_age__unit
        # missing ontology ID or label for non-required metadata: ethnicity
        # invalid header content: donor info (only alphanumeric or underscore allowed)
        metadata = set_up_test("invalid_array_v2.1.2.txt", "issues_array_v2.1.2.json")
        self.assertTrue(
            metadata.validate_format(), "Valid metadata headers should not elicit error"
        )
        self.teardown_metadata(metadata)

        # Arrays have NA values
        set_up_test("has_na_in_array.tsv", "has_na_in_array.json")

        # Arrays have commas instead of pipes
        set_up_test("has_commas_in_arrays.csv", "has_commas_in_arrays.json")

        # File has NA values in required fields
        set_up_test("has_na_in_required_fields.csv", "has_na_in_required_fields.json")

    def test_bigquery_json_content(self):
        """generated newline delimited JSON for BigQuery upload should match expected output
        """
        args = (
            "--convention ../schema/alexandria_convention/alexandria_convention_schema.json "
            "../tests/data/annotation/metadata/convention/valid_array_v2.1.2.txt"
        )
        metadata, convention = self.setup_metadata(args)
        metadata.preprocess(is_metadata_convention=True)
        validate_input_metadata(metadata, convention, bq_json=True)

        generated_bq_json = str(metadata.study_file_id) + ".json"
        # This reference file needs updating with every new metadata convention version
        reference_bq_json = "../tests/data/bq_test.json"
        self.assertListEqual(
            list(io.open(generated_bq_json)), list(io.open(reference_bq_json))
        )

        self.teardown_metadata(metadata)

        # clean up downloaded generated BigQuery upload file
        try:
            os.remove("addedfeed000000000000000.json")
        except OSError:
            print("no file to remove")

    def test_invalid_mba_content(self):
        """Mouse Brain Atlas metadata should validate against MBA ontology file
        """
        args = (
            "--convention ../schema/alexandria_convention/alexandria_convention_schema.json "
            "../tests/data/annotation/metadata/convention/invalid_mba_v2.1.2.tsv"
        )
        metadata, convention = self.setup_metadata(args)
        self.maxDiff = None
        self.assertTrue(
            metadata.validate_format(), "Valid metadata headers should not elicit error"
        )
        collect_jsonschema_errors(metadata, convention)
        self.assertTrue(
            report_issues(metadata), "Valid metadata content should not elicit error"
        )
        validate_collected_ontology_data(metadata, convention)
        # reference errors tests for:
        #   missing organ_region when organ_region__ontology_label provided
        #   Invalid identifier MBA_999999999
        #   mismatch of organ_region__ontology_label value with label value in MBA
        #   mismatch of organ_region__ontology_label value with label from MBA_id lookup
        reference_file = open(
            "mock_data/annotation/metadata/convention/issues_mba_v2.1.2.json"
        )
        reference_issues = json.load(reference_file)
        reference_file.close()
        self.assertEqual(
            metadata.issues,
            reference_issues,
            "Metadata validation issues do not match reference issues",
        )
        self.teardown_metadata(metadata)

    def test_is_empty_string(self):
        self.assertTrue(is_empty_string(""))
        self.assertTrue(is_empty_string("  "))
        self.assertFalse(is_empty_string("Hello"))
        self.assertFalse(is_empty_string(4))

    @patch("requests.get", side_effect=mocked_requests_get)
    def test_request_backoff_handling(self, mocked_requests_get):
        """errors in retrieving data from external resources should attempt MAX_HTTP_ATTEMPTS times and throw an exception
        """
        request_url = "https://www.ebi.ac.uk/ols/api/ontologies/"
        self.assertRaises(
            requests.exceptions.RequestException, request_json_with_backoff, request_url
        )
        self.assertEqual(mocked_requests_get.call_count, MAX_HTTP_ATTEMPTS)

    def test_is_label_or_synonym(self):
        label = "10x 3' v2"
        possible_matches = {"label": "10x 3' v2", "synonyms": ["10X 3' v2", "10x 3' v2 sequencing"]}
        self.assertTrue(is_label_or_synonym(possible_matches, label))
        label = "10X 3' v2"
        self.assertTrue(is_label_or_synonym(possible_matches, label))
        label = "10X 3' v2 sequencing"
        self.assertTrue(is_label_or_synonym(possible_matches, label))
        label = "10x 5' v3"
        self.assertFalse(is_label_or_synonym(possible_matches, label))

    def test_will_allow_synonym_matches(self):
        args = (
            "--convention ../schema/alexandria_convention/alexandria_convention_schema.json "
            "../tests/data/annotation/metadata/convention/valid_no_array_synonyms_v2.0.0.txt"
        )
        metadata, convention = self.setup_metadata(args)
        self.assertTrue(
            metadata.validate_format(), "Valid metadata headers should not elicit error"
        )
        validate_input_metadata(metadata, convention)
        self.assertFalse(
            report_issues(metadata), "Valid ontology content should not elicit error"
        )
        self.teardown_metadata(metadata)

if __name__ == "__main__":
    unittest.main()
