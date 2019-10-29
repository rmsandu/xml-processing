# -*- coding: utf-8 -*-
"""
Created on Wed Jun  6 10:10:24 2018

@author: Raluca Sandu
"""

import re
import os
import sys
import string
import shutil
import zipfile
from XMLProcessing.splitAllPaths import splitall


def copytree(src, dst, symlinks=False, ignore=None):
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        if os.path.isdir(s):
            try:
                shutil.copytree(s, d, symlinks, ignore)
            except Exception:
                print('Filename greater than 255 characters: ', s)
                # TODO: rename the files and folders???
                continue
        else:
            shutil.copy2(s, d)


def copy_rename(src_dir, dst_dir, keyword):
    """
    Copy specific patient folder(s) from src_dir to dest_dir and save the filenames to Excel.
    Removes the trailing numbers at the beginning of the file folder.
    Remove weird unicode characters.
    :param src_dir: [string]. source directory where the files are
    :param dst_dir: [string]. destination directory where the files will be copied
    :param keyword: [string]. here keyword = "Pat" or Pat_JohnSmith to identify main patient folder
    :return: Excel with saved filenames and filepathss
    """
    dict_filenames = []
    pat_counter = 0

    # iterate through each pat directory and rename it
    for dirs in os.listdir(src_dir):
        if not os.path.isdir(os.path.join(src_dir, dirs)):
            continue
        else:
            # if any of the patient names has been found
            if keyword in dirs:
                # remove weird non-ascii characters
                printable = set(string.printable)
                pat_folder_renamed = ''.join(filter(lambda x: x in string.printable, dirs))
                # we have to rename before copying because non-ascii characters can't be parsed
                os.rename(os.path.join(src_dir, dirs),
                          os.path.join(src_dir, pat_folder_renamed))
                pat_filepath_src = os.path.join(src_dir, pat_folder_renamed)
                pat_filepath_dst = os.path.join(dst_dir, pat_folder_renamed)

                # create empty folder with patient filepath name
                if not os.path.exists(pat_filepath_dst):
                    os.makedirs(pat_filepath_dst)
                # copy the folder with the folder name
                copytree(pat_filepath_src, pat_filepath_dst)
                # then remove the date in front
                patient_idx = re.search("Pat_", dirs)  # find starting idx Pat to remove numbers before that
                patient_idx_1 = int(patient_idx.start())
                pat_folder_no_date = dirs[patient_idx_1:]

                os.rename(os.path.join(dst_dir, pat_folder_renamed),
                          os.path.join(dst_dir, pat_folder_no_date))




def move_unzip(dst_dir):
    """
    Move Study to Root folder and Unzip XML Recordings
    :param dst_dir: 
    :param keyword:
    """
    for path, dirs, files in os.walk(dst_dir):
        index_ir = [i for i, s in enumerate(dirs) if 'IR Data' in s]
        index_xml = [i for i, s in enumerate(dirs) if 'XML' in s]
        if index_ir:
            # move Study folder to root patient folder
            ir_data_dir = dirs[index_ir[0]]
            src = os.path.join(path, ir_data_dir)
            all_folders = splitall(src)
            index = [i for i, s in enumerate(all_folders) if "Pat_" in s]
            dst = os.path.join(dst_dir, all_folders[index[0]])
            copytree(src, dst)
        if index_xml:
            # TODO: Error unzipping if filename too long. Must solve
            # unzip the XML Recordings
            xml_dir = dirs[index_xml[0]]
            xml_dir = os.path.join(path, xml_dir)
            for file in os.listdir(xml_dir):
                if file.endswith(".zip"):
                    filename, file_extension = os.path.splitext(file)
                    # unzip file xml recordings
                    zip_filepath = os.path.join(xml_dir, file)
                    with zipfile.ZipFile(zip_filepath, "r") as zip_ref:
                        zip_ref.extractall(os.path.join(xml_dir, filename))
                        zip_ref.close()
    print("Done! All files and folders copied and renamed")


if __name__ == '__main__':
    if len(sys.argv) < 4:
        print(" To few arguments, please specify a source directory, a destination directory and a keyword for every"
              " patients folder name. Please specify keyword [keyword(string), keyword(string)] ")
        exit()
    else:
        # source_directory = r"C:\Patients_Cochlea\Datasets"
        source_directory = os.path.normpath(sys.argv[1])
        print("Source Directory:", source_directory)
        destination_directory = os.path.normpath(sys.argv[2])
        # destination_directory = r"C:\Patients_Cochlea\Datsets_Fabrice_processed"
        print("Destination Directory:", destination_directory)
        keywords = sys.argv[3]
        # keywords = ["Pat_"]
        print("Keyword for Patient Folder(s): ", keywords)

        # look for the keywords in a list of folder.
        # if keyword is "Pat" it selects all patients

        for keyword_folder_name in keywords:
            copy_rename(source_directory, destination_directory, keyword_folder_name)
        # unzip XML Recordings folders and move StudyXX to root folder.
        move_unzip(destination_directory)

