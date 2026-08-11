A simple check50 and checkpy grading server built using Flask.

Submissions are graded in a throwaway container built from [check/Dockerfile](check/Dockerfile), which runs Python 3.14 installed through uv.

## Build

`bash build.sh`

## Running the server

Create a .env file with:

  UID=<your_user_id> # id -u

Create a folder `secrets` within that:

* a file `app_password.txt`. In it store your password for running checks.
* a file `gh_auth.txt`. In it store auth for GitHub in the following format `<gh_username>:<gh_personal_access_token>`. Use a classic token with repo access.

`podman compose up`

### Mac / Windows

```sh
podman machine ssh
echo 'app_user:100000:65536' >> /etc/subuid
echo 'app_user:100000:65536' >> /etc/subgid
systemctl --user enable --now podman.socket
```

### Linux

```sh
systemctl --user enable --now podman.socket
```

## Running the tests

The tests cover the parsing of check50 and checkpy output, and need neither Redis nor podman:

```sh
pip install -r requirements-dev.txt
pytest
```

## Check if the server is running

Visit http://localhost:8080 for a demo and http://localhost:8080/rq to check on worker status.

To see the check containers a job spins up, talk to the same socket the server uses:

```sh
podman --url=unix:///run/user/0/podman/podman.sock ps
```

## Starting a grading job

There are two endpoints, one per grading tool. Both take a zipfile of the submission tagged as `file`, and the `password` from `secrets/app_password.txt`. Both also accept an optional `webhook`: if the job succeeds, the webhook is triggered with a POST request whose json payload is `{"id": <job_id>, "result": <the result below>}`.

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
