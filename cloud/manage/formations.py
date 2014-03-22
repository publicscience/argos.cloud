"""
Formation
==============

Manages CloudFormation stacks.
"""

import time
from cloud import connect

import logging
logger = logging.getLogger(__name__)

class FormationError(Exception):
    def __init__(self, message):
        self.message = message

def wait_until_ready(name):
    status = get_stack(name).stack_status

    while status == 'CREATE_IN_PROGRESS':
        time.sleep(10)
        status = get_stack(name).stack_status

    if status != 'CREATE_COMPLETE':
        raise FormationError('Formation creation failed, status was {0}'.format(status))

def wait_until_terminated(name):
    stack = get_stack(name)

    while stack is not None:
        time.sleep(10)
        stack = get_stack(name)

def wait_until_rolled_back(name):
    status = get_stack(name).stack_status

    while status == 'ROLLBACK_IN_PROGRESS':
        time.sleep(10)
        status = get_stack(name).stack_status

def get_stack(name):
    """
    Get a stack by name.

    This does not retrieve deleted stacks.
    For that, use `connect.cf().list_stacks()`,
    though this returns minimal info about
    each stack (only `stack.stack_name` and
    `stack.stack_status`)

    Stack names are unique per AWS account,
    so we only expect to get one.
    """
    conn = connect.cf()
    stacks = [stack for stack in conn.describe_stacks() if stack.stack_name == name]
    if len(stacks) == 0:
        return None
    return stacks[0]
