# -*- coding: utf-8 -*-
"""
Created on Thu Feb 15 11:15:43 2018

@author: Raluca Sandu
"""

def elementExists(node, attrStr):
    '''check if elements exists, as a xml tag or as an attribute'''
    try:
        xmlElement = eval('node' + '.' + attrStr)
        return True
    except Exception:
        if (node[attrStr]):
             return True
        else:
            return False