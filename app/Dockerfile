FROM python:3.7-alpine

USER root

WORKDIR /app

COPY . /app

ENV PATH=$PATH:/root/.local/bin

# Install any needed packages specified in requirements.txt
RUN python -m pip install -r requirements.txt --user

# Install docker
RUN apk add openrc --no-cache
RUN apk add docker

EXPOSE 80

ENV FLASK_APP=app.py
ENV FLASK_ENV=development

CMD ["python", "app.py"]