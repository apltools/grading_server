FROM cs50/check

USER root

WORKDIR /distro

COPY ./requirements.txt /distro

# Install any needed packages specified in requirements.txt
RUN python3 -m pip install -r requirements.txt --user

# check50 currently crashes the first time it's run with this user
# WORKDIR /home/ubuntu/workspace
# USER ubuntu

WORKDIR /check