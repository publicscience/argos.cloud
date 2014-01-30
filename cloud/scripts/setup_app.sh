#!/bin/bash

# (Salt is already installed on the image)

# Kill the salt minion while we change things.
sudo pkill -9 -f salt-minion

# Edit Minion config to
# set Salt Master location
sudo sed -i 's/#master: salt/master: $master_dns/' /etc/salt/minion
# automatically call 'highstate' on connection.
sudo sed -i "s/#startup_states: ''/startup_states: highstate/" /etc/salt/minion

# Set the `roles` grain for this instance to be 'app'.
echo -e 'roles:\n  - app' | sudo tee -a /etc/salt/grains
echo -e 'dbhost: $db_dns' | sudo tee -a /etc/salt/grains
echo -e 'mqhost: $mq_dns' | sudo tee -a /etc/salt/grains # not using distributed tasks at the moment
echo -e 'env: $env' | sudo tee -a /etc/salt/grains

# Set the env var for the system.
ARGOS_ENV=env
echo -e 'ARGOS_ENV=$env' | sudo tee -a /etc/environment

# Start the salt minion backup.
sudo service salt-minion start
sudo salt-call state.highstate
