Argos Cloud
===========

Cloud (AWS) management and deployment for
[Argos](https://github.com/publicscience/argos).

This provisions and configures infrastructure and handles
deployment of updates and so on.

## Installation
```
$ virtualenv-2.7 ~/envs/argos.cloud --no-site-packages
$ source ~/envs/argos.cloud/bin/activate
$ pip install -r requirements.txt
```

## Configuration
You will need to supply a few configuration files and keys:

*Required*
* The AWS key you use to authenticate on EC2 goes into `keys/`. It must
have the same name as the `key_name` you specify in
`playbooks/group_vars/all.yml`. For example, if `key_name=foobar`, you
must have your key at `keys/foobar.pem`. Ansible needs this to access
your instances and configure them.
* Configure `playbooks/group_vars/all.yml` to your needs.
* Configure `playbooks/roles/app/templates/app_config.py` to your needs (this contains your
        application settings).
* Configure `playbooks/roles/app/templates/celery_config.py` to your needs (this contains your
        [Celery](http://www.celeryproject.org/) settings).
* If you don't already have one, create a Boto config file at `~/.boto` with your AWS access credentials, e.g:

```
[Credentials]
aws_access_key_id = YOURACCESSKEY
aws_secret_access_key = YOURSECRETKEY
```


*Optional*
* Configure other playbook files (`playbooks/roles/*/files/`)
* Configure provisioning variables in `playbooks/roles/*/vars/` as
needed.


You might also want to add this to your SSH config to help prevent
timeouts/broken pipes for especially long-running tasks:
```
# ~/.ssh/config

ServerAliveInterval 120
TCPKeepAlive no
```

---

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

# Update the infrastructure.
$ python manage.py staging update

# Decommission it (i.e. dismantle the infrastructure)
$ python manage.py staging decommission

# Clean it (i.e. delete the image and its instance)
$ python manage.py staging clean

# For other options, see
$ python manage.py -h
```

---

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

---

## Making Changes
If the needs for the Argos application change, for the most part you
won't need to modify anything in the `cloud/` directory (unless more
comprehensive infrastructural changes are necessary). If its a matter of
a few additional packages, for example, you should only need to modify
the playbooks in `playbooks/`, or global configuration options in
`playbooks/group_vars/all.yml`.

If you need to change infrastructural resources, look in `formations/`.
Note that all the formation templates except for `formations/image.json`
are merged into a single mega-template, and because of these you should
take care not to have conflicting resource logical ids (i.e. don't call
a resource `Ec2Instance` in multiple templates, better to be specific,
such as `KnowledgeEc2Instance`, and `BrokerEc2Instance`). The upside to
this is that you can refer to variables/resources/parameters/etc in
the other templates.

---

## About
The application infrastructure runs on Amazon Web Services.

It consists of:
* a database server (AWS RDS)
* application servers (~~in an autoscaling group behind a load balancer~~ during prototyping, just a single instance. See below.)
* a knowledge server (running Apache Fuseki and Stanford NER)
* a broker server (manages distributed tasks) [*currently disabled*]
* worker servers (in an autoscaping group) [*currently disabled*]

Infrastructure creation is handled by AWS's CloudFormation in the `cloud` module.

Server configurations are handled by [Ansible](http://www.ansible.com/)
in `playbooks/`.

### Commissioning
At a high level, the commissioning process works like so:

#### Baking an image
First an image is baked, if one by the specified name (`<app>-image`) doesn't already exist. The image is environment and configuration agnostic; it doesn't store any sensitive information, it can be reused across environments, and you don't need to worry about it if configuration options change. This is probably the longest running step.

*In greater detail:*

An image instance is created, which is used to generate a base
template for the application and worker instances. For this image, all necessary application
packages are installed, but no configuration files are copied over. The
instance is automatically deleted after the image has been created from
it. Images are environment agnostic, that is, they don't load any
environment-specific information. Thus this image instance can be reused
for different environments's infrastructures.

#### Commission the infrastructure
Then the infrastructure is created. That is, the instances, RDS instances, autoscaling groups, etc are all made. Where appropriate, the baked image is used.

As a courtesy the commission function will also try to deploy to this infrastructure (see below).

*In greater detail:*
* The database (RDS) is created.
* The broker instance is created [*currently disabled*].
* ~~An autoscaling group is created for application instances~~An
application instance is created, using the
image instance as the base. (See below)
* An autoscaling group is created for worker instances, using the
image instance as the base [*currently disabled*]. 

### Deploying
Once the infrastructure is up and running it is likely that your future interactions with it will primarily be deployment.

For instance, if you need to update some configuration values or ensure the application is synced with the latest changes in git.

You can make your changes to the config or to the app's git repo and then just run the deploy function. This will run the playbooks for the servers to update them.

Note that the deployment with Ansible is able to locate and identify all hosts by standardized tags (set during the commissioning process) thanks to the EC2 dynamic inventory script. Thus you don't need to, for instance, explicitly set the database host for the application config; the playbooks are setup so Ansible will find the hostname itself and fill it in.

### Decommissioning
This just deletes everything that was created during the commissioning
process, except for the image (unless its deletion is specified).

### Cleaning
If you hit a snag while generating the image, you may want to clean
things up. This command will do that for you by removing the image
instance (if it still exists) and the image itself (if it still exists).


---

## Notes

### Names and tags
For the `cloud` module and the playbooks to coordinate, standardized
names and tags are used.

The `cloud` module sets up the infrastructure resources with these tags
and then Ansible can use these tags to locate the resources and get
their hostnames/IPs.

Every resource is tagged with the following:
* Name: `<app>-<env>-<group>`
* Group: `<group>`
* Env: `<env>`
* App: `<app>`

With the exception of the image instance, which is tagged as just `Name: <app>-image`.
The application image is environment-agnostic (no environment-specific data is baked into it) so it can be reused across environments.

### Variables
To further ensure coordination between the playbooks and the `cloud` module, the `cloud` module uses configuration values from the playbooks' "global" variables in `playbooks/group_vars/all.yml`.

`<app>` is set as `app_name` in the config (`playbooks/group_vars/all.yml`).
`<group>` is typically set by default in the CloudFormation templates (see `formations/`).
`<env>` is passed in when commissioning new infrastructure (see `manage.py`)
Then the `Name` is generated by combining these values (as shown above) in the CloudFormation templates (`formations/`).

---

## The Future

### Application autoscaling group vs single instance
For now application autoscaling groups are on hold. Instead, a single application instance is used (it could be a high-powered instance). For prototyping this is OK. It will be one of the things to revisit if the infrastructure needs to scale (other things include setting up the app's clustering to be offloaded to workers, adding a worker autoscaling group, adding a broker instance, and so on).

Having just a single instance means everything can be configured with Ansible's default push mode instead of figuring out the best way to use its pull mode, which would make it so that autoscaling instances would configure themselves as they were spun up). I was having a lot of trouble coming up with a satisfying design for this autoscaling plus pull mode system. I was considering creating a master instance (as a git server) as part of the infrastructure which is itself configured via Ansible, such that configs are copied to it, then it generates git repositories for the autoscaling roles (app, worker). Then the init script for the autoscaling groups would just involve an ansible-pull command to the proper git repository. But this seems overly complicated and might not work the way I'm thinking it might.

So for now a single app instance is all that's needed, and is much more easily managed.

### Workers
Eventually the heavier processing should be offloaded to workers (in an
autoscaling group) managed by a broker instance. Particularly taxing
processes such as clustering and summarization could potentially be handled by workers.
