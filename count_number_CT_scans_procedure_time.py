# -*- coding: utf-8 -*-
"""
@author: Raluca Sandu
"""
import argparse
import os
import sys
from ast import literal_eval
from datetime import datetime

import pandas as pd
import pydicom


def create_dict_paths_series_dcm(rootdir, ablation_date_redcap, patient_id):
    list_all_ct_series = []
    acquisition_time_list = []
    number_ct_scans = 0
    for subdir, dirs, files in os.walk(rootdir):
        for file in sorted(files):
            try:
                dcm_file = os.path.join(subdir, file)
                dataset_source_ct = pydicom.read_file(dcm_file)
            except Exception:
                continue
            ablation_date_ct = dataset_source_ct.AcquisitionDate
            if str(ablation_date_ct) != str(ablation_date_redcap):
                continue
            ct_time = dataset_source_ct.AcquisitionDateTime
            ct_time_str = ct_time.split('.')[0]
            ct_date_time = datetime.strptime(ct_time_str, "%Y%m%d%H%M%S")
            acquisition_time_list.append(ct_date_time)
            # extract just the first time from a folder

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
    print(len(df))
    print((df.Time.max() - df.Time.min()))
    time_duration_procedure = (df.Time.max() - df.Time.min()).total_seconds() / 60
    dict_pat = {'PatientID:': patient_id,
                'Number CT Scans': number_ct_scans,
                'TimeDurationMin': time_duration_procedure
                }
    list_dict_pat = []
    list_dict_pat.append(dict_pat)
    df_patient = pd.DataFrame(list_dict_pat)

    return df_patient


if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--rootdir", required=False, help="path to the patient folder to be processed")
    ap.add_argument("-b", "--input_batch_proc", required=False,
                    help="input excel file for batch processing")  # Batch_processing_MAVERRIC.xlsx
    args = vars(ap.parse_args())
    if args["rootdir"] is not None:
        print("Single patient folder processing, path to folder: ", args["rootdir"])
    elif (args["input_batch_proc"]) is not None and (args["rootdir"] is None):
        print("Batch Processing Enabled, path to csv: ", args["input_batch_proc"])
    else:
        print("no input values provided either for single patient processing or batch processing. System Exiting")
        sys.exit()
    list_not_validated = []
    # iterate through each patient and send the root dir filepath
    df = pd.read_excel(args["input_batch_proc"])
    df.drop_duplicates(subset=["Patient_ID"], inplace=True)
    df.reset_index(inplace=True)
    df['Patient_Dir_Paths'].fillna("[]", inplace=True)
    df['Patient_Dir_Paths'] = df['Patient_Dir_Paths'].apply(literal_eval)
    frames = []
    for row in df.itertuples():
        rootdir = row.Patient_Dir_Paths[0]
        ablation_date_redcap = row.Ablation_IR_Date
        patient_id = row.Patient_ID
        frames.append(create_dict_paths_series_dcm(rootdir, ablation_date_redcap, patient_id))

    print(len(frames))
    df_final = pd.concat(frames, ignore_index=True)


