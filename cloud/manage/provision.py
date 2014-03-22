"""
Provision
==============

Manages provisioning of instances.
"""

from cloud.command import cmd
import time

def provision(hosts_filename, role, key):
    # Wait for SSH to become active...
    time.sleep(10)
    cmd(['ansible-playbook', '-i',
        'deploy/hosts/{0}'.format(hosts_filename),
        'deploy/playbooks/{0}.yml'.format(role),
        '--private-key={0}'.format(key), '-vvvv'], log=True)
