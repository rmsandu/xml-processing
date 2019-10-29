# -*- coding: utf-8 -*-
"""
Created on Tue Jul  4 16:02:17 2017
calculate angle between vectors
@author: Raluca Sandu
"""

from math import degrees

import numpy as np


def unit_vector(vector):
    """ Returns the unit vector of the vector.  """
    return vector / np.linalg.norm(vector)

def angle_between(epNeedle1,tpNeedle1,epNeedle2,tpNeedle2):
    """ Returns the angle in degrees between entry and reference trajectory needles::

            angle_between((1, 0, 0), (0, 1, 0))
            1.5707963267948966
            angle_between((1, 0, 0), (1, 0, 0))
            0.0
            angle_between((1, 0, 0), (-1, 0, 0))
            3.141592653589793        
    """
    #    vector1 = TargetPoint-EntryPoint
    #    vector2 = TargetPoint-EntryPoint

    # if the vectors are string format
    # epNeedle1 = np.array([float(i) for i in epNeedle1.split()])
    # tpNeedle1 = np.array([float(i) for i in tpNeedle1.split()])
    #
    # epNeedle2 = np.array([float(i) for i in epNeedle2.split()])
    # tpNeedle2 = np.array([float(i) for i in tpNeedle2.split()])
        
    if tpNeedle1 is None or epNeedle1 is None or tpNeedle2  is None or epNeedle2 is None:
        return np.nan
        
    v1 = tpNeedle1- epNeedle1
    v2 = tpNeedle2 - epNeedle2
    
    # angle = atan2(vector2.y, vector2.x) - atan2(vector1.y, vector1.x);
    # if (angle < 0) angle += 2 * M_PI;
        
    v1_u = unit_vector(v1)
    v2_u = unit_vector(v2)
    
    # return the value of the angle in degrees 
    angle_radians = np.arccos(np.clip(np.dot(v1_u, v2_u), -1.0, 1.0))
    
    return degrees(angle_radians)


