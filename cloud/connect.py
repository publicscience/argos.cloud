"""
Connect
==============

Connect to cloud services.

Note:
The AWS access key and secret key are accessed
from the AWS_ACCESS_KEY and AWS_SECRET_KEY env
variables.
"""

from boto.ec2 import connect_to_region as ec2_connect_to_region
from boto.cloudformation import connect_to_region as cf_connect_to_region

from cloud import config
REGION = config.REGION

def ec2():
    """
    Creates an EC2 connection.
    """
    return ec2_connect_to_region(REGION)

def cf():
    """
    Creates a CloudFormation connection.
    """
    return cf_connect_to_region(REGION)
