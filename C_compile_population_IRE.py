# -*- coding: utf-8 -*-
"""
@author: Raluca Sandu
"""

# -*- coding: utf-8 -*-
"""
@author: Raluca Sandu
"""
import os
import pandas as pd
import argparse
from ast import literal_eval

if __name__ == '__main__':

    ap = argparse.ArgumentParser()
    ap.add_argument("-b", "--input_batch_proc_paths", required=True, help="input csv file for batch processing")

    args = vars(ap.parse_args())

    if (args["input_batch_proc_paths"]) is not None:
        print("Path to CSV that has directory paths and subcapsular lesion info: ", args["input_batch_proc_paths"])

    df_download_db_all_info = pd.read_excel(args["input_batch_proc_paths"])
    frames_TPEs = []  # list to store all df per lesion.
    frames_trajectories = []
    frames_angles = []
    frames_areas = []

    df_download_db_all_info['Patient_Dir_Paths'].fillna("[]", inplace=True)
    # df_download_db_all_info['Patient_Dir_Paths'] = df_download_db_all_info['Patient_Dir_Paths'].apply(literal_eval)

    for row in df_download_db_all_info.itertuples(index=False):
        rootdir = row.Patient_Dir_Paths
        for subdir, dirs, files in os.walk(rootdir):
            for file in sorted(files):
                if file == 'tpes.xlsx':
                    # check file extension is xlsx
                    excel_input_file_per_lesion = os.path.join(subdir, file)
                    df_single_lesion = pd.read_excel(excel_input_file_per_lesion, sheet_name='TPEs_Validated')
                    try:
                        # other sheets: Trajectories, Angles, Areas
                        df_single_trajectories = pd.read_excel(excel_input_file_per_lesion, sheet_name='Trajectories')
                        df_angles = pd.read_excel(excel_input_file_per_lesion, sheet_name='Angles')
                        df_areas_IREs = pd.read_excel(excel_input_file_per_lesion, sheet_name='Areas')
                    except Exception:
                        pass
                    df_single_lesion.rename(columns={'LesionNr': 'Lesion_ID', 'PatientID': 'Patient_ID'}, inplace=True)
                    try:
                        patient_id = df_single_lesion.loc[0]['Patient_ID']
                    except Exception as e:
                        print(repr(e))
                        print("Path to bad excel file:", excel_input_file_per_lesion)
                        continue

                    frames_TPEs.append(df_single_lesion)
                    frames_trajectories.append(df_single_trajectories)
                    frames_areas.append(df_areas_IREs)
                    frames_angles.append(df_angles)


#%%
print('no of lesions found:', len(frames_TPEs))
TPEs_validated = pd.concat(frames_TPEs, ignore_index=False)
Trajectories = pd.concat(frames_trajectories, ignore_index=False)
Angles = pd.concat(frames_angles, ignore_index=False)
Areas = pd.concat(frames_areas, ignore_index=False)
print('No of Needles:', len(TPEs_validated))

# df_patient = result[result['Patient_ID'] == 'MAV-G10']
filepath_excel = "TPEs_IRE_2019.xlsx"
writer = pd.ExcelWriter(filepath_excel)
TPEs_validated.to_excel(writer, sheet_name='TPEs', index=False, float_format='%.4f')
Trajectories.to_excel(writer, sheet_name='Trajectories', index=False, float_format='%.4f')
Angles.to_excel(writer, sheet_name='Angles', index=False, float_format='%.4f')

writer.save()
# df_final = pd.merge(df_download_db_all_info, result, how="outer", on=['Patient_ID', 'Lesion_ID'])
# # write treatment id as well. the unique key must be formed out of: [patient_id, treatment_id, lesion_id]
# filepath_excel = "TPEs_MAVERRIC_ECIO.xlsx"
# writer = pd.ExcelWriter(filepath_excel)
# df_final.to_excel(writer, sheet_name='TPEs', index=False, float_format='%.4f')
# writer.save()
