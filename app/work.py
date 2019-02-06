import docker
import subprocess
import json
import os
import requests

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


def run_job(slug, filepath, webhook):
    # In check container
    with CheckContainer() as container:
        # Copy filepath (zipfile) to container
        process = subprocess.Popen(
            ["docker", "cp", filepath, f"{container.id}:/check"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)
        process.wait()

        # Unzip and remove
        container.exec_run(f"unzip {os.path.basename(filepath)}")
        container.exec_run(f"rm {os.path.basename(filepath)}")

        # Run check50
        output = container.exec_run(f"python3 -m check50 -o json {slug}").output.decode('utf8')
        result = json.loads(output)

    # Remove local file
    # os.remove(filepath)

    # Trigger webhook
    if webhook:
        requests.post(webhook, json=result)

    return result
