"""
Utility
==============

Some utility functions.
"""

from string import Template
import json

def template(filename, **kwargs):
    """
    Loads a script from this directory as bytes.
    This script will be passed as `user-data`.

    Args:
        | filename (str)    -- the filename or path of the script to open.
        | **kwargs          -- optional keyword arguments of a variable and
                            the value to replace it with in the script.

    When you specify `**kwargs`, say `foo=bar`, then every instance of `$foo`
    will be replaced with `bar`.
    """
    templ = open(filename, 'r').read()

    # Substitute for specified vars.
    if kwargs:
        templ = Template(templ).substitute(**kwargs)

    # Turn into bytes.
    return templ.encode('utf-8')

def build_template(names):
    """
    Builds the cloud's template by combining
    individual templates into one Voltron template.
    """

    voltron = {}
    keys = ['Parameters', 'Resources', 'Outputs', 'Mappings']

    # Load all the templates.
    templates = [json.load(open('formations/{0}.json'.format(name))) for name in names]

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
            raise Exception('Merging didn\'t preserve all items, aborting.')

    voltron['AWSTemplateFormatVersion'] = '2010-09-09'
    return json.dumps(voltron).encode('utf-8')

