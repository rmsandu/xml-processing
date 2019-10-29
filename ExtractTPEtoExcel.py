# -*- coding: utf-8 -*-
"""
Created on Wed Jun 20 15:45:28 2018
customize the dataframe before writing to Excel
for IRE Angles
@author: Raluca Sandu
"""
import os

import pandas as pd

pd.options.display.float_format = '{:.2f}'.format

def customize_dataframe(dfPatientsTrajectories, no_lesions_redcap, list_not_validated):
    """
    Clean the Dataframe. Keep only validated (TPEs present) trajectories. Correct the lesion and needle count.
    :param dfPatientsTrajectories:
    :param flag_IRE:
    :param flag_MWA:
    :param flag_segmentation_info:
    :return: Clean DataFrame
    """

    # dfPatientsTrajectories.apply(pd.to_numeric, errors='ignore', downcast='float').info()
    dfPatientsTrajectories.apply(pd.to_numeric, errors='ignore', downcast='float')
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
    # KEEP ONLY THE VALIDATED NEEDLES
    dfTPEs_validated = dfPatientsTrajectories.dropna(subset=['EuclideanError'], how='all')

    dfTPEs_validated['PlannedTargetPoint_str'] = dfTPEs_validated['PlannedTargetPoint'].astype(str)
    dfTPEs_validated.drop_duplicates(subset=['PlannedTargetPoint_str'], keep='last', inplace=True)

    if dfTPEs_validated.empty:
        print("None of the Needles were validated at this patient directory:", dfPatientsTrajectories.iloc[0].PatientID)
        list_not_validated.append(
            'None of the Needles were validated for this patient:' + dfPatientsTrajectories.iloc[0].PatientID)
        return
    df_needles_validated = dfTPEs_validated[dfTPEs_validated.NeedleType == 'MWA']
    # execute only if redcap file has been provided
    if no_lesions_redcap != -1:
        if len(df_needles_validated) > no_lesions_redcap:
            if 'G' not in df_needles_validated.iloc[0].PatientID:
                # keep the Groningen Patients because they were validated in 2019
                dfPatientsTrajectories[['CAS_Version']] = dfPatientsTrajectories[['CAS_Version']].apply(pd.to_numeric,
                                                                                                          downcast='float')
                df_needles_validated = df_needles_validated[df_needles_validated['CAS_Version'] != 3]
            else:
                print('merge codul asta:', df_needles_validated.iloc[0].PatientID)
            # df_needles_validated['TimeDateIntervention_Str'] = df_needles_validated['TimeIntervention'].map(
            #     lambda x: x.split(' ')[0])
            # df_needles_validated['TimeDateIntervention_Obj'] = df_needles_validated['TimeDateIntervention_Str'].map(
            #     lambda x: x.replace('_', ' '))
            # df_needles_validated['TimeDateIntervention'] = df_needles_validated['TimeDateIntervention_Obj'].map(
            #     lambda x: datetime.strptime(x, "%Y-%m-%d %H-%M-%S"))
            # most_recent_date = df_needles_validated['TimeDateIntervention'].max()
            # df_needles_validated = df_needles_validated[
            #     df_needles_validated['TimeDateIntervention'] == most_recent_date]
            print('More needles than defined found!!!')
            list_not_validated.append(
                str(no_lesions_redcap) + ' lesions found in RedCap. ' + str(len(df_needles_validated)) +
                ' needles found validated for this patient:' + dfPatientsTrajectories.iloc[0].PatientID)
        elif len(df_needles_validated) < no_lesions_redcap:
            print('Needles not validated!')
            print(str(no_lesions_redcap - len(df_needles_validated)),
                  ' needles were not validated for this patient:',
                  dfPatientsTrajectories.iloc[0].PatientID)
            list_not_validated.append(
                str(no_lesions_redcap) + ' lesions found in RedCap. ' + str(len(df_needles_validated)) +
                ' needles found validated for this patient:' + dfPatientsTrajectories.iloc[0].PatientID)
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


def write_toExcelFile(rootdir, outfile, df_needles_validated, dfPatientsTrajectories):
    """
    Write the processed information from DataFrame to Excel
    :param rootdir:
    :param df_TPEs_validated:
    :param dfPatientsTrajectories:
    :param df_angles:
    :param df_areas:
    :return: nothing, writes Excel File to Disk
    """
    ## write to Excel File
    filename = outfile + '.xlsx'
    filepathExcel = os.path.join(rootdir, filename)
    writer = pd.ExcelWriter(filepathExcel)
    try:
        df_needles_validated.to_excel(writer, sheet_name='TPEs_Validated', index=False, na_rep='NaN')
    except Exception:
        pass
        print('no needles found to be validated')
    dfPatientsTrajectories.to_excel(writer, sheet_name='Trajectories', index=False, na_rep='NaN')
    writer.save()
