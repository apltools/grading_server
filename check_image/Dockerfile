FROM cs50/check

USER root

WORKDIR /distro

COPY ./requirements.txt /distro

# Install any needed packages specified in requirements.txt
RUN python3 -m pip install -r requirements.txt --user

WORKDIR /check

# Make port 80 available to the world outside this container
# EXPOSE 80
