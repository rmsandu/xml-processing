# -*- coding: utf-8 -*-
"""
Created on Wed Jun 20 15:45:28 2018
customize the dataframe before writing to Excel
for IRE Angles
@author: Raluca Sandu
"""
import os
from datetime import datetime

import pandas as pd
import matplotlib.pyplot as plt
import XMLProcessing.extractAreaNeedles as extractAreaNeedles
import XMLProcessing.D_extractIREAngles as D_extractIREAngles

pd.options.display.float_format = '{:.2f}'.format


def compute_area(df):
    """ Compute Area cm^2 for xyz coordinates.
    :param df: Dataframe with Needle Trajectories Coordinates (Target Points - xyz)
    :return: Dataframe with Area [cm^2] between IRE needles
    """
    Area_between_needles = []
    patient_unique = df['PatientID'].unique()
    for PatientIdx, patient in enumerate(patient_unique):
        patient_data = df[df['PatientID'] == patient]
        extractAreaNeedles.compute_areas_needles(patient_data, patient, Area_between_needles)
    df_area_between_needles = pd.DataFrame(Area_between_needles)

    return df_area_between_needles


def compute_angles(df):
    """ Compute Angles Degrees for Needles

    :param df: Dataframe with Needle Trajectories Coordinates (Target Points - EntryPoints vectors in 3D)
    :return: df: Dataframe of Angles (degrees) computed for each needle pair (including reference needle)
    """
    Angles = []
    patient_unique = df['PatientID'].unique()
    for PatientIdx, patient in enumerate(patient_unique):
        patient_data = df[df['PatientID'] == patient]
        D_extractIREAngles.ComputeAnglesTrajectories.FromTrajectoriesToNeedles(patient_data, patient, Angles)
    df_angles = pd.DataFrame(Angles)

    # convert to dataframe & make columns numerical so Excel operations are allowed
    df_angles['A_dash'] = '-'
    df_angles['Electrode Pair'] = df_angles['NeedleA'].astype(str) + df_angles['A_dash'] + df_angles['NeedleB'].astype(
        str)
    df_angles = df_angles[['PatientID', 'LesionNr', 'Electrode Pair', 'Planned Angle', 'Validation Angle']]
    df_angles.sort_values(by=['PatientID', 'LesionNr'], inplace=True)
    df_angles.apply(pd.to_numeric, errors='ignore', downcast='float').info()
    # dfAngles_no_nans = dfAngles.dropna(subset=['Validation Angle'], inplace=True)

    return df_angles


def plot_boxplot_angles(df_angles, rootdir):
    """
    :param dfAngles: DataFrame Angles (plan & validation)
    :return: - saves boxplot in png format
    """

    fig, axes = plt.subplots(figsize=(18, 20))
    df_angles.boxplot(column=['Planned Angle', 'Validation Angle'], patch_artist=False, fontsize=20)
    plt.ylabel('Angle [$^\circ$]', fontsize=20)
    # plt.show()
    savepath_png = os.path.join(rootdir, 'IRE_Angles.png')
    savepath_svg = os.path.join(rootdir, 'IRE_Angles.svg')
    plt.savefig(savepath_png, pad_inches=0)
    plt.savefig(savepath_svg, pad_inches=0)


