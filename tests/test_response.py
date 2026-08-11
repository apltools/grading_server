import json
import pathlib

from response import (
    ErrorResponse,
    Response,
    Result,
    create_check50_response,
    create_checkpy_response,
)

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def fixture(name):
    """The raw output of check50 or checkpy, as work.py reads it off a container."""
    return (FIXTURES / f"{name}.json").read_text()


def checks(response, run=0):
    return response.to_json()["runs"][run]["checks"]


def summary(response):
    return response.to_json()["summary"]


class TestCheck50:
    def test_all_passed(self):
        response = create_check50_response("uva/progik/2018/py/hello", fixture("check50_pass"))

        assert summary(response) == {"total_check_count": 3, "passed_check_count": 3}
        assert response.to_json()["tool"] == {
            "name": "check50",
            "args": {"slug": "uva/progik/2018/py/hello"},
        }
        assert all(check["passed"] for check in checks(response))
        assert all(check["description"].startswith(":)") for check in checks(response))

    def test_run_is_named_after_the_slug(self):
        response = create_check50_response("some/slug", fixture("check50_pass"))

        assert [run["name"] for run in response.to_json()["runs"]] == ["some/slug"]

    def test_failed_checks_report_the_rationale(self):
        response = create_check50_response("some/slug", fixture("check50_fail"))

        assert summary(response) == {"total_check_count": 3, "passed_check_count": 1}

        failed = [check for check in checks(response) if check["passed"] is False]
        assert len(failed) == 2
        for check in failed:
            assert check["description"].startswith(":(")
        assert failed[0]["message"] == 'expected "Emma", not ""'

    def test_passing_check_has_no_message(self):
        response = create_check50_response("some/slug", fixture("check50_fail"))

        passed = [check for check in checks(response) if check["passed"] is True]
        assert [check["message"] for check in passed] == [""]

    def test_help_is_appended_to_the_rationale(self):
        # check50 sets help to null unless help50 recognises the error
        output = json.loads(fixture("check50_fail"))
        output["results"][1]["cause"]["help"] = "did you forget to print a newline?"

        response = create_check50_response("some/slug", json.dumps(output))

        message = checks(response)[1]["message"]
        assert message.startswith('expected "Emma", not ""')
        assert message.endswith("did you forget to print a newline?")
        assert "\n" in message

    def test_skipped_check_is_undecided(self):
        # A check whose dependency failed is reported by check50 as passed: null
        output = json.loads(fixture("check50_fail"))
        output["results"][1]["passed"] = None

        response = create_check50_response("some/slug", json.dumps(output))

        assert checks(response)[1]["passed"] is None
        assert checks(response)[1]["description"].startswith(":|")
        # only True counts as passed, null does not
        assert summary(response)["passed_check_count"] == 1

    def test_log_is_joined_into_one_string(self):
        response = create_check50_response("some/slug", fixture("check50_pass"))

        assert "running python3 hello.py..." in checks(response)[1]["log"]

    def test_invalid_json_is_an_error_response(self):
        response = create_check50_response("some/slug", "Traceback (most recent call last):")

        assert isinstance(response, ErrorResponse)
        assert response.to_json()["error"].startswith("Invalid JSON output from check50")
        assert response.to_json()["tool"]["args"] == {"slug": "some/slug"}

    def test_missing_files_is_an_error_response(self):
        # check50 exits with valid JSON but no results when required files are
        # missing, which is what a student submitting a misnamed file produces
        response = create_check50_response("some/slug", fixture("check50_missing_files"))

        assert isinstance(response, ErrorResponse)
        assert "You seem to be missing these required files" in response.to_json()["error"]
        assert response.to_json()["tool"]["args"] == {"slug": "some/slug"}

    def test_results_without_an_error_object_still_reports_cleanly(self):
        output = {"slug": "some/slug", "version": "3.4.0"}

        response = create_check50_response("some/slug", json.dumps(output))

        assert isinstance(response, ErrorResponse)
        assert response.to_json()["error"] == "check50 failed: check50 produced no results"


