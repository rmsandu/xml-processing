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
import pandas as pd
from time import strftime
from collections import defaultdict

import readInputKeyboard
import NeedlesInfoClasses
import parseNeedleTrajectories as parseNeedleTrajectories
import dataframe_metrics

# %%
#
rootdir = os.path.normpath(readInputKeyboard.getNonEmptyString("Root Directory given as r"))
outfilename = readInputKeyboard.getNonEmptyString("Name of the ouput xlsx file ")
flag_IRE = readInputKeyboard.getChoice('Do you want to analyze only the IRE needles?', ['Y', 'N'])
flag_segmentation_info = readInputKeyboard.getChoice('Do you want to have the segmentation information ?', ['Y', 'N'])

# rootdir = r"C:\PatientDatasets_GroundTruth_Database\Stockholm\3d_segmentation_maverric\maverric"
# outfilename =  "data_analysis_maverric_june_segmented_2018"
# flag_IRE = False
# flag_segmentation_info =  True

# instanstiate the patient repository class
patientsRepo = NeedlesInfoClasses.PatientRepo()
pat_ids = []
pat_id = 0

for subdir, dirs, files in os.walk(rootdir):

    for file in sorted(files):
        fileName, fileExtension = os.path.splitext(file)

        # if fileExtension.lower().endswith('.xml') and (
        #         'validation' in fileName.lower() or 'plan' in fileName.lower()):
        if fileExtension.lower().endswith('.xml') and (
                'validation' in fileName.lower() ):
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
                    continue # no trajectories found in this xml, go on to the next file.
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
                        # TODO: write registration matrix to Excel
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
                        # TODO: add flag in excel if registration existing (write registration to excel)
                        parseNeedleTrajectories.II_extractRegistration(xmlobj.trajectories, patient[0], xmlfilename)

# %% extract information from the object classes into pandas datafr ame
patients = patientsRepo.getPatients()
df_patients_trajectories = None
needles_list = []
if patients :
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
            needles_defaultdict = NeedlesInfoClasses.NeedleToDictWriter.needlesToDict(patientID,
                                                                                      patientName,
                                                                                      l_idx+1,
                                                                                      needles,
                                                                                      img_registration)
            needles_list.append(needles_defaultdict)
    # unpack from defaultdict and list
    needles_unpacked_list = defaultdict(list)
    for needle_trajectories in needles_list:
        for keys, vals in needle_trajectories.items():
            for val in vals:
                needles_unpacked_list[keys].append(val)
    # conver to DataFrame for easier writing to Excel
    df_patients_trajectories = pd.DataFrame(needles_unpacked_list)
    print("success")
elif not patients:
    print('No CAS Recordings found. Check if the files are there and in the correct folder structure.')

#%%  write to excel final list.
if df_patients_trajectories is None:
    print('No Needle Trajectories found in the input file directory:')
else:
    timestr = strftime("%Y%m%d-%H%M%S")
    filename = outfilename + '_' +timestr + '.xlsx'
    filepathExcel = os.path.join(rootdir, filename)
    writer = pd.ExcelWriter(filepathExcel)
    if flag_segmentation_info:
        df_final = df_patients_trajectories
        df_final[["Ablation_Series_UID"]] = df_final[["Ablation_Series_UID"]].astype(str)
        df_final[["Tumor_Series_UID"]] = df_final[["Tumor_Series_UID"]].astype(str)
    else:
        # discard the segmentation information from the final output Excel when segmentation info (paths etc) is not desired
        df_final = df_patients_trajectories.iloc[:,0:19].copy() # use copy to avoid the case where changing df1 also changes df
    # df_final.sort_values(by=['PatientName'], inplace=True)
    df_final.apply(pd.to_numeric, errors='ignore', downcast='float').info()
    df_final[['LateralError']] = df_final[['LateralError']].apply(pd.to_numeric, downcast='float')
    df_final[['AngularError']] = df_final[['AngularError']].apply(pd.to_numeric, downcast='float')
    df_final[['EuclideanError']] = df_final[['EuclideanError']].apply(pd.to_numeric, downcast='float')
    df_final[['LongitudinalError']] = df_final[['LongitudinalError']].apply(pd.to_numeric, downcast='float')
    df_final[["PatientID"]] = df_final[["PatientID"]].astype(str)
    df_final[["TimeIntervention"]] = df_final[["TimeIntervention"]].astype(str)
    df_final.to_excel(writer, sheet_name='Paths', index=False, na_rep='NaN')
    writer.save()
    print("success")

# %% write to Excel the IRE  dataset. Compute Angles & Areas for IREs
if flag_IRE:
    dataframe_metrics.customize_dataframe(df_final, rootdir)
    print("Angles have been computed!")

# TODO: condition for MWA Angles

