#!/bin/bash

# Init script to setup autoscaling
# instances to provision themselves.
sudo apt-add-repository -y ppa:rquillo/ansible
sudo apt-get update
sudo apt-get install -y ansible git-core
sudo ansible-pull -U git://github.com/publicscience/argos.deploy.git
