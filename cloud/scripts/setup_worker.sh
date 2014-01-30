#!/bin/bash

# Install Salt
sudo apt-get install software-properties-common -y
sudo add-apt-repository ppa:saltstack/salt -y
sudo apt-get update -y
sudo apt-get install salt-minion -y
sudo apt-get install salt-master -y
sudo apt-get upgrade -y

# Kill the salt minion while we change things.
sudo pkill -9 -f salt-minion

# Edit Minion config to
# set Salt Master location
sudo sed -i 's/#master: salt/master: $master_dns/' /etc/salt/minion
# automatically call 'highstate' on connection.
sudo sed -i "s/#startup_states: ''/startup_states: highstate/" /etc/salt/minion

# Set the grains so we can target minions as workers.
echo -e 'roles:\n  - worker' | sudo tee -a /etc/salt/grains
echo -e 'dbhost: $db_dns' | sudo tee -a /etc/salt/grains
echo -e 'mqhost: $mq_dns' | sudo tee -a /etc/salt/grains
echo -e 'env: $env' | sudo tee -a /etc/salt/grains

# Set the env var for the system.
ARGOS_ENV=env
echo -e 'ARGOS_ENV=$env' | sudo tee -a /etc/environment

# Start the salt minion backup.
sudo service salt-minion start
sudo salt-call state.highstate
