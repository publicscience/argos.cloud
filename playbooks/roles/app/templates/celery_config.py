# Celery config.
# Broker (message queue) url.
BROKER_URL = 'amqp://guest@{{ broker_host }}:5672//'

# Try connecting ad infinitum.
BROKER_CONNECTION_MAX_RETRIES = None

# Result backend.
CELERY_RESULT_BACKEND = 'redis://{{ broker_host }}:6379/0'

# What modules to import on start.
CELERY_IMPORTS = ('argos.tasks', 'argos.tasks.periodic', )

# Propagate chord errors when they come up.
CELERY_CHORD_PROPAGATES = True

# Acknowledge the task *after* it has completed.
CELERY_ACKS_LATE = True

# Only cache 1 result at most.
CELERY_MAX_CACHED_RESULTS = 1

# Send emails on errors
CELERY_SEND_TASK_ERROR_EMAILS = True
ADMINS = [
    ('{{ celery_admin_name }}', '{{ celery_admin_email }}')
]
SERVER_EMAIL = '{{ celery_email_user }}'
EMAIL_HOST = '{{ email_host }}'
EMAIL_PORT = {{ email_port }}
EMAIL_HOST_USER = '{{ celery_email_user }}'
EMAIL_HOST_PASSWORD = '{{ celery_email_password }}'
EMAIL_USE_TLS = True

# If enabled pid and log directories will be created if missing.
CELERY_CREATE_DIRS=1

# Setting a maximum amount of tasks per worker
# so the worker processes get regularly killed
# (to reclaim memory). Not sure if this is the best
# approach, but see:
# https://github.com/publicscience/argos/issues/112
CELERYD_MAX_TASKS_PER_CHILD=100


from celery.schedules import crontab

CELERY_TIMEZONE = 'UTC'
CELERYBEAT_SCHEDULE = {
    'collect-articles': {
        'task': 'argos.tasks.periodic.collect',
        'schedule': crontab(minute=0, hour='*')
    },
    'cluster-articles': {
        'task': 'argos.tasks.periodic.cluster_articles',
        'schedule': crontab(minute=30, hour='*')
    },
    'cluster-events': {
        'task': 'argos.tasks.periodic.cluster_events',
        'schedule': crontab(minute=30, hour='*')
    }
}

from kombu.common import Broadcast, Queue

# Create a broadcast queue so the tasks are sent to
# *all* workers (that are listening to that queue).
CELERY_DEFAULT_QUEUE = 'default'
CELERY_QUEUES = (Queue('default'), Broadcast('broadcast_tasks'), )
CELERY_ROUTES = {
        'argos.tasks.periodic.collect': {'queue': 'broadcast_tasks'},
        'argos.tasks.periodic.cluster_articles': {'queue': 'broadcast_tasks'},
        'argos.tasks.periodic.cluster_events': {'queue': 'broadcast_tasks'}
}
