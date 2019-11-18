"""OpenDroneMap transformer
"""

import argparse
import os
import logging
import tempfile
import yaml

from opendm import config

from stages.odm_app import ODMApp

import transformer_class

# Forbidden OpenDroneMap setting overrides when using custom configuration
NO_OVERRIDE_SETTINGS = ["project_path"]

# Known image file extensions
KNOWN_IMAGE_FILE_EXTS = ['tif', 'tiff', 'jpg']

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
    # TODO: Digital Elevation Model (dem) file(s)
}

class __internal__():
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
            for one_path in os.listdir(path):
                if not os.path.isdir(one_path):
                    if os.path.splitext(path)[1].lower() in KNOWN_IMAGE_FILE_EXTS:
                        return True
        else:
            if os.path.splitext(path)[1].lower() in KNOWN_IMAGE_FILE_EXTS:
                return True

        return False

    @staticmethod
    def get_merge_options(path):
        """Merges the standard ODM settings with any overrides
        Arguments:
            path: optional file path to settings overrides
        Return:
            Returns the settings with any overrides
        """
        args = config.config()

        # Load any overrides we might have
        if path:
            new_settings = None
            with open(path) as in_file:
                new_settings = yaml.safe_load(in_file)

            if new_settings:
                for name in new_settings:
                    if name not in NO_OVERRIDE_SETTINGS:
                        logging.debug("Configuration: overriding %s to new value '%s'", name, new_settings[name])
                        setattr(args, name, new_settings[name])
                    else:
                        logging.warning("Skipping disallowed configuration value for %s", name)
        return args

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
        working_folder = tempfile.mkstemp(prefix="odm", dir=default_folder)
        logging.debug("Creating project folder at '%s'", working_folder)
        for one_file in files:
            filename = os.path.basename(one_file)
            logging.debug("Linking file to working folder: '%s' ('%s')", filename, one_file)
            ln_name = os.path.join(working_folder, filename)
            os.symlink(one_file, ln_name)

        return working_folder


def add_parameters(parser):
    """Adds parameters
    Arguments:
        parser: instance of argparse.ArgumentParser
    """
    parser.add_argument('--odm_overrides', type=str, help='file containing OpenDroneMap configuration overrides')

    parser.epilog = "accepts a list of files and folders following command line parameters" + \
                    ("\n" + parser.epilog) if parser.epilog else ""


def check_continue(transformer, check_md, transformer_md, full_md):
    """Checks if conditions are right for continuing processing
    Arguments:
        transformer: instance of transformer class
        check_md: metadata on the current request
        transformer_md: the metadata for this transformer
        full_md: the original metadata for this transformer
    Return:
        Returns a tuple containing the return code for continuing or not, and
        an error message if there's an error
    """
    # pylint: disable=unused-argument
    # Check for ODM override file and make sure we can access it
    if transformer.args.odm_overrides:
        if not os.path.exists(transformer.args.odm_overrides):
            return (-1000, "OpenDroneMap overrides specified but file is not available: '%s'" % transformer.args.odm_overrides)

    # Check that there's at least one image file in the list of files
    for one_file in check_md['list_files']():
        if __internal__.check_for_image_file(one_file):
            return tuple(0)

    return (-1001, "Unable to find an image file in files to process. Accepting files types: '%s'" % ", ".join(KNOWN_IMAGE_FILE_EXTS))


def perform_process(transformer, check_md, transformer_md, full_md):
    """Performs the processing of the data
    Arguments:
        transformer: instance of transformer class
        check_md: metadata on the current request
        transformer_md: the metadata for this transformer
        full_md: the original metadata for this transformer
    Return:
        Returns a dictionary with the results of processing
    """
    # pylint: disable=unused-argument
    # Get our OpenDroneMap parameters merged with any overrides
    odm_config = __internal__.get_merge_options(transformer.args.odm_overrides)

    # Create a temporary project folder and link all available images to that folder
    odm_config.project_path = __internal__.prepare_project_folder(check_md['list_files'](), check_md['working_folder'])

    # Process the images
    app = ODMApp(args=odm_config)
    app.execute()

    # Provide a list of returned files
    files_md = []
    for result_folder, result_files in RESULT_FILES.items():
        result_path = os.path.join(odm_config.project_path, result_folder)
        if isinstance(result_files, dict):
            result_files = [result_files]
        for one_file in result_files:
            cur_path = os.path.join(result_path, one_file['name'])
            if os.path.exists(cur_path):
                files_md.append({
                    'path': cur_path,
                    'key': one_file['type']
                })

    return {'files': files_md,
            'code': 0
            }
