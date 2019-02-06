import redis
import rq
import subprocess
import collections
import time
import enum
import zipfile
import tempfile
import os
import subprocess
import json
import signal


class Status(enum.Enum):
    UNKNOWN = enum.auto()
    BUSY = enum.auto()
    FINISHED = enum.auto()


class Scheduler:
    def __init__(self, n_workers=4):
        self.cache = redis.Redis(host='redis', port=6379)
        self.queue = rq.Queue(connection=self.cache)
        self.n_workers = n_workers
        self.jobs = {}

    def __enter__(self):
        # spawn as many workers as requested
        for _ in range(self.n_workers):
            process = subprocess.Popen(
                ["rq", "worker", "--url", "redis://redis:6379"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
        return self

    def __exit__(self, type, value, traceback):
        # find all workers
        workers = rq.Worker.all(queue=self.queue)

        # politely ask workers to kys (warm shutdown)
        for worker in workers:
            try:
                worker.request_stop(signal.SIGINT, None)
            except rq.worker.StopRequested:
                # Once worker is ready to stop, kill
                worker.register_death()

    def start(self, id, slug, filepath):
        job = self.queue.enqueue(run_job, id, slug, filepath)
        self.jobs[id] = job

    def get(self, id):
        job = self.jobs.get(id, None)

        if job == None:
            return Status.UNKNOWN, None

        result = job.result

        if result:
            return Status.FINISHED, result

        return Status.BUSY, None

class Container:
    def __enter__(self):
        # Start check50 container
        process = subprocess.Popen(
            ["docker", "run", "-d", "-t", "grading_server_check"],
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

        stopped_container_id = process.stdout.read().strip().decode('utf8')
        print(f"STOPPED container {stopped_container_id}")

        # Remove check50 container
        process = subprocess.Popen(
            ["docker", "container", "rm", self.id],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT)

        removed_container_id = process.stdout.read().strip().decode('utf8')
        print(f"REMOVED container {removed_container_id}")


def run_job(id, slug, filepath):
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
        process.wait()

    return result
