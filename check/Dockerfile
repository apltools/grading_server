FROM cs50/cli 
##############################cs50/check#####################################
USER root

ARG DEBIANFRONTEND=noninteractive

RUN apt-get update -qq && apt-get install -y jq

# Install Python packages
# TODO remove werkzeug after https://github.com/fengsp/flask-session/issues/99 is fixed
RUN pip3 install \
        flask_sqlalchemy \
        nltk \
        numpy \
        pandas \
        passlib \
        plotly \
        pytz \
        cffi \
        opencv-python && \
    python3 -m nltk.downloader -d /usr/share/nltk_data/ punkt

RUN sed -i '/^ubuntu ALL=(ALL) NOPASSWD:ALL$/d' /etc/sudoers

USER ubuntu

# Clone checks
ENV CHECK50_PATH  "~/.local/share/check50"
#############################################################################

USER root

WORKDIR /distro

COPY ./requirements.txt /distro

# Install any needed packages specified in requirements.txt
RUN python3 -m pip install -r requirements.txt

# Have ubuntu own checkpy dir
RUN chown -R ubuntu:ubuntu $(python3 -c "import site; print(site.getsitepackages()[0] + '/checkpy')")

WORKDIR /home/ubuntu/workspace

RUN chown -R ubuntu:ubuntu /home/ubuntu/workspace

USER ubuntu
