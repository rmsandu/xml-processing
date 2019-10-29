# -*- coding: utf-8 -*-
"""
Created on Fri Jun  1 16:59:22 2018

@author: Raluca Sandu
"""

import pandas as pd
import untangle as ut

filename = "CAS-One_MWA_Database.xml"
''' try to open and parse the xml filename
    if error, return message
'''
# TO DO: add the patient ID from the folder name
try:
    xmlobj = ut.parse(filename)
except Exception:
    print('XML file structure is broken, cannot read XML')

dict_mwa_info = []
needles = xmlobj.Eagles.Database.MWA
for needle in needles: 
        # "Acculis MTA" has id=0
        try:
            geometry = needle.AblationParameters.Geometry
        except Exception:
            continue
        for geo in geometry:
            try:        
                ablation_params = geo.Shape
            except Exception:
                continue
            for idx, ablation_param in enumerate(ablation_params):
                mwa_info ={'NeedleID': needle["id"],
                            'AblationSystem': needle.AblationParameters["systemName"],
                            'AblationShapeIndex': idx,
                            'Type': ablation_param["type"],
                            'Power': ablation_param["power"],
                            'Time_seconds': ablation_param["time"],
                            'Radii': ablation_param["radii"],
                            'Translation': ablation_param["translation"],
                            'Rotation': ablation_param["rotation"]
                            }
                dict_mwa_info.append(mwa_info)
            
df_mwa = pd.DataFrame(dict_mwa_info)
df_mwa["NeedleName"] = "MWA"

#%% write to Excel
filename_excel = 'CAS_IR_MWA_NeedleDatabase' + '.xlsx'
writer = pd.ExcelWriter(filename_excel)
df_mwa.to_excel(writer, sheet_name='MWA', index=False, na_rep='NaN')

