import contextlib
import os
import subprocess

import docker
import requests
import rq

from tools import TOOLS


class JobError(Exception):
    pass

class CheckContainer:
    docker_image = "grading_server_check"

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


def trigger(webhook, result):
    if webhook:
        try:
            requests.post(webhook, json={"id":rq.get_current_job().id, "result":result})
        except requests.exceptions.ConnectionError:
            raise JobError(f"Could not trigger webhook: {webhook}, connection refused")


def run(tool_name, args, filepath, webhook):
    """Grade the submission in filepath with a tool, by name. Returns its result.

    This is what the rq workers run, so both arguments are plain data: a Tool
    itself holds functions and cannot survive being queued.
    """
    tool = TOOLS[tool_name]

    with job(filepath) as container:
        output = tool.run(container, args)
        result = tool.parse(args, output).to_json()
        trigger(webhook, result)
    return result


@contextlib.contextmanager
def job(filepath, container_type=CheckContainer):
    try:
        # In check container
        with container_type() as container:
            # Copy filepath (zipfile) to container
            copy = subprocess.run(
                ["podman", f"--url={os.getenv('DOCKER_HOST')}", "cp", filepath, f"{container.id}:/home/ubuntu/workspace"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)

            # Without the submission there is nothing to grade, and the checks
            # would fail with a confusing "file not found" instead
            if copy.returncode != 0:
                raise JobError(f"Could not copy {filepath} to container: {copy.stdout.decode('utf8')}")

            # Unzip and remove
            container.exec_run(f"unzip {os.path.basename(filepath)}")
            container.exec_run(f"rm {os.path.basename(filepath)}")

            # Yield to run check tool
            yield container
    finally:
        # Remove local file
        os.remove(filepath)
