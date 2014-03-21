"""
Provision
==============

Manages provisioning of instances.
"""

from cloud.command import cmd

def provision(hosts_filename, role, key):
    cmd(['ansible-playbook', '-i',
        'deploy/hosts/{0}'.format(hosts_filename),
        'deploy/playbooks/{0}.yml'.format(role), '--private-key={0}'.format(key)], log=True)
