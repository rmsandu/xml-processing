# -*- coding: utf-8 -*-
"""
Created on Mon Feb  5 15:04:29 2018

@author: Raluca Sandu
"""
import collections
import re
import xml.etree.ElementTree as ET
from collections import defaultdict

import numpy as np
import untangle as ut

from ElementExistsXml import elementExists
from ExtractTPEsXml import extractTPES
from utils.splitAllPaths import splitall


#%%

def extract_patient_id(filename, patient_id_xml, patient_name_flag=True):
    """ Extract patient id & patient name from folder name.
    Assumes root folder name is of the type: Pat_John Smith_0013768450_2017-08-04_08-19-25
    The patient_id will be in this  case = 0013768450
    The patient_id is assumed to be an unique instance
    If no patient id in the folder, then extract patient id from "PatientInformation__yy-mm-dd.xml"
    Note: Only for log files missing patient_id in the attributes
    :param filename: a norm path of the xml log file.
    :param patient_id_xml: string representing numerical id or None
    :param patient_name_flag: bool whether patient name should be written or not.
    :return: patient_id_xml (numerical patient id)
    """
    all_paths = splitall(filename)
    ix_patient_folder_name = [i for i, s in enumerate(all_paths) if "Pat_" in s]
    try:
        patient_folder_name = all_paths[ix_patient_folder_name[0]]
        patient_id = re.search("\d", patient_folder_name)  # numerical id
        ix_patient_id = int(patient_id.start())
        underscore = re.search("_", patient_folder_name[ix_patient_id:])
        if underscore is None:
            ix_underscore = len(patient_folder_name) - 1
        else:
            ix_underscore = int(underscore.start())
        # if no patient id hasn't been found in any of the xmls, replace it
        if patient_id_xml is None:
            patient_id_xml = patient_folder_name[ix_patient_id:ix_underscore + ix_patient_id]
        if patient_name_flag:
            patient_name = patient_folder_name[0:ix_patient_id]
        else:
            patient_name = None
    except Exception as e:
        pass
        patient_name = 'Undefined patient'
        patient_id_xml = 'Undefined patient'
       # print(repr(e))
        # error appears generally because an "UndefinedPatient" folder is created everytime when CAS-One IR is opened.
    return patient_id_xml, patient_name


def I_parseRecordingXML(filename):

    patient_id_xml = None
    patient_name = None
    xml_tree = collections.namedtuple('xml_tree',
                                      ['trajectories', 'patient_id_xml', 'patient_name'])
    try:
        # try to read the xml file
        xmlobj = ut.parse(filename)
    except Exception:
        try:
            # attempt to remove weird characters in the name of the patient by rewriting the xml files
            # TODO: try to to keep 'UTF-8' coding guidelines
            xmlobj = ET.parse(filename, parser=ET.XMLParser(encoding='ISO-8859-1'))
            root = xmlobj.getroot()
            root[0].attrib.pop('seriesPath', None)
            xmlobj.write(filename)
            return 1
        except Exception:
            #print("This file could not be parsed with either library ElementTree or Untangle:", filename)
            return None

    try:
        patient_id_xml = xmlobj.Eagles.PatientData["patientID"]
    except Exception as e:
        pass
        print(repr(e))
    patient_id_xml, patient_name = extract_patient_id(filename, patient_id_xml, patient_name_flag=True)
    result = xml_tree(xmlobj, patient_id_xml, patient_name)
    return result


def IV_parseNeedles(children_trajectories, lesion, needle_type, ct_series, xml_filepath, time_intervention,
                    cas_version):
    """ Parse Individual Needle Trajectories per Lesion.
    Extract planning coordinates and  validation needle coordinate.
    Extract the TPE Errors from the validation coordinates.
    To find the needles assume the distance between the same needle could be up to 35[mm].DISTANCE_BETWEEN_NEEDLES=35
    INPUT:
    1. xml tree structure for child trajectories
    2. lesion class object
    3. needle_type (string) MWA or IRE
    OUTPUT: doesn't return anything, just sets the TPEs
    """

    for singleTrajectory in children_trajectories:

        ep_planning = np.array([float(i) for i in singleTrajectory.EntryPoint.cdata.split()])
        tp_planning = np.array([float(i) for i in singleTrajectory.TargetPoint.cdata.split()])
        # find if the needle exists already in the patient repository
        # for IRE needles the distance shouldn't be larger than 3 (in theory)
        if needle_type is "IRE":
            needle = lesion.findNeedle(needlelocation=tp_planning, DISTANCE_BETWEEN_NEEDLES=0.1)  # distance is in mm
        elif needle_type is "MWA":
            needle = lesion.findNeedle(needlelocation=tp_planning, DISTANCE_BETWEEN_NEEDLES=2)  # distance is in mm
        # case for new needle not currently saved in database
        if needle is None:
            # add the needle to lesion class and init its parameters
            needle = lesion.newNeedle(False, needle_type, ct_series)  # False - the needle is not a reference trajectory
            tps = needle.setTPEs()
            validation = needle.setValidationTrajectory()
        # add the entry and target points to the needle object regardless needle is None or not
        planned = needle.setPlannedTrajectory()
        planned.setTrajectory(ep_planning, tp_planning)
        planned.setLengthNeedle()
        try:
            LengthToTarget = singleTrajectory.LengthToTarget.cdata[0:5]
        except Exception:
            LengthToTarget = None
        planned.setLengthToTarget(LengthToTarget)
        needle.setTimeIntervention(time_intervention)
        needle.setCASversion(cas_version)
        # add the TPEs if they exist in the Measurements field - ie. the needle has been validated
        if elementExists(singleTrajectory, 'Measurements') is False:
            # print('No Measurement for this needle')
            pass
        else:
            # find the right needle to replace the exact TPEs
            # set the validation trajectory
            # set the time of intervention from XML
            ep_validation = np.array(
                [float(i) for i in singleTrajectory.Measurements.Measurement.EntryPoint.cdata.split()])
            tp_validation = np.array(
                [float(i) for i in singleTrajectory.Measurements.Measurement.TargetPoint.cdata.split()])
            validation = needle.setValidationTrajectory()
            validation.setTrajectory(ep_validation, tp_validation)

            entry_lateral, target_lateral, target_angular, target_longitudinal, target_euclidean \
                = extractTPES(singleTrajectory.Measurements.Measurement)

            tps = needle.setTPEs()

            # set TPE errors
            tps.setTPEErrors(entry_lateral, target_lateral, target_angular, target_longitudinal, target_euclidean)


