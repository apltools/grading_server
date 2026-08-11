FROM python:3.13-alpine

USER root

# Install gcc and python dev headers
RUN apk add python3-dev build-base linux-headers pcre-dev

# Install supervisor
RUN apk add --no-cache supervisor gcc musl-dev

# Install openssl
RUN apk add openssl-dev openssl

# Install podman, to run the check container
RUN apk add podman

# Needed for podman run
RUN apk add iptables

WORKDIR /app

# Install any needed packages specified in requirements.txt, before copying the
# app itself, so that editing a template does not invalidate the install
COPY requirements.txt /app
RUN python -m pip install -r requirements.txt

COPY . /app

ENV XDG_RUNTIME_DIR=/run/user/0
ENV DOCKER_HOST=unix:///run/user/0/podman/podman.sock

# Add supervisor config
RUN mkdir -p /etc/supervisor.d
COPY supervisord.conf /etc/supervisor.d/supervisord.conf

CMD sh boot/init.sh
