# -*- coding: utf-8 -*-
"""
@author: Raluca Sandu
"""
import sys
import argparse
import os
import pydicom
import pandas as pd
from datetime import datetime


def create_dict_paths_series_dcm(rootdir, ablation_date_redcap):
    list_all_ct_series = []
    acquisition_time_list = []
    number_ct_scans = 0
    for subdir, dirs, files in os.walk(rootdir):

        for file in sorted(files):
            try:
                dcm_file = os.path.join(subdir, file)
                dataset_source_ct = pydicom.read_file(dcm_file)
                ablation_date_ct = dataset_source_ct.AcquisitionDate
                if ablation_date_ct != ablation_date_redcap:
                    continue
                ct_time_str = dataset_source_ct.AcquisitionDateTime
                ct_date_time = datetime.strptime(ct_time_str, "%Y%m%d%H%M%S")
                acquisition_time_list.append(ct_date_time)
                patient_id = dcm_file.PatientID
                # extract just the first time from a folder
            except Exception:
                # not dicom file so continue until you find one
                continue
            source_series_instance_uid = dataset_source_ct.SeriesInstanceUID
            try:
                source_study_instance_uid = dataset_source_ct.StudyInstanceUID
            except Exception:
                source_study_instance_uid = None
            source_series_number = dataset_source_ct.SeriesNumber
            source_SOP_class_uid = dataset_source_ct.SOPClassUID
            # if the ct series is not found in the dictionary, add it
            result = next((item for item in list_all_ct_series if
                           item["SeriesInstanceNumberUID"] == source_series_instance_uid), None)
            if result is None:
                number_ct_scans +=1
                dict_series_folder = {'PatientID:': patient_id,
                                      "SeriesNumber": source_series_number,
                                      "SeriesInstanceNumberUID": source_series_instance_uid,
                                      "SOPClassUID": source_SOP_class_uid,
                                      "StudyInstanceUID": source_study_instance_uid,
                                      'Number CT Scans': number_ct_scans,
                                      }
                list_all_ct_series.append(dict_series_folder)

    df = pd.DataFrame(data=acquisition_time_list, columns=['Time'], index=range(0, len(acquisition_time_list)))
    time_duration_procedure = (df.Time.max() - df.Time.min()).total_seconds() / 60
    df_patient = pd.DataFrame(list_all_ct_series)
    df_patient['TimeDurationMin'] = time_duration_procedure

    return df_patient


if '__name__' == '__main__':
    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--rootdir", required=False, help="path to the patient folder to be processed")
    ap.add_argument("-b", "--input_batch_proc", required=False,
                    help="input excel file for batch processing")  # Batch_processing_MAVERRIC.xlsx
    ap.add_argument('-r', "--redcap_file", required=False,
                    help="redcap file for no of antenna insertions")  # redcap_file_all_2019-10-14.xlsx
    args = vars(ap.parse_args())
    if args['redcap_file'] is not None:
        print('RedCap File provided for number of lesions treated and no. antenna insertions')
    else:
        print('no redcap file provided')
        flag_redcap = False
    if args["rootdir"] is not None:
        print("Single patient folder processing, path to folder: ", args["rootdir"])
    elif (args["input_batch_proc"]) is not None and (args["rootdir"] is None):
        print("Batch Processing Enabled, path to csv: ", args["input_batch_proc"])
    else:
        print("no input values provided either for single patient processing or batch processing. System Exiting")
        sys.exit()

    df_redcap = pd.read_excel(args['redcap_file'])
    # parse each patient folder # PATIENT LEVEL
    # count the number of scans  and add all the scans and their times to a list
    # calculate the time between the first and last ablation scan