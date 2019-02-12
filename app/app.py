import os
import uuid
import pathlib
import atexit

import schedule

import rq_dashboard
from flask import Flask, jsonify, request, redirect, render_template, url_for, g
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './uploads'
pathlib.Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = set(['zip'])

with open("certs/password.txt") as f:
    PASSWORD = f.read().strip()

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
rq_dashboard.default_settings.REDIS_HOST = "redis"
rq_dashboard.default_settings.REDIS_PORT = 6379
app.config.from_object(rq_dashboard.default_settings)
app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def json_response(message="", status=None, id=None, result=None):
    return jsonify(id=id, status=status, message=message, result=result)


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/checkpy", methods=["POST"])
def checkpy():
    # Ensure password is correct
    password = request.form["password"]
    if password != PASSWORD:
        return "incorrect password", 400

    # Ensure args exists
    if "args" not in request.form or not request.form["args"]:
        return "no 'args' received, be sure to use the tag 'args'", 400

    args = request.form["args"]

    # Ensure repo exists
    if "repo" not in request.form or not request.form["repo"]:
        return "no 'repo' received, be sure to use the tag 'repo'", 400

    repo = request.form["repo"]

    # Ensure file exists
    if "file" not in request.files:
        return "no 'file' received, be sure to use the tag 'file'", 400

    file = request.files["file"]

    # Ensure file is a .zip (allowed)
    if not allowed_file(file.filename):
        return f"file not allowed, accepting only {', '.join(ALLOWED_EXTENSIONS)}", 400

    # Name file after id
    id = str(uuid.uuid4())
    filename = f"{id}.zip"

    # Store file on disk
    filepath = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    file.save(filepath)

    # Get optional webhook
    webhook = request.form["webhook"] if "webhook" in request.form else None

    # Start check50
    job_id = scheduler.start_checkpy(repo, args, filepath, webhook)

    # Communicate id
    return json_response(id=job_id, message="use /get/<id> to get results")


@app.route('/check50', methods=["POST"])
def check50():
    # Ensure password is correct
    password = request.form["password"]
    if password != PASSWORD:
        return "incorrect password", 400

    version = request.form.get("version") or 3

    # Ensure version is an integer
    try:
        version = int(version)
    except ValueError:
        return f"version: {version} must be an integer", 400

    # Ensure version is known
    versions = [2,3]
    if version not in versions:
        return f"unknown version {version}, choose one of: {versions}", 400

    # Ensure slug exists
    if "slug" not in request.form or not request.form["slug"]:
        return "no 'slug' received, be sure to use the tag 'slug'", 400

    slug = request.form["slug"]

    # Ensure file exists
    if "file" not in request.files:
        return "no 'file' received, be sure to use the tag 'file'", 400

    file = request.files["file"]

    # Ensure file is a .zip (allowed)
    if not allowed_file(file.filename):
        return f"file not allowed, accepting only {', '.join(ALLOWED_EXTENSIONS)}", 400

    # Name file after id
    id = str(uuid.uuid4())
    filename = f"{id}.zip"

    # Store file on disk
    filepath = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    file.save(filepath)

    # Get optional webhook
    webhook = request.form.get("webhook") or None

    # Start check50
    if version == 3:
        job_id = scheduler.start_check50(slug, filepath, webhook)
    else:
        job_id = scheduler.start_check50v2(slug, filepath, webhook)

    # Communicate id
    return json_response(id=job_id, message="use /get/<id> to get results")


@app.route('/get/<id>', methods=["GET"])
def get(id):
    status, result = scheduler.get(id)

    if status == schedule.Status.UNKNOWN:
        return json_response(id=id, message="job is unknown", status="unknown")

    if status == schedule.Status.BUSY:
        return json_response(id=id, message="job is running", status="busy")

    if status == schedule.Status.QUEUED:
        return json_response(id=id, message="job is queued", status="queued")

    if status == schedule.Status.FAILED:
        return json_response(id=id, message="job has failed", status="failed", result=result)

    return json_response(id=id, message="job is finished", status="finished", result=result)


scheduler = schedule.Scheduler(n_workers=4)
atexit.register(scheduler.__exit__)
scheduler.__enter__()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
