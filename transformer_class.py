"""Class instance for Transformer
"""

import os

from agpypeline import transformer_class as transform

# EXIF tags to look for, see https://www.exiv2.org/tags.html
EXIF_ORIGINAL_TIMESTAMP = 36867         # Capture timestamp
EXIF_TIMESTAMP_OFFSET = 36881           # Timestamp UTC offset (general)
EXIF_ORIGINAL_TIMESTAMP_OFFSET = 36881  # Capture timestamp UTC offset


class __internal__:
    """Class containing functions for this file only
    """
    def __init__(self):
        """Perform class level initialization
        """

    @staticmethod
    def exif_tags_to_timestamp(exif_tags):
        """Looks up the origin timestamp and a timestamp offset in the exit tags and returns
           a datetime object
        Args:
            exif_tags(dict): The exif tags to search for timestamp information
        Return:
            Returns the origin timestamp when found. The return timestamp is adjusted for UTF if
            an offset is found. None is returned if a valid timestamp isn't found.
        """
        return transform.__internal__.exif_tags_to_timestamp(exif_tags)

    @staticmethod
    def get_first_timestamp(file_path, timestamp):
        """Looks for a timestamp in the specified file and returns
           the earliest timestamp (when compared to the timestamp parameter)
        Arguments:
            file_path: the path to the file to check
            timestamp: the timestamp to compare against (when specified)
        Return:
            The earliest found timestamp
        """
        return transform.__internal__.get_first_timestamp(file_path, timestamp)


class Transformer:
    """Generic class for supporting transformers
    """
    # pylint: disable=unused-argument
    def __init__(self, **kwargs):
        """Performs initialization of class instance
        Arguments:
            kwargs: additional parameters passed in to Transformer
        """
        self.sensor = None
        self.args = None

    @property
    def supported_image_file_exts(self):
        """Returns the list of supported image file extension strings (in lower case)
        """
        return Transformer.supported_file_exts

    @property
    def supported_file_exts(self):
        """Returns the list of supported file extension strings (in lower case)
        """
        return ['tif', 'tiff', 'jpg', 'txt']

    def add_parameters(self, parser):
        """Adds processing parameters to existing parameters
        Arguments:
            parser: instance of argparse
        """
        transform.Transformer.add_parameters(self, parser)

    def get_acceptable_files(self, files_folders: list) -> list:
        """Returns a list of files from the passed in list. Performs a shallow folder check (1 deep)
        Arguments:
            files_folders: a list of files and folders to parse
        Return:
            Returns a list of image files
        """
        return_files = []
        for one_path in files_folders:
            if os.path.isdir(one_path):
                for dir_path in os.listdir(one_path):
                    if not os.path.isdir(dir_path):
                        if os.path.splitext(dir_path)[1].lstrip('.').lower() in self.supported_file_exts:
                            return_files.append(os.path.join(one_path, dir_path))
            elif os.path.splitext(one_path)[1].lstrip('.').lower() in self.supported_file_exts:
                return_files.append(one_path)
        return return_files

    def get_transformer_params(self, args, metadata_list):
        """Returns a parameter list for processing data
        Arguments:
            args: result of calling argparse.parse_args
            metadata_list: the loaded metadata
        """
        return Transformer.get_transformer_params(self, args, metadata_list)
