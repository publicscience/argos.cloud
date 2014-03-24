DEBUG = False

SQLALCHEMY_DATABASE_URI = 'postgresql://{{ db_user }}:{{ db_pass }}@{{ db_host }}:5432/{{ db_name }}'
AES_KEY = '{{ aes_key }}' # must be 32 bytes
AES_IV = '{{ aes_iv }}' # must be 16 bytes
SECRET_KEY = '{{ secret_key }}'

KNOWLEDGE_HOST = '{{ knowledge_host }}'
S3_BUCKET_NAME = '{{ bucket.name }}'
