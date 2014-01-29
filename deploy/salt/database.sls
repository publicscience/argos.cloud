# This sets up a database instance.

postgresql:
    service.running:
        - enable: True
        - require:
            - pkg: postgresql
    pkg.installed:
        - name: postgresql
        - require:
            - cmd: postgresql
