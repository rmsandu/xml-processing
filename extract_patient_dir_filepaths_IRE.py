# -*- coding: utf-8 -*-
"""
@author: Raluca Sandu
"""

from utils.splitAllPaths import  splitall
import argparse
import os
import pandas as pd
# ap = argparse.ArgumentParser()
# ap.add_argument("-i", "--input_dir", required=True, help="input patient folder path to be processed")
# args = vars(ap.parse_args())
# input_dir = args["input_dir"]

input_dir = r"D:\Stockholm_IRE_2019\New_patients_2019"
dir_paths = [os.path.join(input_dir, x) for x in os.listdir(input_dir)]
print(dir_paths)
pats = []
for path_patient in dir_paths:
    all_paths = splitall(path_patient)
    pats.append(all_paths[3])

df = pd.DataFrame()
df['Patient_ID'] = pats
df['Patient_Dir_Paths'] = dir_paths

df.reset_index(drop=True)
writer = pd.ExcelWriter("Batch_processing_Stockholm_IRE_2019.xlsx")
df.to_excel(writer, index=False, float_format='%.4f')
writer.save()
