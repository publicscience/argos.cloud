"""
Command
==============

Interface for commanding the cloud.
"""

import subprocess, time, os

import logging
logger = logging.getLogger(__name__)

def cmd(cmd, log=False):
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

    # Raise an exception if the command exited
    # with a non-zero code.
    if proc.returncode != 0:
        raise subprocess.CalledProcessError(proc.returncode, cmd)

    return output

def add_to_known_hosts(hosts):
    """
    Adds a list of hosts to known hosts.
    """
    known_hosts = open(os.path.expanduser('~/.ssh/known_hosts'), 'a')
    devnull = open(os.devnull, 'w')
    for host in hosts:
        logger.info('Adding {0} to known hosts...'.format(host))
        subprocess.Popen(['ssh-keyscan', '-p', '22', host], stdout=known_hosts, stderr=devnull)
    known_hosts.close()
    devnull.close()
