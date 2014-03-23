"""
Provision
==============

Manages provisioning of instances.
"""

from cloud.command import cmd

def provision(hosts_path, playbook, key_name):
    """
    Calls an Ansible playbook to provision
    remote instances.
    """

    cmd(['ansible-playbook',
        '-i', hosts_path,
        'playbooks/{0}.yml'.format(playbook),
        '--private-key=keys/{0}.pem'.format(key_name), '-vvvv'])

def make_inventory(hosts, group):
    """
    Creates a temporary Ansible hosts
    inventory.
    """
    filename = '/tmp/hosts_{0}'.format(group)

    inventory = open(filename, 'w')
    inventory.write(
            '[{group}]\n{hosts}'.format(
                group=group,
                hosts='\n'.join(hosts)
            )
    )
    inventory.close()

    return filename
