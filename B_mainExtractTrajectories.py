# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 16:49:22 2018

@author: Raluca Sandu

"""
import argparse
import os
import sys
from ast import literal_eval
from collections import defaultdict

import numpy as np
import pandas as pd

import ExtractTPEtoExcel as dataframe_metrics
import NeedlesInfoClasses as C_NeedlesInfoClasses
import ParseNeedleTrajectories as parseNeedleTrajectories


# %%
def call_needle_extraction(rootdir):
    for subdir, dirs, files in os.walk(rootdir):
        # sorted: files by date of creation
        for file in sorted(files):
            fileName, fileExtension = os.path.splitext(file)
            # the tumour segmentation path is in the "Plan.xml"
            # the ablation segmentation path is in the "Validation.xml"
            if fileExtension.lower().endswith('.xml') and (
                    'validation' in fileName.lower() or 'plan' in fileName.lower()):
                xmlFilePathName = os.path.join(subdir, file)
                xmlfilename = os.path.normpath(xmlFilePathName)
                xmlobj = parseNeedleTrajectories.I_parseRecordingXML(xmlfilename)

                if xmlobj is 1:
                    # file was re-written of weird characters so we need to re-open it.
                    xmlobj = parseNeedleTrajectories.I_parseRecordingXML(xmlfilename)
                if xmlobj is not None and xmlobj != 1:
                    pat_id = xmlobj.patient_id_xml
                    pat_ids.append(pat_id)
                    # parse trajectories and other patient specific info
                    trajectories_info = parseNeedleTrajectories.II_parseTrajectories(xmlobj.trajectories)
                    if trajectories_info.trajectories is None:
                        continue  # no trajectories found in this xml, go on to the next file.
                    else:
                        # check if patient exists first, if yes, instantiate new object, otherwise retrieve it from list
                        patients = patientsRepo.getPatients()
                        # perform search based on patient name if patient_id fails
                        patient = [x for x in patients if x.patient_id_xml == pat_id]
                        if not patient:
                            # instantiate patient object
                            # create patient measurements if patient is not already in the PatientsRepository
                            patient = patientsRepo.addNewPatient(pat_id,
                                                                 xmlobj.patient_name)
                            # instantiate extract registration
                            # parseNeedleTrajectories.II_extractRegistration(xmlobj.trajectories, patient, xmlfilename)
                            # add intervention data
                            parseNeedleTrajectories.III_parseTrajectory(trajectories_info.trajectories, patient,
                                                                        trajectories_info.series, xmlfilename,
                                                                        trajectories_info.time_intervention,
                                                                        trajectories_info.cas_version)
                        else:
                            # update patient measurements in the PatientsRepository if the patient (id) already exists
                            # patient[0] because the returned result is a list with one element.
                            parseNeedleTrajectories.III_parseTrajectory(trajectories_info.trajectories, patient[0],
                                                                        trajectories_info.series, xmlfilename,
                                                                        trajectories_info.time_intervention,
                                                                        trajectories_info.cas_version)
                            # add the registration, if several exist (hopefully not)
                            # parseNeedleTrajectories.II_extractRegistration(xmlobj.trajectories, patient[0], xmlfilename)


def call_extract_class_2_df(patients):
    """
    extract information from the object classes into pandas dataframe
    :param patients: dataframe
    :return: dataframe of patient and needle treatment info
    """
    for patient in patients:
        lesions = patient.getLesions()
        patientID = patient.patient_id_xml
        patientName = patient.patient_name
        for l_idx, lesion in enumerate(lesions):
            needles = lesion.getNeedles()
            needles_defaultdict = C_NeedlesInfoClasses.NeedleToDictWriter.needlesToDict(patientID,
                                                                                        patientName,
                                                                                        l_idx + 1,
                                                                                        needles)
            needles_list.append(needles_defaultdict)
    # unpack from defaultdict and list
    needles_unpacked_list = defaultdict(list)
    for needle_trajectories in needles_list:
        for keys, vals in needle_trajectories.items():
            for val in vals:
                needles_unpacked_list[keys].append(val)
    # convert to DataFrame for easier writing to Excel
    df_patients_trajectories = pd.DataFrame(needles_unpacked_list)
    return df_patients_trajectories


if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--rootdir", required=False, help="path to the patient folder to be processed")
    ap.add_argument("-b", "--input_batch_proc", required=False,
                    help="input excel file for batch processing")  # Batch_processing_MAVERRIC.xlsx
    ap.add_argument('-r', "--redcap_file", required=False,
                    help="redcap file for no of antenna insertions")  # redcap_file_all_2019-10-14.xlsx
    flag_redcap = False
    flag_MWA = False
    flag_IRE = True
    flag_segmentation_info = False
    outfilename = "tpes"

    args = vars(ap.parse_args())

    if args['redcap_file'] is not None:
        print('RedCap File provided for number of lesions treated and no. antenna insertions')
        df_redcap = pd.read_excel(args['redcap_file'])
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

    # %% BATCH Processing
    if args["input_batch_proc"] is not None:
        list_not_validated = []
        # iterate through each patient and send the root dir filepath
        df = pd.read_excel(args["input_batch_proc"])
        df.drop_duplicates(subset=["Patient_ID"], inplace=True)
        df.reset_index(inplace=True)
        df['Patient_Dir_Paths'].fillna("[]", inplace=True)
        try:
            df['Patient_Dir_Paths'] = df['Patient_Dir_Paths'].apply(literal_eval)
        except Exception:
            df['Patient_Dir_Paths'] = df['Patient_Dir_Paths']
        # remove the dash from the PatientName variable
        try:
            df['Patient Name'] = df['Patient Name'].map(lambda x: x.split('-')[0] + x.split('-')[1])
        except Exception:
            df['Patient Name'] = df['Patient Name']
        for idx in range(len(df)):
            patient_id = str(df["Patient_ID"].iloc[idx])
            patient_name = str(df['Patient Name'].iloc[idx])
            patient_dir_paths = df.Patient_Dir_Paths[idx]
            if len(patient_dir_paths) > 0:
                for rootdir in patient_dir_paths:
                    rootdir = os.path.normpath(rootdir)
                    patientsRepo = C_NeedlesInfoClasses.PatientRepo()
                    pat_ids = []
                    pat_id = 0
                    # call script for extracting needle trajectories from XML
                    call_needle_extraction(rootdir)
                    patients = patientsRepo.getPatients()
                    df_patients_trajectories = None
                    needles_list = []
                    if patients:
                        df_patients_trajectories = call_extract_class_2_df(patients)
                    else:
                        print('No CAS Folder Recordings found. Check if the files are there and in the correct folder structure:', rootdir)
                        continue
                    Patient_ID = df_patients_trajectories.iloc[0].PatientID
                    try:
                        Patient_ID_xml = Patient_ID.split('-')[1]
                    except Exception:
                        Patient_ID_xml = Patient_ID
                    if flag_redcap:
                        df_patient_redcap = df_redcap[df_redcap.Patient_ID == Patient_ID_xml]
                        for idx, row in df_patient_redcap.iterrows():
                            if not np.isnan(row['Number of ablated lesions']):
                                no_lesions_redcap = row['Number of ablated lesions']
                    else:
                        no_lesions_redcap = -1
                    df_TPEs_validated = dataframe_metrics.customize_dataframe(
                                            df_patients_trajectories, no_lesions_redcap, list_not_validated)
                    dataframe_metrics.write_toExcelFile(rootdir, outfilename, df_TPEs_validated, df_patients_trajectories)
        # write the list of non validated needles to Excel
        list_not_validated_df = pd.DataFrame(list_not_validated)
        filepath = 'list_patients_not_validated.xlsx'
        writer = pd.ExcelWriter(filepath)
        list_not_validated_df.to_excel(writer, index=False)
        writer.save()

    # SINGLE PATIENT PROCESSING. instanstiate the patient repository class\
    elif args["rootdir"] is not None:
        rootdir = args['rootdir']
        patientsRepo = C_NeedlesInfoClasses.PatientRepo()
        pat_ids = []
        pat_id = 0
        # call script for extracting needle trajectories from XML
        call_needle_extraction(rootdir)
        patients = patientsRepo.getPatients()
        df_patients_trajectories = None
        needles_list = []
        list_not_validated = []
        if patients:
            df_patients_trajectories = call_extract_class_2_df(patients)
        else:
            print('No CAS Folder Recordings found. Check if the files are there and in the correct folder structure:',
                  rootdir)
        Patient_ID = df_patients_trajectories.iloc[0].PatientID
        try:
            Patient_ID_xml = Patient_ID.split('-')[1]
        except Exception:
            Patient_ID_xml = Patient_ID
        if flag_redcap:
            df_patient_redcap = df_redcap[df_redcap.Patient_ID == Patient_ID_xml]
            for idx, row in df_patient_redcap.iterrows():
                if not np.isnan(row['Number of ablated lesions']):
                    no_lesions_redcap = row['Number of ablated lesions']
        else:
            no_lesions_redcap = -1
        df_TPEs_validated = dataframe_metrics.customize_dataframe(df_patients_trajectories,
                                                                  no_lesions_redcap,
                                                                  list_not_validated)
        if flag_MWA:
            dataframe_metrics.write_toExcelFile(rootdir, outfilename, df_TPEs_validated, df_patients_trajectories)
        if flag_IRE:
            df_area_between_needles = dataframe_metrics.compute_area(df_TPEs_validated)
            df_areas = df_area_between_needles[
                ['PatientID', 'LesionNr', 'NeedleCount', 'Planned Area', 'Validation Area']]
            # %% compute angles between IRE Needles
            df_angles = dataframe_metrics.compute_angles(df_TPEs_validated)
            dataframe_metrics.plot_boxplot_angles(df_angles, rootdir)
            # write to Excel File...
            dataframe_metrics.write_toExcelFile(rootdir=rootdir,
                                                outfile=outfilename,
                                                df_needles_validated=df_TPEs_validated,
                                                dfPatientsTrajectories=df_patients_trajectories,
                                                df_angles=df_angles,
                                                df_areas=df_areas)

            print('Success! Extracting and Writing Information to the Excel File.....')
        # write out the needles that weren't validated
        list_not_validated_df = pd.DataFrame(list_not_validated)
        filepath = 'list_patients_not_validated.xlsx'
        writer = pd.ExcelWriter(filepath)
        list_not_validated_df.to_excel(writer, index=False)
        writer.save()
        print('Success! Extracting and Writing Information to the Excel File.....')