class TestCheckpy:
    def test_all_passed(self):
        response = create_checkpy_response("spcourse/tests", "hello", fixture("checkpy_pass"))

        assert summary(response) == {"total_check_count": 2, "passed_check_count": 2}
        assert response.to_json()["tool"] == {
            "name": "checkpy",
            "args": {"repo": "spcourse/tests", "args": "hello"},
        }
        assert all(check["description"].startswith(":)") for check in checks(response))

    def test_run_is_named_after_the_tested_file(self):
        response = create_checkpy_response("spcourse/tests", "hello", fixture("checkpy_pass"))

        assert [run["name"] for run in response.to_json()["runs"]] == ["hello.py"]

    def test_failed_check_keeps_the_assertion_message(self):
        response = create_checkpy_response("spcourse/tests", "hello", fixture("checkpy_fail"))

        assert summary(response) == {"total_check_count": 2, "passed_check_count": 1}

        failed = checks(response)[1]
        assert failed["passed"] is False
        assert failed["description"].startswith(":(")
        assert "assert" in failed["message"]
        assert failed["log"] == "nope\n"

    def test_counts_are_summed_over_runs(self):
        output = json.loads(fixture("checkpy_pass")) + json.loads(fixture("checkpy_fail"))

        response = create_checkpy_response("spcourse/tests", "hello", json.dumps(output))

        assert len(response.to_json()["runs"]) == 2
        assert summary(response) == {"total_check_count": 4, "passed_check_count": 3}

    def test_timeout_zeroes_the_counts(self):
        response = create_checkpy_response("spcourse/tests", "hello", fixture("checkpy_timeout"))

        assert summary(response) == {"total_check_count": 0, "passed_check_count": 0}

    def test_timeout_reports_the_message_without_ansi_escapes(self):
        response = create_checkpy_response("spcourse/tests", "hello", fixture("checkpy_timeout"))

        check = checks(response)[0]
        assert check["passed"] is None
        assert check["description"] == "Timeout: hello.py took longer than 10 seconds to run"

    def test_one_timed_out_run_zeroes_every_count(self):
        output = json.loads(fixture("checkpy_pass")) + json.loads(fixture("checkpy_timeout"))

        response = create_checkpy_response("spcourse/tests", "hello", json.dumps(output))

        assert summary(response) == {"total_check_count": 0, "passed_check_count": 0}

    def test_invalid_json_is_an_error_response(self):
        response = create_checkpy_response("spcourse/tests", "hello", "checkpy: command not found")

        assert isinstance(response, ErrorResponse)
        assert response.to_json()["error"].startswith("Invalid JSON output from checkpy")
        assert response.to_json()["raw"] == "checkpy: command not found"


class TestTruncation:
    def test_long_log_keeps_its_head_and_tail(self):
        log = "a" * (Result.MAX_LOG_LENGTH + 1000)

        result = Result(passed=True, description="", log=log)

        assert len(result.log) < len(log)
        assert result.log.startswith("Too Long Truncated Log:\na")
        assert result.log.endswith("a")
        assert "\n...\n" in result.log

    def test_short_log_is_left_alone(self):
        result = Result(passed=True, description="", log="all good")

        assert result.log == "all good"

    def test_long_string_nested_in_raw_is_cut(self):
        output = json.loads(fixture("checkpy_pass"))
        output[0]["results"][0]["output"] = "b" * (Response.MAX_FIELD_LENGTH + 1000)

        response = create_checkpy_response("spcourse/tests", "hello", json.dumps(output))

        assert f"Truncated (length > {Response.MAX_FIELD_LENGTH})" in response.to_json()["raw"]
        assert len(response.to_json()["raw"]) < Response.MAX_FIELD_LENGTH + 1000

    def test_error_response_raw_is_cut(self):
        response = create_check50_response("some/slug", "x" * (ErrorResponse.MAX_FIELD_LENGTH + 1000))

        assert len(response.to_json()["raw"]) == ErrorResponse.MAX_FIELD_LENGTH
