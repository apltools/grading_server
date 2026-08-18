import json
import re

from dataclasses import dataclass

@dataclass
class Result:
    passed: bool | None
    description: str
    message: str = ""
    log: str = ""

    MAX_LOG_LENGTH = 10000

    def __post_init__(self):
        if len(self.log) > self.MAX_LOG_LENGTH:
            self.log = (
                "Too Long Truncated Log:\n"
                + self.log[:self.MAX_LOG_LENGTH//2]
                + "\n...\n"
                + self.log[-self.MAX_LOG_LENGTH//2:]
            )

    def to_json(self):
        return {
            "description": self.description,
            "log": self.log,
            "message": self.message,
            "passed": self.passed,
        }

@dataclass
class Run:
    name: str
    results: list[Result]

    def to_json(self):
        return {
            "name": self.name,
            "checks": [r.to_json() for r in self.results]
        }

@dataclass
class Response:
    runs: list[Run]
    n_tests: int
    n_passed: int
    tool: str
    args: dict[str, str]
    raw: str

    MAX_FIELD_LENGTH = 10000

    @staticmethod
    def _remove_long_strings(obj, max_len=10_000):
        if isinstance(obj, dict):
            return {k: Response._remove_long_strings(v, max_len) for k, v in obj.items()}

        if isinstance(obj, list):
            return [Response._remove_long_strings(v, max_len) for v in obj]

        if isinstance(obj, str):
            if len(obj) <= max_len:
                return obj

            return (
                f"Truncated (length > {max_len})\n"
                + obj[:max_len]
            )

        return obj

    def __post_init__(self):
        try:
            parsed_json = json.loads(self.raw)
        except json.JSONDecodeError:
            parsed_json = self.raw
        self.raw = str(Response._remove_long_strings(parsed_json, self.MAX_FIELD_LENGTH))

    def to_json(self):
        return {
            "tool": {
                "name": self.tool,
                "args": self.args,
            },
            "summary": {
                "total_check_count": self.n_tests,
                "passed_check_count": self.n_passed,
            },
            "runs": [r.to_json() for r in self.runs],
            "raw": self.raw
        }


@dataclass
class ErrorResponse:
    tool: str
    args: dict[str, str]
    message: str
    raw: str

    MAX_FIELD_LENGTH = 10000

    def __post_init__(self):
        self.raw = self.raw[:ErrorResponse.MAX_FIELD_LENGTH]

    def to_json(self):
        return {
            "tool": {
                "name": self.tool,
                "args": self.args,
            },
            "error": self.message,
            "raw": self.raw
        }


def create_check50_response(slug: str, output: str) -> Response | ErrorResponse:
    try:
        json_output = json.loads(output)
    except json.JSONDecodeError:
        return ErrorResponse(
            tool="check50",
            args={"slug": slug},
            message=f"Invalid JSON output from check50:\n{output}",
            raw=output
        )

    # check50 reports an error instead of results when it could not run at all,
    # like when the submission is missing a required file
    if "results" not in json_output:
        error = json_output.get("error", {})
        message = error.get("value") or "check50 produced no results"
        return ErrorResponse(
            tool="check50",
            args={"slug": slug},
            message=f"check50 failed: {message}",
            raw=output
        )

    results = get_check50_results(json_output)

    run = Run(name=slug, results=results)

    n_tests = len(json_output["results"])

    n_passed = 0
    for result in json_output["results"]:
        n_passed += 1 if result["passed"] else 0

    return Response(
        runs=[run],
        n_tests=n_tests,
        n_passed=n_passed,
        tool="check50",
        args={
            "slug": slug
        },
        raw=output
    )

def create_checkpy_response(repo: str, args: str, output: str) -> Response | ErrorResponse:
    try:
        json_output = json.loads(output)
    except json.JSONDecodeError:
        return ErrorResponse(
            tool="checkpy",
            args={
                "repo": repo,
                "args": args
            },
            message=f"Invalid JSON output from checkpy:\n{output}",
            raw=output
        )

    n_tests = 0
    for run in json_output:
        n_tests += run["nTests"]

    # n_tests is 0 if any nTests == 0 (Timeout reached)
    if any(run["nTests"] == 0 for run in json_output):
        n_tests = 0

    runs: list[Run] = []
    for run in json_output:
        runs.append(Run(
            name=run["name"],
            results=get_checkpy_results(run)
        ))

    n_passed = 0
    for run in json_output:
        n_passed += run["nPassed"]

    # n_passed is 0 if any nPassed == 0 (Timeout reached)
    if any(run["nPassed"] == 0 for run in json_output):
        n_passed = 0

    return Response(
        runs=runs,
        n_tests=n_tests,
        n_passed=n_passed,
        tool="checkpy",
        args={
            "repo": repo,
            "args": args
        },
        raw=output
    )

# run_checknb reports back with this when the submission holds no notebook,
# in which case there is no checknb output to parse at all
CHECKNB_NO_NOTEBOOK = "checknb: no .ipynb file in the submission"

def create_checknb_response(output: str) -> Response | ErrorResponse:
    if output == CHECKNB_NO_NOTEBOOK:
        return ErrorResponse(
            tool="checknb",
            args={},
            message="checknb failed: the submission contains no .ipynb file",
            raw=output
        )

    try:
        json_output = json.loads(output)
    except json.JSONDecodeError:
        return ErrorResponse(
            tool="checknb",
            args={},
            message=f"Invalid JSON output from checknb:\n{output}",
            raw=output
        )

    n_tests = 0
    for run in json_output:
        n_tests += run["nTests"]

    n_passed = 0
    for run in json_output:
        n_passed += run["nPassed"]

    runs: list[Run] = []
    for run in json_output:
        runs.append(Run(
            name=run["name"],
            results=get_checknb_results(run)
        ))

    return Response(
        runs=runs,
        n_tests=n_tests,
        n_passed=n_passed,
        tool="checknb",
        args={},
        raw=output
    )

def get_check50_results(check: dict) -> list[Result]:
    check50_results: list[Result] = []
    for result in check["results"]:
        descr: str = result["description"]

        smiley = ":)"
        if result["passed"] is False:
            smiley = ":("
        elif result["passed"] is None:
            smiley = ":|"
        
        descr = f"{smiley} {descr}"

        message = ""
        if result.get("cause") is not None:
            message = result["cause"]["rationale"]

            if result["cause"].get("help") is not None:
                message += "    \n" + result["cause"]["help"]

        log = ""
        if "log" in result:
            log = "\n".join(result["log"])

        check50_results.append(Result(
            passed=result["passed"],
            description=descr,
            message=message,
            log=log
        ))
    
    return check50_results

def get_checkpy_results(check: dict) -> list[Result]:
    if check["nTests"] == 0:
        return [Result(
            passed=None,
            description=re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', check["output"][0]),
            message="",
            log=""
        )]

    checkpy_results: list[Result] = []
    for result in check["results"]:
        descr: str = result["description"]

        smiley = ":)"
        if result["passed"] is False:
            smiley = ":("
        elif result["passed"] is None:
            smiley = ":|"
        
        descr = f"{smiley} {descr}"

        checkpy_results.append(Result(
            passed=result["passed"],
            description=descr,
            message=result["message"],
            log=result["output"]
        ))
    
    return checkpy_results

def get_checknb_results(check: dict) -> list[Result]:
    if check["nTests"] == 0:
        return [Result(
            passed=None,
            description=re.sub(r'\x1B\[[0-?]*[ -/]*[@-~]', '', check["output"][0]),
            message="",
            log=""
        )]

    checknb_results: list[Result] = []
    for result in check["results"]:
        # checknb reports tests it could not judge automatically as "manual"
        passed = result["passed"]
        if result["status"] == "manual":
            passed = None

        smiley = ":)"
        if passed is False:
            smiley = ":("
        elif passed is None:
            smiley = ":|"

        points = f"{result['points']:g}/{result['maxPoints']:g}"
        descr = f"{smiley} {result['description']} {points}"

        message = result["message"]
        if result["exception"] is not None:
            message = f"{result['exception']}: {message}" if message else result["exception"]

        checknb_results.append(Result(
            passed=passed,
            description=descr,
            message=message,
            log=result["output"]
        ))

    return checknb_results