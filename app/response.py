import json

from dataclasses import dataclass

@dataclass
class Result:
    passed: bool | None
    description: str
    message: str = ""
    log: str = ""

    def to_json(self):
        return {
            "description": self.description,
            "log": self.log,
            "message": self.message,
            "passed": self.passed,
        }

@dataclass
class Response:
    results: list[Result]
    n_tests: int
    n_passed: int
    tool: str
    args: dict[str, str]
    raw: str

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
            "checks": self.results,
            "raw": self.raw
        }

@dataclass
class ErrorResponse:
    tool: str
    args: dict[str, str]
    message: str
    raw: str

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

    results = get_check50_results(json_output)

    n_tests = len(json_output["results"])

    n_passed = 0
    for result in json_output["results"]:
        n_passed += 1 if result["passed"] else 0

    return Response(
        results=results,
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

    results: list[Result] = []
    for check in json_output:
        results += get_checkpy_results(check)

    n_tests = 0
    for check in json_output:
        n_tests += check["nTests"]

    n_passed = 0
    for check in json_output:
        n_passed += check["nPassed"]

    return Response(
        results=results,
        n_tests=n_tests,
        n_passed=n_passed,
        tool="checkpy",
        args={
            "repo": repo,
            "args": args
        },
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
