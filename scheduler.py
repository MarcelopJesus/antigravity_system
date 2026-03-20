#!/usr/bin/env python3
"""Scheduler — Triggers article generation at configured times.

Usage:
    python scheduler.py                 # Run once (for cron)
    python scheduler.py --daemon        # Run continuously (APScheduler)
    python scheduler.py --tenant mjesus # Process only one tenant
    python scheduler.py --dry-run       # Enqueue in dry-run mode
"""
import argparse
import sys
import time
from datetime import datetime
from core.tenant_config import TenantConfig
from core.queue_manager import QueueManager
from core.queue_config import is_redis_available
from core.sheets_client import SheetsClient
from core.logger import setup_logger, get_logger

setup_logger()
logger = get_logger("scheduler")


def schedule_tenant(tc, qm, dry_run=False):
    """Enqueue pending keywords for a single tenant.

    Args:
        tc: TenantConfig instance.
        qm: QueueManager instance.
        dry_run: If True, jobs will save locally instead of publishing.

    Returns:
        Number of jobs enqueued.
    """
    schedule = tc.get_schedule()
    max_articles = schedule.get("max_articles_per_run", 1)

    try:
        sheets = SheetsClient('config/service_account.json')
        pending = sheets.get_pending_rows(tc.spreadsheet_id)

        if not pending:
            logger.info("[%s] No pending keywords.", tc.company_id)
            return 0

        # Limit to max_articles_per_run
        batch = pending[:max_articles]
        logger.info("[%s] Found %d pending, scheduling %d (max=%d)",
                    tc.company_id, len(pending), len(batch), max_articles)

        jobs = qm.enqueue_tenant_batch(
            tenant_id=tc.company_id,
            keywords=batch,
            dry_run=dry_run,
            delay_between=5,
        )
        return len(jobs)

    except Exception as e:
        logger.error("[%s] Scheduling failed: %s", tc.company_id, e)
        return 0


def run_once(tenant_filter=None, dry_run=False):
    """Run scheduler once — enqueue jobs for all (or one) tenant(s).

    Designed to be called by cron.
    """
    logger.info("=" * 60)
    logger.info("Scheduler started at %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))
    logger.info("=" * 60)

    if not is_redis_available():
        logger.error("Redis is not available. Cannot enqueue jobs.")
        return 1

    qm = QueueManager()
    tenants = TenantConfig.list_all()

    if tenant_filter:
        tenants = [t for t in tenants if t == tenant_filter]

    if not tenants:
        logger.warning("No tenants found.")
        return 0

    total_enqueued = 0
    for tenant_id in tenants:
        try:
            tc = TenantConfig.load(tenant_id)
            count = schedule_tenant(tc, qm, dry_run=dry_run)
            total_enqueued += count
        except Exception as e:
            logger.error("Error loading tenant '%s': %s", tenant_id, e)

    logger.info("=" * 60)
    logger.info("Scheduler complete: %d job(s) enqueued for %d tenant(s)",
                total_enqueued, len(tenants))
    logger.info("=" * 60)
    return 0


def main():
    parser = argparse.ArgumentParser(description="Article Factory Scheduler")
    parser.add_argument("--daemon", action="store_true", help="Run continuously")
    parser.add_argument("--tenant", type=str, default=None, help="Process only this tenant")
    parser.add_argument("--dry-run", action="store_true", help="Dry-run mode")
    parser.add_argument("--interval", type=int, default=3600, help="Daemon check interval in seconds")
    args = parser.parse_args()

    if args.daemon:
        logger.info("Starting scheduler in daemon mode (interval=%ds)...", args.interval)
        while True:
            try:
                run_once(tenant_filter=args.tenant, dry_run=args.dry_run)
            except KeyboardInterrupt:
                logger.info("Scheduler stopped.")
                break
            except Exception as e:
                logger.error("Scheduler error: %s", e)
            time.sleep(args.interval)
    else:
        exit_code = run_once(tenant_filter=args.tenant, dry_run=args.dry_run)
        sys.exit(exit_code)


if __name__ == "__main__":
    main()
