#!/usr/bin/env python3
"""OpenDroneMap transformer
"""

import argparse
import os
import logging
import subprocess
import time
import datetime
from agpypeline import entrypoint, algorithm
from agpypeline.environment import Environment

from configuration import ConfigurationOdm

# Known image file extensions
KNOWN_IMAGE_FILE_EXTS = ['.tif', '.tiff', '.jpg']

# Known additional acceptable files
KNOWN_GCP_FILES = ['gcp_list.txt']

# Paths and files available after processing
RESULT_FILES = {
    'odm_orthophoto': {'name': 'odm_orthophoto.tif', 'type': 'rgb'},
    'odm_georeferencing': [
        {'name': 'odm_georeferenced_model.laz', 'type': 'lidar'},
        {'name': 'odm_georeferenced_model.bounds.shp', 'type': 'shapefile'},
        {'name': 'odm_georeferenced_model.bounds.dbf', 'type': 'shapefile'},
        {'name': 'odm_georeferenced_model.bounds.prj', 'type': 'shapefile'},
        {'name': 'odm_georeferenced_model.bounds.shx', 'type': 'shapefile'},
        {'name': 'proj.txt', 'type': 'shapefile'},
        {'name': 'odm_georeferenced_model.bounds.geojson', 'type': 'shapefile'},
        {'name': 'odm_georeferenced_model.boundary.json', 'type': 'shapefile'},
    ],
    'mve': {'name': 'mve_dense_point_cloud.ply', 'type': 'pointcloud'},
    'odm_dem': [
        {'name': 'dsm.tif', 'type': 'dsm'},
        {'name': 'dtm.tif', 'type': 'dtm'},
    ]
}


