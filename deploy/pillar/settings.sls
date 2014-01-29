# Setup Git info.
git_rev: master
git_repo: git@github.com:publicscience/argos.git

# Application info.
{% set app_name = 'argos' %}
app_name: {{ app_name }}
app_path: /var/www/{{ app_name }}/
env_path: /var/env/