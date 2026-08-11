import zipfile

import pytest

from submission import zip_into


def entries(path):
    with zipfile.ZipFile(path) as archive:
        return {name: archive.read(name) for name in archive.namelist()}


def test_a_loose_file_becomes_a_zip_holding_it(tmp_path):
    filepath = tmp_path / "upload.zip"

    name = zip_into(filepath, "hello.py", b"print('hello')\n")

    assert name == "hello.py"
    assert entries(filepath) == {"hello.py": b"print('hello')\n"}


def test_the_name_the_checks_look_for_is_kept(tmp_path):
    filepath = tmp_path / "upload.zip"

    # check50 and checkpy find a submission by name, so this has to survive
    assert zip_into(filepath, "climate.ipynb", b"{}") == "climate.ipynb"


def test_a_path_cannot_escape_the_workspace(tmp_path):
    filepath = tmp_path / "upload.zip"

    name = zip_into(filepath, "../../etc/passwd", b"x")

    assert name == "etc_passwd"
    assert all(not entry.startswith(("/", "..")) for entry in entries(filepath))


def test_a_directory_component_is_flattened(tmp_path):
    filepath = tmp_path / "upload.zip"

    assert zip_into(filepath, "src/hello.py", b"x") == "src_hello.py"


def test_a_name_that_survives_nothing_is_refused(tmp_path):
    filepath = tmp_path / "upload.zip"

    with pytest.raises(ValueError):
        zip_into(filepath, "..", b"x")


def test_empty_content_still_produces_a_readable_zip(tmp_path):
    filepath = tmp_path / "upload.zip"

    zip_into(filepath, "empty.py", b"")

    assert entries(filepath) == {"empty.py": b""}
