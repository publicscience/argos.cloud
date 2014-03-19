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
            - file: uwsgi-init
            - file: fastrouter
    pkg.installed:
        - name: uwsgi


nginx-conf:
    file.managed:
        - name: /etc/nginx/sites-available/default
        - source: salt://deploy/nginx.conf
        - template: jinja
        - require:
            - pkg: nginx

nginx:
    pkg.installed:
        - name: nginx
    file.symlink:
        - name: /etc/nginx/sites-enabled/default
        - target: /etc/nginx/sites-available/default
        - require:
            - file: nginx-conf
    service.running:
        - enable: True
        - require:
            - service: uwsgi
            - pkg: nginx
            - file: nginx

# Copy over the app config.
app-config:
    file.managed:
        - name: {{ pillar['app_path'] }}conf/{{ grains['env'] }}_app.py
        - source: salt://deploy/app_config.py
        - template: jinja
        - require:
            - git: app

# Copy over the Celery config.
celery-config:
    file.managed:
        - name: {{ pillar['app_path'] }}conf/{{ grains['env'] }}_celery.py
        - source: salt://deploy/celery_config.py
        - template: jinja
        - require:
            - git: app