# File is responsible for defining globals and initializing them
from mongo_connection import MongoConnection
from bson.objectid import ObjectId

MONGO_CONNECTION = MongoConnection()


def init(study_id, study_file_id):
    global __child_events
    global __metric_properties

    __child_events = []
    study = Study(study_id)
    study_file = StudyFile(study_file_id)
    __metric_properties = MetricProperties(study, study_file)


def get_metric_properties():
    global __metric_properties
    return __metric_properties


class MetricProperties:
    def __init__(self, study, study_file):
        self.__properties = {
            "studyAccession": study.accession,
            "fileName": study_file.file_name,
            "fileType": study_file.file_type,
            "fileSize": study_file.file_size,
            "appId": "single-cell-portal",
        }

    def get_properties(self):
        return self.__properties

    def update(self, props):
        if props:
            self.__properties = {**self.__properties, **props}


def add_child_event(event):
    global __child_events
    __child_events.append(event)


class Study:
    def __init__(self, study_id):
        self.study = study_id

    @property
    def study(self):
        return self.__study

    @study.setter
    def study(self, study_id: str):
        try:
            study_id = ObjectId(study_id)
        except Exception:
            raise ValueError("Must pass in valid object id for study file id")
        study = list(
            MONGO_CONNECTION._client["study_accessions"].find(
                {"study_id": study_id}, {"_id": 0}
            )
        )
        if not study:
            raise ValueError(
                "Study ID is not registered with a study. Please provide a valid study ID"
            )
        else:
            self.__study = study.pop()
            self.accession = self.__study["accession"]


class StudyFile:
    def __init__(self, study_file_id):
        self.study_file = study_file_id

    @property
    def study_file(self):
        return self.__study_file

    @study_file.setter
    def study_file(self, study_file_id):
        query = MONGO_CONNECTION._client["study_files"].find(
            {"_id": ObjectId(study_file_id)}
        )
        query_results = list(query)
        if not query_results:
            raise ValueError(
                "Study file ID is not registered with a study. Please provide a valid study file ID."
            )
        else:
            self.__study_file = query_results.pop()
            self.file_type = self.study_file["file_type"]
            self.file_size = self.study_file["upload_file_size"]
            self.file_name = self.study_file["name"]
