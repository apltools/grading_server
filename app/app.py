import requests
import os
import subprocess

import redis
import rq

from flask import Flask, render_template, request
from werkzeug import secure_filename

app = Flask(__name__)

SCHEDULER = "scheduler"

cache = redis.Redis(host='redis', port=6379)
queue = rq.Queue(connection=cache)

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/start", methods=["POST"])
def start():
    file = request.files['submission']
    slug = request.form['slug']

    filename = secure_filename(file.filename)
    filepath = os.path.join("uploads/", filename)
    file.save(filepath)

    with open(filepath, "rb") as f:
        r = requests.post(f"http://{SCHEDULER}:80/start/{slug}", files={"file": f})
    response = r.json()

    return response['id']

@app.route("/get/<id>")
def get(id):
    return requests.get(f"http://{SCHEDULER}:80/get/{id}").content

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
