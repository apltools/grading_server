import docker
import subprocess
import json
import os
import requests
import rq
import contextlib

class JobError(Exception):
    pass


class CheckContainer:
    def __enter__(self):
        client = docker.from_env()

        # Start check50 container
        self.container = client.containers.run("grading_server_check", detach=True, tty=True)
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
    with job(filepath) as container:
        container.exec_run(f"python3 -m checkpy -d {repo}")
        output = container.exec_run(f"python3 -m checkpy --json {args}").output.decode('utf8')
        json = parse(output)
        trigger(webhook, json)
    return json


def check50(slug, filepath, webhook):
    with job(filepath) as container:
        output = container.exec_run(f"python3 -m check50 -o json {slug}").output.decode('utf8')
        json = parse(output)
        trigger(webhook, json)
    return json


@contextlib.contextmanager
def job(filepath):
    try:
        # In check container
        with CheckContainer() as container:
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
