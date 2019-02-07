import os
import uuid
import schedule
import pathlib

from flask import Flask, jsonify, request, redirect, render_template, url_for, g
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './uploads'
pathlib.Path(UPLOAD_FOLDER).mkdir(parents=True, exist_ok=True)
ALLOWED_EXTENSIONS = set(['zip'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def json_response(message="", status=None, id=None, result=None):
    return jsonify(id=id, status=status, message=message, result=result)

@app.route("/")
def index():
    return render_template("index.html")


@app.route('/start', methods=["POST"])
def start():
    # Ensure slug exists
    if "slug" not in request.form:
        return "no 'slug' received, be sure to use the tag 'slug'", 400

    slug = request.form["slug"]

    # Ensure file exists
    if "file" not in request.files:
        return "no 'file' received, be sure to use the tag 'file'", 400

    file = request.files["file"]

    # Get optional webhook
    webhook = request.form["webhook"] if "webhook" in request.form else None

    # Ensure file is a .zip (allowed)
    if not allowed_file(file.filename):
        return f"file not allowed, accepting only {', '.join(ALLOWED_EXTENSIONS)}", 400

    # Name file after id
    id = str(uuid.uuid4())
    filename = f"{id}.zip"

    # Store file on disk
    filepath = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    file.save(filepath)

    # Start check50
    job_id = scheduler.start(slug, filepath, webhook)

    # Communicate id
    return json_response(id=job_id, message="use /get/<id> to get results")


@app.route('/get/<id>', methods=["GET"])
def get(id):
    status, result = scheduler.get(id)

    if status == schedule.Status.UNKNOWN:
        return json_response(id=id, message="job is unknown", status="unknown")

    if status == schedule.Status.BUSY:
        return json_response(id=id, message="job is enqueued or running", status="busy")

    if status == schedule.Status.FAILED:
        return json_response(id=id, message="job has failed", status="failed", result=result)

    return json_response(id=id, message="job is finished", status="finished", result=result)


if __name__ == "__main__":
    with schedule.Scheduler(n_workers=4) as scheduler:
        app.run(host='0.0.0.0', port=80)
