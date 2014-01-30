"""
Config
==============

Handles loading configurations.
"""

from configparser import ConfigParser
from cloud.util import get_filepath

config = ConfigParser()
config_file = get_filepath('config.ini')
config.read(config_file)

def load(name):
    """
    Return a section of the config file.

    Args:
        | name (str)    -- the name of the section to return.
    """
    return config[name]


def cloud_names(env):
    """
    Loads the names for the cloud's components.
    """

    name = config['cloud']['CLOUD_NAME']

    names = {
            'LC': '{0}-{1}-launchconfig'.format(name, env),
            'AG': '{0}-{1}-autoscale'.format(name, env),
            'DB': '{0}-{1}-database'.format(name, env),
            'MQ': '{0}-{1}-broker'.format(name, env),
            'MASTER': '{0}-{1}-master'.format(name, env),

            # App image is same across envs so the name can
            # stay the same (so it doesn't get reprovisioned for
            # each environment).
            'APP_IMAGE': '{0}-app_image'.format(name)
    }
    return names


def update():
    """
    Updates the config file by writing
    any changed values.
    """
    config.write(open(config_file, 'w'))

