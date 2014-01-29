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
        interacting with AWS)
* Configure `deploy/config.py` to your needs (this contains your
        application settings)
* Configure `deploy/celery_config.py` to your needs (this contains your
        [Celery](http://www.celeryproject.org/) settings)
* Configure `deploy/mail_config.py` to your needs (this contains your
        email settings)



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

# For other options, see
$ python manage.py -h
```

## About
The application infrastructure runs on Amazon Web Services.

It consists of:
* a database server
* a broker server (manages distributed tasks) [currently disabled]
* application servers (in an autoscaling group)
* worker servers (in an autoscaping group) [not yet implemented]
* a master server (provisions application and worker servers)

Server configurations and provisioning is handled by
[SaltStack](http://www.saltstack.com/).

### Commissioning
The commissioning process works like so:
* An image instance is created, which is used to generate a base
template for the application and worker instances. This instance
provisions itself with SaltStack, then removes the Salt state trees (to
scrub it of sensitive data). For this image, all necessary application
packages are installed, but no configuration files are copied over.
* The master instance is created; this is the Salt master which
provisions everything else.
* The database instance is created; it is provisioned by the master
instance.
* The broker instance is created; it is provisioned by the master
instance. [currently disabled]
* An autoscaling group is created for application instances, using the
image instance as the base. As they are spun up they will query the Salt
master to be provisioned to the latest state.
* An autoscaling group is created for worker instances, using the
image instance as the base. As they are spun up they will query the Salt
master to be provisioned to the latest state. [not yet implemented]

### Deploying
The deploying process works like so:
* The Salt master instance provisions the application and worker
instances to the latest state. This process involves pulling the latest
commit from GitHub on all the application and worker instances.

### Decommissioning
This just deletes everything that was created during the commissioning
process, except for the image (unless its deletion is specified).
