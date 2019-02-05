FROM python:3.7-alpine

USER root

WORKDIR /app

COPY . /app

# Install any needed packages specified in requirements.txt
RUN python -m pip install -r requirements.txt --user

EXPOSE 80

ENV FLASK_APP=app.py
ENV FLASK_ENV=development

RUN ls

CMD ["python", "app.py"]
