# grading_server

A grading server for student programming submissions, built with Flask. You POST a zipfile, it runs [check50](https://cs50.readthedocs.io/projects/check50/en/latest/) or [checkpy](https://github.com/jelleas/checkpy) against it, and you poll for the result as json.

Every submission is graded inside a throwaway container, so student code never touches the server itself.

## How a job flows

1. You POST a zipfile to `/check50` or `/checkpy`. The server saves it, puts a job on a queue, and immediately hands you a job id.
2. A worker picks the job up, starts a fresh container from [check/Dockerfile](check/Dockerfile) (Python 3.14, installed with uv, with check50 and checkpy preinstalled), and copies the zipfile in.
3. check50 or checkpy runs in that container. The container is then stopped and deleted.
4. The output is parsed into a compact json result, stored under the job id, and optionally POSTed to a webhook you gave.
5. You GET `/get/<id>` to fetch it.

Running that requires three pieces, and `podman compose` starts the first two for you:

| piece | what it is |
| --- | --- |
| `scheduler` | the Flask app plus four queue workers, reachable on port 8080 |
| `redis` | holds the job queue and the finished results |
| `grading_server_check` | the image the workers launch per job. Not a running service - it is started and destroyed per submission |

## Prerequisites

- **podman** - runs the containers. `brew install podman` on Mac, or your package manager on Linux.
- **docker-compose** - `podman compose` does not implement compose itself, it shells out to an external provider. Without it every `podman compose` command below fails immediately. `brew install docker-compose` on Mac.
- **On Mac and Windows**, containers cannot run natively, so podman runs them inside a small Linux VM that you have to start once:

  ```sh
  podman machine init   # only the very first time
  podman machine start
  ```

- **About 5 GB of disk**, and patience for the first build: the check image carries a full scientific Python stack (numpy, pandas, matplotlib, opencv, jupyter) and takes many minutes to build. That is normal, do not kill it.

## Setup

Both steps are per clone - `secrets/` and `.env` are gitignored, so a fresh clone has neither.

### 1. Create the secrets

```sh
mkdir -p secrets
echo 'your-password-here' > secrets/app_password.txt
touch secrets/gh_auth.txt
```

- `app_password.txt` - every grading request must send this password. Pick anything.
- `gh_auth.txt` - GitHub credentials for fetching *private* test repositories, in the format `<gh_username>:<gh_personal_access_token>`, using a classic token with repo access. Leave the file empty if your test repos are public, but do create it: compose refuses to start if either file is missing.

### 2. Create the .env

The server starts the check containers by talking to podman's socket, which compose mounts into it. It needs to know the user id that podman runs as, so it can find that socket:

```sh
echo "UID=$(id -u)" > .env
```

**On Mac and Windows**, containers run inside the VM, so the id that matters is the one *inside* it, not your own:

```sh
echo "UID=$(podman machine ssh id -u)" > .env
```

### 3. Enable the podman socket

The socket is not on by default. Run this as the same user whose id you just put in `.env`.

On Linux:

```sh
systemctl --user enable --now podman.socket
```

On Mac and Windows, run it inside the VM:

```sh
podman machine ssh
systemctl --user enable --now podman.socket
exit
```

While in there, you may also need subordinate id ranges, which is what lets a rootless container create users of its own. Check with `cat /etc/subuid` - if the user running podman (`core` in the podman machine, your own user on Linux) already has a line, you are done. The deployment box runs podman as `app_user`, hence:

```sh
echo 'app_user:100000:65536' >> /etc/subuid
echo 'app_user:100000:65536' >> /etc/subgid
```

## Build and run

```sh
bash build.sh        # builds the app image and the check image
podman compose up    # starts the server on http://localhost:8080
```

Everyday commands:

```sh
podman compose up -d              # run in the background
podman compose logs -f scheduler  # follow the server logs
podman compose down               # stop everything
bash build.sh && podman compose up -d --force-recreate   # after changing code
```

## Check that it works

Open <http://localhost:8080>. It serves a small form for both tools, which is the quickest way to confirm the server is alive without touching curl. <http://localhost:8080/rq> shows the queue and its workers.

End to end from the command line, using a public CS50 problem:

```sh
cat > hello.py <<'EOF'
name = input("What is your name? ")
print(f"hello, {name}")
EOF
zip hello.zip hello.py

curl -F 'file=@hello.zip' \
     -F slug='cs50/problems/2024/x/sentimental/hello' \
     -F password="$(cat secrets/app_password.txt)" \
     localhost:8080/check50
```

That returns a job id. Grading takes some seconds, so poll until the status is `finished`:

```sh
curl localhost:8080/get/<id>
```

You should see `"passed_check_count": 3`. The same submission through checkpy, whose tests live in a GitHub repository rather than in a slug:

```sh
curl -F 'file=@hello.zip' \
     -F repo='spcourse/tests' \
     -F args='hello' \
     -F password="$(cat secrets/app_password.txt)" \
     localhost:8080/checkpy
```

To watch the throwaway containers appear and disappear while a job runs, talk to the same socket the server uses:

```sh
podman --url=unix:///run/user/0/podman/podman.sock ps
```

## Starting a grading job

There are two endpoints, one per grading tool. Both take the submission tagged as `file`, and the `password` from `secrets/app_password.txt`. `file` is normally a zipfile; send a single loose file instead and the server zips it for you, keeping its name, which is handy for trying something out quickly. Both also accept an optional `webhook`: if the job succeeds, the webhook is triggered with a POST request whose json payload is `{"id": <job_id>, "result": <the result below>}`.

### check50

POST to `/check50` (`/check50v3` is an alias) with a `slug` like `cs50/problems/2024/x/sentimental/hello`.

```sh
curl -F 'file=@hello.zip' \
     -F slug='cs50/problems/2024/x/sentimental/hello' \
     -F password='<password>' \
     localhost:8080/check50
```

### checkpy

POST to `/checkpy` with a `repo` holding the tests, like `spcourse/tests`, and the `args` to pass to checkpy, which is usually the name of the file to check.

```sh
curl -F 'file=@hello.zip' \
     -F repo='spcourse/tests' \
     -F args='hello' \
     -F password='<password>' \
     localhost:8080/checkpy
```

Either way the server responds with a json object like so:

```json
{
  "id":"e83d0142-61e9-4ea7-bddf-b1f2ac15c9a2",
  "message":"use /get/<id> to get results",
  "result":null,
  "status":null
}
```

## Retrieving results

Send a GET request to `/get/<id>`

For instance via curl
`curl localhost:8080/get/e83d0142-61e9-4ea7-bddf-b1f2ac15c9a2`

The server will respond with a json object like so:

```json
{
  "id": "e83d0142-61e9-4ea7-bddf-b1f2ac15c9a2",
  "message": "job is finished",
  "status": "finished",
  "result": {
    "tool": {
      "name": "check50",
      "args": {
        "slug": "cs50/problems/2024/x/sentimental/hello"
      }
    },
    "summary": {
      "total_check_count": 3,
      "passed_check_count": 3
    },
    "runs": [
      {
        "name": "cs50/problems/2024/x/sentimental/hello",
        "checks": [
          {
            "description": ":) hello.py exists.",
            "log": "checking that hello.py exists...",
            "message": "",
            "passed": true
          },
          {
            "description": ":) responds to name Emma.",
            "log": "running python3 hello.py...\nsending input Emma...\nchecking for output \"Emma\"...",
            "message": "",
            "passed": true
          }
        ]
      }
    ],
    "raw": "<the full, unmodified output of the grading tool>"
  }
}
```

checkpy reports one run per file it tested, so `runs` can hold more than one entry. `status` is one of `unknown`, `queued`, `busy`, `failed` or `finished`; only `finished` carries the result above.

If the grading tool produced something unparseable, `result` holds an error instead:

```json
{
  "tool": {"name": "check50", "args": {"slug": "..."}},
  "error": "Invalid JSON output from check50:\n...",
  "raw": "<what the tool printed>"
}
```

## Adding another grading tool

Say you want to grade with a tool called `mytool`. Each tool is one entry in [app/tools.py](app/tools.py) plus a parser in [app/response.py](app/response.py); its endpoint, queueing, container, and result storage all come for free.

### 1. Install it in the check image

Add it to the `uv pip install` block in [check/Dockerfile](check/Dockerfile), then `bash build.sh`. Installs happen as the `ubuntu` user into the `/opt/venv` virtualenv, which is also what `python3` and `pip` in that image point at.

Your tool must **print json on stdout**. Everything the command writes is captured together, stdout and stderr merged, and handed to your parser — so a stray warning from the interpreter ends up in the text being parsed. That is why the check image compiles bytecode at build time, and why checkpy's output is trimmed up to its first `[`.

### 2. Write a parser

In [app/response.py](app/response.py), next to `create_check50_response` and `create_checkpy_response`:

```python
def create_mytool_response(target: str, output: str) -> Response | ErrorResponse:
    try:
        json_output = json.loads(output)
    except json.JSONDecodeError:
        return ErrorResponse(
            tool="mytool",
            args={"target": target},
            message=f"Invalid JSON output from mytool:\n{output}",
            raw=output
        )

    results = [
        Result(
            passed=check["ok"],
            description=f"{':)' if check['ok'] else ':('} {check['title']}",
            message=check.get("hint", ""),
            log=check.get("stdout", "")
        )
        for check in json_output["checks"]
    ]

    return Response(
        runs=[Run(name=target, results=results)],
        n_tests=len(results),
        n_passed=sum(1 for r in results if r.passed),
        tool="mytool",
        args={"target": target},
        raw=output
    )
```

Two conventions worth keeping: return an `ErrorResponse` rather than raising whenever the output is not what you expect, and prefix descriptions with `:)`, `:(` or `:|` for passed, failed and undecided, so every tool renders the same way for clients.

### 3. Register the tool

In [app/tools.py](app/tools.py):

```python
def run_mytool(container, args):
    return container.exec_run(f"mytool --json {args['target']}").output.decode('utf8')


MYTOOL = Tool(
    name="mytool",                 # serves POST /mytool
    fields=("target",),            # required form fields, in validation order
    run=run_mytool,
    parse=lambda args, output: create_mytool_response(args["target"], output),
)

TOOLS = {tool.name: tool for tool in (CHECK50, CHECKPY, MYTOOL)}
```

That is the whole wiring: the endpoint, the password check, the `file` upload, the optional `webhook`, the queueing, the `/get/<id>` plumbing **and the form on the demo page** all follow from this entry. `placeholders` is optional and only affects that form; a field without one shows its own name.

Things to know about `run`:

- It executes in `/home/ubuntu/workspace` as the `ubuntu` user, with the submission already unzipped there.
- Command strings are split like shell words but **not** interpreted by a shell, so `;`, `|` and `>` in a form value are inert. They do still arrive as arguments, so validate them yourself if your tool has flags you would not want a caller to set.
- Run as many commands as you need — checkpy fetches its tests with one and grades with the next.
- A job is killed after 600 seconds, and the container is destroyed either way.

### 4. Rebuild and try it

```sh
bash build.sh
podman compose up -d --force-recreate

curl -F 'file=@hello.zip' \
     -F target='hello.py' \
     -F password="$(cat secrets/app_password.txt)" \
     localhost:8080/mytool
```

The demo page on <http://localhost:8080> now has a `mytool` form too, generated from the entry — [app/templates/index.html](app/templates/index.html) loops over the registry and [app/static/script.js](app/static/script.js) wires up whatever forms it finds, so neither file needs editing.

Jobs are queued by tool name, so let the queue drain before deploying a change that renames or removes a tool — an in-flight job naming a tool that no longer exists will fail.

## Running the tests

The tests cover the parsing of check50 and checkpy output, and need neither Redis nor podman:

```sh
pip install -r requirements-dev.txt
pytest
```

The fixtures under `tests/fixtures/` are real captured output from both tools; [tests/fixtures/README.md](tests/fixtures/README.md) records how to recapture them.

## Troubleshooting

**`executing /opt/homebrew/bin/docker-compose: no such file`, or compose does nothing**
The compose provider is missing. Install docker-compose (see Prerequisites).

**`secrets/app_password.txt: no such file or directory`**
Compose will not start without both secret files. See Setup step 1; `gh_auth.txt` may be empty but must exist.

**The scheduler container starts and exits immediately**
Check `podman compose logs scheduler`. A traceback ending in `FileNotFoundError: '/run/secrets/app_password'` means the secret did not reach the container - recreate it and `podman compose up --force-recreate`.

**Jobs never leave `busy`, or the logs show a podman connection error**
The server cannot reach the podman socket. Three usual causes: `UID` in `.env` does not match the user running podman (on Mac it must come from `podman machine ssh id -u`, not from your Mac account), the socket was never enabled (Setup step 3), or, on Mac and Windows, the VM is not running - `podman machine start`.

**`incorrect password`**
The `password` field must match `secrets/app_password.txt` exactly. Note that `echo` adds a trailing newline; the server strips it, so that is fine, but a shell that does not strip it on your side is not.

**The first build seems stuck**
It is not. The check image is around 4 GB and installs a full scientific Python stack. `podman images` in another terminal shows progress.
