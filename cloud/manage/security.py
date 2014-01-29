from boto.exception import EC2ResponseError
from cloud import connect

import logging
logger = logging.getLogger(__name__)

def create_security_group(name, desc='A security group.', ports=[80]):
    """
    Creates or gets an existing security group,
    and authorizes the specified ports.

    Args:
        | name (str)    -- the name of the security group.
        | desc (str)    -- the description of the security group.
        | ports (list)  -- list of the ports to open on the security group.
    """
    ec2 = connect.ec2()
    sec_group = get_security_group(name)
    if not sec_group:
        sec_group = ec2.create_security_group(name, desc)

    # Authorize specified ports.
    for port in ports:
        sec_group.authorize('tcp', port, port, '0.0.0.0/0')

    # Authorize internal communication.
    sec_group.authorize(src_group=sec_group)

    return sec_group


def get_security_group(name):
    """
    Get a security group by name.

    Args:
        | name (str)    -- the name of the security group.
    """
    ec2 = connect.ec2()
    for sg in ec2.get_all_security_groups():
        if sg.name == name:
            return sg


def delete_security_group(name, purge=False):
    """
    Delete a security group by name.

    Args:
        | name (str)    -- name of the security group
        | purge (bool)  -- whether or not to terminate all instances
                           in order to delete the group.
    """
    ec2 = connect.ec2()
    try:
        ec2.delete_security_group(name=name)
    except EC2ResponseError as e:
        # Check if there are still instances in the group.
        sg = get_security_group(name)
        if sg:
            sg_instances = sg.instances()

            # Purge instances.
            if purge:
                logger.info('Security group still has instances. Terminating instances and trying again...')
                for instance in sg_instances:
                    instance.terminate()
                wait_until_terminated(sg_instances)

                # Try deleting again...
                delete_security_group(name)
            else:
                logger.error('Could not delete security group. It still has running instances.')

        else:
            logger.warning('Could not delete security group. It may already be deleted.')


def open_ssh(name):
    rule = ['tcp', 22, 22, '0.0.0.0/0']
    sec_group = get_security_group(name)

    if not check_ssh(sec_group):
        sec_group.authorize(*rule)

    # Wait a little...
    time.sleep(5)

def close_ssh(name):
    rule = ['tcp', 22, 22, '0.0.0.0/0']
    sec_group = get_security_group(name)
    sec_group.revoke(*rule)

def check_ssh(sec_group):
    # Check if SSH is already authorized.
    rule_exists = False
    for r in sec_group.rules:
        if r.from_port == '22' and r.to_port == '22' and r.ip_protocol == 'tcp':
            for grant in r.grants:
                if grant.cidr_ip == '0.0.0.0/0':
                    rule_exists = True
                    break
    return rule_exists

