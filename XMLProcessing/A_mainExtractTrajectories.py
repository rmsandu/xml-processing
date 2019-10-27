# -*- coding: utf-8 -*-
"""
Created on Tue Feb 27 16:49:22 2018

@author: Raluca Sandu

example how to call the function reading from Keyboard
# rootdir = r""
# outfilename = 'ire_analysis'
# flag_segmentation_info = 'n'
"""
import os
import sys
import pandas as pd
import numpy as np
import argparse
from time import strftime
from ast import literal_eval
from collections import defaultdict

import XMLProcessing.C_NeedlesInfoClasses as C_NeedlesInfoClasses
import XMLProcessing.B_parseNeedleTrajectories as parseNeedleTrajectories
import XMLProcessing.dataframe_metrics as dataframe_metrics

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
                if xmlobj is not None and xmlobj!=1:
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
                            parseNeedleTrajectories.II_extractRegistration(xmlobj.trajectories, patient, xmlfilename)
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
                            parseNeedleTrajectories.II_extractRegistration(xmlobj.trajectories, patient[0], xmlfilename)


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
        img_registration = patient.registrations
        # check-up if more than one distinct img_registration available
        if len(img_registration) > 1:
            print('more than one registration available for patient', patientName)
        for l_idx, lesion in enumerate(lesions):
            needles = lesion.getNeedles()
            needles_defaultdict = C_NeedlesInfoClasses.NeedleToDictWriter.needlesToDict(patientID,
                                                                                        patientName,
                                                                                        l_idx + 1,
                                                                                        needles,
                                                                                        img_registration)
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
    print("Success unpacking from class to dataframe....")


if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-i", "--rootdir", required=False, help="path to the patient folder to be processed")
    ap.add_argument("-b", "--input_batch_proc", required=False, help="input excel file for batch processing")
    ap.add_argument('-r', "--redcap_file", required=False, help="redcap file for no of antenna insertions")
    flag_redcap = True
    flag_IRE = False
    flag_MWA = True
    flag_segmentation_info = False
    outfilename = "tpes"

    args = vars(ap.parse_args())

    if args['redcap_file'] is not None:
        print('Recap File provided for number of lesions treated and no. antenna insertions')
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

    #%% SINGLE PATIENT PROCESSING. instanstiate the patient repository class\
    if args["input_batch_proc"] is not None:
        print('Flag to anonymize all files:', args["anonymize_all_dcm_files"])
        # iterate through each patient and send the root dir filepath
        df = pd.read_excel(args["input_batch_proc"])
        df.drop_duplicates(subset=["Patient_ID"], inplace=True)
        df.reset_index(inplace=True)
        df['Patient_Dir_Paths'].fillna("[]", inplace=True)
        df['Patient_Dir_Paths'] = df['Patient_Dir_Paths'].apply(literal_eval)
        # remove the dash from the PatientName variable
        df['Patient Name'] = df['Patient Name'].map(lambda x: x.split('-')[0] + x.split('-')[1])
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
                        print(
                            'No CAS Folder Recordings found. Check if the files are there and in the correct folder structure:',
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
                                                                              flag_IRE,
                                                                              flag_MWA,
                                                                              no_lesions_redcap)
                    if flag_MWA is True:
                        dataframe_metrics.write_toExcelFile(rootdir, outfilename, df_TPEs_validated,
                                                            df_patients_trajectories)

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
                                                                  flag_IRE,
                                                                  flag_MWA,
                                                                  no_lesions_redcap)
        if flag_MWA is True:
            dataframe_metrics.write_toExcelFile(rootdir, outfilename, df_TPEs_validated, df_patients_trajectories)
            print('Success! Extracting and Writing Information to the Excel File.....')

        if flag_IRE is True:
            # %% compute area between IRE Needles
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






