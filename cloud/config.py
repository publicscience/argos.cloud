"""
Config
==============

Loads the config.

This uses `group_vars/all.yml` as the config,
so that Ansible and this module share the same
values.

The values are exported in uppercase form,
i.e. 'git_repo' becomes `config.GIT_REPO`.
"""

import yaml
import os

# Load from Ansible's "global" vars.
c = yaml.load(open('playbooks/group_vars/all.yml'))

namespace = globals()

for (k, v) in c.items():
    k = k.upper()
    if isinstance(v, str):
        namespace[k] = v.format(**globals())
    else:
        namespace[k] = v
