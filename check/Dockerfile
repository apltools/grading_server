FROM cs50/cli
##############################cs50/check#####################################
USER root

ARG DEBIANFRONTEND=noninteractive

RUN apt-get update -qq && apt-get install -y jq

# Install uv
# https://docs.astral.sh/uv/getting-started/installation/
RUN curl --fail --location --show-error --silent https://astral.sh/uv/install.sh | \
        env UV_INSTALL_DIR=/usr/local/bin INSTALLER_NO_MODIFY_PATH=1 sh

# Install Python 3.14.x through uv, and have python, python3, pip and pip3
# point to a uv managed environment rather than cs50/cli's Python
# https://docs.astral.sh/uv/concepts/python-versions/
ENV UV_PYTHON_INSTALL_DIR=/opt/uv/python
ENV UV_PROJECT_ENVIRONMENT=/opt/venv
ENV VIRTUAL_ENV=/opt/venv
ENV UV_PYTHON=/opt/venv/bin/python
ENV PATH="/opt/venv/bin:$PATH"
# Compile at install time, so that no SyntaxWarnings from older packages (like
# check50) end up in the JSON that the grading server parses
ENV UV_COMPILE_BYTECODE=1
# Don't leave uv's download cache behind in the image
ENV UV_NO_CACHE=1
# ubuntu owns the venv, as check50 installs a slug's dependencies at runtime,
# and pip cannot fall back to a --user install from within a venv. Install as
# ubuntu rather than chowning afterwards, as a chown --recursive would copy the
# entire venv into another layer.
RUN install --directory --owner=ubuntu --group=ubuntu /opt/uv /opt/venv
USER ubuntu
RUN uv python install 3.14 && \
    uv venv --python 3.14 --seed /opt/venv
USER root
RUN ln --symbolic --force /opt/venv/bin/python /usr/local/bin/python && \
    ln --symbolic --force /opt/venv/bin/python /usr/local/bin/python3 && \
    ln --symbolic --force /opt/venv/bin/pip /usr/local/bin/pip && \
    ln --symbolic --force /opt/venv/bin/pip /usr/local/bin/pip3

# Reinstall cs50/cli's Python packages, as those live in cs50/cli's Python
USER ubuntu
RUN uv pip install \
        autopep8 \
        cachelib \
        "check50<4" \
        cli50 \
        compare50 \
        cs50==9.4.0 \
        Flask \
        Flask-Session \
        help50 \
        pytest \
        render50 \
        setuptools \
        "style50>=3.0.0" \
        "submit50<4" \
        lib50

# Install Python packages
# TODO remove werkzeug after https://github.com/fengsp/flask-session/issues/99 is fixed
RUN uv pip install \
        flask_sqlalchemy \
        nltk \
        numpy \
        pandas \
        passlib \
        plotly \
        pytz \
        cffi \
        opencv-python

USER root
RUN python3 -m nltk.downloader -d /usr/share/nltk_data/ punkt

# Python 3.14 defaults to the forkserver start method on Linux, which check50
# does not support (it only special cases fork and spawn, and otherwise loses
# the globals it sets before running checks), so restore fork
RUN printf '%s\n' \
        'import multiprocessing' \
        'multiprocessing.set_start_method("fork", force=True)' \
        > $(python3 -c "import site; print(site.getsitepackages()[0])")/sitecustomize.py

RUN sed -i '/^ubuntu ALL=(ALL) NOPASSWD:ALL$/d' /etc/sudoers

ENV CHECK50_PATH="~/.local/share/check50"

#############################################################################

USER root

WORKDIR /distro

COPY ./requirements.txt /distro

# Install any needed packages specified in requirements.txt
USER ubuntu
RUN uv pip install -r requirements.txt --upgrade
USER root

WORKDIR /home/ubuntu/workspace

RUN chown -R ubuntu:ubuntu /home/ubuntu/workspace

USER ubuntu
