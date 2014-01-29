#!/bin/bash

# Install Salt
sudo apt-get install software-properties-common -y
sudo add-apt-repository ppa:saltstack/salt -y
sudo apt-get update -y
sudo apt-get install salt-minion -y
sudo apt-get install salt-master -y
sudo apt-get upgrade -y

# Enable Salt's firewall rules
sudo ufw allow salt

# Edit Master config to
# Accept all pending Minion keys
sudo sed -i 's/#auto_accept: False/auto_accept: True/' /etc/salt/master
# Enable fileserver at /srv/salt
# and enable pillar at /srv/pillar
# (looking for a nicer way of handling this...)
sudo sed -i '/#\(file\|pillar\)_roots:/ s/^#//' /etc/salt/master
sudo sed -i '/#\s\{2\}base:/ s/^#//' /etc/salt/master
sudo sed -i '/#\s\{4\}\-\s\/srv\/\(salt\|pillar\)/ s/^#//' /etc/salt/master

# Restart Salt Master.
sudo service salt-master restart
