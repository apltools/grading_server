A simple check50 3.0 grading server build using Flask.

## Running the server

`bash run.sh`

## Starting a grading job
Send a POST request to `/start/<slug>` with a zipfile tagged as `file`.

For instance via curl
`curl -F 'file=@hello.zip' localhost:5000/start/uva/progik/2018/py/hello`

The server will respond with a json object like so:

```json
{
  "id": "23423a2d-2d74-410e-a577-da7a6f8400aa",
  "message": "use /get/<id> to get results",
  "result": null
}
```

## Retrieving results
Send a GET request to `/get/<id>`

For instance via curl
`curl localhost:5000/get/23423a2d-2d74-410e-a577-da7a6f8400aa`

The server will respond with a json object like so:

```json
{
  "id": "5375d957-7830-4dcf-ad71-9498b0b2b2e6",
  "message": "finished",
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
  }
}
```
