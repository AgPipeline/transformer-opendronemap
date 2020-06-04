"""Class instance for Transformer
"""

import datetime
import json
import logging
import os
#from pyclowder.utils import setup_logging as pyc_setup_logging
import tempfile
import piexif
import requests

import yaml
import configuration

# EXIF tags to look for, see https://www.exiv2.org/tags.html
EXIF_ORIGINAL_TIMESTAMP = 36867         # Capture timestamp
EXIF_TIMESTAMP_OFFSET = 36881           # Timestamp UTC offset (general)
EXIF_ORIGINAL_TIMESTAMP_OFFSET = 36881  # Capture timestamp UTC offset


class __internal__():
    """Class containing functions for this file only
    """
    def __init__(self):
        """Perform class level initialization
        """

    @staticmethod
    def fromisoformat(timestamp):
        """Converts YYYY-MM-DDTHH:MI:SS, YYYY-MM-DDTHH:MI:SS.mmmm with or without a timezone offset to a datetime object
        Arguments:
            timestamp(str): the timestamp to convert
        """
        if not timestamp:
            return None
        try:
            logging.debug("Checking for specific characters in timestamp")
            if 'T' in timestamp:
                base_format = '%Y-%m-%dT%H:%M:%S'
            elif '-' in timestamp:
                base_format = '%Y-%m-%d %H:%M:%S'
            else:
                base_format = '%Y:%m:%d %H:%M:%S'
            if '.' in timestamp:
                base_format = base_format + '.%f'
            if '+' in timestamp or (timestamp.rfind('-') > timestamp.rfind(':')):
                base_format = base_format + '%z'

            logging.info("Converting timestamp: '%s' %s", str(timestamp), base_format)
            return datetime.datetime.strptime(timestamp, base_format)
        except Exception as ex:
            logging.error("Continuing after exception converting timestamp '%s': %s", str(timestamp), str(ex))

        return None

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
        cur_stamp, cur_offset = (None, None)

        def convert_and_clean_tag(value):
            """Internal helper function for handling EXIF tag values. Tests for an empty string after
               stripping colons, '+', '-', and whitespace [the spec is unclear if a +/- is needed when
               the timestamp offset is unknown (and spaces are used)].
            Args:
                value(bytes or str): The tag value
            Return:
                Returns the cleaned up, and converted from bytes, string. Or None if the value is empty
                after stripping above characters and whitespace.
            """
            if not value:
                return None

            # Convert bytes to string
            if isinstance(value, bytes):
                value = value.decode('UTF-8').strip()
            else:
                value = value.strip()

            # Check for an empty string after stripping colons
            if value:
                if not value.replace(":", "").replace("+:", "").replace("-", "").strip():
                    value = None

            return None if not value else value

        # Process the EXIF data
        if EXIF_ORIGINAL_TIMESTAMP in exif_tags:
            cur_stamp = convert_and_clean_tag(exif_tags[EXIF_ORIGINAL_TIMESTAMP])
        if not cur_stamp:
            return None

        if EXIF_ORIGINAL_TIMESTAMP_OFFSET in exif_tags:
            cur_offset = convert_and_clean_tag(exif_tags[EXIF_ORIGINAL_TIMESTAMP_OFFSET])
        if not cur_offset and EXIF_TIMESTAMP_OFFSET in exif_tags:
            cur_offset = convert_and_clean_tag(exif_tags[EXIF_TIMESTAMP_OFFSET])

        # Format the string to a timestamp and return the result
        try:
            if not cur_offset:
                logging.debug("Converting EXIF timestamp without offset: '%s'", str(cur_stamp))
                cur_ts = __internal__.fromisoformat(cur_stamp)
            else:
                logging.debug("Converting EXIF timestamp and offset: '%s' '%s'", str(cur_stamp), str(cur_offset))
                cur_offset = cur_offset.replace(":", "")
                cur_ts = __internal__.fromisoformat(cur_stamp + cur_offset)
        except Exception as ex:
            cur_ts = None
            logging.debug("Exception caught converting EXIF tag to timestamp: %s", str(ex))

        return cur_ts

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
        logging.debug("Getting first timestamp from timestamp and file: '%s' '%s'", str(timestamp), str(file_path))
        first_stamp = __internal__.fromisoformat(timestamp)
        try:
            tags_dict = piexif.load(file_path)
            if tags_dict and "Exif" in tags_dict:
                cur_stamp = __internal__.exif_tags_to_timestamp(tags_dict["Exif"])
                if cur_stamp:
                    first_stamp = cur_stamp if first_stamp is None or cur_stamp < first_stamp else first_stamp
        except Exception as ex:
            logging.debug("Exception caught getting timestamp from file: %s", file_path)
            logging.debug("    %s", str(ex))

        if first_stamp:
            return first_stamp.isoformat()

        return timestamp


