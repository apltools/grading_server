FROM python:3.7-alpine

USER root

# Install gcc and python dev headers
RUN apk add python3-dev build-base linux-headers pcre-dev

# Install openssl
RUN apk add openssl-dev openssl

# Add user without password (-D), give it UID 99999 and name it app_user
# RUN stat -c '%g' /var/run/docker.sock
# RUN addgroup -g 999 docker

# move ping (999) to 99, because docker GUID is probably 999
# https://github.com/willfarrell/docker-crontab/issues/20
RUN sed -i "s/999/99/" /etc/group

# RUN addgroup -g 999 docker
RUN addgroup -S app_group && adduser -s /bin/sh -D -u 99999 -S app_user -G app_group
# RUN addgroup app_user docker

# Install docker
RUN apk add openrc --no-cache
RUN apk add docker

WORKDIR /app

USER app_user

# WORKDIR /app

COPY . /app

USER root

RUN chown -R app_user:app_group /app

USER app_user

# Add dest of pip to path
ENV PATH=$PATH:/home/app_user/.local/bin:/home/app_user/.local/lib/python3.7/site-packages
# ENV PATH=$PATH:/root/.local/bin

# Install any needed packages specified in requirements.txt
RUN python -m pip install -r requirements.txt --user

USER root

# CMD uwsgi --http 0.0.0.0:5000 --wsgi-file app.py --callable app --processes 4 --threads 2 --uid user
CMD sh init.sh
# && uwsgi --master --https 0.0.0.0:5000,certs/pub.pem,certs/priv.pem --wsgi-file app.py --callable app --processes 4 --threads 2 # --uid app_user
