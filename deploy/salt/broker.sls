# This sets up the message queue/broker for distributed tasks.

rabbitmq-server:
    service.running:
        - enable: True
        - require:
            - pkg: rabbitmq-server
    pkg.installed:
        - require:
            - cmd: rabbitmq-server
    cmd.script:
        # Set up apt repository to install RabbitMQ.
        - source: salt://scripts/install-rabbitmq.sh

redis-server:
    service.running:
        - enable: True
        - require:
            - file: redis-server
            - file: redis-config
    file.managed:
        - name: /etc/init/redis-server.conf
        - source: salt://deploy/redis/redis-server.conf
        - require:
            - cmd: redis-server
    cmd.script:
        # Install Redis.
        - source: salt://scripts/install-redis.sh

redis-config:
    file.managed:
        - name: /etc/redis/redis.conf
        - makedirs: True
        - source: salt://deploy/redis/redis.conf
