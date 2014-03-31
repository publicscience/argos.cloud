import smtplib
from email.mime.text import MIMEText

from cloud import config

def notify(message):
    user        = config.ERROR_EMAIL_USER
    password    = config.ERROR_EMAIL_PASSWORD
    admins      = config.ERROR_ADMINS
    host        = config.EMAIL_HOST
    port        = config.EMAIL_PORT

    msg = MIMEText(message)
    msg['Subject'] = 'argos.cloud notification'
    msg['From'] = user
    msg['To'] = ', '.join(admins)
    s = smtplib.SMTP('{host}:{port}'.format(
        host=host,
        port=port
    ))
    s.starttls()
    s.login(user, password)
    s.sendmail(user, admins, msg.as_string())