class Transformer():
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
        return ['tif', 'tiff', 'jpg']

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
        # pylint: disable=no-self-use
        parser.add_argument('--logging', '-l', nargs='?', default=os.getenv("LOGGING"),
                            help='file or url or logging configuration (default=None)')

        parser.epilog = configuration.TRANSFORMER_NAME + ' version ' + configuration.TRANSFORMER_VERSION + \
                        ' author ' + configuration.AUTHOR_NAME + ' ' + configuration.AUTHOR_EMAIL

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
        # Setup logging

        if args.logging:
            temp_file = None
            if args.logging.startswith("http://") or args.logging.startswith("https://"):
                request_current = requests.get(args.logging)
                request_current.raise_for_status()
                (temp_file) = tempfile.mkstemp()[0]
                with os.fdopen(temp_file, "wb") as tmp:
                    for chunk in request_current.iter_content(chunk_size=1024):
                        tmp.write(chunk)
                args.logging = temp_file

            if os.path.isfile(args.logging):
                if args.logging.endswith('.yml'):
                    with open(args.logging, 'r') as configfile:
                        config = yaml.safe_load(configfile)
                        logging.config.dictConfig(config)
                elif args.logging.endswith('.json'):
                    with open(args.logging, 'r') as configfile:
                        config = json.load(configfile)
                        logging.config.dictConfig(config)
                else:
                    logging.config.fileConfig(args.logging)
            else:
                config = json.load(args.logging)
                logging.config.dictConfig(config)

            if temp_file:
                os.remove(temp_file)
        else:
            logging.basicConfig(format='%(asctime)-15s [%(threadName)-15s] %(levelname)-7s :'
                                       ' %(name)s - %(message)s',
                                level=logging.INFO)
            logging.getLogger('requests.packages.urllib3.connectionpool').setLevel(logging.WARN)

        self.args = args

        # Determine if we're using JSONLD
        metadata = metadata_list[0]
        if 'content' in metadata:
            parse_md = metadata['content']
        else:
            parse_md = metadata

        # Get the season, experiment, etc information
        timestamp, season_name, experiment_name = None, None, None
        logging.debug("Using the following experimental metadata: %s", str(parse_md))
        if 'observationTimeStamp' in parse_md:
            timestamp = parse_md['observationTimeStamp']
        if 'season' in parse_md:
            season_name = parse_md['season']
        if 'studyName' in parse_md:
            experiment_name = parse_md['studyName']

        # Get the list of files, if there are some and find the earliest timestamp if a timestamp
        # hasn't been specified yet
        file_list = []
        working_timestamp = timestamp
        if args.file_list:
            logging.debug("Looking for files in following list: %s", str(args.file_list))
            check_list = self.get_acceptable_files(args.file_list)
            logging.debug("Found the following files: %s", str(check_list))
            for one_file in check_list:
                # Filter out arguments that are obviously not files
                if not one_file.startswith('-'):
                    file_list.append(one_file)
                    # Only bother to get a timestamp if we don't have one specified
                    if timestamp is None:
                        working_timestamp = __internal__.get_first_timestamp(one_file, working_timestamp)
        if timestamp is None and working_timestamp is not None:
            timestamp = working_timestamp
            parse_md['observationTimeStamp'] = timestamp

        # Check for transformer specific metadata
        transformer_md = None
        if configuration.TRANSFORMER_NAME in parse_md:
            transformer_md = parse_md[configuration.TRANSFORMER_NAME]

        # Prepare our parameters
        check_md = {'timestamp': timestamp,
                    'season': season_name,
                    'experiment': experiment_name,
                    'container_name': None,
                    'target_container_name': None,
                    'trigger_name': None,
                    'context_md': parse_md,
                    'working_folder': args.working_space,
                    'list_files': lambda: file_list
                   }

        return {'check_md': check_md,
                'transformer_md': transformer_md,
                'full_md': parse_md
               }
