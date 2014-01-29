from boto.ec2.blockdevicemapping import BlockDeviceMapping, BlockDeviceType

def create_block_device(size=10, delete=False):
    """
    Create a BlockDeviceMapping and a BlockDevice.

    Args:
        | size (int)        -- size in GB for the volume
        | delete (bool)     -- whether or not to delete the volume
                               when its instance has terminated.
    """
    block_device = BlockDeviceType(size=size, delete_on_termination=delete)
    bdm = BlockDeviceMapping()
    bdm['/dev/sda1'] = block_device
    return bdm
