# -*- coding: utf-8 -*-
"""
Created on Mon Jan 7 2019

@author: Raluca Sandu

- extract area formed by IRE needles
- found the clockwise direction of vertices
- using Shoelace formula to determine the area of a simple polygon
- the vertices are described by their Cartesian coordinates in the plane

"""

import sys

def det(a):
    # determinant of matrix a
    return a[0][0] * a[1][1] * a[2][2] + a[0][1] * a[1][2] * a[2][0] \
           + a[0][2] * a[1][0] * a[2][1] - a[0][2] * a[1][1] * a[2][0] \
           - a[0][1] * a[1][0] * a[2][2] - a[0][0] * a[1][2] * a[2][1]


# unit normal vector of plane defined by points a, b, and c
def unit_normal(a, b, c):
    x = det([[1, a[1], a[2]],
             [1, b[1], b[2]],
             [1, c[1], c[2]]])
    y = det([[a[0], 1, a[2]],
             [b[0], 1, b[2]],
             [c[0], 1, c[2]]])
    z = det([[a[0], a[1], 1],
             [b[0], b[1], 1],
             [c[0], c[1], 1]])
    magnitude = (x ** 2 + y ** 2 + z ** 2) ** .5
    return (x / magnitude, y / magnitude, z / magnitude)


# dot product of vectors a and b
def dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]


# cross product of vectors a and b
def cross(a, b):

    x = a[1] * b[2] - a[2] * b[1]
    y = a[2] * b[0] - a[0] * b[2]
    z = a[0] * b[1] - a[1] * b[0]

    return (x, y, z)


# area of polygon poly
def area(poly):
    if len(poly) < 3:  # not a plane - no area
        return 0

    total = [0, 0, 0]
    for i in range(len(poly)):
        vi1 = poly[i]
        if i is len(poly) - 1:
            vi2 = poly[0]
        else:
            vi2 = poly[i + 1]
        prod = cross(vi1, vi2)
        total[0] += prod[0]
        total[1] += prod[1]
        total[2] += prod[2]
    result = dot(total, unit_normal(poly[0], poly[1], poly[2]))
    return abs(result / 2)


def compute_areas_needles(df_IREs, patientID, Areas_between_needles):
    """
    :param df_IREs: 
    :param patientID: 
    :param Areas_between_needles: 
    :return: 
    """
    df_IREs_no_reference_needle = df_IREs[~df_IREs.ReferenceNeedle]
    list_lesion_count = df_IREs_no_reference_needle['LesionNr'].tolist()
    # get unique values from the lesion index count
    lesion_unique = list(set(list_lesion_count))
    try:
        df_IREs_no_reference_needle['LesionNr'] = list_lesion_count
    except Exception as e:
        print(repr(e))
        sys.exit()

    for i, lesion in enumerate(lesion_unique):
        lesion_data = df_IREs_no_reference_needle[df_IREs_no_reference_needle['LesionNr'] == lesion]
        needles_count = lesion_data['NeedleNr'].tolist()

        PlannedTargetPoint = lesion_data['PlannedTargetPoint'].tolist()
        ValidationTargetPoint = lesion_data['ValidationTargetPoint'].tolist()

        # assume that the target points describe a simple polygon
        area_planned = area(PlannedTargetPoint) / 100  # convert from mm_square to cm_square divide by 100
        area_validation = area(ValidationTargetPoint) / 100

        area_dict = {
            'PatientID': patientID,
            'LesionNr': lesion,
            'NeedleCount': len(needles_count),
            'Planned Area': area_planned,
            'Validation Area': area_validation
        }

        Areas_between_needles.append(area_dict)


if __name__ == '__main__':
    target_points_x = [1, 4, 2]
    target_points_y = [1, 1, 3]
    p = [[1, 1], [1, 4], [2, 3]]
    # poly = [[0, 0, 0], [10, 0, 0], [10, 3, 4], [0, 3, 4]]
    poly = ((0, 0, 0), (10, 0, 0), (10, 3, 4), (0, 3, 4))
    poly_translated = [[0 + 5, 0 + 5, 0 + 5], [10 + 5, 0 + 5, 0 + 5], [10 + 5, 3 + 5, 4 + 5], [0 + 5, 3 + 5, 4 + 5]]
    print(area(poly))
    # polygon represented as list of tuples [(x1, y1, z1), (x2, y2, z3), ...(xn, yn, zn)]
    # poly_triangle =[[x1,y1,z1], [x2, y2,z2], [x3,y3,z3]]
    # poly_triangle = [[1,1, 1], [1,1, 4], [1, 2, 3]]
    # print(area(poly_triangle))
