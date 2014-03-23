"""
Name
==============

A module for standardizing names.

Standardized names and tags are crucial
because it is how hosts are remembered.

That is, we don't need to save their hostnames
or IPs if we have standard names with which we can
locate them.
"""

def image(app):
    return '{app}-image'.format(app=app)

def stack(app, env):
    return '{app}-{env}'.format(app=app, env=env)

def instance(app, env, group):
    return '{app}-{env}-{group}'.format(app=app, env=env, group=group)
