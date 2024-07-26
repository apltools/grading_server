import docker
import subprocess
import json
import os
import requests
import rq
import contextlib
import os

if os.path.exists("certs/gh_auth.txt"): 
    with open("certs/gh_auth.txt") as f:
        GH_AUTH = f.read().strip()
else:
    GH_AUTH = None

class JobError(Exception):
    pass

class CheckContainer:
    docker_image = "grading_server-check"

    def __enter__(self):
        client = docker.from_env()

        # Start check50 container
        self.container = client.containers.run(self.docker_image, detach=True, tty=True)
        print(f"STARTED container {self.container.id}")

        return self.container

    def __exit__(self, type, value, traceback):
        self.container.stop()
        print(f"STOPPED container {self.container.id}")

        self.container.remove()
        print(f"REMOVED container {self.container.id}")


def parse(output):
    try:
        return json.loads(output)
    except:
        raise JobError(f"Could not parse json crashed, output: {output}")


def trigger(webhook, json):
    if webhook:
        try:
            requests.post(webhook, json={"id":rq.get_current_job().id, "result":json})
        except requests.exceptions.ConnectionError:
            raise JobError(f"Could not trigger webhook: {webhook}, connection refused")


def checkpy(repo, args, filepath, webhook):
    gh_auth = f"--gh-auth {GH_AUTH}" if GH_AUTH else ""
    with job(filepath) as container:
        container.exec_run(f"python3 -m checkpy {gh_auth} -d {repo}")
        output = container.exec_run(f"python3 -m checkpy {gh_auth} --json {args}").output.decode('utf8')

        # rm any output until the first open square bracket
        # to prevent any python warnings from breaking json.parse
        for i, line in enumerate(output.split("\n")):
            if line.strip().startswith("["):
                output = "\n".join(output.split("\n")[i:])
                break

        json = {"checkpy": parse(output)}
        trigger(webhook, json)
    return json


def check50(slug, filepath, webhook):
    with job(filepath) as container:
        output = container.exec_run(f"check50 --local -o json -- {slug}").output.decode('utf8')
        json = {"check50": parse(output)}
        trigger(webhook, json)
    return json


@contextlib.contextmanager
def job(filepath, container_type=CheckContainer):
    try:
        # In check container
        with container_type() as container:
            # Copy filepath (zipfile) to container
            process = subprocess.Popen(
                ["docker", "cp", filepath, f"{container.id}:/home/ubuntu/workspace"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            process.wait()

            # Unzip and remove
            container.exec_run(f"unzip {os.path.basename(filepath)}")
            container.exec_run(f"rm {os.path.basename(filepath)}")

            # Yield to run check tool
            yield container
    finally:
        # Remove local file
        os.remove(filepath)
