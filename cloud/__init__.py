"""
Cloud
==============

Setup and manage an autoscaling cloud.

Here, an EC2 AutoScale Group is used.

The following are created:
    * AMI of the worker machine
    * Master EC2 instance
    * Security Group
    * Launch Configuration
    * AutoScaling Group
    * Scaling Policies
    * CloudWatch MetricAlarms

And they can all also be dismantled.

Configuration is in `config.ini`.
"""


from cloud.util import get_filepath, load_script
from cloud import manage, config, command

# Logging
from logger import logger
logger = logger(__name__)

# Cloud logging.
import logging
logging.basicConfig(filename='logger/logs/cloud.log', level=logging.DEBUG)

c = config.load('cloud')

DB_PORT = c['DB_PORT']
MQ_PORT = c['MQ_PORT']
MQ_BACKEND_PORT = c['MQ_BACKEND_PORT']
INSTANCE_USER = c['INSTANCE_USER']
KEYPAIR_NAME = c['KEYPAIR_NAME']
PATH_TO_KEY = get_filepath(c['PATH_TO_KEY'])
BASE_AMI_ID = c['BASE_AMI_ID']

def commission(env, min_size=1, max_size=4, instance_type='m1.medium', master_instance_type='m1.small', database_instance_type='m1.medium', broker_instance_type='m1.medium', ssh=False):
    """
    Commission the application infrastructure.

    Args:
        | env (str)                     -- the environment name for this cloud (e.g production, test, qa, etc)
        | min_size (int)                -- the minimum size of the cloud
        | max_size (int)                -- the maximum size of the cloud
        | instance_type (str)           -- the type of instance to use in the cloud.
                                           See: https://aws.amazon.com/ec2/instance-types/instance-details/
        | master_instance_type (str)    -- the type of master instance to use for the cloud.
        | database_instance_type (str)  -- the type of database instance to use for the cloud.
        | broker_instance_type (str)    -- the type of broker (message queue) instance to use for the cloud.
        | ssh (bool)                    -- whether or not to enable SSH access on the app and master instances.
    """
    names = config.cloud_names(env)

    logger.info('Commissioning new application cloud...')

    # Check to see if the AutoScale Group already exists.
    if manage.autoscaling_group_exists(names['AG']):
        logger.warn('The AutoScale Group already exists, exiting!')
        return

    # Get the app image.
    app_ami_id = manage.get_image(names['APP_IMAGE'])

    if app_ami_id is None:
        # CREATE if it doesnt exist
        logger.info('Existing app image wasn\'t found, creating one...')
        manage.create_image_instance(names['APP_IMAGE'], BASE_AMI_ID, KEYPAIR_NAME, INSTANCE_USER, PATH_TO_KEY)
        app_ami_id = manage.create_image(names['APP_IMAGE'])

    # The security groups.
    sec = {}
    for name in ['MASTER', 'AG', 'DB', 'MQ']:
        sec[name] = manage.security_group_name(names[name])

    ports = []
    if ssh:
        logger.warn('SSH is enabled!')
        ports.append(22)

    # Create the security groups.
    # Authorize HTTP port.
    logger.info('Creating the application security group ({0})...'.format(sec['AG']))
    p = ports + [80]
    app_sec_group = manage.create_security_group(sec['AG'], 'The cloud application security group.', ports=p)

    # Authorize database port.
    logger.info('Creating the database security group ({0})...'.format(sec['DB']))
    manage.create_security_group(sec['DB'], 'The cloud database security group.', ports=[DB_PORT], src_group=app_sec_group)

    # Authorize broker port.
    logger.info('Creating the broker security group ({0})...'.format(sec['MQ']))
    manage.create_security_group(sec['MQ'], 'The cloud broker security group.', ports=[MQ_PORT, MQ_BACKEND_PORT], src_group=app_sec_group)

    # Authorize the master.
    logger.info('Creating the master security group ({0})...'.format(sec['MASTER']))
    p = ports + [4505, 4506]
    sec_group = manage.create_security_group(sec['MASTER'], 'The cloud master security group.', ports=p, src_group=app_sec_group)

    logger.info('Using AMI {0}'.format(app_ami_id))

    # Create the infrastructure!
    ms_pub_dns, ms_prv_dns = create_master(names['MASTER'], instance_type=master_instance_type)
    db_pub_dns, db_prv_dns = create_database(names['DB'], env, ms_prv_dns, instance_type=database_instance_type)
    #mq_pub_dns, mq_prv_dns = create_broker(names['MQ'], env, ms_prv_dns, instance_type=broker_instance_type) # Not using distributed tasks at the moment.
    mq_pub_dns, mq_prv_dns = ('111.111.111.111', '111.111.111.111') # fake

    # Replace the $master_dns var in the app init script with the Salt Master DNS name,
    # so app instances (minions) will know where to connect to get provisioned.
    app_init_script = load_script('scripts/setup_app.sh',
            master_dns=ms_prv_dns,
            db_dns=db_prv_dns,
            mq_dns=mq_prv_dns,
            env=env
    )

    # Create the app autoscaling group.
    manage.create_autoscaling_group(
            names['AG'],
            app_ami_id,
            app_init_script,
            names['LC'],
            sec['AG'],
            KEYPAIR_NAME,
            instance_type=instance_type,
            min_size=min_size,
            max_size=max_size
    )

    logger.info('Commissioning complete.')

