"""
Salt
==============

Manages the transferring and clean up
of the Salt state tree.
"""

from cloud import command
from cloud.util import get_filepath
import time

import logging
logger = logging.getLogger(__name__)

def transfer_salt(host, user, key):
    """
    Transfer Salt state and other necessary files
    to the specified host.

    Args:
        | host (str)    -- the host to connect to.
        | user (str)    -- the user to connect as.
        | key (str)  -- the path to the key to connect with.
    """

    # Wait for SSH to become active...
    time.sleep(10)

    # Copy over Salt state tree to the host.
    # First have to move to a temporary directory.
    # '-o StrictHostKeyChecking no' automatically adds
    # the instance to SSH known hosts.
    logger.info('Secure copying Salt state tree to /tmp/salt on the instance...')
    salt_path = get_filepath('../deploy/')
    command.scp(salt_path, '/tmp/salt', host=host, user=user, key=key)

    # Move it to the real directory.
    logger.info('Moving Salt state tree to /srv/salt on the instance...')
    command.ssh(['sudo', 'mv', '/tmp/salt/*', '/srv'], host=host, user=user, key=key)


def clean_salt(host, user, key):
    """
    Cleans up the Salt state tree.
    """
    command.ssh(['sudo', 'rm', '-rf', '/srv/salt'], host=host, user=user, key=key)
    command.ssh(['sudo', 'rm', '-rf', '/srv/pillar'], host=host, user=user, key=key)
