base:
    'roles:app':
        - match: grain
        - app

    'roles:database':
        - match: grain
        - database

    'roles:worker':
        - match: grain
        - worker

    'roles:broker':
        - match: grain
        - broker

    'image':
        - image