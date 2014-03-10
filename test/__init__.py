"""
Test
==============

Test deployments of different
roles.

Note that this doesn't test any
of the infrastructure provisioning.


This does require some preliminary setup on
the instance/VM you are testing on.

Note that the following instructions assume that
whatever instance (hereafter, "VM") you are using
is a throwaway which will be destroyed after testing.

The recommended OS is Ubuntu 13.04 since this is
what the AWS infrastructure uses.

If starting from a fresh install, make sure you do the following::

    sudo apt-get update && sudo apt-get upgrade
    sudo apt-get install openssh-server

Assuming the VM's username is the same as your local username,
you can use your own SSH key for authenticating. Copy over your public
SSH key by running the following on your local machine::

    ssh-copy-id <username>@<host>

Once that's done, you can check that things work ok with::

    ssh -t -i ~/.ssh/id_rsa.pub -o StrictHostKeychecking=no <username>@<host>

You should be able to login to the VM without having to enter a
password.

Finally, on the VM you need to setup up passwordless sudo::

    sudo visudo

Then enter this as the last line:
    <username> ALL=(ALL) NOPASSWD: ALL

This is dangerous in a real setting, but again, this is assuming you're
working with a throwaway instance.

Now you can test deployments. For example, testing image provisioning::

    >>> import test
    >>> test.deploy('ftseng', '192.168.124.168', key='~/.ssh/id_rsa.pub')
"""

import os
from cloud import util, manage, command

def deploy(user, host, key='~/.ssh/id_rsa.pub', skip_image=False, role=None):
    """
    If using an instance already provisioned as an image,
    specify `skip_image=True` to save time.
    """
    key = os.path.expanduser(key)
    env = 'testing'
    if not skip_image:
        manage.images.setup_image(host, user, key)
    if role == 'master':
        _run_script('setup_master.sh', host, user, key)
    elif role == 'app':
        # Setup the instance as its own master.
        _run_script('setup_master.sh', host, user, key)
        _run_script('setup_app.sh', host, user, key,
                    master_dns=host,
                    db_dns=host,
                    mq_dns=host,
                    env=env)

def _run_script(script_name, host, user, key, **kwargs):
        tmp_script_path = '/tmp/{0}'.format(script_name)

        # Get the script data.
        script = util.load_script('scripts/{0}'.format(script_name), **kwargs)

        # Write the script data to a temporary file.
        script_file = open(tmp_script_path, 'wb')
        script_file.write(script)
        script_file.close()

        # Copy the script to the remote machine.
        command.scp(tmp_script_path, '/tmp/', host=host, user=user, key=key)

        # Execute the remote script.
        command.ssh(['sudo', 'bash', tmp_script_path], host=host, user=user, key=key)

        # Cleanup.
        os.remove(tmp_script_path)
