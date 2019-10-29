# -*- coding: utf-8 -*-
"""
Created on Thu Mar  1 11:28:21 2018

@author: Raluca Sandu
"""
import numpy as np
import AngleNeedles as AngleNeedles
from itertools import combinations


class ComputeAnglesTrajectories:

    def FromTrajectoriesToNeedles(df_patient_data, patientID, Angles):

        # keep just the IRE Needles
        df_IREs = df_patient_data[df_patient_data.NeedleType == 'IRE']

        # get unique values from the lesion index count
        lesion_unique = list(set(df_IREs['LesionNr']))

        for i, lesion in enumerate(lesion_unique):

            lesion_data = df_IREs[df_IREs['LesionNr'] == lesion]
            needles_lesion_1 = lesion_data['NeedleNr']
            needles_lesion = needles_lesion_1.tolist()
            PlannedEntryPoint = lesion_data['PlannedEntryPoint'].tolist()
            PlannedTargetPoint = lesion_data['PlannedTargetPoint'].tolist()
            ValidationEntryPoint = lesion_data['ValidationEntryPoint'].tolist()
            ValidationTargetPoint = lesion_data['ValidationTargetPoint'].tolist()
            ReferenceNeedle = lesion_data['ReferenceNeedle'].tolist()

            ref_needle = False
            for idx, val in enumerate(ReferenceNeedle):
                if val is True:
                    ref_needle = True
            # if true reference needle --> k=0
            # if all false reference needle --> k=1
            # %%
            if ref_needle is False:
                k = 1
            else:
                # if there is no reference needle for this trajectories, then start needle naming at 1
                k = 0

            for combination_angles in combinations(needles_lesion, 2):

                if ReferenceNeedle[combination_angles[0]-k] is False and ReferenceNeedle[combination_angles[1]-k] is False:
                    # no reference needle available, older version of XML CAS Logs
                    needleA = needles_lesion[combination_angles[0]-k]
                    needleB = needles_lesion[combination_angles[1]-k]

                    if PlannedTargetPoint[combination_angles[0]].all() and PlannedTargetPoint[
                            combination_angles[0]].all():
                        angle_planned = AngleNeedles.angle_between(PlannedEntryPoint[combination_angles[0]-k],
                                                                   PlannedTargetPoint[combination_angles[0]-k],
                                                                   PlannedEntryPoint[combination_angles[1]-k],
                                                                   PlannedTargetPoint[combination_angles[1]-k])
                    else:
                        angle_planned = np.nan

                    if ValidationTargetPoint[combination_angles[0]-k] is not None \
                            and ValidationTargetPoint[combination_angles[1]-k] is not None:
                        # if values exist for the validation then compute the validation angle
                        angle_validation = AngleNeedles.angle_between(ValidationEntryPoint[combination_angles[0]-k],
                                                                      ValidationTargetPoint[combination_angles[0]-k],
                                                                      ValidationEntryPoint[combination_angles[1]-k],
                                                                      ValidationTargetPoint[combination_angles[1]-k])
                    else:
                        # this angle pair hasn't been validated so assign NaN to the angle validation
                        angle_validation = np.nan

                elif ReferenceNeedle[combination_angles[0]-k] is True:
                    # ReferenceNeedle is never validated, only plan trajectories are available
                    needleA = 'Reference'
                    needleB = needles_lesion[combination_angles[1]-k]

                    if (PlannedTargetPoint[combination_angles[0]-k]) is not None \
                            and (PlannedTargetPoint[combination_angles[0]-k]) is not None:

                        angle_planned = AngleNeedles.angle_between(PlannedEntryPoint[combination_angles[0]-k],
                                                                   PlannedTargetPoint[combination_angles[0]-k],
                                                                   PlannedEntryPoint[combination_angles[1]-k],
                                                                   PlannedTargetPoint[combination_angles[1]-k])

                    else:
                        angle_planned = np.nan

                    if ValidationTargetPoint[combination_angles[1]-k] is not None:
                        # if values exist for the validation then compute the validation angle
                        angle_validation = AngleNeedles.angle_between(PlannedEntryPoint[combination_angles[0]-k],
                                                                      PlannedTargetPoint[combination_angles[0]-k],
                                                                      ValidationEntryPoint[combination_angles[1]-k],
                                                                      ValidationTargetPoint[combination_angles[1]-k])
                    else:
                        angle_validation = np.nan

                needles_angles = {'PatientID': patientID,
                                  'LesionNr': lesion,
                                  'NeedleA': needleA,
                                  'NeedleB': needleB,
                                  'Planned Angle': float("{0:.2f}".format(angle_planned)),
                                  'Validation Angle': float("{0:.2f}".format(angle_validation)),
                                  'Distance Planned': float("{0:.2f}".format(np.nan)),
                                  'Distance Validation': float("{0:.2f}".format(np.nan))
                                  }

                Angles.append(needles_angles)

        return Angles
