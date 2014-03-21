"""
Cloud
==============

Setup and manage an autoscaling cloud.

Here, an EC2 AutoScale Group is used.

The following are created:
    * AMI of the worker machine
    * Security Group
    * Launch Configuration
    * AutoScaling Group
    * Scaling Policies
    * CloudWatch MetricAlarms

And they can all also be dismantled.

Configuration is in `config.ini`.
"""


from cloud.util import get_filepath, template
from cloud import manage, config, command, roles

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
KEYPAIR_NAME = c['KEYPAIR_NAME']
PATH_TO_KEY = get_filepath(c['PATH_TO_KEY'])
BASE_AMI_ID = c['BASE_AMI_ID']

def commission(env, min_size=1, max_size=4, instance_type='m1.medium', database_instance_type='m1.medium', broker_instance_type='m1.medium', ssh=False):
    """
    Commission the application infrastructure.

    Args:
        | env (str)                     -- the environment name for this cloud (e.g production, test, qa, etc)
        | min_size (int)                -- the minimum size of the cloud
        | max_size (int)                -- the maximum size of the cloud
        | instance_type (str)           -- the type of instance to use in the cloud.
                                           See: https://aws.amazon.com/ec2/instance-types/instance-details/
        | database_instance_type (str)  -- the type of database instance to use for the cloud.
        | broker_instance_type (str)    -- the type of broker (message queue) instance to use for the cloud.
        | ssh (bool)                    -- whether or not to enable SSH access on the app instance(s).
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
        manage.create_image_instance(names['APP_IMAGE'], BASE_AMI_ID, KEYPAIR_NAME, PATH_TO_KEY)
        app_ami_id = manage.create_image(names['APP_IMAGE'])

    # The security groups.
    sec = {}
    for name in ['AG', 'DB', 'MQ']:
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
    # Not using distributed tasks at the moment so this is disabled.
    #logger.info('Creating the broker security group ({0})...'.format(sec['MQ']))
    #manage.create_security_group(sec['MQ'], 'The cloud broker security group.', ports=[MQ_PORT, MQ_BACKEND_PORT], src_group=app_sec_group)

    logger.info('Using AMI {0}'.format(app_ami_id))

    # Create the infrastructure!
    db_pub_dns, db_prv_dns = roles.create_database(names['DB'], env, instance_type=database_instance_type)
    #mq_pub_dns, mq_prv_dns = roles.create_broker(names['MQ'], env, instance_type=broker_instance_type) # Not using distributed tasks at the moment.

    # Set the ARGOS_ENV variable for instances,
    # so Ansible knows which config files to load.
    init_script = template('templates/setup_env.sh', env=env)

    # Create the app autoscaling group.
    manage.create_autoscaling_group(
            names['AG'],
            app_ami_id,
            init_script,
            names['LC'],
            sec['AG'],
            KEYPAIR_NAME,
            instance_type=instance_type,
            min_size=min_size,
            max_size=max_size
    )

    logger.info('Deploying to infrastructure...')
    deploy(env);

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

    #logger.info('Deleting the broker (message queue) instance ({0})...'.format(names['MQ']))
    #manage.delete_instances(names['MQ']) # Not using distributed tasks at the moment

    logger.info('Deleting the database instance ({0})...'.format(names['DB']))
    manage.delete_instances(names['DB'])

    # Delete the security groups.
    for name in ['AG', 'DB', 'MQ']:
        sec_name = manage.security_group_name(names[name])
        logger.info('Deleting the security group ({0})...'.format(sec_name))
        manage.delete_security_group(sec_name)


    # Delete the worker image.
    if not preserve_image:
        manage.delete_image(names['APP_IMAGE'])

    logger.info('Decommissioning complete.')


def deploy(env):
    """
    Updates all infrastructure,
    such as the app repository.
    """
    names = config.cloud_names(env)
    sec_names = [manage.security_group_name(names[name]) for name in ['AG', 'DB', 'MQ']]

    # Open SSH so we can reach the instances.
    for sec_name in sec_names:
        manage.open_ssh(sec_name)

    hosts_filename = make_hosts(env)

    for role in ['app', 'database']:
        manage.provision(hosts_filename, role, PATH_TO_KEY)

    # Close SSH when we're done.
    for sec_name in sec_names:
        manage.close_ssh(sec_name)


def make_hosts(env):
    """
    Generates an Ansible host file
    for the infrastructure.
    """
    names = config.cloud_names(env)

    # Get all the instances
    db_instances = manage.get_instances(names['DB'])
    db_public_dns_s = [i.public_dns_name for i in db_instances]
    db_private_dns_s = [i.private_dns_name for i in db_instances]
    # We want the infrastructure to communicate with each other
    # through internal DNS.

    # Not using dist jobs at the moment.
    #mq_instances = manage.get_instances(names['MQ'])
    #mq_public_dns_s = [i.public_dns_name for i in mq_instances]
    # Would also need to add a bit for workers.

    # Get all app autoscaling instances.
    app_instances = manage.get_autoscaling_instances(names['AG'])
    app_public_dns_s = [i.public_dns_name for i in app_instances]

    hosts_filename = 'hosts_{0}'.format(env)
    hosts_file = open('deploy/hosts/{0}'.format(hosts_filename), 'wb')
    hosts_file.write(template('templates/hosts',
            app_hosts='\n'.join(app_public_dns_s),
            db_hosts='\n'.join(db_public_dns_s),
            db_hosts_internal='\n'.join(db_private_dns_s),
            broker_hosts='foo', # placeholder
            worker_hosts='foo'  # placeholder
        ))
    hosts_file.close()

    return hosts_filename


def clean(env):
    """
    Cleans up image instances and images.
    """
    names = config.cloud_names(env)
    name = names['APP_IMAGE']
    manage.delete_image_instance(name)
    manage.delete_image(name)
