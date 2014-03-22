#!/bin/bash

# Set the env var for the system.
ARGOS_ENV=env
echo -e 'ARGOS_ENV=$env' | sudo tee -a /etc/environment
