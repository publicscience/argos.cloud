# This sets up the base image for all other instances.
# This is here to reduce the redundancy/time of installing the same things across instances.
# No sensitive files, configs, or data should be added to this image!

include:
    - deploy.git

# Grab latest version from GitHub.
# Make sure you add the proper public
# key as a deploy key on the GitHub repo.
app:
    git.latest:
        - name: {{ pillar['git_repo'] }}
        - rev: {{ pillar['git_rev'] }}
        - target: {{ pillar['app_path'] }}
        - force: true
        - require:
            - pkg: app-pkgs
            - file: deploykey
            - file: publickey
            - file: ssh_config

# Clean up sensitive files.
clean:
    file.absent:
        - names:
            - /root/.ssh/github.pub
            - /root/.ssh/github
        - require:
            - git: app

# Setup the virtualenv.
venv:
    virtualenv.managed:
        - name: {{ pillar['env_path'] }}
        - cwd: {{ pillar['app_path'] }}
        - venv_bin: virtualenv-3.3
        - requirements: {{ pillar['app_path'] }}requirements.txt
        - system_site_packages: false
        - require:
            - pkg: app-pkgs
            - pip: pip-pkgs
            - git: app
            - pkg: lxml-deps
            - pkg: mwlib-deps
            - cmd: scipy-deps

# Ensure necessary packages are installed.
app-pkgs:
    pkg.installed:
        - names:
            - git
            - python3.3
            - python-pip # Salt requires this to properly check pip.installed.
            - python3-pip
            - unzip # For the NRE server and for NLTK data.
            - bzr # For getting latest python-dateutil.
            - openjdk-7-jre # For the NRE server.
            - postgresql-server-dev-9.1 # For psycopg.

# Ensure virtualenv-3.3 is installed.
pip-pkgs:
    pip.installed:
        - names:
            - virtualenv
            - cython
        #- bin_env: pip-3.3
        - bin_env: pip3
        - require:
            - pkg: app-pkgs

# Download NLTK data.
nltk-data:
    # NLTK data still indefinitely hangs when downloading.
    # https://github.com/nltk/nltk/issues/565
    #cmd.run:
        #- cwd: {{ pillar['app_path'] }}
        #- name: {{ pillar['env_path'] }}bin/python -m nltk.downloader wordnet stopwords punkt words maxent_treebank_pos_tagger maxent_ne_chunker
        #- require:
            #- virtualenv: venv
    # Ugh even this hangs indefinitely.
    #cmd.script:
        #- source: salt://scripts/install-nltk_data.sh
    # Do this instead:
    file.managed:
        - name: /usr/share/nltk_data.tar.gz
        - source: salt://deploy/nltk_data.tar.gz
        - makedirs: True
    cmd.run:
        - cwd: /usr/share/
        - name: tar -zxvf nltk_data.tar.gz

# Required by mwlib.
mwlib-deps:
    pkg.installed:
        - names:
            - libevent-dev
            - re2c

# Required by lxml.
lxml-deps:
    pkg.installed:
        - names:
            - libxml2-dev
            - libxslt1-dev
            - python-dev
            - lib32z1-dev

# Required by scipy.
scipy-deps:
    cmd.run:
        - name: sudo apt-get -y build-dep python3-scipy