def III_parseTrajectory(trajectories, patient, ct_series, xml_filepath, time_intervention, cas_version):
    """ Parse Trajectories at lesion level.
    For each lesion, a new Parent Trajectory is defined.
    A lesion is defined when the distance between needles is minimum 35 mm.
    A patient can have both MWA and IREs
    INPUT:
    - trajectories which is object with Parent Trajectories
    - patient id
    OUTPUT: list of Needle Trajectories passed to Needle Trajectories function
    """
    for xmlTrajectory in trajectories:
        # xmltrajectory count contains the number of lesions
        # Trajectories contains all the upper-level Parent trajectories
        # check whether it's IRE trajectory
        ep_planning = np.array([float(i) for i in xmlTrajectory.EntryPoint.cdata.split()])
        tp_planning = np.array([float(i) for i in xmlTrajectory.TargetPoint.cdata.split()])

        if (xmlTrajectory['type']) and 'IRE' in xmlTrajectory['type']:
            needle_type = 'IRE'
            try:
                children_trajectories = xmlTrajectory.Children.Trajectory
                # function to check if the lesion exists based on location returning true or false
                lesion = patient.findLesion(lesionlocation=tp_planning, DISTANCE_BETWEEN_LESIONS=1)
                if lesion is None:
                    lesion = patient.addNewLesion(tp_planning, time_intervention)
                needle = lesion.findNeedle(needlelocation=tp_planning, DISTANCE_BETWEEN_NEEDLES=1)
                if needle is None:
                    needle = lesion.newNeedle(True, needle_type, ct_series)
                # the reference needle has only planning data
                tps = needle.setTPEs()
                validation = needle.setValidationTrajectory()
                planned = needle.setPlannedTrajectory()
                planned.setTrajectory(ep_planning, tp_planning)
                planned.setLengthNeedle()
                needle.setTimeIntervention(time_intervention)
                needle.setCASversion(cas_version)
                # individual needle level
                IV_parseNeedles(children_trajectories, lesion, needle_type, ct_series, xml_filepath, time_intervention,
                                cas_version)

            except Exception as e:
                print('Error when parsing IRE validated in 2018:', repr(e))
                children_trajectories = xmlTrajectory
                lesion = patient.findLesion(lesionlocation=tp_planning, DISTANCE_BETWEEN_LESIONS=10000)
                # look for another needle withing distance of 100cm. in this case a tp needle will always be found
                # so no new lesion will be added. we assume only one lesion was treated for older cases
                if lesion is None:
                    lesion = patient.addNewLesion(tp_planning, time_intervention)
                # individual needle level
                IV_parseNeedles(children_trajectories, lesion, needle_type, ct_series, xml_filepath, time_intervention,
                                cas_version)


        elif (xmlTrajectory['type'] and 'EG_ATOMIC' in xmlTrajectory['type']) :
            # assuming 'EG_ATOMIC_TRAJECTORY' stands for MWA type of needle
            needle_type = "MWA"
            # drop the lesion identification for MWA. multiple needles might be
            # no clear consensus for minimal distance between lesions and no info in the log version <=2.9
            lesion = patient.findLesion(lesionlocation=tp_planning,  DISTANCE_BETWEEN_LESIONS=1)
            if lesion is None:
                lesion = patient.addNewLesion(tp_planning, time_intervention)
            children_trajectories = xmlTrajectory
            IV_parseNeedles(children_trajectories, lesion, needle_type,
                            ct_series, xml_filepath, time_intervention, cas_version)


        elif not (xmlTrajectory['type'] and 'EG_ATOMIC' in xmlTrajectory['type']):
            # the case when CAS XML Log is old version 2.5
            # the distance between needles shouldn't be more than 22 mm according to a paper
            # DISTANCE_BETWEEN_LESIONS [mm]
            # remove the lesion identification based on the distance between needles, too much variation for accurate identification
            #  put an absurd value for DISTANCE_BETWEEN_LESIONS
            needle_type = 'IRE'
            lesion = patient.findLesion(lesionlocation=tp_planning, DISTANCE_BETWEEN_LESIONS=100000)
            # look for another needle withing distance of 100cm. in this case a tp needle will always be found
            # so no new lesion will be added. we assume only one lesion was treated for older cases
            if lesion is None:
                lesion = patient.addNewLesion(tp_planning, time_intervention)
            children_trajectories = xmlTrajectory
            IV_parseNeedles(children_trajectories, lesion, needle_type,
                            ct_series, xml_filepath, time_intervention, cas_version)


