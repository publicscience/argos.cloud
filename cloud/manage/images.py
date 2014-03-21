"""
Images
==============

Manages image instances and
the creation of images from them.
"""

from boto.exception import EC2ResponseError
from cloud import connect, command
from . import instances, security, storage, provision
from cloud.util import get_filepath, template

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
    base_instances = ec2.get_all_instances(filters={'tag-key': 'name', 'tag-value': name})
    for reservation in base_instances:
        if reservation.instances:
            base_instance = reservation.instances[0]
            if base_instance.update() != 'ready':
                continue
            else:
                logger.info('Existing base instance found.')
                break
        else:
            raise Exception('No base instance named {0} was found. Please create one first.'.format(name))

    try:
        # Create the AMI and get its ID.
        logger.info('Creating image...')
        ami_id = base_instance.create_image(name, description='Base image {0}'.format(name))

        # Wait until worker is ready.
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
    Deregisters the worker AMI and deletes its snapshot.
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

def delete_image_instance(name):
    """
    Decommissions the infrastructure used to
    construct the image.
    """
    logger.info('Cleaning up image infrastructure...')
    instances.delete_instances(name)
    logger.info('Deleting the temporary security group...')
    security.delete_security_group(name, purge=True)
    logger.info('Base instance cleanup complete.')


def create_image_instance(name, ami_id, keypair_name, path_to_key):
    """
    Create the base instance for an image.
    """
    ec2 = connect.ec2()

    # Clean up any existing base instances
    # since it will screw things up.
    delete_image_instance(name)

    try:
        if security.get_security_group(name):
            logger.info('Conflicting security group exists. Deleting...')
            security.delete_security_group(name, purge=True)

        # Create a new security group.
        logger.info('Creating a temporary security group...')
        sec_group = ec2.create_security_group(name, 'Temporary, for the image')

        # Authorize SSH access (temporarily).
        logger.info('Temporarily enabling SSH access to base instance...')
        sec_group.authorize('tcp', 22, 22, '0.0.0.0/0')

        # Create an EBS (block storage) for the image.
        # Size is in GB.
        bdm = storage.create_block_device(size=10, delete=True)

        # Create the instance the AMI will be generated from.
        # *Not* using a user data init script here; instead
        # executing it via ssh.
        # Executing the init script via user data makes it
        # difficult to know when the system is ready to be
        # turned into an image.
        # Running the init script manually means image creation
        # can be executed serially after the script is done.
        logger.info('Creating the base instance...')
        instance = instances.create_instance(
                name=name,
                ami_id=ami_id,
                keypair_name=keypair_name,
                security_group_name=name,
                instance_type='m1.medium',
                block_device_map=bdm
        )

        logger.info('Base instance has launched at {0}. Configuring...'.format(instance.public_dns_name))
        setup_image(host=instance.public_dns_name,
                    key=path_to_key)

        logger.info('Base instance successfully created.')

        return instance

    except EC2ResponseError as e:
        logger.error('Error creating the worker base instance, undoing...')

        # Try to undo all the changes.
        delete_image_instance(name)

        # Re-raise the error.
        raise e

def setup_image(host, key):
    # Create a hosts file with the proper image instance host.
    image_host_file = open('deploy/hosts/image', 'wb')
    image_host_file.write(template('templates/image_host', image_host=host))
    image_host_file.close()

    # Provision the host image.
    logger.info('Using key at {0}.'.format(path_to_key))
    provision.provision('image', 'image', key)
