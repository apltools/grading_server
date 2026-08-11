# Fixtures

Captured from the real tools in the `grading_server_check` image, so that the
tests break when check50 or checkpy changes its output format.

To recapture, with `hello.py` in the current directory:

```sh
podman run --rm -v "$PWD/hello.py:/home/ubuntu/workspace/hello.py:ro,z" grading_server_check \
    check50 --local -o json -- cs50/problems/2024/x/sentimental/hello

podman run --rm -v "$PWD/hello.py:/home/ubuntu/workspace/hello.py:ro,z" grading_server_check \
    sh -c 'python3 -m checkpy -d spcourse/tests > /dev/null; python3 -m checkpy --json hello'
```

| fixture | how it was produced |
| --- | --- |
| `check50_pass.json` | a `hello.py` that asks for a name and greets it |
| `check50_fail.json` | a `hello.py` that prints `goodbye`, so both greeting checks fail with a `cause` |
| `check50_missing_files.json` | no `hello.py` at all, so check50 reports a top level `error` and no `results` |
| `checkpy_pass.json` | a `hello.py` that prints `Hello, world!` |
| `checkpy_fail.json` | a `hello.py` that prints `nope` |
| `checkpy_timeout.json` | hand written: checkpy emits `nTests: 0` with an ANSI coloured message when a run times out, which is awkward to trigger on demand |