def II_parseTrajectories(xmlobj):
    """ Parse upper-level trajectories structure.
    :param:  xmlobj tree structured parsed by library such as untangle, XMLTree etc.
    :return: Trajectories (if they exist) extracted from XML File
    :return: CT SeriesNumber
    :return: time_intervention
    :return: cas_version
    """
    tuple_results = collections.namedtuple('tuples_results',
                                           ['trajectories',
                                            'series',
                                            'time_intervention',
                                            'cas_version'])
    try:
        trajectories = xmlobj.Eagles.Trajectories.Trajectory
    except Exception as e:
        # pass
        # print(repr(e))
        # print('No trajectory was found in the XML file')
        result = tuple_results(None, None, None, None)
        return result
    try:
        series = xmlobj.Eagles.PatientData["seriesNumber"]  # CT series number
    except Exception:
        # no series image number in the XML
        series = None
    try:
        time_intervention = xmlobj.Eagles["time"]
    except Exception:
        # no time intervention found in the xml
        time_intervention = None
    try:
        cas_version = xmlobj.Eagles["version"]
    except Exception:
        # no cas version defined in the XML file
        cas_version = None

    result = tuple_results(trajectories, series, time_intervention, cas_version)
    return result


def II_extractRegistration(xmlobj, patient, xmlfilename):
    """
    Check if there is any registration matrix and extracts it if True.
    :param xmlobj: xmlobj tree structured parsed by library such as untangle, XMLTree etc.
    :return: RegistrationType, error, Transform Matrix, PointPairsPlanning, Validation  + set flag.
    """
    # check if the element exists
    if not elementExists(xmlobj.Eagles, 'Registration'):
        # if it doesn't exist is the wrong file that doesn't contain registration
        pass
    else:
        registration_matrix = xmlobj.Eagles.Registration.ValidationToPlanning.Transform.cdata
        registration_type = xmlobj.Eagles.Registration.ValidationToPlanning["RegistrationType"]
        # just add the registration matrix once
        if not patient.registrations:
            # if list is emtpy add it once
            registration = patient.addNewRegistration()
        else:  # if list is not empty and the registration hasn't been added already add it to the list
            if (xmlobj.Eagles.Registration.PointPairs and 'none' != registration_type):
                registration_exists = patient.findRegistration(registration_matrix)
                if registration_exists is not None and len(patient.registrations) > 1:
                    return  # exists
                elif registration_exists is None and len(patient.registrations) == 1:
                    # that means the registration has been initialized with an empty matrix
                    registration = patient.registrations[0]
                    try:
                        pp_val_dict = defaultdict(list)
                        pp_plan_dict = defaultdict(list)

                        for PointPair in xmlobj.Eagles.Registration.PointPairs.PointPair:
                            pp_plan_dict['RegistrationPlanPoints'].append(PointPair.Planning.cdata)
                            pp_val_dict['RegistrationValidationPoints'].append(PointPair.Validation.cdata)

                        # instantiate registration
                        registration.setRegistrationInfo(registration_matrix,
                                                         registration_type,
                                                         pp_plan_dict,
                                                         pp_val_dict,
                                                         )
                    except Exception:
                        print('Registration Matrix Extraction Issue in file:', xmlfilename)

                elif registration_exists is None and len(patient.registrations) > 1:
                    registration = patient.addNewRegistration()
                    try:
                        pp_val_dict = defaultdict(list)
                        pp_plan_dict = defaultdict(list)

                        for PointPair in xmlobj.Eagles.Registration.PointPairs.PointPair:
                            pp_plan_dict['RegistrationPlanPoints'].append(PointPair.Planning.cdata)
                            pp_val_dict['RegistrationValidationPoints'].append(PointPair.Validation.cdata)

                        # instantiate registration
                        registration.setRegistrationInfo(registration_matrix,
                                                         registration_type,
                                                         pp_plan_dict,
                                                         pp_val_dict,
                                                         )
                    except Exception:
                        print('Registration Matrix Extraction Issue in file:', xmlfilename)
