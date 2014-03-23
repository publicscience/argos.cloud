"""
Utility
==============

Some utility functions.
"""

from string import Template

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
