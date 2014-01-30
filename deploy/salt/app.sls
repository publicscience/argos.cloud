# This setups the application.

include:
    - deploy.git
    - image

# uWSGI fastrouter config
fastrouter:
    file.managed:
        - name: /opt/uwsgi/etc/uwsgi.d/fastrouter
        - source: salt://deploy/uwsgi/fastrouter
        - makedirs: True

# uWSGI init script
uwsgi-init:
    file.managed:
        - name: /etc/init.d/uwsgi
        - source: salt://deploy/uwsgi/init-script
        - mode: 755

uwsgi:
    file.managed:
        - name: /opt/uwsgi/etc/uwsgi.d/vassal.ini
        - source: salt://deploy/uwsgi/vassal.ini
        - template: jinja
    service.running:
        - enable: True
        - require:
            - pkg: uwsgi
            - file: uwsgi_init
            - file: fastrouter
    pkg.installed:
        - name: uwsgi

nginx:
    pkg.installed:
        - name: nginx
    service.running:
        - enable: True
        - require:
            - service: uwsgi
            - pkg: nginx

# Copy over the app config.
# TO DO this needs to get the proper database host.
app-config:
    file.managed:
        - name: {{ pillar['app_path'] }}config.py
        - source: salt://deploy/config.py
        - require:
            - git: app

# Copy over the Celery config.
# TO DO this needs to get the proper broker and backend hosts.
celery-config:
    file.managed:
        - name: {{ pillar['app_path'] }}jobs/celery_config.py
        - source: salt://deploy/celery_config.py
        - require:
            - git: app