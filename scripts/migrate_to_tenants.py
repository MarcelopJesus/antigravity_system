#!/usr/bin/env python3
"""Migrate from sites.json to config/tenants/ structure.

Usage:
    python scripts/migrate_to_tenants.py              # Execute migration
    python scripts/migrate_to_tenants.py --dry-run     # Preview only
    python scripts/migrate_to_tenants.py --rollback    # Restore backups
"""
import argparse
import json
import os
import re
import shutil
import sys
import yaml

PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SITES_JSON = os.path.join(PROJECT_ROOT, "config", "sites.json")
COMPANIES_DIR = os.path.join(PROJECT_ROOT, "config", "companies")
TENANTS_DIR = os.path.join(PROJECT_ROOT, "config", "tenants")
PROMPTS_PY = os.path.join(PROJECT_ROOT, "config", "prompts.py")


def extract_cta_from_prompts():
    """Extract CTA info from hardcoded prompts.py."""
    try:
        with open(PROMPTS_PY, 'r', encoding='utf-8') as f:
            content = f.read()

        # Extract WhatsApp URL
        url_match = re.search(r'href="(https://wa\.me/[^"]+)"', content)
        # Extract button text
        text_match = re.search(r'→\s*(.+?)</a>', content)
        # Extract box text
        box_match = re.search(r'<p>(.+?)</p>\s*\n\s*<a', content)

        return {
            "type": "whatsapp",
            "url": url_match.group(1) if url_match else "",
            "text": text_match.group(1).strip() if text_match else "",
            "box_text": box_match.group(1).strip() if box_match else "",
        }
    except Exception:
        return {"type": "whatsapp", "url": "", "text": "", "box_text": ""}


def migrate_site(site_config, cta_info, dry_run=False):
    """Migrate one site entry to tenant config."""
    company_id = site_config.get("company_id", "default")
    tenant_dir = os.path.join(TENANTS_DIR, company_id)

    print(f"\n  Migrating: {company_id}")

    # Build tenant.yaml
    tenant_data = {
        "company_id": company_id,
        "site_name": site_config.get("site_name", ""),
        "wordpress_url": site_config.get("wordpress_url", ""),
        "credentials_env_prefix": site_config.get("credentials_env_prefix", ""),
        "spreadsheet_id": site_config.get("spreadsheet_id", ""),
        "author_name": site_config.get("author_name", ""),
        "business_name": site_config.get("business_name", ""),
        "address": site_config.get("address", ""),
        "phone": site_config.get("phone", ""),
        "geo_lat": site_config.get("geo_lat", ""),
        "geo_lng": site_config.get("geo_lng", ""),
        "local_seo": site_config.get("local_seo", {}),
        "persona": {
            "name": site_config.get("author_name", ""),
            "title": site_config.get("persona_prompt", ""),
            "expertise": site_config.get("persona_prompt", ""),
            "prompt": site_config.get("persona_prompt", ""),
        },
        "cta": cta_info,
        "agents": {
            "enabled": ["analyst", "writer", "humanizer", "editor", "visual", "growth"],
            "config": {
                "analyst": {"max_retries": 3},
                "writer": {"max_retries": 3, "min_word_count": 1000},
                "humanizer": {"max_retries": 2},
                "editor": {"max_retries": 2},
                "visual": {"max_retries": 2},
                "growth": {"max_retries": 1},
            },
        },
        "schedule": {
            "frequency": "twice_daily",
            "times": ["09:00", "21:00"],
            "timezone": "America/Sao_Paulo",
            "max_articles_per_run": 1,
        },
        "seo": {
            "min_score": 40,
            "max_internal_links": 5,
        },
    }

    if dry_run:
        print(f"    [DRY-RUN] Would create: {tenant_dir}/tenant.yaml")
        print(f"    [DRY-RUN] Would copy KB from: config/companies/{company_id}/knowledge_base/")
        return True

    # Create directories
    os.makedirs(tenant_dir, exist_ok=True)
    os.makedirs(os.path.join(tenant_dir, "knowledge_base"), exist_ok=True)
    os.makedirs(os.path.join(tenant_dir, "prompts"), exist_ok=True)
    os.makedirs(os.path.join(tenant_dir, "images"), exist_ok=True)

    # Write tenant.yaml
    yaml_path = os.path.join(tenant_dir, "tenant.yaml")
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(tenant_data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)
    print(f"    Created: {yaml_path}")

    # Copy knowledge_base
    old_kb = os.path.join(COMPANIES_DIR, company_id, "knowledge_base")
    new_kb = os.path.join(tenant_dir, "knowledge_base")
    if os.path.exists(old_kb):
        for filename in os.listdir(old_kb):
            src = os.path.join(old_kb, filename)
            dst = os.path.join(new_kb, filename)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                print(f"    Copied KB: {filename}")

    # Copy images
    old_images = os.path.join(COMPANIES_DIR, company_id, "images")
    new_images = os.path.join(tenant_dir, "images")
    if os.path.exists(old_images):
        for filename in os.listdir(old_images):
            src = os.path.join(old_images, filename)
            dst = os.path.join(new_images, filename)
            if os.path.isfile(src):
                shutil.copy2(src, dst)
                print(f"    Copied image: {filename}")

    return True


def rollback():
    """Restore backups."""
    backup = SITES_JSON + ".bak"
    if os.path.exists(backup):
        shutil.copy2(backup, SITES_JSON)
        print(f"Restored: {SITES_JSON}")
    else:
        print("No backup found.")


def main():
    parser = argparse.ArgumentParser(description="Migrate sites.json to tenants/")
    parser.add_argument("--dry-run", action="store_true", help="Preview without changes")
    parser.add_argument("--rollback", action="store_true", help="Restore backups")
    args = parser.parse_args()

    if args.rollback:
        rollback()
        return

    print("=" * 60)
    print("Migration: sites.json → config/tenants/")
    print("=" * 60)

    if not os.path.exists(SITES_JSON):
        print(f"ERROR: {SITES_JSON} not found.")
        sys.exit(1)

    with open(SITES_JSON, 'r', encoding='utf-8') as f:
        sites = json.load(f)

    print(f"Found {len(sites)} site(s) to migrate.")

    # Extract CTA from prompts.py
    cta_info = extract_cta_from_prompts()
    if cta_info["url"]:
        print(f"Extracted CTA: {cta_info['type']} → {cta_info['url']}")

    # Backup sites.json
    if not args.dry_run:
        backup = SITES_JSON + ".bak"
        shutil.copy2(SITES_JSON, backup)
        print(f"Backup: {backup}")

    # Migrate each site
    success = 0
    for site in sites:
        if migrate_site(site, cta_info, dry_run=args.dry_run):
            success += 1

    print(f"\n{'=' * 60}")
    print(f"Migration {'preview' if args.dry_run else 'complete'}: {success}/{len(sites)} tenant(s)")
    print(f"{'=' * 60}")


if __name__ == "__main__":
    main()
