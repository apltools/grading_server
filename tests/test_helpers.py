import io
import json
import zipfile

import pytest

from flask import Flask

from helpers import (
    InvalidRequest,
    form_field,
    is_zipfile,
    json_response,
    requires_password,
    save_upload,
    zip_into,
)

app = Flask(__name__)


def post(**form):
    """A request context holding a POST of form, for the request bound helpers."""
    return app.test_request_context("/", method="POST", data=form)


def upload(name, content=b"x"):
    return (io.BytesIO(content), name)


def entries(path):
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


class TestZipInto:
    def test_a_loose_file_becomes_a_zip_holding_it(self, tmp_path):
        filepath = tmp_path / "upload.zip"

        name = zip_into(filepath, "hello.py", b"print('hello')\n")

        assert name == "hello.py"
        assert entries(filepath) == {"hello.py": b"print('hello')\n"}

    def test_the_name_the_checks_look_for_is_kept(self, tmp_path):
        # check50 and checkpy find a submission by name, so this has to survive
        assert zip_into(tmp_path / "u.zip", "climate.ipynb", b"{}") == "climate.ipynb"

    def test_a_path_cannot_escape_the_workspace(self, tmp_path):
        filepath = tmp_path / "upload.zip"

        name = zip_into(filepath, "../../etc/passwd", b"x")

        assert name == "etc_passwd"
        assert all(not entry.startswith(("/", "..")) for entry in entries(filepath))

    def test_a_directory_component_is_flattened(self, tmp_path):
        assert zip_into(tmp_path / "u.zip", "src/hello.py", b"x") == "src_hello.py"

    def test_a_name_that_survives_nothing_is_refused(self, tmp_path):
        with pytest.raises(ValueError):
            zip_into(tmp_path / "u.zip", "..", b"x")

    def test_empty_content_still_produces_a_readable_zip(self, tmp_path):
        zip_into(tmp_path / "u.zip", "empty.py", b"")

        assert entries(tmp_path / "u.zip") == {"empty.py": b""}


class TestSaveUpload:
    def test_a_zipfile_is_stored_as_it_arrived(self, tmp_path):
        raw = b"PK\x03\x04 whatever was uploaded, kept verbatim"

        with post(file=upload("submission.zip", raw)):
            filepath = save_upload(str(tmp_path))

        assert open(filepath, "rb").read() == raw

    def test_a_loose_file_is_zipped(self, tmp_path):
        with post(file=upload("hello.py", b"print(1)")):
            filepath = save_upload(str(tmp_path))

        assert entries(filepath) == {"hello.py": b"print(1)"}

    def test_every_upload_lands_under_its_own_name(self, tmp_path):
        with post(file=upload("hello.py")):
            first = save_upload(str(tmp_path))
        with post(file=upload("hello.py")):
            second = save_upload(str(tmp_path))

        assert first != second
        assert first.endswith(".zip") and second.endswith(".zip")

    def test_a_missing_file_is_refused(self, tmp_path):
        with post(slug="a/b/c"), pytest.raises(InvalidRequest) as error:
            save_upload(str(tmp_path))

        assert "no 'file' received" in str(error.value)

    def test_an_empty_file_input_is_refused(self, tmp_path):
        # what a browser sends for a form submitted without picking a file
        with post(file=upload("")), pytest.raises(InvalidRequest) as error:
            save_upload(str(tmp_path))

        assert "no 'file' received" in str(error.value)

    def test_an_unusable_filename_is_refused(self, tmp_path):
        with post(file=upload("..")), pytest.raises(InvalidRequest):
            save_upload(str(tmp_path))


class TestFormField:
    def test_a_field_that_is_there(self):
        with post(slug="a/b/c"):
            assert form_field("slug") == "a/b/c"

    def test_a_field_that_is_missing(self):
        with post(), pytest.raises(InvalidRequest) as error:
            form_field("slug")

        assert str(error.value) == "no 'slug' received, be sure to use the tag 'slug'"

    def test_a_field_that_is_empty(self):
        with post(slug=""), pytest.raises(InvalidRequest):
            form_field("slug")


class TestRequiresPassword:
    def route(self):
        return requires_password("hunter2")(lambda: "graded")

    def test_the_right_password_gets_through(self):
        with post(password="hunter2"):
            assert self.route()() == "graded"

    def test_a_wrong_password_does_not(self):
        with post(password="hunter3"):
            assert self.route()() == ("incorrect password", 400)

    def test_no_password_does_not(self):
        with post():
            assert self.route()() == ("incorrect password", 400)


class TestMisc:
    def test_is_zipfile_looks_at_the_extension(self):
        assert is_zipfile("submission.zip")
        assert is_zipfile("SUBMISSION.ZIP")
        assert not is_zipfile("hello.py")
        assert not is_zipfile("zip")

    def test_json_response_always_carries_every_key(self):
        with app.test_request_context():
            body = json.loads(json_response(message="hi", id="1").get_data())

        assert body == {"id": "1", "message": "hi", "result": None, "status": None}
