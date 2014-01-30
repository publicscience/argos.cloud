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
def ssh(cmd, host=None, user=None, key=None, log=False):
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
    return _call_remote_process(ssh + cmd, log=log)


def scp(local, remote, host=None, user=None, key=None, log=False):
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
    return _call_remote_process(scp, log=log)


def _call_remote_process(cmd, log=False):
    """
    Calls a remote process and retries
    a few times before giving up.
    """
    # Get output of command to check for errors.
    out = _call_process(cmd, log=log)

    # Check if we couldn't connect, and try again.
    tries = 0
    while b'Connection refused' in out and tries < 20:
        time.sleep(2)
        out = _call_process(cmd, log=log)
    return out



def _call_process(cmd, log=False):
    """
    Convenience method for calling a process and getting its results.

    This prints output of the process realtime and stores it in a variable for return.
    It's a bit hacky; stderr is redirected to stdout which itself is piped, so
    both the error and output streams go to the same place. This isn't ideal, but
    treating them separately is tricky because, for instance, if nothing is being sent
    to stderr, and it redirects to its own pipe, then it will block the process.

    Args:
        | cmd (list)    -- list of args for the command.
    """
    #out, err = subprocess.Popen(cmd, stderr=subprocess.PIPE, stdout=subprocess.PIPE).communicate()
    proc = subprocess.Popen(cmd, stderr=subprocess.STDOUT, stdout=subprocess.PIPE)
    output = b''
    while proc.poll() is None:
        line = proc.stdout.readline()
        print(line.decode('utf-8'))
        output += line

    # Captures any missed output.
    # Note that because we are redirecting stderr to stdout,
    # `err` will be None; its output is included in `out`.
    out, err = proc.communicate()
    output += out

    if log:
        logger.info('COMMAND OUTPUT for {0}:\n'.format(' '.join(cmd)) + output.decode('utf-8'))

    return output

