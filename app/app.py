import functools
import hmac
import os
import uuid
import pathlib

import schedule

import rq_dashboard
from flask import Flask, jsonify, request, render_template

UPLOAD_FOLDER = './uploads'
pathlib.Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = set(['zip'])

with open("/run/secrets/app_password") as f:
    PASSWORD = f.read().strip()

app = Flask(__name__)
app.config.from_object(rq_dashboard.default_settings)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024
app.config["RQ_DASHBOARD_REDIS_URL"] = "redis://redis:6379"

rq_dashboard.web.setup_rq_connection(app)
app.register_blueprint(rq_dashboard.blueprint, url_prefix="/rq")


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def json_response(message="", status=None, id=None, result=None):
    return jsonify(id=id, status=status, message=message, result=result)


def requires_password(route):
    """Refuse the request unless it carries the password from secrets/app_password.txt."""
    @functools.wraps(route)
    def wrapper(*args, **kwargs):
        password = request.form.get("password", "")
        if not hmac.compare_digest(password, PASSWORD):
            return "incorrect password", 400
        return route(*args, **kwargs)
    return wrapper


class InvalidRequest(Exception):
    """The request is missing something, or sent something we cannot grade."""


def form_field(name):
    """The value of a required form field."""
    if not request.form.get(name):
        raise InvalidRequest(f"no '{name}' received, be sure to use the tag '{name}'")
    return request.form[name]


def save_upload():
    """Store the uploaded zipfile under a unique name. Returns its path."""
    if "file" not in request.files:
        raise InvalidRequest("no 'file' received, be sure to use the tag 'file'")

    file = request.files["file"]

    if not allowed_file(file.filename):
        raise InvalidRequest(f"file not allowed, accepting only {', '.join(ALLOWED_EXTENSIONS)}")

    filepath = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}.zip"))
    file.save(filepath)
    return filepath


@app.errorhandler(InvalidRequest)
def invalid_request(error):
    return str(error), 400


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/checkpy", methods=["POST"])
@requires_password
def checkpy():
    repo = form_field("repo")
    args = form_field("args")
    filepath = save_upload()
    webhook = request.form.get("webhook") or None

    job_id = scheduler.start_checkpy(repo, args, filepath, webhook)

    return json_response(id=job_id, message="use /get/<id> to get results")


@app.route("/check50", methods=["POST"])
@app.route("/check50v3", methods=["POST"])
@requires_password
def check50():
    slug = form_field("slug")
    filepath = save_upload()
    webhook = request.form.get("webhook") or None

    job_id = scheduler.start_check50(slug, filepath, webhook)

    return json_response(id=job_id, message="use /get/<id> to get results")


@app.route('/get/<id>', methods=["GET"])
def get(id):
    status, result = scheduler.get(id)

    if status == schedule.Status.UNKNOWN:
        return json_response(id=id, message="job is unknown", status="unknown")

    if status == schedule.Status.BUSY:
        return json_response(id=id, message="job is running", status="busy")

    if status == schedule.Status.QUEUED:
        return json_response(id=id, message=f"job is queued at position: {result}", status="queued", result=result)

    if status == schedule.Status.FAILED:
        return json_response(id=id, message="job has failed", status="failed", result=result)

    return json_response(id=id, message="job is finished", status="finished", result=result)

scheduler = schedule.Scheduler()

if __name__ == "__main__":
    app.run(host='0.0.0.0', port=5000)
