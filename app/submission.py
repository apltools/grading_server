"""Turning an upload into the zipfile that the check container grades."""
import zipfile

from werkzeug.utils import secure_filename


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
