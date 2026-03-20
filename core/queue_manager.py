"""QueueManager — Enqueues article generation jobs to Redis/rq."""
import time
from core.queue_config import get_redis_connection
from core.logger import get_logger

logger = get_logger(__name__)

QUEUE_NAME = "article-queue"
JOB_TIMEOUT = "30m"


class QueueManager:
    """Manages article generation job queue."""

    def __init__(self):
        self.redis = get_redis_connection()
        self._queue = None

    @property
    def available(self):
        return self.redis is not None

    def _get_queue(self, priority="normal"):
        """Get or create rq Queue."""
        if not self.available:
            return None
        from rq import Queue
        queue_name = f"{QUEUE_NAME}-{priority}" if priority != "normal" else QUEUE_NAME
        return Queue(queue_name, connection=self.redis)

    def enqueue_article(self, tenant_id, keyword, row_num=0, dry_run=False, priority="normal"):
        """Enqueue a single article generation job.

        Args:
            tenant_id: Company ID.
            keyword: Target keyword.
            row_num: Sheet row number.
            dry_run: If True, save locally.
            priority: Job priority (high, normal, low).

        Returns:
            rq Job instance, or None if Redis unavailable.
        """
        queue = self._get_queue(priority)
        if not queue:
            logger.warning("Redis unavailable. Job not enqueued: %s/%s", tenant_id, keyword)
            return None

        from jobs.article_job import process_article

        job = queue.enqueue(
            process_article,
            tenant_id=tenant_id,
            keyword=keyword,
            row_num=row_num,
            dry_run=dry_run,
            priority=priority,
            job_timeout=JOB_TIMEOUT,
            description=f"article:{tenant_id}:{keyword[:30]}",
        )
        logger.info("Enqueued: %s/%s (job=%s)", tenant_id, keyword, job.id)
        return job

    def enqueue_tenant_batch(self, tenant_id, keywords, dry_run=False, delay_between=10):
        """Enqueue multiple keywords for a tenant with delay between jobs.

        Args:
            tenant_id: Company ID.
            keywords: List of {keyword, row_num} dicts.
            dry_run: If True, save locally.
            delay_between: Seconds between enqueue operations.

        Returns:
            List of enqueued job IDs.
        """
        job_ids = []
        for i, kw in enumerate(keywords):
            job = self.enqueue_article(
                tenant_id=tenant_id,
                keyword=kw["keyword"],
                row_num=kw.get("row_num", 0),
                dry_run=dry_run,
            )
            if job:
                job_ids.append(job.id)
            if i < len(keywords) - 1 and delay_between > 0:
                time.sleep(delay_between)

        logger.info("Batch enqueued: %d jobs for tenant '%s'", len(job_ids), tenant_id)
        return job_ids

    def get_queue_stats(self):
        """Get queue statistics.

        Returns:
            Dict with pending, started, failed, finished counts.
        """
        if not self.available:
            return {"available": False}

        from rq import Queue
        from rq.registry import StartedJobRegistry, FailedJobRegistry, FinishedJobRegistry

        queue = self._get_queue()
        started = StartedJobRegistry(queue=queue)
        failed = FailedJobRegistry(queue=queue)
        finished = FinishedJobRegistry(queue=queue)

        return {
            "available": True,
            "pending": len(queue),
            "started": len(started),
            "failed": len(failed),
            "finished": len(finished),
        }
