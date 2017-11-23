# -*- coding: utf-8 -*-
"""
Created on Thu Nov 16 10:00:32 2017

@author: Raluca Sandu
"""

# -*- coding: utf-8 -*-
"""
Created on Thu Nov  9 13:43:49 2017

@author: Raluca Sandu
"""
# libraries import

import numpy as np
import pandas as pd
from enum import Enum
from medpy import metric
import SimpleITK as sitk

#plt.style.use('ggplot')
#plt.style.use('classic')
#print(plt.style.available)

#%%
class DistanceMetrics(object):

    
    def __init__(self,mask, reference):

        # image read as img[x,y,z]
        reference_segmentation = sitk.ReadImage(reference, sitk.sitkUInt8)
        segmentation = sitk.ReadImage(mask,sitk.sitkUInt8)
        
         
        class SurfaceDistanceMeasuresITK(Enum):
            hausdorff_distance, min_surface_distance, mean_surface_distance, median_surface_distance, std_surface_distance, rms_surface_distance = range(6)
        
        
        class MedpyMetricDists(Enum):
            hausdorff_distanceMedPy, avg_surface_distanceMedPy, avg_symmetric_surface_distanceMedPy = range(3)
        
        surface_distance_results = np.zeros((1,len(SurfaceDistanceMeasuresITK.__members__.items())))
        surface_dists_Medpy = np.zeros((1,len(MedpyMetricDists.__members__.items())))
        
        #%%
        reference_surface = sitk.LabelContour(reference_segmentation)
        reference_surface_array =sitk.GetArrayFromImage(reference_surface)
        rf_pts = reference_surface_array.nonzero()
        self.num_reference_surface_pixels = len(list(zip(rf_pts[0], rf_pts[1], rf_pts[2])))
                        
        # init signed mauerer distance as reference metrics
        self.reference_distance_map = sitk.SignedMaurerDistanceMap(reference_segmentation, squaredDistance=False, useImageSpacing=True)
        
        hausdorff_distance_filter = sitk.HausdorffDistanceImageFilter()
        hausdorff_distance_filter.Execute(reference_segmentation, segmentation)

        surface_distance_results[0,SurfaceDistanceMeasuresITK.hausdorff_distance.value] = hausdorff_distance_filter.GetHausdorffDistance()
        
        #%%
        # get the Contour
        segmented_surface_mask = sitk.LabelContour(segmentation)
        segmented_surface_mask_array =sitk.GetArrayFromImage(segmented_surface_mask)
        rf_pts = segmented_surface_mask_array.nonzero()
        # Get the number of pixels in the mask surface by counting all pixels that are non-zero
        self.num_segmented_surface_pixels = len(list(zip(rf_pts[0], rf_pts[1], rf_pts[2])))
        
        # Compute Mauerer Distance
        self.mask_distance_map = sitk.SignedMaurerDistanceMap(segmentation, squaredDistance=False, useImageSpacing=True)
        
        # Multiply the binary surface segmentations with the distance maps. The resulting distance
        # maps contain non-zero values only on the surface (they can also contain zero on the surface)
        self.seg2ref_distance_map = self.mask_distance_map*sitk.Cast(reference_surface, sitk.sitkFloat32) 
        self.ref2seg_distance_map = self.reference_distance_map*sitk.Cast(segmented_surface_mask, sitk.sitkFloat32)
            
        
        # Get all non-zero distances and then add zero distances if required.
        seg2ref_distance_map_arr = sitk.GetArrayFromImage(self.seg2ref_distance_map)
        self.seg2ref_distances = list(seg2ref_distance_map_arr[seg2ref_distance_map_arr!=0]/-255) 

        ref2seg_distance_map_arr = sitk.GetArrayFromImage(self.ref2seg_distance_map)
        self.ref2seg_distances = list(ref2seg_distance_map_arr[ref2seg_distance_map_arr!=0]/255) 

        self.all_surface_distances = self.seg2ref_distances + self.ref2seg_distances        
        #%% Compute the symmetric surface distances min, mean, median, std
    
        surface_distance_results[0,SurfaceDistanceMeasuresITK.min_surface_distance.value] = np.min(self.all_surface_distances)
        surface_distance_results[0,SurfaceDistanceMeasuresITK.mean_surface_distance.value] = np.mean(self.all_surface_distances)
        surface_distance_results[0,SurfaceDistanceMeasuresITK.median_surface_distance.value] = np.median(self.all_surface_distances)
        surface_distance_results[0,SurfaceDistanceMeasuresITK.std_surface_distance.value] = np.std(self.all_surface_distances)
        
        # Compute the root mean square distance
        ref2seg_distances_squared = np.asarray(self.ref2seg_distances) ** 2
        seg2ref_distances_squared = np.asarray(self.seg2ref_distances) ** 2
        
        rms = np.sqrt(1. / (self.num_reference_surface_pixels + self.num_segmented_surface_pixels)) * np.sqrt(seg2ref_distances_squared.sum()  + ref2seg_distances_squared.sum())
        surface_distance_results[0,SurfaceDistanceMeasuresITK.rms_surface_distance.value] = rms

        
        # Save to DataFrame
        self.surface_distance_results_df = pd.DataFrame(data=surface_distance_results, index = list(range(1)),
                                      columns=[name for name, _ in SurfaceDistanceMeasuresITK.__members__.items()])
        
        # change the name of the columns
        self.surface_distance_results_df.columns = ['Maximum Symmetric Distance', 'Minimum Symmetric Surface Distance','Average Symmetric Distance', 'Median Symmetric Distance', 'Standard Deviation', 'RMS Symmetric Distance']
        #%%
        # img read as img[z,y,x]
        img_array = sitk.GetArrayFromImage(reference_segmentation)
        seg_array = sitk.GetArrayFromImage(segmentation)
        # reverse array in the order x, y, z
        img_array_rev = np.flip(img_array,2)
        seg_array_rev = np.flip(seg_array,2)
        vxlspacing = segmentation.GetSpacing()
        
        # use the MedPy metric library
        surface_dists_Medpy[0,MedpyMetricDists.hausdorff_distanceMedPy.value] = metric.binary.hd(seg_array_rev,img_array_rev, voxelspacing=vxlspacing)
        surface_dists_Medpy[0,MedpyMetricDists.avg_surface_distanceMedPy.value] = metric.binary.asd(seg_array_rev,img_array_rev, voxelspacing=vxlspacing)
        surface_dists_Medpy[0,MedpyMetricDists.avg_symmetric_surface_distanceMedPy.value] = metric.binary.assd(seg_array_rev,img_array_rev, voxelspacing=vxlspacing)
        self.surface_dists_Medpy_df = pd.DataFrame(data=surface_dists_Medpy, index = list(range(1)),
                                      columns=[name for name, _ in MedpyMetricDists.__members__.items()])

    #%%
    
    def get_Distances(self):
        # convert to DataFrame
        metrics_all = pd.concat([self.surface_dists_Medpy_df, self.surface_distance_results_df], axis=1)
        return(metrics_all)
    
    def get_SitkDistances(self):
        return self.surface_distance_results_df
    
    def get_MedPyDistances(self):
        return self.surface_dists_Medpy_df
    
    def get_avg_symmetric_dist(self):
        return (self.n1*self.avg_ref + self.n2*self.avg_seg)/(self.n1+self.n2)
    
    def get_std_symmetric_dist(self):
        return self.symmetric_std
    
    def get_mask_dist_map(self):
        return self.seg2ref_distance_map
    
    def get_reference_dist_map(self):
        return self.ref2seg_distance_map 
    
    def get_ref2seg_distances(self):
        return self.ref2seg_distances 
    
    def get_seg2ref_distances(self):
        return self.seg2ref_distances
    
    def get_all_distances(self):
        return self.all_surface_distances