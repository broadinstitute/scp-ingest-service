import copy
import json
import pprint
import random

import numpy as np
import pandas
from clusters import Clusters
from ingest_files import IngestFiles


class SubSample(IngestFiles):
    ALLOWED_FILE_TYPES = ['text/csv',
                          'text/plain', 'text/tab-separated-values']
    MAX_THRESHOLD = 100_000
    SUBSAMPLE_THRESHOLDS = [MAX_THRESHOLD, 20000, 600, 200]

    def __init__(self, file_path, annot_scope):
        IngestFiles.__init__(self,
                             file_path, self.ALLOWED_FILE_TYPES, open_as='pandas')
        self.header = list(self.file.head())
        self.annot_scope = annot_scope
        self.has_z = 'z' in (annot[0].lower()
                             for annot in self.header[0])
        self.coordinates_and_cell_names,  self.columns = self.dermine_coordinates_and_cell_names()
        # conver_group_to_string()

    def round_numeric_annot(self):
        for idx, annot_name in enumerate(self.header):
            if annot_name[1] == 'numeric':
                self.file.round({annot_name: 3})

    def dermine_coordinates_and_cell_names(self):
        if self.annot_scope is 'cluster':
            if self.has_z:
                return [header_name[0] for header_name in self.header[:3]], self.file.iloc[:, 4:]
            else:
                return [header_name[0] for header_name in self.header[:3]], self.file.iloc[:, 3:]
        else:
            return header_name[0]

    def bin(self, annotation):
        bin = {}
        if 'group' in annotation:
            # get unique values from columns if the annotation is of type 'group'
            unique_values = self.file[annotation].unique()

            for col_val in unique_values:
                subset = self.file[self.file[annotation] == col_val]
                bin[col_val] = subset[self.coordinates_and_cell_names]
        else:
            columns = self.coordinates_and_cell_names
            columns.append(annotation[0])
            subset = self.file[columns]
            subset.sort_values(
                by=[annotation], inplace=True)
            for index, df in enumerate(np.array_split(subset, 20)):
                bin[str(index)] = df
        return bin, annotation

    def subsample(self):

        sample_sizes = [
            sample_size for sample_size in self.SUBSAMPLE_THRESHOLDS if sample_size < len(self.file.index)]
        for bins in map(self.bin, self.columns):
            print('shit')
            print(bins)
            annotation_name = bins[1]
            anotation_dict = bins[0]
            group_size = len(anotation_dict.keys())
            for sample_size in sample_sizes:
                unique_keys = anotation_dict.keys()
                num_per_group = int(sample_size / group_size)
                print(f'num per group in {num_per_group}')

                # k is a single group
                for k in self.return_sorted_bin(anotation_dict, annotation_name):
                    print(f'This is k: {k}')
                    cells_left = sample_size
                    random.seed(0)
                    # Iterate over columns in df minus column = annotation_name
                    for idx, x in enumerate(anotation_dict[k[0]].keys()):
                            # Grab value or x, y, z coordinates, or cell names
                    y = anotation_dict[k[0]][x]
                    # Shuffle array randomly using the same seed
                    random.shuffle(y)
                    # If the amounf of sampled values we need is larger
                    # than the whole array, take the whole array
                    if num_per_group > len(y):
                        len_picked_values = len(y) - 1
                    else:
                        len_picked_values = num_per_group - 1

                    picked_values = y[:len_picked_values]
                    yield (x, self.header[idx][1], picked_values, f'{annotation_name[0]}-{annotation_name[1]}-{self.annot_scope}', threshold)
                    if idx < len(anotation_dict[k[0]].keys()) - 1:
                        cells_left -= len_picked_values
                        group_size -= 1
                        num_per_group = int(cells_left / (group_size))

    def return_sorted_bin(self, bin, annot_name):

        if('group' in annot_name):
            return sorted(bin.items(), key=lambda x: len(x[1]))
        else:
            return bin.items()
