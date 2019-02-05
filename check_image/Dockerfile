FROM cs50/check

USER root

WORKDIR /distro

COPY ./requirements.txt /distro

# Install any needed packages specified in requirements.txt
RUN python3 -m pip install -r requirements.txt --user

WORKDIR /check
