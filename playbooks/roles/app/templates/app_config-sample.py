SQLALCHEMY_DATABASE_URI = 'postgresql://{{ db_user }}@{{ db_host }}:5432/{{ db_name }}'
AES_KEY = '123456789abcdefg123456789abcdefg' # must be 32 bytes
AES_IV = '123456789abcdefg' # must be 16 bytes
SECRET_KEY = 'development'
DEBUG = False

# Security Config
SECURITY_SEND_REGISTER_EMAIL = False
SECURITY_SEND_PASSWORD_CHANGE_EMAIL = False
SECURITY_SEND_PASSWORD_RESET_NOTICE_EMAIL = False
