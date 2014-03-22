"""
Images
==============

Manages image instances and
the creation of images from them.
"""

from boto.exception import EC2ResponseError
from cloud import connect, util
from cloud.manage import instances, formations

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
        instances.wait_until_ready(image)
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


def create_image_instance(name, base_ami_id):
    conn = connect.cf()

    if formations.get_stack(name) is not None:
        logger.info('Image instance already exists.')
        return

    image_template = open('formations/image.json', 'rb').read()
    init_script = util.template('templates/init.sh')

    logger.info('Creating image instance...')
    conn.create_stack(
            name,
            image_template,
            parameters=[
                ('ImageId', base_ami_id),
                ('UserData', init_script),
                ('InstanceName', name)
            ]
    )

    logger.info('Waiting for image instance to launch...')
    try:
        formations.wait_until_ready(name)
        logger.info('Image instance is ready.')
    except formations.FormationError as e:
        logger.info('There was an error creating the image instance: {0}'.format(e.message))
        logger.info('If the image instance was rolled back, it is likely due to an error with the image instance template.')
        logger.info('Cleaning up...')
        delete_image_instance()


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


