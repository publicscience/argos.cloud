from cloud import connect, manage, config, name, command

# Logging
from cloud.logger import logger
logger = logger(__name__)
import logging
logger = logging.getLogger(__name__)

def commission(env, min_size=1, max_size=4, instance_type='m3.xlarge', db_instance_type='db.m1.large', knowledge_instance_type='m3.xlarge'):
    conn = connect.cf()
    app = config.APP_NAME
    stack_name = name.stack(app, env)
    img_name = name.image(app)

    logger.info('Commissioning new application cloud (app={0}, stack_name={1}, image_name={2})...'.format(app, stack_name, img_name))

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

    logger.info('SPAWNING INFRASTRUCTURE ===================================================')
    if manage.formations.get_stack(stack_name) is not None:
        logger.info('Infrastructure for the environment [{0}] already exists.'.format(env))
    else:
        templates = ['global', 'bucket', 'app', 'database', 'knowledge']
        logger.info('Merging individual templates: {0}'.format(templates))
        template = manage.formations.build_template(templates)

        # Load init script, which sets up ansible-pull.
        init_script = open('playbooks/roles/common/files/init.sh', 'r').read().encode('utf-8')

        logger.info('Creating the infrastructure...')
        logger.info('You can see its progress (and debug issues more easily) by checking out [https://console.aws.amazon.com/cloudformation/]')
        conn.create_stack(
                stack_name,
                template,
                parameters=[
                    # Refer to the formation JSON templates for
                    # details on these parameters.

                    # Global
                    ('AppName', app),
                    ('EnvironmentName', env),
                    ('BaseImageId', config.BASE_AMI),
                    ('KeyName', config.KEY_NAME),

                    # App (webserver) group
                    ('WebServerInstanceType', instance_type),
                    #('InstancePort', 8888),             # Port the ELB forwards to on the instances.
                    #('MinSize', min_size),
                    #('MaxSize', max_size),
                    ('AppImageAMI', app_ami_id),

                    # Knowledge
                    ('KnowledgeInstanceType', knowledge_instance_type),

                    # Database
                    ('DBName', config.DB_NAME), # dashes must be underscore for psql
                    ('DBUser', config.DB_USER),
                    ('DBPassword', config.DB_PASS),
                    ('DBAllocatedStorage', 50),                  # in GB
                    ('DBInstanceClass', db_instance_type),
                    ('MultiAZ', 'true')
                ]
        )

        try:
            manage.formations.wait_until_ready(stack_name)

        except manage.formations.FormationError as e:
            logger.info('There was an error creating the infrastructure: {0}'.format(e.message))
            logger.info('If the stack was rolled back, it is likely due to an error with the template.')
            logger.info('Cleaning up...')
            manage.formations.wait_until_rolled_back(stack_name)
            decommission(stack_name)

    # Return the output from the stack creation.
    stack = manage.formations.get_stack(stack_name)
    logger.info('Stack output: {0}'.format(stack.outputs))
    logger.info('SPAWNING INFRASTRUCTURE =================================================== DONE')

    logger.info('CONFIGURING INFRASTRUCTURE ================================================')
    logger.info('Adding instances to known hosts...')
    targets = [manage.formations.get_output(stack, key) for key in ['KnowledgePublicIP', 'KnowledgePublicDNS', 'WebServerPublicIP', 'WebServerPublicDNS']]
    command.add_to_known_hosts(targets)

    deploy(env)
    logger.info('CONFIGURING INFRASTRUCTURE ================================================ DONE')

    logger.info('Stack output: {0}'.format(stack.outputs))
    logger.info('Commissioning complete.')
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

def deploy(env):
    app = config.APP_NAME
    key_name = config.KEY_NAME

    for playbook in ['knowledge', 'app']:
        logger.info('Configuring with playbook [{0}]'.format(playbook))
        manage.provision.provision(app, playbook, key_name, env=env)

def clean():
    """
    Cleans up image instances and images.
    """
    app = config.APP_NAME
    img_name = name.image(app)
    manage.images.delete_image_instance(img_name)
    manage.images.delete_image(img_name)
