#!/usr/bin/env python3
"""Health Check — Verifies system health for monitoring.

Usage:
    python health_check.py              # Print status
    python health_check.py --json       # JSON output
    python health_check.py --alert      # Exit code 1 if unhealthy
"""
import argparse
import json
import sys
from datetime import datetime
from core.queue_config import is_redis_available, get_redis_connection
from core.tenant_config import TenantConfig
from core.logger import setup_logger, get_logger

setup_logger()
logger = get_logger("health")


def check_health():
    """Run all health checks.

    Returns:
        Dict with health status.
    """
    checks = {
        "timestamp": datetime.now().isoformat(),
        "status": "healthy",
        "redis": False,
        "workers_active": 0,
        "tenants_configured": 0,
        "queue_pending": 0,
        "queue_failed": 0,
        "issues": [],
    }

    # Check Redis
    checks["redis"] = is_redis_available()
    if not checks["redis"]:
        checks["issues"].append("Redis is not available")

    # Check tenants
    try:
        tenants = TenantConfig.list_all()
        checks["tenants_configured"] = len(tenants)
        if not tenants:
            checks["issues"].append("No tenants configured")
    except Exception as e:
        checks["issues"].append(f"Tenant config error: {e}")

    # Check queue stats
    if checks["redis"]:
        try:
            from rq import Queue
            from rq.worker import Worker as RqWorker
            conn = get_redis_connection()

            # Workers
            workers = RqWorker.all(connection=conn)
            checks["workers_active"] = len(workers)
            if not workers:
                checks["issues"].append("No active workers")

            # Queue
            q = Queue("article-queue", connection=conn)
            checks["queue_pending"] = len(q)

            from rq.registry import FailedJobRegistry
            failed = FailedJobRegistry(queue=q)
            checks["queue_failed"] = len(failed)
            if len(failed) > 5:
                checks["issues"].append(f"{len(failed)} failed jobs in queue")

        except ImportError:
            checks["issues"].append("rq not installed")
        except Exception as e:
            checks["issues"].append(f"Queue check error: {e}")

    # Determine overall status
    if not checks["redis"] or checks["tenants_configured"] == 0:
        checks["status"] = "critical"
    elif checks["workers_active"] == 0 or checks["queue_failed"] > 5:
        checks["status"] = "degraded"

    return checks


def main():
    parser = argparse.ArgumentParser(description="Article Factory Health Check")
    parser.add_argument("--json", action="store_true", help="JSON output")
    parser.add_argument("--alert", action="store_true", help="Exit 1 if unhealthy")
    args = parser.parse_args()

    health = check_health()

    if args.json:
        print(json.dumps(health, indent=2))
    else:
        print(f"Status: {health['status'].upper()}")
        print(f"Redis: {'OK' if health['redis'] else 'DOWN'}")
        print(f"Workers: {health['workers_active']}")
        print(f"Tenants: {health['tenants_configured']}")
        print(f"Queue Pending: {health['queue_pending']}")
        print(f"Queue Failed: {health['queue_failed']}")
        if health["issues"]:
            print(f"Issues:")
            for issue in health["issues"]:
                print(f"  - {issue}")

    if args.alert and health["status"] != "healthy":
        sys.exit(1)


if __name__ == "__main__":
    main()