class __internal__:
    """Internal use only class
    """
    def __init__(self):
        """Initialized class instance
        """

    @staticmethod
    def check_for_image_file(path):
        """Checks the specified path for image files. If a folder is specified,
           it's only searched to a depth of 1 (immediately inside of the folder)
        Arguments:
            path: the path to check for image(s)
        Return:
            Returns True if an image file is found and False if none are found
        Notes:
            Only the file extension is checked as an indication of file type
        """
        # Iterate over a folder
        if os.path.isdir(path):
            logging.debug("Checking folder")
            for one_path in os.listdir(path):
                if not os.path.isdir(one_path):
                    logging.debug("Checking file in folder (%s): %s", os.path.splitext(one_path)[1].lower(), one_path)
                    if os.path.splitext(one_path)[1].lower() in KNOWN_IMAGE_FILE_EXTS:
                        return True
        else:
            if os.path.splitext(path)[1].lower() in KNOWN_IMAGE_FILE_EXTS:
                return True

        return False

    @staticmethod
    def check_gcp_file(path):
        """Checks if the path is acceptable
        Arguments:
            path: the path to check
        Return:
            Returns True if the file is acceptable
        """
        logging.debug("Checking if %s is in %s", os.path.basename(path), str(KNOWN_GCP_FILES))
        if os.path.basename(path) in KNOWN_GCP_FILES:
            return True
        return False

    @staticmethod
    def prepare_project_folder(files, default_folder):
        """Prepares the project folder
        Arguments:
            files: the list of files and folders to prepare
            default_folder: the folder to use as the default start folder when preparing the  project folder
        Return:
             The path to the project folder
        """
        # Create a temporary folder and link the images to it
        working_folder = default_folder
        logging.debug("Creating project folder at '%s'", working_folder)
        images_folder = os.path.join(working_folder, 'images')
        if not os.path.exists(images_folder):
            os.mkdir(images_folder)
        logging.debug("Creating images folder at '%s'", images_folder)

        # Get the list of files to process
        file_list = []
        gcp_file = None
        for one_file in files:
            if os.path.isdir(one_file):
                for file_name in os.listdir(one_file):
                    if not os.path.isdir(file_name):
                        if __internal__.check_for_image_file(file_name):
                            file_list.append(os.path.join(one_file, file_name))
                        elif __internal__.check_gcp_file(file_name):
                            gcp_file = os.path.join(one_file, file_name)
            elif __internal__.check_for_image_file(one_file):
                file_list.append(one_file)
            elif __internal__.check_gcp_file(one_file):
                gcp_file = one_file

        logging.debug("Found image files: %s", str(file_list))
        for one_file in file_list:
            filename = os.path.basename(one_file)
            logging.debug("Linking file to image folder: '%s' ('%s')", filename, one_file)
            ln_name = os.path.join(images_folder, filename)
            logging.debug("symlink: '%s' to '%s'", one_file, ln_name)
            os.symlink(one_file, ln_name)

        logging.debug("Handling GCP file: %s", str(gcp_file))
        if gcp_file:
            filename = os.path.basename(gcp_file)
            logging.debug("Linking file to working folder: '%s' ('%s')", filename, gcp_file)
            ln_name = os.path.join(working_folder, filename)
            logging.debug("symlink: '%s' to '%s'", gcp_file, ln_name)
            os.symlink(gcp_file, ln_name)

        return working_folder

    @staticmethod
    def consume_proc_output(proc):
        """Consumes output from the specified process
        Arguments:
            proc: the process to read from
        Notes:
            Assumes the process was started with stdout being piped
        """
        try:
            while True:
                line = proc.stdout.readline()
                if line:
                    if isinstance(line, bytes):
                        line = line.decode('UTF-8').strip()
                    logging.debug(line.rstrip('\n'))
                else:
                    break
        except Exception as ex:
            logging.debug("Ignoring exception while waiting: %s", str(ex))
            if logging.getLogger().level in [logging.INFO, logging.DEBUG]:
                logging.exception(ex)

    @staticmethod
    def run_stitch(project_path, override_path=None):
        """Runs open drone map through another script (allows us to control command line parameters and
           other ODM expected dependencies
        Arguments:
            project_path: the path of the project folder
            override_path: optional path to ODM override file
        """
        logging.debug('OpenDroneMap app beginning - %s', datetime.datetime.now().isoformat())
        my_env = os.environ.copy()

        # Set environment variables
        my_env["ODM_PROJECT"] = project_path
        if override_path:
            logging.debug("Override settings file at: %s", override_path)
            my_env["ODM_SETTINGS"] = override_path

        # Build up path to ODM working script
        my_path = os.path.dirname(os.path.realpath(__file__))
        if not my_path:
            my_path = "."
        script_path = os.path.join(my_path, "worker.py")

        # Start the process
        logging.info("Starting ODM script at: %s", script_path)
        # pylint: disable=consider-using-with
        proc = subprocess.Popen([script_path, "code"], bufsize=-1, env=my_env,
                                stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

        # Wait for the script to finish
        return_value = -1
        if proc:
            # Loop here processing the output until the proc finishes
            logging.info("Waiting for process to finish")
            while proc.returncode is None:
                if proc.stdout is not None:
                    __internal__.consume_proc_output(proc)
                    proc.poll()

                # Sleep and try again for process to complete
                time.sleep(1)
            logging.debug("Return code: %s", str(proc.returncode))
            return_value = proc.returncode

        logging.debug('OpenDroneMap app finished - %s', datetime.datetime.now().isoformat())
        return return_value


class Opendronemap(algorithm.Algorithm):
    """Runs open drone map"""

    def add_parameters(self, parser: argparse.ArgumentParser):
        """Adds parameters
        Arguments:
            parser: instance of argparse.ArgumentParser
        """
        parser.add_argument('--odm_overrides', type=str, help='file containing OpenDroneMap configuration overrides')

        parser.epilog = "accepts a list of files and folders following command line parameters" + \
                        ("\n" + parser.epilog) if parser.epilog else ""

    def check_continue(self, environment: Environment, check_md: dict, transformer_md: list, full_md: list) -> tuple:
        """Checks if conditions are right for continuing processing
        Arguments:
            environment: instance of environment class
            check_md: metadata on the current request
            transformer_md: the metadata for this transformer
            full_md: the original metadata for this transformer
        Return:
            Returns a tuple containing the return code for continuing or not, and
            an error message if there's an error
        """
        # pylint: disable=unused-argument
        # Check for ODM override file and make sure we can access it
        if environment.args.odm_overrides:
            if not os.path.exists(environment.args.odm_overrides):
                return (-1000, "OpenDroneMap overrides specified but file is not available: '%s'" %
                        environment.args.odm_overrides)

        # Check that there's at least one image file in the list of files
        for one_file in check_md['list_files']():
            logging.debug("Checking if image file: %s", one_file)
            if __internal__.check_for_image_file(one_file):
                logging.debug("Found an image file")
                return 0

        return (-1001, "Unable to find an image file in files to process. Accepting files types: '%s'" %
                ", ".join(KNOWN_IMAGE_FILE_EXTS))

    def perform_process(self, environment: Environment, check_md: dict, transformer_md: dict,
                        full_md: list) -> dict:
        """Performs the processing of the data
        Arguments:
            environment: instance of environment class
            check_md: metadata on the current request
            transformer_md: the metadata for this transformer
            full_md: the original metadata for this transformer
        Return:
            Returns a dictionary with the results of processing
        """
        # pylint: disable=unused-argument
        # Create a temporary project folder and link all available images to that folder
        project_path = __internal__.prepare_project_folder(check_md['list_files'](), check_md['working_folder'])

        # Process the images
        logging.debug("Calling ODM with project path: %s", str(project_path))
        stitch_code = __internal__.run_stitch(project_path, environment.args.odm_overrides)

        # Provide a list of returned files
        files_md = []
        for result_folder, result_files in RESULT_FILES.items():
            result_path = os.path.join(project_path, result_folder)
            if isinstance(result_files, dict):
                result_files = [result_files]
            for one_file in result_files:
                cur_path = os.path.join(result_path, one_file['name'])
                if os.path.exists(cur_path):
                    files_md.append({
                        'path': cur_path,
                        'key': one_file['type']
                    })

        return {'file': files_md,
                'code': stitch_code
                }


if __name__ == "__main__":
    CONFIGURATION = ConfigurationOdm()
    entrypoint.entrypoint(CONFIGURATION, Opendronemap())
