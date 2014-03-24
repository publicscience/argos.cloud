"""
Provision
==============

Manages provisioning of instances.
"""

from cloud.command import cmd
import yaml

def provision(app, playbook, key_name, env=None):
    """
    Calls an Ansible playbook to provision
    remote instances.

    This uses the EC2 dynamic inventory script
    to get all EC2 hosts.
    """

    vars = ['app_name={0}'.format(app)]
    if env is not None:
        vars.append('env_name={0}'.format(env))

    command = ['ansible-playbook',
        '-i', 'playbooks/hosts/ec2.py',                 # Use the EC2 dynamic inventory script.
        'playbooks/{0}.yml'.format(playbook),           # Load the playbook.
        '--private-key=keys/{0}.pem'.format(key_name),  # Load the proper key.
        '-e', '""{vars}""'.format(vars=' '.join(vars)), # Set the necessary variables. Double quotes are necessary!
        '-vvvv']                                       # Verbose output for debugging.

    cmd(command)
