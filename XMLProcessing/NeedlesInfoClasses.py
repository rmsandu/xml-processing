# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 10:20:31 2018

@author: Raluca Sandu
"""
import numpy as np
from collections import defaultdict


class PatientRepo:

    def __init__(self):
        self.patients = []

    def addNewPatient(self, patient_id_xml, patient_name):
        patient = Patient(patient_id_xml, patient_name)
        self.patients.append(patient)
        return patient

    def getPatients(self):
        return self.patients


class Patient:

    def __init__(self, patient_id_xml, patient_name):
        self.lesions = []
        self.registrations = []
        self.patient_id_xml = patient_id_xml
        self.patient_name = patient_name

    def addNewRegistration(self):
        registration = Registration()
        self.registrations.append(registration)
        return registration

    def findRegistration(self, REGISTRATION_MATRIX):
        foundRegistrations = [rg.r_matrix for rg in self.registrations if np.array_equal(np.array(rg.r_matrix), np.array(REGISTRATION_MATRIX))]
        if len(foundRegistrations) == 0:
            return None
        elif len(foundRegistrations) > 0:
            return foundRegistrations[0]
        else:
            raise Exception('Something went wrong')

    def addLesion(self, lesion):
        self.lesions.append(lesion)

    def addNewLesion(self, location, time_intervention):
        lesion = Lesion(location, time_intervention)
        self.addLesion(lesion)
        return lesion

    def getLesions(self):
        return self.lesions

    def findLesion(self, lesionlocation, DISTANCE_BETWEEN_LESIONS):
        foundLesions = list(filter(lambda l:
                                   l.distanceTo(lesionlocation) < DISTANCE_BETWEEN_LESIONS, self.lesions))
        if len(foundLesions) == 0:
            return None
        elif len(foundLesions) > 0:
            return foundLesions[0]
        else:
            raise Exception('Something went wrong')


class Registration:

    def __init__(self):
        self.r_matrix = None
        self.r_type = None
        self.pp_planning = None
        self.pp_validation = None
        self.r_flag = False

    def setRegistrationInfo(self,  r_matrix, r_type, pp_planning, pp_validation):
        self.r_matrix = r_matrix
        self.r_type = r_type
        self.pp_planning = pp_planning
        self.pp_validation = pp_validation
        self.r_flag = True


class Lesion:
    # location is a numpy array
    def __init__(self, location, intervention_date):
        self.needles = []
        self.intervention_date = intervention_date
        if location is not None and len(location) is 3:
            self.location = location
        else:
            raise Exception('Lesion Location not given')

    def distanceTo(self, lesionlocation):
        # compute euclidean distances for TPE to check whether the same lesion
        tp1 = lesionlocation
        tp2 = self.location
        dist = np.linalg.norm(tp1 - tp2)
        return dist
        pass

    def getNeedles(self):
        return self.needles

    def newNeedle(self, isreference, needle_type, ct_series):
        # here self represents the lesion
        needle = Needle(self, isreference, needle_type, ct_series)
        self.needles.append(needle)
        return needle

    def findNeedle(self, needlelocation, DISTANCE_BETWEEN_NEEDLES):
        """ Find and return the needles. Based on euclidean distance.
            Might not work because there is no clear and constant agreement
            to tell if it's a new needle or the same one which was moved with 50mm.
        """
        foundNeedles = list(filter(lambda l:
                                   l.distanceToNeedle(needlelocation) < DISTANCE_BETWEEN_NEEDLES, self.needles))
        if len(foundNeedles) == 0:
            return None
        elif len(foundNeedles) > 0:
            return foundNeedles[0]
        else:
            raise Exception('Something went wrong')


class Segmentation:

    def __init__(self, needle, source_path, path, needle_type, ct_series, series_UID, sphere_radius, segmentation_type, segmentation_datetime):
        self.source_path = source_path
        self.mask_path = path
        self.needle_type = needle_type
        self.ct_series = ct_series
        self.series_UID = series_UID
        self.sphere_radius = sphere_radius
        self.needle = needle
        self.segmentation_type = segmentation_type  # ablation, tumor, vessel (etc)
        self.segmentation_datetime = segmentation_datetime
        self.needle_specifications = None
        self.ellipsoid_info = None # TODO: is this instantiated?

    def setNeedleSpecifications(self):
        self.needle_specifications = NeedleSpecifications()
        return self.needle_specifications


class NeedleSpecifications:

    def __init__(self):
        self.ablator_id = None
        self.ablationSystem = None
        self.ablationSystemVersion = None
        self.ablatorType = None
        self.ablationShapeIndex = None  # id field which connects with the MWA Needle Database

    def setNeedleSpecifications(self, ablator_id, ablationSystem,
                                ablationSystemVersion, ablatorType,
                                ablationShapeIndex):
        self.ablator_id = ablator_id
        self.ablationSystem = ablationSystem
        self.ablationSystemVersion = ablationSystemVersion
        self.ablatorType = ablatorType
        self.ablationShapeIndex = ablationShapeIndex  # id field which connects with the MWA Needle Database


class Needle:

    def __init__(self, lesion, isreference, needle_type, ct_series):
        self.segmentations_tumor = []
        self.segmentations_ablation = []
        self.isreference = isreference
        self.planned = None
        self.validation = None
        self.tpeerorrs = None
        self.time_intervention = None
        self.cas_version = None
        self.lesion = lesion
        self.needle_type = needle_type
        self.ct_series = ct_series

    def distanceToNeedle(self, needlelocation):
        # compute euclidean distances for TPE to check whether the same lesion
        tp1 = needlelocation
        tp2 = self.planned.targetpoint
        dist = np.linalg.norm(tp1 - tp2)
        return dist
        pass

    def setCASversion(self, cas_version):
        self.cas_version = cas_version

    def setTimeIntervention(self, time_intervention):
        self.time_intervention = time_intervention

    def setPlannedTrajectory(self):
        self.planned = Trajectory()
        return self.planned

    def setValidationTrajectory(self):
        self.validation = Trajectory()
        return self.validation

    def setTPEs(self):
        self.tpeerorrs = TPEErrors()
        return self.tpeerorrs

    def getTPEs(self):
        return self.tpeerorrs

    def getPlannedTrajectory(self):
        return self.planned

    def getValidationTrajectory(self):
        return self.validation

    def getIsNeedleReference(self):
        return self.isreference

    def to_dict_unpack(self, patientID, patient_name, lesionIdx, needle_idx, dict_needles):
        """ Unpack Needle Object class to dict.
            Return needle information.
            If one needle has several segmentations, iterate and return all.
            If no segmentation, return empty fields for the segmentation.
            self = needle here
        """
        dict_needles['PatientID'].append(patientID)
        dict_needles['PatientName'].append(patient_name)
        dict_needles['LesionNr'].append(lesionIdx)
        dict_needles['NeedleNr'].append(needle_idx)
        dict_needles['NeedleType'].append(self.needle_type)
        dict_needles['CAS_Version'].append(self.cas_version)
        dict_needles['CT_series_Plan'].append(self.ct_series)
        dict_needles['TimeIntervention'].append(self.time_intervention)
        dict_needles['PlannedEntryPoint'].append(self.planned.entrypoint)
        dict_needles['PlannedTargetPoint'].append(self.planned.targetpoint)
        dict_needles['PlannedNeedleLength'].append(self.planned.length_needle)
        dict_needles['ValidationEntryPoint'].append(self.validation.entrypoint)
        dict_needles['ValidationTargetPoint'].append(self.validation.targetpoint)
        dict_needles['ReferenceNeedle'].append(self.isreference)
        dict_needles['EntryLateral'].append(self.tpeerorrs.entry_lateral)
        dict_needles['AngularError'].append(self.tpeerorrs.angular)
        dict_needles['LateralError'].append(self.tpeerorrs.lateral)
        dict_needles['LongitudinalError'].append(self.tpeerorrs.longitudinal)
        dict_needles['EuclideanError'].append(self.tpeerorrs.euclidean)

        return dict_needles


class NeedleToDictWriter:
    """ Extracts the needle information into dictionary format.
    Attributes:
        needle_data: an empty list to append to.
        patientID : str specifying patient id
        lesionIDX: int specifying the needle count
        needles: needles class object
    """

    def needlesToDict(patientID, patient_name, lesion_count, needles):
        if len(needles)>0:
            # for each patient the dict_needles defaultdict is reset
            dict_needles = defaultdict(list)

            for needle_idx, needle in enumerate(needles):
                needle.to_dict_unpack(patientID, patient_name, lesion_count, needle_idx, dict_needles)

            return dict_needles
        else:
            #print('No needles for this lesion')
            pass


class TPEErrors:

    def __init__(self):
        self.entry_lateral = None
        self.angular = None
        self.longitudinal = None
        self.lateral = None
        self.euclidean = None

    def setTPEErrors(self, entry_lateral, lateral, angular, longitudinal, euclidean):
        self.entry_lateral = entry_lateral
        self.angular = angular
        self.longitudinal = longitudinal
        self.lateral = lateral
        self.euclidean = euclidean

    def calculateTPEErrors(self, plannedTrajectory, validationTrajectory, offset):
        # TO DO: in case of offset that wasn't accounted for in the old versions of cascination
        pass


class Trajectory:

    def __init__(self):
        self.entrypoint = None
        self.targetpoint = None
        self.length_needle = None

    def setTrajectory(self, entrypoint, targetpoint):
        self.entrypoint = entrypoint
        self.targetpoint = targetpoint

    def setLengthNeedle(self):
        if self.targetpoint is not None and self.entrypoint is not None:
            self.length_needle = np.linalg.norm(self.targetpoint - self.entrypoint)
        else:
            self.length_needle = None
