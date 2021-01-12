"""Base class for annotation files (such as cluster and metadata files)

DESCRIPTION
Class defines common functions and validation methods for annotation files

PREREQUISITES
Must have python 3.6 or higher.
"""

import abc
from collections import defaultdict

import pandas as pd
from bson.objectid import ObjectId

try:
    # Used when importing internally and in tests
    from ingest_files import IngestFiles
    from monitor import setup_logger, log_exception

except ImportError:
    # Used when importing as external package, e.g. imports in single_cell_portal code
    from .ingest_files import IngestFiles
    from .monitor import setup_logger, log_exception


class Annotations(IngestFiles):
    __metaclass__ = abc.ABCMeta

    # Logger provides more details
    dev_logger = setup_logger(__name__, "log.txt", format="support_configs")
    user_logger = setup_logger(__name__ + ".user_logger", "user_log.txt")

    def __init__(
        self, file_path, allowed_file_types, study_id=None, study_file_id=None
    ):
        IngestFiles.__init__(self, file_path, allowed_file_types)
        if study_id is not None:
            self.study_id = ObjectId(study_id)
        else:
            self.extra_log_params = {"study_id": None, "duration": None}
        if study_file_id is not None:
            self.study_file_id = ObjectId(study_file_id)
        # lambda below initializes new key with nested dictionary as value and avoids KeyError
        self.issues = defaultdict(lambda: defaultdict(lambda: defaultdict(list)))
        csv_file, self.file_handle = self.open_file(self.file_path)
        # Remove white spaces, quotes (only lowercase annot_types)
        self.headers = [header.strip().strip('"') for header in next(csv_file)]
        self.annot_types = [type.strip().strip('"').lower() for type in next(csv_file)]

    def reset_file(self):
        self.preprocess()

    @abc.abstractmethod
    def transform(self):
        """Returns data model"""

    @abc.abstractmethod
    def set_data_array(self):
        """Sets DataArray"""

    def determine_coordinates_and_cell_names(self):
        """Finds column names for coordinates, annotations, and cell names"""
        self.coordinates_and_cell_headers = [
            annot[0]
            for annot in self.file.columns
            if annot[0].lower() in ("z", "y", "x", "name")
        ]
        # annotation column names
        self.annot_column_headers = [
            annot
            for annot in self.file.columns
            if annot[0].lower() not in ("z", "y", "x", "name")
        ]

    @staticmethod
    def get_cell_names(df):
        cell_names_str: str = df[("NAME", "TYPE")].to_string(index=False)
        cell_names: list = cell_names_str.strip().splitlines()
        return cell_names

    def merge_df(self, first_df, second_df):
        """ Does an inner join on a dataframe """
        self.file = pd.merge(second_df, first_df, on=[("NAME", "TYPE")])

    def preprocess(self, is_metadata_convention=False):
        """Ensures that:
            - 'NAME' in first header row is capitalized
            - 'TYPE' in second header row is capitalized
        """

        # Uppercase NAME and TYPE
        self.headers[0] = self.headers[0].upper()
        self.annot_types[0] = self.annot_types[0].upper()
        if self.validate_unique_header():
            self.create_data_frame(self, is_metadata_convention)
        else:
            msg = (
                "Unable to parse file - Duplicate annotation header names are not allowed. \n"
                "This error can be also be caused by a row with too many entries. \n"
            )
            log_exception(Annotations.dev_logger, Annotations.user_logger, msg)
            raise ValueError(msg)

    def reset_header(df, columns):
        index = pd.MultiIndex.from_tuples(columns, names=["Name", "TYPE"])
        df.columns = pd.MultiIndex.from_tuples(index)
        return df

    @staticmethod
    def set_dtypes(header, annot_types, is_metadata_convention=False):
        import numpy as np

        dtypes = {}
        for annotation, annot_type in zip(header, annot_types):
            if annot_type == "group":
                dtypes[annotation] = np.str
            # Number metadata convention may have an array that's pipedelimited.
            # In that case, we leave the column as a string.
            elif annot_type != "numeric" and not is_metadata_convention:
                dtypes[annotation] = np.float32
        return dtypes

    def create_columns(headers, annot_types):
        new_column_names = []
        for annotation, annot_type in zip(headers, annot_types):
            new_column_names.append((annotation, annot_type))
        return new_column_names

    def create_data_frame(self, is_metadata_convention=False):
        """
        - Create dataframe with proper dtypes to ensure:
            - Labels are treated as strings (objects)
            - Numeric annotations are treated as float32
            - Numeric columns are rounded to 3 decimals points
        """

        dtypes = Annotations.set_dtypes(
            self.headers[1:], self.annot_types[1:], is_metadata_convention
        )
        df = self.open_file(
            self.file_path,
            open_as="dataframe",
            converters=dtypes,
            # names=index,
            skiprows=[1],
            engine="python",
        )[0]
        new_header_namese = Annotations.create_columns(self.headers, self.annot_types)
        self.file = Annotations.reset_header(df, new_header_namese)
        # # dtype of object allows mixed dtypes in columns, including numeric dtypes
        # # coerce group annotations that pandas detects as non-object types to type string
        # if "group" in self.annot_types:
        #     group_columns = self.file.xs(
        #         "group", axis=1, level=1, drop_level=False
        #     ).columns.tolist()
        #     try:
        #         # coerce group annotations to type string
        #         self.file[group_columns] = self.file[group_columns].astype(str)
        #     except Exception as e:
        #         log_exception(
        #             Annotations.dev_logger,
        #             Annotations.user_logger,
        #             "Unable to coerce group annotation to string type" + str(e),
        #         )
        # if "numeric" in self.annot_types:
        #     numeric_columns = self.file.xs(
        #         "numeric", axis=1, level=1, drop_level=False
        #     ).columns.tolist()
        #     try:
        #         # Round numeric columns to 3 decimal places
        #         self.file[numeric_columns] = (
        #             self.file[numeric_columns].round(3).astype(float)
        #         )
        #     except Exception as e:
        #         log_exception(Annotations.dev_logger, Annotations.user_logger, e)

    def store_validation_issue(self, type, category, msg, associated_info=None):
        """Store validation issues in proper arrangement
            :param type: type of issue (error or warn)
        :param category: issue category (format, jsonschema, ontology)
        :param msg: issue message
        :param value: list of IDs associated with the issue
        """
        if associated_info:
            self.issues[type][category][msg].extend(associated_info)
        else:
            self.issues[type][category][msg] = None

    def validate_header_keyword(self):
        """Check header row starts with NAME (case-insensitive).

            return: boolean   True if valid, False otherwise
        """

        valid = False
        if self.headers[0].upper() == "NAME":
            valid = True
            if self.headers[0] != "NAME":
                msg = f'File keyword "NAME" provided as {self.headers[0]}'
                self.store_validation_issue("warn", "format", msg)
        else:
            msg = "Malformed file header row, missing NAME keyword. (Case Sensitive)"
            self.store_validation_issue("error", "format", msg)
        return valid

    def validate_unique_header(self):
        """Check all header names are unique and not empty.
            :return: boolean   True if valid, False otherwise
        """
        valid = False
        unique_headers = set(self.headers)
        if len(unique_headers) == len(self.headers):
            valid = True
        else:
            seen_headers = set()
            duplicate_headers = set()
            for x in self.headers:
                if x in seen_headers or seen_headers.add(x):
                    duplicate_headers.add(x)
            msg = f"Duplicated header names are not allowed: {duplicate_headers}"
            log_exception(Annotations.dev_logger, Annotations.user_logger, msg)
            self.store_validation_issue("error", "format", msg)
            valid = False
        if any("Unnamed" in s for s in list(unique_headers)):
            msg = "Headers cannot contain empty values"
            log_exception(Annotations.dev_logger, Annotations.user_logger, msg)
            self.store_validation_issue("error", "format", msg)
            valid = False
        return valid

    def validate_type_keyword(self):
        """Check second row starts with TYPE (case-insensitive).
        :return: boolean   True if valid, False otherwise
        """
        valid = False
        if self.annot_types[0].upper() == "TYPE":
            valid = True
            if self.annot_types[0] != "TYPE":
                msg = f'File keyword "TYPE" provided as {self.annot_types[0]}'
                self.store_validation_issue("warn", "format", msg)
        else:
            msg = "Malformed TYPE row, missing TYPE. (Case Sensitive)"
            self.store_validation_issue("error", "format", msg)
        return valid

    def validate_type_annotations(self):
        """Ensure second row contains only 'group' or 'numeric'.
        :return: boolean   True if all type annotations are valid, otherwise False
        """
        valid = False
        invalid_types = []
        # skipping the TYPE keyword, iterate through the types
        # collecting invalid type annotations in list annots
        for t in self.annot_types[1:]:
            if t.lower() not in ("group", "numeric"):
                # if the value is a blank space, store a higher visibility
                # string for error reporting
                if "Unnamed" in t:
                    invalid_types.append("<empty value>")
                # Duplicated metadata header name causes type annotation issue.
                # Side effect of Pandas adding a suffix to uniquefy the header.
                # These invalid annotations should not be included in invalid
                # type annotation count. This exception may cause miscount of
                # type annot errors if user-supplied annotation has period.
                elif "." in t:
                    pass
                else:
                    invalid_types.append(t)
        if invalid_types:
            msg = 'TYPE row annotations should be "group" or "numeric"'
            self.store_validation_issue("error", "format", msg, invalid_types)
        else:
            valid = True
        return valid

    def validate_against_header_count(self):
        """Header and type counts should match.
        :return: boolean   True if header and type counts match, otherwise False
        """
        valid = False
        len_headers = len(
            [header for header in self.headers if "Unnamed" not in header]
        )
        len_annot_type = len(
            [
                annot_type
                for annot_type in self.annot_types
                if "Unnamed" not in annot_type
            ]
        )
        if not len_headers == len_annot_type:
            msg = (
                f"Header mismatch: {len_annot_type} TYPE declarations "
                f"for {len_headers} column headers"
            )
            self.store_validation_issue("error", "format", msg)
        else:
            valid = True
        return valid

    def validate_format(self):
        """Check common format criteria for annotation files
        """
        return all(
            [
                self.validate_header_keyword(),
                self.validate_type_keyword(),
                self.validate_type_annotations(),
                self.validate_unique_header(),
                self.validate_against_header_count(),
            ]
        )

    def validate_numeric_annots(self):
        """Check numeric annotations are not string dtype
        """
        valid = True
        for annot_header in self.file.columns[0:]:
            annot_name = annot_header[0]
            annot_type = annot_header[1]
            if (
                annot_type == "numeric"
                and self.file[annot_name].dtypes[annot_type] == "object"
            ):
                valid = False
                msg = f"Numeric annotation, {annot_name}, contains non-numeric data (or unidentified NA values)"
                self.store_validation_issue("error", "format", msg)
        return valid
