FROM python:3.7-alpine

USER root

# Install gcc and python dev headers
RUN apk add python3-dev build-base linux-headers pcre-dev

# Install openssl
RUN apk add openssl-dev openssl

# Install docker
RUN apk add openrc --no-cache
RUN apk add docker

# Add user without password (-D), give it UID 99999 and name it app_user
RUN addgroup -S app_group && adduser -D -u 99999 -S app_user -G app_group

USER app_user

WORKDIR /app

COPY . /app

# Add dest of pip to path
ENV PATH=$PATH:/home/app_user/.local/bin
ENV PATH=$PATH:/root/.local/bin

# Own docker sock
# RUN chown app_user:app_group /var/run/docker.sock

USER root

# Install any needed packages specified in requirements.txt
RUN python -m pip install -r requirements.txt

# CMD uwsgi --http 0.0.0.0:5000 --wsgi-file app.py --callable app --processes 4 --threads 2 --uid user
CMD uwsgi --master --https 0.0.0.0:5000,certs/pub.pem,certs/priv.pem --wsgi-file app.py --callable app --processes 4 --threads 2 --uid app_user
