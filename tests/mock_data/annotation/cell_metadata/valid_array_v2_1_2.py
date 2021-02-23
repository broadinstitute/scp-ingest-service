from bson.objectid import ObjectId

valid_array_v2_1_2_models = {
    "cell_metadata_models": {
        "disease__time_since_onset": {
            "_id": ObjectId("600f4325e164652b111111a6"),
            "name": "disease__time_since_onset",
            "annotation_type": "numeric",
            "values": [],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "disease__time_since_onset__unit": {
            "_id": ObjectId("600f4325e164652b111111a8"),
            "name": "disease__time_since_onset__unit",
            "annotation_type": "group",
            "values": ["UO_0000035"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "organ_region": {
            "_id": ObjectId("600f4325e164652b111111aa"),
            "name": "organ_region",
            "annotation_type": "group",
            "values": [
                "MBA:000000944",
                "MBA:000000302|MBA:000000294|MBA:000000795",
                "MBA:000000714|MBA:000000972",
                "MBA:000001041",
                "MBA:000000909|MBA:000000502",
            ],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "organ_region__ontology_label": {
            "_id": ObjectId("600f4325e164652b111111ac"),
            "name": "organ_region__ontology_label",
            "annotation_type": "group",
            "values": [
                "Folium-tuber vermis (VII)",
                "Superior colliculus, sensory related|Superior colliculus, motor related|Periaqueductal gray",
                "",
                "Paraflocculus",
                "Entorhinal area|Subiculum",
            ],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "annotation_type": {
            "_id": ObjectId("600f4325e164652b111111ae"),
            "name": "donor",
            "annotation_type": "group",
            "values": ["BM01"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "disease__treated": {
            "_id": ObjectId("600f4325e164652b111111b0"),
            "name": "disease__treated",
            "annotation_type": "group",
            "values": ["False|False", "FALSE", "True|False", "True|False|False"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "species": {
            "_id": ObjectId("600f4325e164652b111111b2"),
            "name": "species",
            "annotation_type": "group",
            "values": ["NCBITaxon_9606"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "species__ontology_label": {
            "_id": ObjectId("600f4325e164652b111111b4"),
            "name": "species__ontology_label",
            "annotation_type": "group",
            "values": ["Homo sapiens"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "geographical_region": {
            "_id": ObjectId("600f4325e164652b111111b6"),
            "name": "geographical_region",
            "annotation_type": "group",
            "values": ["GAZ_00003181"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "geographical_region__ontology_label": {
            "_id": ObjectId("600f4325e164652b111111b8"),
            "name": "geographical_region__ontology_label",
            "annotation_type": "group",
            "values": ["Boston"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "library_preparation_protocol": {
            "_id": ObjectId("600f4325e164652b111111ba"),
            "name": "library_preparation_protocol",
            "annotation_type": "group",
            "values": ["EFO_0008919"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "library_preparation_protocol__ontology_label": {
            "_id": ObjectId("600f4325e164652b111111bc"),
            "name": "library_preparation_protocol__ontology_label",
            "annotation_type": "group",
            "values": ["Seq-Well"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "annotation_type": {
            "_id": ObjectId("600f4325e164652b111111be"),
            "name": "organ",
            "annotation_type": "group",
            "values": ["UBERON_0001913"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "organ__ontology_label": {
            "_id": ObjectId("600f4325e164652b111111c0"),
            "name": "organ__ontology_label",
            "annotation_type": "group",
            "values": ["milk"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "sex": {
            "_id": ObjectId("600f4325e164652b111111c2"),
            "name": "sex",
            "annotation_type": "group",
            "values": ["female"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "is_living": {
            "_id": ObjectId("600f4325e164652b111111c4"),
            "name": "is_living",
            "annotation_type": "group",
            "values": ["yes"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "organism_age__unit": {
            "_id": ObjectId("600f4325e164652b111111c6"),
            "name": "organism_age__unit",
            "annotation_type": "group",
            "values": ["UO_0000036"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "organism_age__unit_label": {
            "_id": ObjectId("600f4325e164652b111111c8"),
            "name": "organism_age__unit_label",
            "annotation_type": "group",
            "values": ["year"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "ethnicity__ontology_label": {
            "_id": ObjectId("600f4325e164652b111111ca"),
            "name": "ethnicity__ontology_label",
            "annotation_type": "group",
            "values": ["European", "European|British", ""],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
        "ethnicity": {
            "_id": ObjectId("600f4325e164652b111111cc"),
            "name": "ethnicity",
            "annotation_type": "group",
            "values": ["HANCESTRO_0005", "HANCESTRO_0005|HANCESTRO_0462"],
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
        },
    },
    "data_arrays": {
        "All Cells": {
            "_id": ObjectId("600f4325e164652b111111a5"),
            "name": "All Cells",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "cells",
            "array_index": 0,
            "values": [
                "BM01_16dpp_AAGCAGTGGTAT",
                "BM01_16dpp_TAAGCAGTGGTA",
                "BM01_16dpp_CTAAGCAGTGGT",
                "BM01_16dpp_CGGTAAACCATT",
                "BM01_16dpp_CCGAATTCACCG",
            ],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "Study",
            "linear_data_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "disease__time_since_onset": {
            "_id": ObjectId("600f4325e164652b111111a7"),
            "name": "disease__time_since_onset",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": ["12|2", "1", "24|2", "36|3|1", "0"],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111a6"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "disease__time_since_onset__unit": {
            "_id": ObjectId("600f4325e164652b111111a9"),
            "name": "disease__time_since_onset__unit",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": [
                "UO_0000035",
                "UO_0000035",
                "UO_0000035",
                "UO_0000035",
                "UO_0000035",
            ],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111a8"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "organ_region": {
            "_id": ObjectId("600f4325e164652b111111ab"),
            "name": "organ_region",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": [
                "MBA:000000944",
                "MBA:000000302|MBA:000000294|MBA:000000795",
                "MBA:000000714|MBA:000000972",
                "MBA:000001041",
                "MBA:000000909|MBA:000000502",
            ],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111aa"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "organ_region__ontology_label": {
            "_id": ObjectId("600f4325e164652b111111ad"),
            "name": "organ_region__ontology_label",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": [
                "Folium-tuber vermis (VII)",
                "Superior colliculus, sensory related|Superior colliculus, motor related|Periaqueductal gray",
                "",
                "Paraflocculus",
                "Entorhinal area|Subiculum",
            ],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111ac"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "donor": {
            "_id": ObjectId("600f4325e164652b111111af"),
            "name": "donor",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": ["BM01", "BM01", "BM01", "BM01", "BM01"],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111ae"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "disease__treated": {
            "_id": ObjectId("600f4325e164652b111111b1"),
            "name": "disease__treated",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": [
                "False|False",
                "FALSE",
                "True|False",
                "True|False|False",
                "FALSE",
            ],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111b0"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "species": {
            "_id": ObjectId("600f4325e164652b111111b3"),
            "name": "species",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": [
                "NCBITaxon_9606",
                "NCBITaxon_9606",
                "NCBITaxon_9606",
                "NCBITaxon_9606",
                "NCBITaxon_9606",
            ],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111b2"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "species__ontology_label": {
            "_id": ObjectId("600f4325e164652b111111b5"),
            "name": "species__ontology_label",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": [
                "Homo sapiens",
                "Homo sapiens",
                "Homo sapiens",
                "Homo sapiens",
                "Homo sapiens",
            ],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111b4"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "geographical_region": {
            "_id": ObjectId("600f4325e164652b111111b7"),
            "name": "geographical_region",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": [
                "GAZ_00003181",
                "GAZ_00003181",
                "GAZ_00003181",
                "GAZ_00003181",
                "GAZ_00003181",
            ],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111b6"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "geographical_region__ontology_label": {
            "_id": ObjectId("600f4325e164652b111111b9"),
            "name": "geographical_region__ontology_label",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": ["Boston", "Boston", "Boston", "Boston", "Boston"],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111b8"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "library_preparation_protocol": {
            "_id": ObjectId("600f4325e164652b111111bb"),
            "name": "library_preparation_protocol",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": [
                "EFO_0008919",
                "EFO_0008919",
                "EFO_0008919",
                "EFO_0008919",
                "EFO_0008919",
            ],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111ba"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "library_preparation_protocol__ontology_label": {
            "_id": ObjectId("600f4325e164652b111111bd"),
            "name": "library_preparation_protocol__ontology_label",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": ["Seq-Well", "Seq-Well", "Seq-Well", "Seq-Well", "Seq-Well"],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111bc"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "organ": {
            "_id": ObjectId("600f4325e164652b111111bf"),
            "name": "organ",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": [
                "UBERON_0001913",
                "UBERON_0001913",
                "UBERON_0001913",
                "UBERON_0001913",
                "UBERON_0001913",
            ],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111be"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "organ__ontology_label": {
            "_id": ObjectId("600f4325e164652b111111c1"),
            "name": "organ__ontology_label",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": ["milk", "milk", "milk", "milk", "milk"],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111c0"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "sex": {
            "_id": ObjectId("600f4325e164652b111111c3"),
            "name": "sex",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": ["female", "female", "female", "female", "female"],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111c2"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "is_living": {
            "_id": ObjectId("600f4325e164652b111111c5"),
            "name": "is_living",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": ["yes", "yes", "yes", "yes", "yes"],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111c4"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "organism_age__unit": {
            "_id": ObjectId("600f4325e164652b111111c7"),
            "name": "organism_age__unit",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": [
                "UO_0000036",
                "UO_0000036",
                "UO_0000036",
                "UO_0000036",
                "UO_0000036",
            ],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111c6"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "organism_age__unit_label": {
            "_id": ObjectId("600f4325e164652b111111c9"),
            "name": "organism_age__unit_label",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": ["year", "year", "year", "year", "year"],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111c8"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
        "ethnicity__ontology_label": {
            "_id": ObjectId("600f4325e164652b111111cb"),
            "name": "ethnicity__ontology_label",
            "cluster_name": "valid_array_v2.1.2.txt",
            "array_type": "annotations",
            "array_index": 0,
            "values": ["European", "European", "European|British", "", "European"],
            "subsample_threshold": None,
            "subsample_annotation": None,
            "linear_data_type": "CellMetadatum",
            "linear_data_id": ObjectId("600f4325e164652b111111ca"),
            "study_id": ObjectId("5ea08bb17b2f150f29f4d952"),
            "study_file_id": ObjectId("600f42bdb067340e777b1385"),
        },
    },
}
