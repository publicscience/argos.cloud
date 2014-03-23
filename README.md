Argos Cloud
===========

Cloud (AWS) management and deployment for
[Argos](https://github.com/publicscience/argos).

## Installation
```
$ virtualenv ~/envs/argos.cloud --no-site-packages
$ source ~/envs/argos.cloud/bin/activate
$ pip install -r requirements.txt
```

## Configuration
You will need to supply a few configuration files and keys:

*Required*
* The AWS key you use to authenticate on EC2 goes into `keys/`. It must
have the same name as the `key_name` you specify in
`playbooks/group_vars/all.yml`. For example, if `key_name=foobar`, you
must have your key at `keys/foobar.pem`.
* Configure `playbooks/group_vars/all.yml` to your needs.
* Configure `playbooks/roles/app/templates/app_config.py` to your needs (this contains your
        application settings).
* Configure `playbooks/roles/app/templates/celery_config.py` to your needs (this contains your
        [Celery](http://www.celeryproject.org/) settings).

You must also set the `AWS_ACCESS_KEY` and `AWS_SECRET_KEY` environment variables.

*Optional*
* Configure other files in `deploy/files/` as needed.
* Configure provisioning variables in `deploy/playbooks/vars/` as
needed.


## Usage
The most important functionality is accessed via the `manage.py` script.

For example:
```
# Activate the virtualenv
$ source ~/envs/argos.cloud/bin/activate

# Commission new staging environment application infrastructure
$ python manage.py staging commission

# Deploy new changes to it.
$ python manage.py staging deploy

# Decommission it (i.e. dismantle the infrastructure)
$ python manage.py staging decommission

# Clean it (i.e. delete the image and its instance)
$ python manage.py staging clean

# For other options, see
$ python manage.py -h
```

## Testing
You can test that the provisioning works with the testing script:
```
# ./test <role>

# Example:
$ ./test app
```

This sets up a [Vagrant](https://www.vagrantup.com/) VM (using a base
Ubuntu 13.10 image) and then provisions it with the Ansible playbook for
the specified role.

## Making Changes
If the needs for the Argos application change, for the most part you
won't need to modify anything in the `cloud/` directory (unless more
comprehensive infrastructural changes are necessary). If its a matter of
a few additional packages, for example, you should only need to modify
the playbooks in `deploy/`, or configuration options in `config.py`.

## About
The application infrastructure runs on Amazon Web Services.

It consists of:
* a database server (AWS RDS)
* a broker server (manages distributed tasks) [currently disabled]
* application servers (in an autoscaling group behind a load balancer)
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
it. Images are environment agnostic, that is, they don't load any
environment-specific information. Thus this image instance can be reused
for different environments's infrastructures.
* The database instance is created.
* The broker instance is created [currently disabled].
* An autoscaling group is created for application instances, using the
image instance as the base.
* An autoscaling group is created for worker instances, using the
image instance as the base [not yet implemented]. 
* The database host name(s) and application host name(s) (and eventually
broker and workers as well) are saved to `deploy/hosts/hosts_<env
name>` so Ansible can provision them (refer to `cloud#make_hosts`). Note
that because Ansible is provisioning these instances from your local
computer (which may need to change at some point), these host names must
be public host names. However, for configuration, e.g. what database
host the application uses, internal host names are used, so this
hosts file keeps track of those for filling in configuration files.

### Deploying
The deploying process works like so:
* The environment hosts file (i.e. `deploy/hosts/hosts_<env name>`) is
updated by finding matching instances on AWS (using their name tags).
* Ansible runs playbooks on these hosts and keeps
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
