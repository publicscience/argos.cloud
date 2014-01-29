#!/bin/bash

# Install Salt
sudo apt-get install software-properties-common -y
sudo add-apt-repository ppa:saltstack/salt -y
sudo apt-get update -y
sudo apt-get install salt-minion -y
sudo apt-get install salt-master -y
sudo apt-get upgrade -y

# Give this a Minion id of "image"
echo 'image' | sudo tee /etc/salt/minion_id

# Provision as a masterless minion.
sudo salt-call state.highstate --local