def decommission(env, preserve_image=True):
    """
    Dismantle the application infrastructure.

    Args:
        | env (str)                 -- the environment name for this cloud (e.g production, test, qa, etc)
        | preserve_image (bool)     -- whether or not to keep
                                       the app image.
    """
    names = config.cloud_names(env)

    logger.info('Decommissioning the application cloud...')

    manage.delete_autoscaling_group(names['AG'], names['LC'])

    logger.info('Deleting the master instance ({0})...'.format(names['MASTER']))
    manage.delete_instances(names['MASTER'])

    #logger.info('Deleting the broker (message queue) instance ({0})...'.format(names['MQ']))
    #manage.delete_instances(names['MQ']) # Not using distributed tasks at the moment

    logger.info('Deleting the database instance ({0})...'.format(names['DB']))
    manage.delete_instances(names['DB'])

    # Delete the security groups.
    for name in ['MASTER', 'AG', 'DB', 'MQ']:
        sec_name = manage.security_group_name(names[name])
        logger.info('Deleting the security group ({0})...'.format(sec_name))
        manage.delete_security_group(sec_name)


    # Delete the worker image.
    if not preserve_image:
        manage.delete_image(names['APP_IMAGE'])

    logger.info('Decommissioning complete.')

def deploy(env):
    """
    Updates all application and worker minion
    instances for this environment.

    Salt handles getting the latest git commit and
    ensuring everything else is provisioned correctly.
    """
    names = config.cloud_names(env)
    master = names['MASTER']
    sec_name = manage.security_group_name(master)
    instances = manage.get_instances(master)
    if not instances:
        logger.warn('A master instance for {0} was not found (looked for {1})'.format(env, master))
    else:
        master_dns = instances[0].public_dns_name
        logger.info('Using key at {0} as {1}.'.format(PATH_TO_KEY, INSTANCE_USER))
        logger.info('Deploying through master instance at {0}'.format(master_dns))

        connection = {
            'host': master_dns,
            'user': INSTANCE_USER,
            'key': PATH_TO_KEY
        }

        manage.open_ssh(sec_name)
        command.ssh(['sudo', 'salt', '-G', 'roles:app', 'state.highstate'], **connection)
        manage.close_ssh(sec_name)

def clean(env):
    """
    Cleans up image instances and images.
    """
    names = config.cloud_names(env)
    name = names['APP_IMAGE']
    manage.delete_image_instance(name)
    manage.delete_image(name)


def create_broker(name, env, master_dns, instance_type='m1.medium', size=50):
    """
    Create the broker/message queue instance (RabbitMQ and Redis).
    """
    logger.info('Creating the broker (message queue) instance ({0})...'.format(name))

    bdm = manage.create_block_device(size=size, delete=True)
    init_script = load_script('scripts/setup_mq.sh',
            master_dns=master_dns,
            env=env
    )

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

def create_database(name, env, master_dns, instance_type='m1.medium', size=500):
    """
    Create the database instance.
    """
    logger.info('Creating the database instance ({0})...'.format(name))

    # Create an EBS (block storage) for the image.
    # Size is in GB.
    # Do NOT delete this volume on termination, since it will have our processed data.
    bdm = manage.create_block_device(size=size, delete=False)
    init_script = load_script('scripts/setup_db.sh',
            master_dns=master_dns,
            env=env
    )

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

def create_master(name, instance_type='m1.medium', size=150):
    """
    Create a Salt Master for provisioning other machines.
    """
    logger.info('Creating the master instance ({0})...'.format(name))

    bdm = manage.create_block_device(size=size, delete=True)
    init_script = load_script('scripts/setup_master.sh')
    instance = manage.create_instance(
            name=name,
            ami_id=BASE_AMI_ID,
            keypair_name=KEYPAIR_NAME,
            security_group_name=manage.security_group_name(name),
            instance_type=instance_type,
            init_script=init_script,
            block_device_map=bdm
    )

    connection = {
            'host': instance.public_dns_name,
            'user': INSTANCE_USER,
            'key': PATH_TO_KEY
    }
    logger.info('Using key at {0} as {1}.'.format(PATH_TO_KEY, INSTANCE_USER))

    # Setup master instance with the Salt state tree.
    # This waits until the instance is ready to accept commands.
    manage.transfer_salt(**connection)

    return instance.public_dns_name, instance.private_dns_name