def customize_dataframe(dfPatientsTrajectories, flag_IRE, flag_MWA, no_lesions_redcap):
    """
    Clean the Dataframe. Keep only validated (TPEs present) trajectories. Correct the lesion and needle count.
    :param dfPatientsTrajectories:
    :param flag_IRE:
    :param flag_MWA:
    :param flag_segmentation_info:
    :return: Clean DataFrame
    """

    dfPatientsTrajectories.apply(pd.to_numeric, errors='ignore', downcast='float').info()
    dfPatientsTrajectories[['LateralError']] = dfPatientsTrajectories[['LateralError']].apply(pd.to_numeric,
                                                                                              downcast='float')
    dfPatientsTrajectories.LateralError = dfPatientsTrajectories.LateralError.round(decimals=2)
    dfPatientsTrajectories[['EntryLateral']] = dfPatientsTrajectories[['EntryLateral']].apply(pd.to_numeric,
                                                                                              downcast='float')
    dfPatientsTrajectories.EntryLateral = dfPatientsTrajectories.EntryLateral.round(decimals=2)
    dfPatientsTrajectories[['AngularError']] = dfPatientsTrajectories[['AngularError']].apply(pd.to_numeric,
                                                                                              downcast='float')
    dfPatientsTrajectories.AngularError = dfPatientsTrajectories.AngularError.round(decimals=2)
    dfPatientsTrajectories[['EuclideanError']] = dfPatientsTrajectories[['EuclideanError']].apply(pd.to_numeric,
                                                                                                  downcast='float')
    dfPatientsTrajectories.EuclideanError = dfPatientsTrajectories.EuclideanError.round(decimals=2)
    dfPatientsTrajectories[['LongitudinalError']] = dfPatientsTrajectories[['LongitudinalError']].apply(pd.to_numeric,
                                                                                                        downcast='float')
    dfPatientsTrajectories.LongitudinalError = dfPatientsTrajectories.LongitudinalError.round(decimals=2)

    dfPatientsTrajectories.sort_values(by=['PatientID', 'LesionNr', 'NeedleNr'], inplace=True)

    dfTPEs_validated = dfPatientsTrajectories.dropna(subset=['EuclideanError'], how='all')
    # dfTPEs_validated['PlannedTargetPoint_str'] = dfTPEs_validated['PlannedTargetPoint'].astype(str)
    # dfTPEs_validated.drop_duplicates(subset=['PlannedTargetPoint_str'], inplace=True)
    # dfTPEs_validated.iloc[0].PlannedTargetPoint  ==  dfTPEs_validated.iloc[1].PlannedTargetPoint
    if dfTPEs_validated.empty:
        print("None of the Needles were validated at this patient directory:", dfPatientsTrajectories.iloc[0].PatientID)
        return

    if flag_IRE is True and flag_MWA is False:
        # TODO: fix later
        # select only IRE Needles, drop the MWAs
        df_needles_validated = dfTPEs_validated[dfTPEs_validated.NeedleType == 'IRE']
        dfTPEs_validated = dfPatientsTrajectories[dfPatientsTrajectories['EuclideanError'].notnull() | (
            dfPatientsTrajectories['ReferenceNeedle'])]
        # select rows where the needle is not a reference, but part of child trajectories. drop the other rows
        # df_TPEs_validated = dfIREs[~(dfIREs.ReferenceNeedle)]
        # df_TPEs_validated = dfIREs

    elif flag_MWA is True and flag_IRE is False:
        df_needles_validated = dfTPEs_validated[dfTPEs_validated.NeedleType == 'MWA']
        # execute only if redcap file has been provided
        if no_lesions_redcap != -1 :
            if len(df_needles_validated) > no_lesions_redcap:
                df_needles_validated['TimeDateIntervention_Str'] = df_needles_validated['TimeIntervention'].map(
                    lambda x: x.split(' ')[0])
                df_needles_validated['TimeDateIntervention_Obj'] = df_needles_validated['TimeDateIntervention_Str'].map(
                    lambda x: x.replace('_', ' '))
                df_needles_validated['TimeDateIntervention'] = df_needles_validated['TimeDateIntervention_Obj'].map(
                    lambda x: datetime.strptime(x, "%Y-%m-%d %H-%M-%S"))
                most_recent_date = df_needles_validated['TimeDateIntervention'].max()
                df_needles_validated = df_needles_validated[df_needles_validated['TimeDateIntervention'] == most_recent_date]

            elif len(df_needles_validated) < no_lesions_redcap:
                print(str(no_lesions_redcap - len(df_needles_validated)), ' needles were not validated for this patient:',
                      dfPatientsTrajectories.iloc[0].PatientID)

    # %% Correct the lesion and needle index
    patient_unique = df_needles_validated['PatientID'].unique()
    for PatientIdx, patient in enumerate(patient_unique):
        patient_data = df_needles_validated[df_needles_validated['PatientID'] == patient]
        lesion_unique = patient_data['LesionNr'].unique()
        list_lesion_count_new = []
        NeedleCount = patient_data['NeedleNr'].tolist()
        new_idx_lesion = 1
        # update needle nr count for older CAS versions where no reference needle was available
        for l_idx, lesion in enumerate(lesion_unique):
            lesion_data = patient_data[patient_data['LesionNr'] == lesion]
            if lesion_data['ReferenceNeedle'].iloc[0] == True:
                k = 0
            else:
                k = 1
            needles_new = lesion_data['NeedleNr'] + k
            # if df_IRE_only still has needles starting with 0 add 1 to all the columns
            if lesion_data.NeedleNr.iloc[0] == 0:
                df_needles_validated.loc[
                    (df_needles_validated['PatientID'] == patient) & (df_needles_validated['LesionNr'] == lesion),
                    ['NeedleNr']] = needles_new

        # update lesion count (per patient) after keeping only the IRE needles
        for needle_idx, needle in enumerate(NeedleCount):
            if needle_idx == 0:
                list_lesion_count_new.append(new_idx_lesion)
            else:
                if NeedleCount[needle_idx] <= NeedleCount[needle_idx - 1]:
                    new_idx_lesion += 1
                    list_lesion_count_new.append(new_idx_lesion)
                else:
                    list_lesion_count_new.append(new_idx_lesion)
        # replace the re-calculated lesion count in the final dataframe
        df_needles_validated.loc[
            (df_needles_validated['PatientID'] == patient), ['LesionNr']] = list_lesion_count_new
        # replace the new lesion count and remove NaNs in the trajectories as well
        return df_needles_validated


