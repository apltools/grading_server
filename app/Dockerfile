FROM python:3.7-alpine

USER root

WORKDIR /app

COPY . /app

ENV PATH=$PATH:/root/.local/bin

# Install gcc and python dev headers
RUN apk add python3-dev build-base linux-headers pcre-dev

# Install any needed packages specified in requirements.txt
RUN python -m pip install -r requirements.txt --user

# Install docker
RUN apk add openrc --no-cache
RUN apk add docker

# EXPOSE 80
# EXPOSE 5050
# EXPOSE 5000
# EXPOSE 9191

# ENV FLASK_APP=app.py
# ENV FLASK_ENV=development

# CMD ["python", "app.py"]

CMD uwsgi --http 0.0.0.0:5000 --wsgi-file app.py --callable app --processes 4 --threads 2
