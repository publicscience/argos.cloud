# This sets up a worker for distributed tasks.

include:
    - app

# Start the Celery worker.
worker:
    cmd.run:
        - cwd: {{ pillar['app_path'] }}
        - name: {{ pillar['env_path'] }}bin/celeryd --loglevel=info --config=cloud.celery_config --logfile=/var/log/celery.log
        - require:
            - virtualenv: venv
            - cmd: nltk-data
            - file: app-config
            - file: celery-config
