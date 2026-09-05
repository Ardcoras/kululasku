#!/bin/sh

echo localsettings
ln -sf /etc/nginx/sites-available/django_local_nginx.conf /etc/nginx/sites-enabled

CODE_UID="$(stat -c '%u' /code)"
CODE_GID="$(stat -c '%g' /code)"
NGINX_GROUP="$(getent group "$CODE_GID" | cut -d: -f1)"
NGINX_USER="$(getent passwd "$CODE_UID" | cut -d: -f1)"

if [ -z "$NGINX_GROUP" ]; then
    NGINX_GROUP=codegroup
    groupadd -g "$CODE_GID" "$NGINX_GROUP"
fi

if [ -z "$NGINX_USER" ]; then
    NGINX_USER=codeuser
    useradd -u "$CODE_UID" -g "$CODE_GID" -M -s /usr/sbin/nologin "$NGINX_USER"
fi

sed -i "s/^user .*/user $NGINX_USER $NGINX_GROUP;/" /etc/nginx/nginx.conf

python manage.py migrate --fake-initial
python manage.py collectstatic --no-input

mkdir /logs
touch /logs/gunicorn.log
touch /logs/access.log
tail -n 0 -f /logs/*.log /var/log/nginx/*.log &


echo Starting Gunicorn.
rm -f django_app.sock
exec gunicorn expenses.wsgi \
    --name src \
    --bind unix:django_app.sock \
    --workers 1 \
    --log-level=info \
    --log-file=/logs/gunicorn.log \
    --access-logfile=/logs/access.log \
    --reload &

#exec python manage.py runserver

echo Starting nginx.
exec service nginx start

exec "$@"
