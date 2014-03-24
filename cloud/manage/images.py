"""
Images
==============

Manages image instances and
the creation of images from them.
"""

from boto.exception import EC2ResponseError

from cloud import connect, command
from cloud.manage import formations, provision

from subprocess import CalledProcessError
from time import sleep

import logging
logger = logging.getLogger(__name__)

def get_image(name):
    """
    Tries to get an existing image.
    """
    logger.info('Looking for an existing image...')
    ec2 = connect.ec2()
    images = ec2.get_all_images(filters={'name': name})
    if images:
        ami_id = images[0].id

        logger.info('Existing image found. ({0})'.format(ami_id))
        return ami_id
    return None


def create_image(name):
    """
    Create an image from an instance.
    """
    ec2 = connect.ec2()

    # Clean up any existing images.
    # Things usually mess up if there
    # is conflicting/existing stuff.
    delete_image(name)

    # Try to use an existing base if specified.
    logger.info('Looking for an existing base instance...')
    base_instance = None
    base_instances = ec2.get_all_instances(filters={'tag-key': 'Name', 'tag-value': name})
    for reservation in base_instances:
        if reservation.instances:
            base_instance = reservation.instances[0]
            if base_instance.update() != 'ready':
                continue
            else:
                logger.info('Existing base instance found.')
                break

    if base_instance is None:
        raise Exception('No base instance named {0} was found. Please create one first.'.format(name))

    try:
        # Create the AMI and get its ID.
        logger.info('Creating image...')
        ami_id = base_instance.create_image(name, description='Base image {0}'.format(name))

        # Wait until instance is ready.
        image = ec2.get_all_images([ami_id])[0]
        wait_until_ready(image)
        logger.info('Created image with id {0}'.format(ami_id))

        # Clean up the image infrastructure.
        delete_image_instance(name)

        logger.info('AMI creation complete. ({0})'.format(ami_id))

        return ami_id

    except EC2ResponseError as e:
        logger.error('Error creating the image, undoing...')

        # Try to undo all the changes.
        delete_image(name)

        # Re-raise the error.
        raise e


def delete_image(name):
    """
    Deregisters the AMI and deletes its snapshot.
    """
    ec2 = connect.ec2()
    images = ec2.get_all_images(filters={'name': name})
    for image in images:
        image_id = image.id
        logger.info('Deleting image with id {0}'.format(image_id))
        try:
            try:
                ec2.deregister_image(image_id, delete_snapshot=True)

            # If the snapshot doesn't exist, just try deregistering the image.
            except AttributeError as e:
                ec2.deregister_image(image_id)

        except EC2ResponseError as e:
            logger.warning('Could not deregister the image. It may already be deregistered.')


def create_image_instance(name, base_ami_id, key_name):
    conn = connect.cf()

    if formations.get_stack(name) is not None:
        logger.info('Image instance already exists.')
        return

    image_template = open('formations/image.json', 'rb').read()

    logger.info('Creating image instance ({0})...'.format(name))
    conn.create_stack(
            name,
            image_template,
            parameters=[
                ('ImageId', base_ami_id),
                ('InstanceName', name),
                ('KeyName', key_name)
            ]
    )

    logger.info('Waiting for image instance to launch...')
    try:
        formations.wait_until_ready(name)
        logger.info('Image instance has launched.')
    except formations.FormationError as e:
        logger.error('There was an error creating the image instance: {0}'.format(e.message))
        logger.error('If the image instance was rolled back, it is likely due to an error with the image instance template.')
        logger.info('Cleaning up...')
        delete_image_instance(name)
        raise Exception('Image instance creation failed.')

    stack = formations.get_stack(name)
    instance_ip = formations.get_output(stack, 'PublicIP')
    instance_host = formations.get_output(stack, 'PublicDNSName')
    logger.info('Instance up at {0} ({1}).'.format(instance_host, instance_ip))

    logger.info('Waiting for SSH to become active...')
    sleep(120)

    # Need to add the instance to known hosts.
    logger.info('Adding instance to known hosts...')
    command.add_to_known_hosts([instance_ip, instance_host])
    logger.info('Image instance successfully created.')

def configure_image_instance(name, app, key_name):
    logger.info('Configuring image instance {0} (this may take awhile)...'.format(name))
    try:
        provision.provision(app, 'image', key_name)
    except CalledProcessError:
        logger.error('There was an error provisioning the image instance. It is likely an error with the Ansible playbook, or perhaps the image instance\'s security group does not have port 22 open, or perhaps an image instance doesn\'t exist.')
        logger.error('The image instance will be preserved so that you can re-run this method to retry configuring.')
        raise Exception('Image instance configuring failed.')

def delete_image_instance(name):
    conn = connect.cf()

    stacks = [stack for stack in conn.describe_stacks() if stack.stack_name == name]
    if len(stacks) == 0:
        logger.info('Image instance is already deleted.')
        return

    conn.delete_stack(name)

    logger.info('Waiting for image instance to delete...')
    formations.wait_until_terminated(name)
    logger.info('Image instance deleted.')


def wait_until_ready(instance):
    """
    Wait until an instance is ready.
    """
    istatus = instance.update()
    while istatus == 'pending':
        sleep(10)
        istatus = instance.update()
