import redis
import rq
import collections
import enum
import subprocess
import json
import signal

import work


class Status(enum.Enum):
    UNKNOWN = enum.auto()
    BUSY = enum.auto()
    FAILED = enum.auto()
    FINISHED = enum.auto()


class Scheduler:
    def __init__(self, n_workers=4):
        self.cache = redis.Redis(host='redis', port=6379)
        self.queue_name = "check50"
        self.queue = rq.Queue(self.queue_name, connection=self.cache)
        self.finished_registry = rq.registry.FinishedJobRegistry("default", queue=self.queue)
        self.n_workers = n_workers

    def __enter__(self):
        # Spawn as many workers as requested
        for _ in range(self.n_workers):
            process = subprocess.Popen(
                ["rq", "worker", self.queue_name, "--url", "redis://redis:6379"],
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT)
        return self

    def __exit__(self, type=None, value=None, traceback=None):
        # Find all workers
        workers = rq.Worker.all(queue=self.queue)

        # Politely ask workers to kys (warm shutdown)
        for worker in workers:
            try:
                worker.request_stop(signal.SIGINT, None)
            except rq.worker.StopRequested:
                # Once worker is ready to stop, kill
                worker.register_death()

    def start_check50(self, slug, filepath, webhook):
        """Starts a check50 job. Returns job_id."""
        return self.queue.enqueue(work.check50, slug, filepath, webhook).id

    def start_checkpy(self, repo, args, filepath, webhook):
        """Starts a checkpy job. Returns job_id."""
        return self.queue.enqueue(work.checkpy, repo, args, filepath, webhook).id

    def get(self, id):
        """Get job result. Returns Status and result as parsed json or None."""
        # Get job from queue
        job = self.queue.fetch_job(id)

        # Check if job is in queue
        if job:
            print(job.status)

            if job.status == "finished":
                return Status.FINISHED, job.result

            if job.status == "failed":
                return Status.FAILED, job.exc_info

            return Status.BUSY, None

        # Retrieve all (non-expired) finished jobs
        finished_ids = self.finished_registry.get_job_ids()

        # If Job is not finished, notify unknown and stop
        if id not in finished_ids:
            return Status.UNKNOWN, None

        # Retrieve finished Job
        job = rq.job.Job.fetch(id, connection=self.cache)
        return Status.FINISHED, job.result
