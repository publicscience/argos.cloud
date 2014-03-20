Argos Cloud
===========

Cloud (AWS) management and deployment for
[Argos](https://github.com/publicscience/argos).

## Installation
```
$ virtualenv-3.3 ~/envs/argos.cloud --no-site-packages
$ source ~/envs/argos.cloud/bin/activate
$ pip install -r requirements.txt
```

## Configuration
You will need to supply a few configuration files and keys:
* The AWS key you use to authenticate on EC2 goes into `cloud/keys/`.
* Configure `cloud/config.ini` to your needs (this contains settings for
        interacting with AWS).
* Configure `deploy/files/<env name>/app_config.py` to your needs (this contains your
        application settings).
* Configure `deploy/files/<env name>celery_config.py` to your needs (this contains your
        [Celery](http://www.celeryproject.org/) settings).


## Usage
The most important functionality is accessed via the `manage.py` script.

For example:
```
# Commission new QA environment application infrastructure
$ python manage.py qa commission

# Deploy new changes to it.
$ python manage.py qa deploy

# Decommission it (i.e. dismantle the infrastructure)
$ python manage.py qa decommission

# Clean it (i.e. delete the image and its instance)
$ python manage.py qa clean

# For other options, see
$ python manage.py -h
```

## Testing
You can test that the provisioning works with the testing script:
```
# ./test.sh <role>

# Example:
$ ./test.sh app
```

This sets up a [Vagrant](https://www.vagrantup.com/) VM (using a base
Ubuntu 13.10 image) and then provisions it with the Ansible playbook for
the specified role.

## Making Changes
If the needs for the Argos application change, for the most part you
won't need to modify anything in the `cloud/` directory (unless more
comprehensive infrastructural changes are necessary). If its a matter of
a few additional packages, for example, you should only need to modify
the playbooks in `deploy/`.

## About
The application infrastructure runs on Amazon Web Services.

It consists of:
* a database server
* a broker server (manages distributed tasks) [currently disabled]
* application servers (in an autoscaling group)
* worker servers (in an autoscaping group) [not yet implemented]

Server configurations and provisioning is handled by
[Ansible](http://www.ansible.com/).

### Commissioning
The commissioning process works like so (everything is provisioned via
Ansible):
* An image instance is created, which is used to generate a base
template for the application and worker instances. For this image, all necessary application
packages are installed, but no configuration files are copied over. The
instance is automatically deleted after the image has been created from
it.
provisions everything else.
* The database instance is created.
* The broker instance is created [currently disabled].
* An autoscaling group is created for application instances, using the
image instance as the base.
* An autoscaling group is created for worker instances, using the
image instance as the base. 

### Deploying
The deploying process works like so:
* Use Ansible to run playbooks on the remote instances and keep
everything up to date.

### Decommissioning
This just deletes everything that was created during the commissioning
process, except for the image (unless its deletion is specified).

### Cleaning
If you hit a snag while generating the image, you may want to clean
things up. This command will do that for you by removing the image
instance (if it still exists) and the image itself (if it still exists).
Normally, commissioning will automatically clean things before it gets
going, but sometimes you have to be explicit.
