from cloud import connect, manage, config, name, command

from boto.exception import BotoServerError

# Logging
from cloud.logger import logger, notify
logger = logger(__name__)
import logging
logger = logging.getLogger(__name__)

DEFAULT_INSTANCE_TYPE='m3.medium'
TEMPLATES = ['global', 'bucket', 'api', 'front', 'database', 'knowledge', 'collector']

def update(env, min_size=1, max_size=4, instance_type=DEFAULT_INSTANCE_TYPE, db_instance_type='db.m1.medium', knowledge_instance_type='m3.large', collector_instance_type='c3.large', db_size=250):
    conn = connect.cf()
    app = config.APP_NAME
    stack_name = name.stack(app, env)
    img_name = name.image(app)

    logger.info('Updating application cloud (app={0}, stack_name={1}, image_name={2})...'.format(app, stack_name, img_name))

    stacks = [stack for stack in conn.describe_stacks() if stack.stack_name == stack_name]
    if len(stacks) == 0:
        logger.info('Infrastructure doesn\'t exist yet. Please commission it first.')
        return

    app_ami_id = get_or_create_image(img_name)

    logger.info('UPDATING INFRASTRUCTURE ===================================================')
    logger.info('Merging individual templates: {0}'.format(TEMPLATES))
    template = manage.formations.build_template(TEMPLATES)

    parameters = build_parameters(env, app, app_ami_id, instance_type, knowledge_instance_type, collector_instance_type, db_size, db_instance_type)

    logger.info('Updating the infrastructure...')
    logger.info('You can see its progress (and debug issues more easily) by checking out [https://console.aws.amazon.com/cloudformation/]')

    try:
        conn.update_stack(
                stack_name,
                template,
                parameters=parameters
        )
    except BotoServerError as e:
        if e.message == 'No updates are to be performed.':
            logger.info('There are no updates to make! If you wish to deploy non-infrastructural updates, use the `deploy` command.')
            return
        else:
            raise e

    try:
        manage.formations.wait_until_ready(stack_name)

    except manage.formations.FormationError as e:
        logger.info('There was an error updating the infrastructure: {0}'.format(e.message))
        logger.info('If the stack was rolled back, it is likely due to an error with the template.')
        logger.info('Cleaning up...')
        manage.formations.wait_until_rolled_back(stack_name)
        return

    # Return the output from the stack creation.
    stack = manage.formations.get_stack(stack_name)
    logger.info('Stack output: {0}'.format(stack.outputs))
    logger.info('UPDATING INFRASTRUCTURE =================================================== DONE')

    logger.info('CONFIGURING INFRASTRUCTURE ================================================')
    logger.info('Adding instances to known hosts...')
    targets = [manage.formations.get_output(stack, key) for key in ['KnowledgePublicIP', 'KnowledgePublicDNS', 'APIServerPublicIP', 'APIServerPublicDNS', 'FrontServerPublicIP', 'FrontServerPublicDNS', 'CollectorPublicIP', 'CollectorPublicDNS']]
    print(targets)
    command.add_to_known_hosts(targets)

    deploy(env)
    logger.info('CONFIGURING INFRASTRUCTURE ================================================ DONE')

    logger.info('Stack output: {0}'.format(stack.outputs))

    logger.info('Updating complete.')
    notify.notify('Updating for [{0}] complete.'.format(env))
    return stack.outputs

