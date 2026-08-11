"""The grading tools this server exposes.

Every tool gets a POST endpoint named after it, runs inside a throwaway
container built from check/Dockerfile, and has its output parsed into the
Response that /get/<id> hands back.

Adding one means adding a Tool below and a parser in response.py. See the
"Adding another grading tool" section of the readme.
"""
import os

from dataclasses import dataclass, field
from typing import Callable

from response import Response, ErrorResponse, create_check50_response, create_checkpy_response

if os.path.exists("/run/secrets/gh_auth"):
    with open("/run/secrets/gh_auth") as f:
        GH_AUTH = f.read().strip()
else:
    GH_AUTH = None


@dataclass(frozen=True)
class Tool:
    # the name of the tool, which doubles as its route: /<name>
    name: str

    # form fields the request must carry, in the order they are validated
    fields: tuple[str, ...]

    # run the tool in the container, and return whatever it printed
    run: Callable[..., str]

    # turn that output into a Response, or an ErrorResponse if it makes no sense
    parse: Callable[[dict, str], Response | ErrorResponse]

    # additional routes serving this same tool
    aliases: tuple[str, ...] = field(default_factory=tuple)


def run_check50(container, args):
    return container.exec_run(f"check50 --local -o json -- {args['slug']}").output.decode('utf8')


def run_checkpy(container, args):
    gh_auth = f"--gh-auth {GH_AUTH}" if GH_AUTH else ""

    # download the tests before running them
    container.exec_run(f"python3 -m checkpy {gh_auth} -d {args['repo']}")

    output = container.exec_run(f"python3 -m checkpy {gh_auth} --json {args['args']}").output.decode('utf8')

    # rm any output until the first open square bracket
    # to prevent any python warnings from breaking json.parse
    for i, line in enumerate(output.split("\n")):
        if line.strip().startswith("["):
            return "\n".join(output.split("\n")[i:])

    return output


CHECK50 = Tool(
    name="check50",
    fields=("slug",),
    run=run_check50,
    parse=lambda args, output: create_check50_response(args["slug"], output),
    aliases=("check50v3",),
)

CHECKPY = Tool(
    name="checkpy",
    fields=("repo", "args"),
    run=run_checkpy,
    parse=lambda args, output: create_checkpy_response(args["repo"], args["args"], output),
)

TOOLS = {tool.name: tool for tool in (CHECK50, CHECKPY)}
