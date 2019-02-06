import redis
import rq
import docker
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
        self.finished_registry = rq.registry.FinishedJobRegistry('default', queue=self.queue)
        self.n_workers = n_workers

    def __enter__(self):
        # Spawn as many workers as requested
        for _ in range(self.n_workers):
            process = subprocess.Popen(
                ["rq", "worker", "--url", "redis://redis:6379"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
        return self

    def __exit__(self, type, value, traceback):
        # Find all workers
        workers = rq.Worker.all(queue=self.queue)

        # Politely ask workers to kys (warm shutdown)
        for worker in workers:
            try:
                worker.request_stop(signal.SIGINT, None)
            except rq.worker.StopRequested:
                # Once worker is ready to stop, kill
                worker.register_death()

    def start(self, slug, filepath):
        """Starts a job. Returns job_id."""
        return self.queue.enqueue(run_job, slug, filepath).id

    def get(self, id):
        """Get job result. Returns Status and result as parsed json or None."""
        # Get job from queue
        job = self.queue.fetch_job(id)

        # Check if job is in queue
        if job:
            if job.status != "finished":
                return Status.BUSY, None
            else:
                return Status.FINISHED, job.result

        # Retrieve all (non-expired) finished jobs
        finished_ids = self.finished_registry.get_job_ids()

        # If Job is not finished, notify unknown and stop
        if id not in finished_ids:
            return Status.UNKNOWN, None

        # Retrieve finished Job
        job = rq.job.Job.fetch(id, connection=self.cache)
        return Status.FINISHED, job.result


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


def run_job(slug, filepath):
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
        os.remove(filepath)

    return result
