A simple check50 3.0 grading server build using Flask.

## Build

`bash build.sh`

## Running the server

`docker-compose up`

## Check if the server is running

Visit http://localhost:5000 for a demo and http://localhost:5000/rq to check on worker status.

## Starting a grading job
Send a POST request to `/start/` with a zipfile tagged as `file` and a `slug` like `uva/progik/2018/py/hello` named `slug`. Optionally send a webhook named `webhook`. If the job succeeds, the webhook will be triggered with a POST request and a json payload.

For instance via curl
`curl -F 'file=@files/hello.zip' -F slug='uva/progik/2018/py/hello' localhost:5000/start`

The server will respond with a json object like so:

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
`curl localhost:5000/get/e83d0142-61e9-4ea7-bddf-b1f2ac15c9a2`

The server will respond with a json object like so:

```json
{
  "id": "e83d0142-61e9-4ea7-bddf-b1f2ac15c9a2",
  "message": "job is finished",
  "result": {
    "results": [
      {
        "cause": null,
        "data": {},
        "dependency": null,
        "description": "hello.py exists.",
        "log": [
          "checking that hello.py exists..."
        ],
        "name": "exists",
        "passed": true
      },
      {
        "cause": null,
        "data": {},
        "dependency": "exists",
        "description": "hello.py compiles.",
        "log": [
          "compiling hello.py into byte code..."
        ],
        "name": "compiles",
        "passed": true
      },
      {
        "cause": null,
        "data": {},
        "dependency": "compiles",
        "description": "prints \"hello, world\\n\" ",
        "log": [
          "importing hello"
        ],
        "name": "prints_hello",
        "passed": true
      }
    ],
    "version": "3.0.0"
  },
  "status": "finished"
}
```