def write_toExcelFile(rootdir, outfile, df_needles_validated, dfPatientsTrajectories, df_angles=None, df_areas=None):
    """
    Write the processed information from DataFrame to Excel
    :param rootdir:
    :param df_TPEs_validated:
    :param dfPatientsTrajectories:
    :param df_angles:
    :param df_areas:
    :return: nothing, writes Excel File to Disk
    """
    # %% Group statistics
    try:
        df_TPEs_validated = df_needles_validated[~df_needles_validated.ReferenceNeedle]
    except AttributeError:
        df_TPEs_validated = df_needles_validated
    grpd_needles = df_TPEs_validated.groupby(['PatientID', 'NeedleNr']).size().to_frame('Needle Count')
    df_count = df_TPEs_validated.groupby(['PatientID', 'LesionNr']).size().to_frame('NeedleCount')
    # question: how many needles (pairs) were used per lesion?
    dfNeedles = df_TPEs_validated.groupby(['PatientID', 'LesionNr']).NeedleNr.size().to_frame('TotalNeedles')
    dfNeedlesIndex = dfNeedles.add_suffix('_Count').reset_index()

    # question: what is the frequency of the needle configuration (3 paired, 4 paired) ?
    dfLesionsNeedlePairs = dfNeedlesIndex.groupby(['TotalNeedles_Count']).LesionNr.count()
    dfLesionsIndex = dfLesionsNeedlePairs.add_suffix('-Paired').reset_index()

    # how many patients & how many lesions ?
    dfLesionsTotal = df_TPEs_validated.groupby(['PatientID']).LesionNr.max().to_frame('Total Lesions')
    dfLesionsTotalIndex = dfLesionsTotal.add_suffix(' Count').reset_index()
    ## write to Excel File
    filename = outfile + '.xlsx'
    filepathExcel = os.path.join(rootdir, filename)
    writer = pd.ExcelWriter(filepathExcel)
    df_TPEs_validated.to_excel(writer, sheet_name='TPEs_Validated', index=False, na_rep='NaN')
    dfPatientsTrajectories.to_excel(writer, sheet_name='Trajectories', index=False, na_rep='NaN')

    df_TPEs = df_TPEs_validated[['PatientID', 'PatientName', 'LesionNr', 'NeedleNr', 'NeedleType',
                                 'TimeIntervention', 'ReferenceNeedle', 'EntryLateral',
                                 'LongitudinalError', 'LateralError', 'EuclideanError', 'AngularError']]
    df_TPEs.to_excel(writer, sheet_name='TPEs_Only', index=False, na_rep='NaN')
    dfLesionsTotalIndex.to_excel(writer, sheet_name='LesionsTotal', index=False, na_rep='Nan')
    dfNeedlesIndex.to_excel(writer, sheet_name='NeedlesLesion', index=False, na_rep='Nan')
    dfLesionsIndex.to_excel(writer, sheet_name='NeedleFreq', index=False, na_rep='Nan')
    if df_angles is not None:
        df_angles.to_excel(writer, sheet_name='Angles', index=False, na_rep='NaN')
    if df_areas is not None:
        df_areas.to_excel(writer, sheet_name='Areas', index=False, na_rep='NaN')

    writer.save()
