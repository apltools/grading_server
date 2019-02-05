import os
import uuid
import runner

from flask import Flask, jsonify, request, redirect, url_for, g
from werkzeug.utils import secure_filename

UPLOAD_FOLDER = './uploads'
ALLOWED_EXTENSIONS = set(['zip'])

app = Flask(__name__)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 10 * 1024 * 1024

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

def response(message, id=None, result=None):
    return jsonify(id=id, message=message, result=result)


@app.route('/start/<path:slug>', methods=["POST"])
def start(slug):
    # Ensure file exists
    if "file" not in request.files:
        return response("no 'file' received, be sure to use the tag 'file'")

    file = request.files["file"]

    # Ensure file is a .zip (allowed)
    if not allowed_file(file.filename):
        return response(f"file not allowed, accepting only {', '.join(ALLOWED_EXTENSIONS)}")

    # Name file after id
    id = str(uuid.uuid4())
    filename = f"{id}.zip"

    # Store file on disk
    filepath = os.path.abspath(os.path.join(app.config['UPLOAD_FOLDER'], filename))
    file.save(filepath)

    # Start check50
    runner.manager.start(id, slug, filepath)

    # Communicate id
    return response(id=id, message="use /get/<id> to get results")


@app.route('/get/<id>', methods=["GET"])
def get(id):
    status, result = runner.manager.get(id)

    if status == runner.Status.UNKNOWN:
        return response(id=id, message="unknown")

    if status == runner.Status.BUSY:
        return response(id=id, message="busy")

    return response(id=id, message="finished", result=result)


if __name__ == "__main__":
    app.run(host='0.0.0.0', port=80)
