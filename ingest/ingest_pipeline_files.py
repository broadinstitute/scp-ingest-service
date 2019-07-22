import csv
import mimetypes
import os

from mtx import Mtx


class IngestFiles:
    def __init__(self, file_path, allowed_file_types):
        if not os.path.exists(file_path):
            raise IOError(f"File '{matrix_file}' not found")
        self.file_type, self.file = self.open_file(file_path)
        self.allowed_file_types = allowed_file_types

    # Inherited function
    def open_file(self, file_path):
        # Check file type
        file_type = self.get_file_type(file_path)
        # See if file type is allowed
        if file_type in self.allowed_file_types:
            # open file
            file_connections = {
                'text/csv': open(file_path),
                'text/plain': self.open_csv(open(file_path)),
                'text/tab-separated-values': open,
            }

        # Return file object and type
        return file_type, file_connections.get(file_type)

    def extract(self):
        file_type_extract_fns = {
            'text/csv': self.extract_csv(),
            'text/plain': self.extract_txt(),
            'text/tab-separated-values': open,
        }
        return file_type_extract_fns.get(self.file_type)

    def get_file_type(self, file_path):
        return mimetypes.guess_type(file_path)

    def open_csv(self, opened_file_object):
        csv.register_dialect('myDialect',
                             delimiter=',',
                             quoting=csv.QUOTE_ALL,
                             skipinitialspace=True)
        return csv.reader(opened_file_object, dialect='myDialect')

    def extract_csv(self):
        for row in self.file:
            yield next(row)

    def extract_txt(self):
        while True:
            next_lines = list(islice(self.file, size))
            if not next_lines:
                break
            print(next_lines)
