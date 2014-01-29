"""
Command
==============

Interface for commanding the cloud.
"""

import subprocess, time
from os.path import join
from cloud.util import get_filepath, load_script
from cloud.manage import get_security_group

import logging
logger = logging.getLogger(__name__)


# Eventually Fabric can replace all the below.
def ssh(cmd, host=None, user=None, key=None):
    """
    Convenience method for SSHing.

    Args:
        | cmd (list)    -- a list of the command parameters.
        | host (str)    -- the ip or hostname to connect to.
        | user (str)    -- the user to connect as.
        | key (str)     -- path to the key for authenticating.
    """
    ssh = [
        'ssh',
        '-t',
        '-i',
        key,
        '-o',
        'StrictHostKeyChecking=no',
        '{0}@{1}'.format(user, host)
    ]
    return _call_remote_process(ssh + cmd)


def scp(local, remote, host=None, user=None, key=None):
    """
    Convenience method for SCPing.

    Args:
        | local (str)   -- path to local file or directory to copy.
        | remote (str)  -- path to remote file or directory to copy to.
        | host (str)    -- the ip or hostname to connect to.
        | user (str)    -- the user to connect as.
        | key (str)     -- path to the key for authenticating.
    """
    scp = [
            'scp',
            '-r',
            '-o',
            'StrictHostKeyChecking=no',
            '-i',
            key,
            local,
            '{0}@{1}:{2}'.format(user, host, remote)
    ]
    return _call_remote_process(scp)


def _call_remote_process(cmd):
    """
    Calls a remote process and retries
    a few times before giving up.
    """
    # Get output of command to check for errors.
    out, err = _call_process(cmd)

    # Check if we couldn't connect, and try again.
    tries = 0
    while b'Connection refused' in err and tries < 20:
        time.sleep(2)
        out, err = _call_process(cmd)
    return out, err



def _call_process(cmd, log=False):
    """
    Convenience method for calling a process and getting its results.

    Args:
        | cmd (list)    -- list of args for the command.
    """
    out, err = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    if out: logger.info(out.decode('utf-8'))
    if err: logger.info(err.decode('utf-8'))
    return out, err

