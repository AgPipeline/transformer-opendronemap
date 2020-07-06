"""Contains transformer configuration information
"""
from agpypeline.configuration import Configuration


class ConfigurationOdm(Configuration):
    """Configuration information for Open Drone Map"""
    # Silence this error until we have public methods
    # pylint: disable=too-few-public-methods

    # The version number of the transformer
    transformer_version = '2.0'

    # The transformer description
    transformer_description = 'Provides OpenDroneMap functionality'

    # Short name of the transformer
    transformer_name = 'opendronemap'

    # The sensor associated with the transformer
    transformer_sensor = 'rgb'

    # The transformer type (eg: 'rgbmask', 'plotclipper')
    transformer_type = 'opendronemap'

    # The name of the author of the extractor
    author_name = 'Chris Schnaufer'

    # The email of the author of the extractor
    author_email = 'schnaufer@email.arizona.edu'

    # Contributors to this transformer
    contributors = []

    # Repository URI of where the source code lives
    repository = 'https://github.com/AgPipeline/transformer-opendronemap.git'

    # Override flag for disabling the metadata file requirement.
    # Uncomment and set to False to override default behavior
    # metadata_needed = True
