"""Request and response helpers shared by every endpoint in app.py."""
import functools
import hmac
import os
import uuid
import zipfile

from flask import jsonify, request
from werkzeug.utils import secure_filename

ALLOWED_EXTENSIONS = set(['zip'])


class InvalidRequest(Exception):
    """The request is missing something, or sent something we cannot grade."""


def is_zipfile(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


def json_response(message="", status=None, id=None, result=None):
    return jsonify(id=id, status=status, message=message, result=result)


def requires_password(expected):
    """Decorator refusing any request that does not carry the expected password."""
    def decorator(route):
        @functools.wraps(route)
        def wrapper(*args, **kwargs):
            password = request.form.get("password", "")
            if not hmac.compare_digest(password, expected):
                return "incorrect password", 400
            return route(*args, **kwargs)
        return wrapper
    return decorator


def form_field(name):
    """The value of a required form field."""
    if not request.form.get(name):
        raise InvalidRequest(f"no '{name}' received, be sure to use the tag '{name}'")
    return request.form[name]


def save_upload(folder):
    """Store the submission in folder as a zipfile under a unique name. Returns its path.

    A submission is graded by unzipping it in the check container, so anything
    that is not a zipfile is zipped here. That way a single loose file, like the
    hello.py you would drop into the form to try something out, just works.
    """
    if "file" not in request.files or not request.files["file"].filename:
        raise InvalidRequest("no 'file' received, be sure to use the tag 'file'")

    file = request.files["file"]

    filepath = os.path.abspath(os.path.join(folder, f"{uuid.uuid4()}.zip"))

    if is_zipfile(file.filename):
        file.save(filepath)
        return filepath

    try:
        zip_into(filepath, file.filename, file.read())
    except ValueError as error:
        raise InvalidRequest(str(error))

    return filepath


def zip_into(filepath, filename, data):
    """Write data into a new zipfile at filepath, stored under filename.

    Returns the name the file ended up with inside the archive. The checks look
    for a submission by name, so the name is kept, but it is stripped down to a
    plain one first: the archive is unzipped inside the container's workspace,
    and a name like ../../elsewhere should not reach out of it.
    """
    name = secure_filename(filename)

    if not name:
        raise ValueError(f"cannot make a filename out of '{filename}'")

    with zipfile.ZipFile(filepath, "w") as archive:
        archive.writestr(name, data)

    return name
