#!/usr/bin/env bash
set -o errexit

pip install -r requirements.txt

# Clean existing static files before collecting fresh assets
python manage.py collectstatic --no-input --clear

python manage.py migrate
python manage.py createcachetable

python manage.py shell -c "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.filter(username='admin').exists() or User.objects.create_superuser('admin', '', 'admin123')"