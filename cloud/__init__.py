from cloud import connect, manage, util, config

# Logging
from cloud.logger import logger
logger = logger(__name__)
import logging
logger = logging.getLogger(__name__)

def commission(env, min_size=1, max_size=4, instance_type='m1.medium', db_instance_type='db.m1.large'):
    conn = connect.cf()
    name = '{app}-{env}'.format(app=config.APP_NAME, env=env)
    img_name = config.IMAGE_NAME

    logger.info('Commissioning new application cloud...')

    # Get the app image.
    app_ami_id = manage.images.get_image(img_name)

    if app_ami_id is None:
        # CREATE if it doesnt exist
        logger.info('Existing app image wasn\'t found, creating one...')
        manage.images.create_image_instance(img_name, config.BASE_AMI, config.KEY_NAME)
        app_ami_id = manage.images.create_image(img_name)

    if manage.formations.get_stack(name) is not None:
        logger.info('Infrastructure for the environment [{0}] already exists.'.format(env))
        return

    templates = ['bucket', 'app', 'database']
    logger.info('Merging individual templates: {0}'.format(templates))
    template = manage.formations.build_template(templates)

    #print(conn.estimate_template_cost(template))
    init_script = util.template('templates/init.sh', env=env)

    logger.info('Creating the infrastructure...')
    conn.create_stack(
            name,
            template,
            parameters=[
                # Refer to the formation JSON templates for
                # details on these parameters.

                # App group
                ('InstanceType', instance_type),
                ('InstancePort', 8888),             # Port the ELB forwards to on the instances.
                ('MinSize', min_size),
                ('MaxSize', max_size),
                ('ImageAMI', app_ami_id),

                # Database
                ('DBName', name.replace('-', '_')), # dashes must be underscore for psql
                ('DBUser', config.DB_USER),
                ('DBPassword', config.DB_PASS),
                ('DBAllocatedStorage', 50),                  # in GB
                ('DBInstanceClass', db_instance_type),
                ('EC2SecurityGroup', 'default'),    # for now, use the default sec group. should be creating one for the app group i think.
                ('MultiAZ', 'true')
            ]
    )

    try:
        manage.formations.wait_until_ready(name)
        logger.info('Commissioning complete.')

        # Return the output from the stack creation.
        stack = manage.formations.get_stack(name)
        logger.info('Stack output: {0}'.format(stack.outputs))

        # TO DO: Ansible provisioning should happen here.
        # That is, database hosts and what not need to be added to config files.

        return stack.outputs
    except manage.formations.FormationError as e:
        logger.info('There was an error creating the infrastructure: {0}'.format(e.message))
        logger.info('If the stack was rolled back, it is likely due to an error with the template.')
        logger.info('Cleaning up...')
        manage.formations.wait_until_rolled_back(name)
        decommission(name)

def decommission(env):
    conn = connect.cf()
    name = '{app}-{env}'.format(app=config.APP_NAME, env=env)

    stacks = [stack for stack in conn.describe_stacks() if stack.stack_name == name]
    if len(stacks) == 0:
        logger.info('Infrastructure is already decommissioned.')
        return

    logger.info('Decommissioning...')
    conn.delete_stack(name)
    manage.formations.wait_until_terminated(name)
    logger.info('Decommissioning complete.')

def deploy(env):
    pass

def clean():
    """
    Cleans up image instances and images.
    """
    img_name = config.IMAGE_NAME
    manage.images.delete_image_instance(img_name)
    manage.images.delete_image(img_name)
