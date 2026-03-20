#!/usr/bin/env python3
"""Worker entry point — starts rq workers for article generation.

Usage:
    python worker.py                    # Start 1 worker
    python worker.py --workers 3        # Start 3 workers (use Supervisor in production)
"""
import argparse
import sys
from core.queue_config import get_redis_connection, is_redis_available
from core.logger import setup_logger, get_logger

setup_logger()
logger = get_logger("worker")


def main():
    parser = argparse.ArgumentParser(description="Article Factory Worker")
    parser.add_argument("--workers", type=int, default=1, help="Number of workers (default: 1)")
    parser.add_argument("--queues", type=str, default="article-queue-high,article-queue,article-queue-low",
                        help="Comma-separated queue names (priority order)")
    args = parser.parse_args()

    if not is_redis_available():
        logger.error("Redis is not available. Start Redis first: redis-server")
        sys.exit(1)

    from rq import Worker

    conn = get_redis_connection()
    queues = [q.strip() for q in args.queues.split(",")]

    logger.info("Starting %d worker(s) listening on: %s", args.workers, queues)

    # For single worker, run directly
    # For multiple workers, use Supervisor in production
    worker = Worker(queues, connection=conn)
    worker.work(with_scheduler=True)


if __name__ == "__main__":
    main()
