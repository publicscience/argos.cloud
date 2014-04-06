# Celery config.
# Broker (message queue) url.
BROKER_URL = 'amqp://guest@{{ broker_host }}:5672//'

# Try connecting ad infinitum.
BROKER_CONNECTION_MAX_RETRIES = None

# Result backend.
CELERY_RESULT_BACKEND = 'redis://{{ broker_host }}:6379/0'

# What modules to import on start.
CELERY_IMPORTS = ('argos.tasks',)

# Propagate chord errors when they come up.
CELERY_CHORD_PROPAGATES = True

# Acknowledge the task *after* it has completed.
CELERY_ACKS_LATE = True

# Only cache 1 result at most.
CELERY_MAX_CACHED_RESULTS = 1

# Send emails on errors
CELERY_SEND_TASK_ERROR_EMAILS = True
ADMINS = (
    ('{{ celery_admin_name }}', '{{ celery_admin_email }}')
)
SERVER_EMAIL = '{{ celery_email_user }}'
EMAIL_HOST = '{{ email_host }}'
EMAIL_PORT = 587
EMAIL_HOST_USER = '{{ celery_email_user }}'
EMAIL_HOST_PASSWORD = '{{ celery_email_password }}'

# If enabled pid and log directories will be created if missing.
CELERY_CREATE_DIRS=1

# Setting a maximum amount of tasks per worker
# so the worker processes get regularly killed
# (to reclaim memory). Not sure if this is the best
# approach, but see:
# https://github.com/publicscience/argos/issues/112
CELERYD_MAX_TASKS_PER_CHILD=100
