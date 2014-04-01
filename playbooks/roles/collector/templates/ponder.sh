#!/bin/bash

PIDFILE=/tmp/ponder.pid

if [ -e "${PIDFILE}" ]; then
  echo "Already running."
  exit 99
fi

# Ensure PID file is removed on program exit.
trap "rm -f -- '$PIDFILE'" EXIT

# Create a file with current PID to indicate that process is running.
echo $! > "$PIDFILE"
chmod 644 "$PIDFILE"

cd {{ app_path }}
{{ venv_path }}/bin/python -c 'from argos.core.membrane.collector import ponder; ponder()'

