





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
import C_NeedlesInfoClasses
import B_parseNeedleTrajectories as parseNeedleTrajectories
import dataframe_metrics

# %%

def call_needle_extraction(rootdir):

    for subdir, dirs, files in os.walk(rootdir):

        for file in sorted(files): # sort files by date of creation

            fileName, fileExtension = os.path.splitext(file)

            # the tumour segmentation path is in the "Plan.xml" and the ablation segmentation path is in the "Validation.xml"
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


def call_extract_class_2_df(patients):
    """
    extract information from the object classes into pandas dataframe
    :param patients:
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
    # conver to DataFrame for easier writing to Excel
    df_patients_trajectories = pd.DataFrame(needles_unpacked_list)
    return df_patients_trajectories
    print("Success unpacking from class to dataframe....")


def  write_df_2Excel(df_patients_trajectories, flag_segmentation_info, outfilename):
    """
    write to excel final list.
    :param df_patients_trajectories:
    :return:  simplified dataframe and Excel file to disk
    """
    timestr = strftime("%Y%m%d-%H%M%S")
    filename = outfilename + '_' +timestr + '.xlsx'
    filepathExcel = os.path.join(rootdir, filename)
    writer = pd.ExcelWriter(filepathExcel)

    if flag_segmentation_info is True:
        df_final = df_patients_trajectories
    else:
        # discard the segmentation information from the final output Excel when not needed
        df_final = df_patients_trajectories.iloc[:,0:19].copy() # use copy to avoid the case where changing df1 also changes df
    # df_final.sort_values(by=['PatientName'], inplace=True)
    # some numerical conversions
    df_final.apply(pd.to_numeric, errors='ignore', downcast='float').info()
    df_final[['LateralError']] = df_final[['LateralError']].apply(pd.to_numeric, downcast='float')
    df_final[['AngularError']] = df_final[['AngularError']].apply(pd.to_numeric, downcast='float')
    df_final[['EuclideanError']] = df_final[['EuclideanError']].apply(pd.to_numeric, downcast='float')
    df_final[['LongitudinalError']] = df_final[['LongitudinalError']].apply(pd.to_numeric, downcast='float')
    df_final[["PatientID"]] = df_final[["PatientID"]].astype(str)
    df_final[["TimeIntervention"]] = df_final[["TimeIntervention"]].astype(str)
    df_final.to_excel(writer, sheet_name='Paths', index=False, na_rep='NaN')
    writer.save()
    print("Succes writing info to Excel file....")
    return df_final


#%%
if __name__ == '__main__':

    # rootdir = "C:\test_patient"
    # outfilename =  "info_logs"
    # flag_IRE = False
    # flag_MWA = True
    # flag_segmentation_info =  True

    rootdir = os.path.normpath(readInputKeyboard.getNonEmptyString("Root Directory File Path"))
    outfilename = readInputKeyboard.getNonEmptyString("Name of the ouput xlsx file ")
    # todo: better questions
    flag_IRE = readInputKeyboard.getChoiceYesNo('Do you want to analyze the IRE needles ?', ['Y', 'N'])
    flag_MWA = readInputKeyboard.getChoiceYesNo('Do you want to analyze the MWA Needles ?', ['Y', 'N'])
    flag_segmentation_info = readInputKeyboard.getChoiceYesNo('Do you want to have the segmentation information ?', ['Y', 'N'])

    # instanstiate the patient repository class
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
        print('No CAS Folder Recordings found. Check if the files are there and in the correct folder structure.')

    try:
        df_TPEs_validated = dataframe_metrics.customize_dataframe(df_patients_trajectories, flag_IRE, flag_MWA, flag_segmentation_info)
        print("Dataframe cleaning successful. Lesion and Needle Nr updated...")
    except Exception as e:
        print(repr(e))
        print('No Needle Trajectories found in the input file directory!')

    if flag_IRE is True:
        #%% compute area between IRE Needles
        # TODO: calculate angles
        df_area_between_needles = dataframe_metrics.compute_area(df_TPEs_validated)
        df_areas = df_area_between_needles[['PatientID', 'LesionNr','NeedleCount', 'Planned Area', 'Validation Area']]
        #%% compute angles between IRE Needles
        df_angles = dataframe_metrics.compute_angles(df_TPEs_validated)
        dataframe_metrics.plot_boxplot_angles(df_angles, rootdir)
        # write to Excel File...
        dataframe_metrics.write_toExcelFile(rootdir=rootdir, outfile=outfilename, df_TPEs_validated=df_TPEs_validated,
                                            dfPatientsTrajectories=df_patients_trajectories, df_angles=df_angles, df_areas=df_areas)

    else:
        # write to Excel file all the information extracted without the df_angles and df_areas
        dataframe_metrics.write_toExcelFile(rootdir, outfilename, df_TPEs_validated, df_patients_trajectories)
        print('Succes! Extracting and Writing Information to the Excel File.....')

