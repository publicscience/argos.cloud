from boto.exception import EC2ResponseError
from cloud import connect
import time

import logging
logger = logging.getLogger(__name__)

def create_security_group(name, desc='A security group.', ports=[80], src_group=None):
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
        if not check_rule(sec_group, port, src_group=src_group):
            if src_group is not None:
                sec_group.authorize('tcp', port, port, src_group=src_group)
            else:
                sec_group.authorize('tcp', port, port, '0.0.0.0/0')

    # Authorize internal communication.
    try:
        sec_group.authorize(src_group=sec_group)
    except EC2ResponseError:
        logger.info('Ingress security group access already authorized.')

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

def security_group_name(name):
    """
    Helper to generate security group names.
    """
    return '{0}-security'.format(name)


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
    return check_rule(sec_group, 22)

def check_rule(sec_group, port, protocol='tcp', ip='0.0.0.0/0', src_group=None):
    """
    Check if a port has been authorized on a security group.
    It can check that it has been authorized for either an ip or a particular group.

    Args:
        | sec_group         -- the security group to check on
        | port (str)        -- the port to check for
        | protocol (str)    -- the protocol to check (tcp, udp, or icmp)
        | ip (str)          -- the ip to check if is allowed access
        | src_group         -- the security group to check if is allowed access
    """
    rule_exists = False
    if type(port) == int:
        port = str(port)
    for r in sec_group.rules:
        if r.from_port == port and r.to_port == port and r.ip_protocol == protocol:
            for grant in r.grants:
                if src_group is not None:
                    if grant.group_id == src_group.id:
                        rule_exists = True
                        break
                else:
                    if grant.cidr_ip == ip:
                        rule_exists = True
                        break
    return rule_exists

