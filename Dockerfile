FROM python:3.7-alpine

USER root

WORKDIR /app

COPY . /app

# Install any needed packages specified in requirements.txt
RUN python -m pip install -r requirements.txt --user

# Install docker
RUN apk add openrc --no-cache
RUN apk add docker

EXPOSE 80

ENV FLASK_APP=server.py
ENV FLASK_ENV=development

CMD ["python", "server.py"]
