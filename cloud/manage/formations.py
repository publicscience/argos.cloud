"""
Formation
==============

Manages CloudFormation stacks.
"""

import time, json
from cloud import connect

import logging
logger = logging.getLogger(__name__)

class FormationError(Exception):
    def __init__(self, message):
        self.message = message

def wait_until_ready(name):
    status = get_stack(name).stack_status

    while status in ['CREATE_IN_PROGRESS', 'UPDATE_IN_PROGRESS']:
        time.sleep(10)
        status = get_stack(name).stack_status

    if status not in ['CREATE_COMPLETE', 'UPDATE_COMPLETE']:
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

def get_output(stack, key):
    """
    Gets an output value from a stack
    for the specified key.
    """
    for output in stack.outputs:
        if output.key == key:
            return output.value
    return None

def build_template(names):
    """
    Builds the cloud's template by combining
    individual templates into one Voltron template.
    """

    voltron = {}
    keys = ['Parameters', 'Resources', 'Outputs', 'Mappings']

    # Load all the templates.
    try:
        templates = [json.load(open('formations/{0}.json'.format(name))) for name in names]
    except ValueError as e:
        logger.error('Error with template: {0}'.format(name))
        raise e

    for key in keys:
        merged = {}
        expected_items = 0
        for template in templates:
            if key in template:
                expected_items += len(template[key])
                if not merged:
                    merged = template[key].copy()
                else:
                    merged.update(template[key])
        voltron[key] = merged
        if len(voltron[key]) != expected_items:
            raise Exception('Merging didn\'t preserve all items for key {0}. There may be conflicting names, exiting!'.format(key))

    voltron['AWSTemplateFormatVersion'] = '2010-09-09'
    return json.dumps(voltron).encode('utf-8')
