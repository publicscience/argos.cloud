#!/bin/bash

# Set the env var for the system.
ARGOS_ENV=env
echo -e 'ARGOS_ENV=$env' | sudo tee -a /etc/environment

# Init script to setup autoscaling
# instances to provision themselves.
sudo ansible-pull -U git://github.com/publicscience/argos.deploy.git