def commission(env, min_size=1, max_size=4, instance_type=DEFAULT_INSTANCE_TYPE, db_instance_type='db.m1.medium', knowledge_instance_type='m3.large', collector_instance_type='c3.large', db_size=250):
    conn = connect.cf()
    app = config.APP_NAME
    stack_name = name.stack(app, env)
    img_name = name.image(app)

    logger.info('Commissioning new application cloud (app={0}, stack_name={1}, image_name={2})...'.format(app, stack_name, img_name))

    app_ami_id = get_or_create_image(img_name)

    logger.info('SPAWNING INFRASTRUCTURE ===================================================')
    if manage.formations.get_stack(stack_name) is not None:
        logger.info('Infrastructure for the environment [{0}] already exists.'.format(env))
    else:
        logger.info('Merging individual templates: {0}'.format(TEMPLATES))
        template = manage.formations.build_template(TEMPLATES)

        parameters = build_parameters(env, app, app_ami_id, instance_type, knowledge_instance_type, collector_instance_type, db_size, db_instance_type)

        logger.info('Creating the infrastructure...')
        logger.info('You can see its progress (and debug issues more easily) by checking out [https://console.aws.amazon.com/cloudformation/]')
        conn.create_stack(
                stack_name,
                template,
                parameters=parameters
        )

        try:
            manage.formations.wait_until_ready(stack_name)

        except manage.formations.FormationError as e:
            logger.info('There was an error creating the infrastructure: {0}'.format(e.message))
            logger.info('If the stack was rolled back, it is likely due to an error with the template.')
            logger.info('Cleaning up...')
            manage.formations.wait_until_rolled_back(stack_name)
            decommission(stack_name)
            return

    # Return the output from the stack creation.
    stack = manage.formations.get_stack(stack_name)
    logger.info('Stack output: {0}'.format(stack.outputs))
    logger.info('SPAWNING INFRASTRUCTURE =================================================== DONE')

    logger.info('CONFIGURING INFRASTRUCTURE ================================================')
    logger.info('Adding instances to known hosts...')
    targets = [manage.formations.get_output(stack, key) for key in ['KnowledgePublicIP', 'KnowledgePublicDNS', 'APIServerPublicIP', 'APIServerPublicDNS', 'FrontServerPublicIP', 'FrontServerPublicDNS', 'CollectorPublicIP', 'CollectorPublicDNS']]
    command.add_to_known_hosts(targets)

    deploy(env)
    logger.info('CONFIGURING INFRASTRUCTURE ================================================ DONE')

    logger.info('Stack output: {0}'.format(stack.outputs))

    logger.info('Commissioning complete.')
    notify.notify('Commissioning for [{0}] complete.'.format(env))
    return stack.outputs

def decommission(env):
    conn = connect.cf()
    app = config.APP_NAME
    stack_name = name.stack(app, env)

    stacks = [stack for stack in conn.describe_stacks() if stack.stack_name == stack_name]
    if len(stacks) == 0:
        logger.info('Infrastructure is already decommissioned.')
        return

    logger.info('Decommissioning...')
    conn.delete_stack(stack_name)
    manage.formations.wait_until_terminated(stack_name)
    logger.info('Decommissioning complete.')
    notify.notify('Decommissioning for [{0}] complete.'.format(env))

def deploy(env, roles=['knowledge', 'api', 'front', 'collector']):
    app = config.APP_NAME
    key_name = config.KEY_NAME

    for playbook in roles:
        logger.info('Configuring with playbook [{0}]'.format(playbook))
        manage.provision.provision(app, playbook, key_name, env=env)

    notify.notify('Deployment for [{0}] complete.'.format(env))

def clean():
    """
    Cleans up image instances and images.
    """
    app = config.APP_NAME
    img_name = name.image(app)
    manage.images.delete_image_instance(img_name)
    manage.images.delete_image(img_name)


def get_or_create_image(img_name):
    # Get the app image.
    logger.info('CHECKING IMAGE ============================================================')
    app_ami_id = manage.images.get_image(img_name)

    if app_ami_id is None:
        # CREATE if it doesnt exist
        logger.info('Existing app image wasn\'t found, creating one...')
        logger.info('BAKING IMAGE ==============================================================')
        manage.images.create_image_instance(img_name, config.BASE_AMI, config.KEY_NAME)
        manage.images.configure_image_instance(img_name, app, config.KEY_NAME)
        app_ami_id = manage.images.create_image(img_name)
        logger.info('BAKING IMAGE ============================================================== DONE')
    logger.info('CHECKING IMAGE ============================================================ DONE')

    return app_ami_id

def build_parameters(env, app, app_ami_id, instance_type, knowledge_instance_type, collector_instance_type, db_size, db_instance_type):
    parameters = [
        # Refer to the formation JSON templates for
        # details on these parameters.

        # Global
        ('AppName', app),
        ('EnvironmentName', env),
        ('BaseImageId', config.BASE_AMI),
        ('KeyName', config.KEY_NAME),

        # Front group
        ('FrontServerInstanceType', instance_type),

        # API group
        ('APIServerInstanceType', instance_type),
        #('APIInstancePort', 8888),             # Port the ELB forwards to on the instances.
        #('APIMinSize', min_size),
        #('APIMaxSize', max_size),

        ('AppImageAMI', app_ami_id),

        # Knowledge
        ('KnowledgeInstanceType', knowledge_instance_type),

        # Collector
        ('CollectorInstanceType', collector_instance_type),

        # Database
        ('DBName', config.DB_NAME), # dashes must be underscore for psql
        ('DBUser', config.DB_USER),
        ('DBPassword', config.DB_PASS),
        ('DBAllocatedStorage', db_size),                  # in GB
        ('DBInstanceClass', db_instance_type),
        ('MultiAZ', 'false') # no multi-AZ for now since its overkill and almost double the price
    ]
    return parameters
