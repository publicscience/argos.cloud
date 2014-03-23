# Celery config.
# Broker (message queue) url.
BROKER_URL = 'amqp://guest@{{ broker_host }}:5672//'

# Try connecting ad infinitum.
BROKER_CONNECTION_MAX_RETRIES = None

# Result backend.
CELERY_RESULT_BACKEND = 'redis://{{ broker_host }}:6379/0'

# What modules to import on start.
CELERY_IMPORTS = ('tests.tasks_test', 'jobs', 'digester.wikidigester',)

# Propagate chord errors when they come up.
CELERY_CHORD_PROPAGATES = True

# Acknowledge the task *after* it has completed.
CELERY_ACKS_LATE = True

# Only cache 1 result at most.
CELERY_MAX_CACHED_RESULTS = 1

# Send emails on errors
CELERY_SEND_TASK_ERROR_EMAILS = True
ADMINS = (
    ('{{ admin_name }}', '{{ admin_email }}')
)
SERVER_EMAIL = 'bot@gmail.com'
EMAIL_HOST = 'smtp.gmail.com'
EMAIL_PORT = 587
EMAIL_HOST_USER = 'bot@gmail.com'
EMAIL_HOST_PASSWORD = 'your-pass'
