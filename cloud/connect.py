"""
Connect
==============

Connect to cloud services.
"""

from boto.ec2.autoscale import AutoScaleConnection
from boto.ec2 import connect_to_region as ec2_connect_to_region
from boto.ec2.cloudwatch import connect_to_region as cw_connect_to_region
from boto.cloudformation import connect_to_region as cf_connect_to_region

import config

REGION = config.REGION
ACCESS_KEY = config.AWS_ACCESS_KEY
SECRET_KEY = config.AWS_SECRET_KEY

def asg():
    """
    Create an AutoScale Group connection.
    """
    return AutoScaleConnection(ACCESS_KEY, SECRET_KEY)


def ec2():
    """
    Creates an EC2 connection.
    """
    return ec2_connect_to_region(
                REGION,
                aws_access_key_id=ACCESS_KEY,
                aws_secret_access_key=SECRET_KEY
           )


def clw():
    """
    Creates a CloudWatch connection.
    """
    return cw_connect_to_region(
                    REGION,
                    aws_access_key_id=ACCESS_KEY,
                    aws_secret_access_key=SECRET_KEY
                 )


def cf():
    """
    Creates a CloudFormation connection.
    """
    return cf_connect_to_region(
                REGION,
                aws_access_key_id=ACCESS_KEY,
                aws_secret_access_key=SECRET_KEY
           )
