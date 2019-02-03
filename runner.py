import multiprocessing
import collections
import time
import enum
import zipfile
import tempfile
import os
import subprocess
import json

class Status(enum.Enum):
    UNKNOWN = enum.auto()
    BUSY = enum.auto()
    FINISHED = enum.auto()

class Manager:
    def __init__(self):
        self.task_queue = multiprocessing.Queue()
        self.result_queue = multiprocessing.Queue()
        self.process = multiprocessing.Process(target=run, args=(self.task_queue, self.result_queue))
        self.results = {}
        self.status = collections.defaultdict(lambda: Status.UNKNOWN)
        self.process.start()

    def start(self, id, slug, filepath):
        self.task_queue.put((id, slug, filepath))
        self.status[id] = Status.BUSY

    def get(self, id):
        while not self.result_queue.empty():
            result_id, result = self.result_queue.get()
            self.results[result_id] = result
            self.status[result_id] = Status.FINISHED

        result = self.results.get(id)
        status = self.status[id]

        if result:
            del self.results[id]
            self.status[id] = Status.UNKNOWN

        return status, result

def run(task_queue, result_queue):
    while True:
        id, slug, filepath = task_queue.get()

        # In check50 container
        with Container() as container:
            # Copy filepath (zipfile) to container
            process = subprocess.Popen(
                ["docker", "cp", filepath, f"{container.id}:/check"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            process.wait()

            # Unzip zipfile in container
            process = subprocess.Popen(
                ["docker", "exec", container.id, "unzip", os.path.basename(filepath)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            process.wait()

            # rm zipfile in container
            process = subprocess.Popen(
                ["docker", "exec", container.id, "rm", os.path.basename(filepath)],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            process.wait()

            # Run check50
            process = subprocess.Popen(
                ["docker", "exec", container.id, "python3", "-m", "check50", "-o", "json", slug],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
            result = json.loads(process.stdout.read().decode('utf8'))

            # Remove local file
            process = subprocess.Popen(
                ["rm", filepath],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)

        result_queue.put((id, result))

class Container:
    def __enter__(self):
        # Start check50 container
        process = subprocess.Popen(
            ["docker", "run", "-d", "-t", "grading_server"],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

        self.id = process.stdout.read().strip().decode('utf8')
        print(f"STARTED container {self.id}")

        return self

    def __exit__(self, type, value, traceback):
        # Stop check50 container
        process = subprocess.Popen(
            ["docker", "container", "stop", self.id],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

        stopped_container_id = process.stdout.read().strip()
        print(f"STOPPED container {stopped_container_id}")

        # Remove check50 container
        process = subprocess.Popen(
            ["docker", "container", "rm", self.id],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

        removed_container_id = process.stdout.read().strip()
        print(f"REMOVED container {removed_container_id}")


manager = Manager()
