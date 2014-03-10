"""
Instances
==============

Manages instances.
"""

import time
from cloud import connect

import logging
logger = logging.getLogger(__name__)

def create_instance(name, ami_id, keypair_name, security_group_name, instance_type='m1.medium', block_device_map=None, init_script=None):
    """
    Convenience method for creating a new instance.

    Args:
        | name (str)                -- the name of the instance
        | ami_id (str)              -- the AMI ID of the instance
        | keypair_name (str)        -- name of the keypair
        | security_group_name (str) -- the name of the security group
        | instance_type (str)       -- the instance type (default: m1.medium)
        | block_device_map          -- a block device map (optional)
        | init_script               -- an initialization script (optional)
    """
    ec2 = connect.ec2()

    reservations = ec2.run_instances(
                       ami_id,
                       key_name=keypair_name,
                       security_groups=[security_group_name],
                       instance_type=instance_type,
                       user_data=init_script,
                       block_device_map=block_device_map
                   )
    instance = reservations.instances[0]

    logger.info('Waiting for instance {0} to launch...'.format(name))
    wait_until_ready(instance)
    logger.info('Instance {0} has launched at {1}'.format(name, instance.public_dns_name))

    # Tag the instance with a name so we can find it later.
    instance.add_tag('name', name)
    return instance


def get_instances(name):
    """
    Gets running instances tagged with
    the specified name.
    """
    ec2 = connect.ec2()
    reservations = ec2.get_all_instances(filters={'tag-key': 'name', 'tag-value': name})
    instances = []
    for reservation in reservations:
        instances += [i for i in reservation.instances if i.update() != 'terminated']
    return instances

def delete_instances(name):
    instances = get_instances(name)
    for i in instances:
        i.terminate()
    wait_until_terminated(instances)

def wait_until_ready(instance):
    """
    Wait until an instance is ready.
    """
    istatus = instance.update()
    while istatus == 'pending':
        time.sleep(10)
        istatus = instance.update()


def wait_until_terminated(instance):
    """
    Wait until an instance or instances is terminated.
    """
    if isinstance(instance, list):
        instances = instance
        while len(instances) > 0:
            time.sleep(10)
            instances = [i for i in instances if i.update() != 'terminated']
    else:
        istatus = instance.update()
        while istatus == 'shutting-down':
            time.sleep(10)
            istatus = instance.update()
