import pathlib

from response import ErrorResponse
from tools import TOOLS

FIXTURES = pathlib.Path(__file__).parent / "fixtures"


def fixture(name):
    return (FIXTURES / f"{name}.json").read_text()


def test_every_tool_is_registered_under_its_own_name():
    assert all(name == tool.name for name, tool in TOOLS.items())


def test_the_expected_tools_are_registered():
    assert set(TOOLS) == {"check50", "checkpy"}


def test_check50_takes_a_slug_and_answers_to_its_old_alias():
    assert TOOLS["check50"].fields == ("slug",)
    assert TOOLS["check50"].aliases == ("check50v3",)


def test_checkpy_takes_a_repo_and_args():
    # the order is the order the fields are validated in
    assert TOOLS["checkpy"].fields == ("repo", "args")


def test_check50_parses_its_own_output():
    response = TOOLS["check50"].parse({"slug": "some/slug"}, fixture("check50_pass"))

    assert response.to_json()["tool"] == {"name": "check50", "args": {"slug": "some/slug"}}
    assert response.to_json()["summary"]["passed_check_count"] == 3


def test_checkpy_parses_its_own_output():
    args = {"repo": "spcourse/tests", "args": "hello"}

    response = TOOLS["checkpy"].parse(args, fixture("checkpy_pass"))

    assert response.to_json()["tool"] == {"name": "checkpy", "args": args}
    assert response.to_json()["summary"]["passed_check_count"] == 2


def test_a_tool_that_prints_nonsense_yields_an_error_response():
    for tool, args in [(TOOLS["check50"], {"slug": "s"}),
                       (TOOLS["checkpy"], {"repo": "r", "args": "a"})]:
        assert isinstance(tool.parse(args, "command not found"), ErrorResponse)


def test_run_is_callable_with_a_container_and_the_form_values():
    class FakeExec:
        output = b'{"slug": "some/slug", "results": []}'

    class FakeContainer:
        def __init__(self):
            self.commands = []

        def exec_run(self, command):
            self.commands.append(command)
            return FakeExec()

    container = FakeContainer()
    output = TOOLS["check50"].run(container, {"slug": "some/slug"})

    assert container.commands == ["check50 --local -o json -- some/slug"]
    assert output == '{"slug": "some/slug", "results": []}'


def test_checkpy_downloads_the_tests_before_running_them():
    class FakeExec:
        output = b"[]"

    class FakeContainer:
        def __init__(self):
            self.commands = []

        def exec_run(self, command):
            self.commands.append(command)
            return FakeExec()

    container = FakeContainer()
    TOOLS["checkpy"].run(container, {"repo": "spcourse/tests", "args": "hello"})

    assert len(container.commands) == 2
    assert container.commands[0].endswith("-d spcourse/tests")
    assert container.commands[1].endswith("--json hello")


def test_checkpy_drops_output_printed_before_the_json():
    class FakeExec:
        output = b"DeprecationWarning: something\n[{}]"

    class FakeContainer:
        def exec_run(self, command):
            return FakeExec()

    output = TOOLS["checkpy"].run(FakeContainer(), {"repo": "r", "args": "a"})

    assert output == "[{}]"
