"""
Roles
==============

Handles specific role-instances.
"""

from cloud.util import get_filepath, template
from cloud import manage, config

# Logging
from logger import logger
logger = logger(__name__)

# Cloud logging.
import logging
logging.basicConfig(filename='logger/logs/cloud.log', level=logging.DEBUG)

c = config.load('cloud')
KEYPAIR_NAME = c['KEYPAIR_NAME']
BASE_AMI_ID = c['BASE_AMI_ID']

def create_broker(name, env, instance_type='m1.medium', size=50):
    """
    Create the broker/message queue instance (RabbitMQ and Redis).
    """
    logger.info('Creating the broker (message queue) instance ({0})...'.format(name))

    bdm = manage.create_block_device(size=size, delete=True)
    init_script = template('templates/setup_env.sh', env=env)

    instance = manage.create_instance(
            name=name,
            ami_id=BASE_AMI_ID,
            keypair_name=KEYPAIR_NAME,
            security_group_name=manage.security_group_name(name),
            instance_type=instance_type,
            init_script=init_script,
            block_device_map=bdm
    )

    return instance.public_dns_name, instance.private_dns_name


def create_database(name, env, instance_type='m1.medium', size=500):
    """
    Create the database instance.
    """
    logger.info('Creating the database instance ({0})...'.format(name))

    # Create an EBS (block storage) for the image.
    # Size is in GB.
    # Do NOT delete this volume on termination, since it will have our processed data.
    bdm = manage.create_block_device(size=size, delete=False)
    init_script = template('templates/setup_env.sh', env=env)

    instance = manage.create_instance(
            name=name,
            ami_id=BASE_AMI_ID,
            keypair_name=KEYPAIR_NAME,
            security_group_name=manage.security_group_name(name),
            instance_type=instance_type,
            init_script=init_script,
            block_device_map=bdm
    )

    return instance.public_dns_name, instance.private_dns_name
