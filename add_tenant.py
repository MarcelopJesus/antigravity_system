#!/usr/bin/env python3
"""Add Tenant CLI — Interactive setup for new tenants.

Usage:
    python add_tenant.py                          # Interactive mode
    python add_tenant.py --non-interactive input.json  # Automated mode
"""
import argparse
import json
import os
import sys
import yaml
import requests
from core.logger import setup_logger, get_logger

setup_logger()
logger = get_logger("add_tenant")

TENANTS_DIR = "config/tenants"


def prompt_input(label, default="", required=True):
    """Prompt user for input with optional default."""
    if default:
        value = input(f"  {label} [{default}]: ").strip() or default
    else:
        value = input(f"  {label}: ").strip()
    if required and not value:
        print(f"  ERROR: {label} is required.")
        return prompt_input(label, default, required)
    return value


def interactive_setup():
    """Run interactive tenant setup."""
    print("=" * 60)
    print("Article Factory — New Tenant Setup")
    print("=" * 60)

    data = {}

    # Basic info
    print("\n1. Basic Information")
    data["company_id"] = prompt_input("Company ID (slug, e.g., 'clinica-xyz')")
    data["site_name"] = prompt_input("Site Name (display name)")
    data["wordpress_url"] = prompt_input("WordPress URL (e.g., https://site.com)")
    data["credentials_env_prefix"] = prompt_input(
        "Env Prefix for credentials",
        default=data["company_id"].upper().replace("-", "_")
    )
    data["spreadsheet_id"] = prompt_input("Google Spreadsheet ID")

    # Author / Business
    print("\n2. Author & Business")
    data["author_name"] = prompt_input("Author Name")
    data["business_name"] = prompt_input("Business Name", required=False)
    data["address"] = prompt_input("Address", required=False)
    data["phone"] = prompt_input("Phone", required=False)

    # Persona
    print("\n3. Persona")
    data["persona"] = {
        "name": data["author_name"],
        "title": prompt_input("Professional Title (e.g., 'Psicólogo')"),
        "expertise": prompt_input("Area of Expertise (e.g., 'terapia cognitiva')"),
    }

    # CTA
    print("\n4. Call to Action (CTA)")
    cta_types = {"1": "whatsapp", "2": "email", "3": "phone", "4": "link"}
    print("  CTA Types: 1) WhatsApp  2) Email  3) Phone  4) Custom Link")
    cta_choice = prompt_input("Choose CTA type (1-4)", default="1")
    data["cta"] = {
        "type": cta_types.get(cta_choice, "whatsapp"),
        "url": prompt_input("CTA URL (e.g., https://wa.me/5511...)"),
        "text": prompt_input("Button text (e.g., 'Falar com Dr. João')"),
        "box_text": prompt_input("Box description", default="Quer saber mais? Entre em contato."),
    }

    # Local SEO
    print("\n5. Local SEO (optional)")
    has_local = input("  Add local SEO? (y/N): ").strip().lower() == "y"
    if has_local:
        data["local_seo"] = {
            "primary_location": prompt_input("Primary Location (e.g., 'Moema, São Paulo')"),
            "neighborhood": prompt_input("Neighborhood", required=False),
            "city": prompt_input("City"),
            "state": prompt_input("State (2 letters)", required=False),
            "local_keywords": [
                k.strip() for k in
                prompt_input("Local keywords (comma-separated)").split(",")
                if k.strip()
            ],
        }
    else:
        data["local_seo"] = {}

    # Agents
    print("\n6. Agents")
    all_agents = ["analyst", "writer", "humanizer", "editor", "visual", "growth"]
    print(f"  Available: {', '.join(all_agents)}")
    print("  Press Enter to enable all, or type agent names to enable:")
    agent_input = input("  Enabled agents: ").strip()
    if agent_input:
        data["agents"] = {
            "enabled": [a.strip() for a in agent_input.split(",") if a.strip() in all_agents],
        }
    else:
        data["agents"] = {"enabled": all_agents}

    # Schedule
    print("\n7. Schedule")
    print("  Frequencies: 1) Daily  2) Twice Daily  3) Weekly")
    freq_map = {"1": "daily", "2": "twice_daily", "3": "weekly"}
    freq = prompt_input("Frequency (1-3)", default="2")
    data["schedule"] = {
        "frequency": freq_map.get(freq, "twice_daily"),
        "times": ["09:00", "21:00"],
        "timezone": "America/Sao_Paulo",
        "max_articles_per_run": int(prompt_input("Max articles per run", default="1")),
    }

    # SEO
    data["seo"] = {"min_score": 40, "max_internal_links": 5}

    return data


def create_tenant(data, validate=True):
    """Create tenant directory structure and config files.

    Args:
        data: Tenant configuration dict.
        validate: If True, validate WordPress and Sheets access.

    Returns:
        True if successful.
    """
    company_id = data["company_id"]
    tenant_dir = os.path.join(TENANTS_DIR, company_id)

    if os.path.exists(tenant_dir):
        print(f"\n  WARNING: Tenant '{company_id}' already exists at {tenant_dir}")
        overwrite = input("  Overwrite? (y/N): ").strip().lower()
        if overwrite != "y":
            print("  Aborted.")
            return False

    # Create directories
    os.makedirs(os.path.join(tenant_dir, "knowledge_base"), exist_ok=True)
    os.makedirs(os.path.join(tenant_dir, "prompts"), exist_ok=True)
    os.makedirs(os.path.join(tenant_dir, "images"), exist_ok=True)

    # Write .gitkeep in empty dirs
    for subdir in ["knowledge_base", "prompts", "images"]:
        gitkeep = os.path.join(tenant_dir, subdir, ".gitkeep")
        if not os.listdir(os.path.join(tenant_dir, subdir)):
            open(gitkeep, 'w').close()

    # Write tenant.yaml
    yaml_path = os.path.join(tenant_dir, "tenant.yaml")
    with open(yaml_path, 'w', encoding='utf-8') as f:
        yaml.dump(data, f, default_flow_style=False, allow_unicode=True, sort_keys=False)

    print(f"\n  Created: {yaml_path}")
    print(f"  Created: {tenant_dir}/knowledge_base/")
    print(f"  Created: {tenant_dir}/prompts/")
    print(f"  Created: {tenant_dir}/images/")

    # Add env vars to .env
    prefix = data.get("credentials_env_prefix", company_id.upper())
    env_lines = f"\n# Tenant: {company_id}\n{prefix}_WP_USERNAME=\n{prefix}_WP_APP_PASSWORD=\n"

    env_path = ".env"
    if os.path.exists(env_path):
        with open(env_path, 'a') as f:
            f.write(env_lines)
        print(f"  Added to .env: {prefix}_WP_USERNAME, {prefix}_WP_APP_PASSWORD")
    else:
        print(f"  NOTE: Add to .env: {prefix}_WP_USERNAME and {prefix}_WP_APP_PASSWORD")

    # Validation
    if validate:
        print("\n  Validating...")
        _validate_wordpress(data)
        _validate_sheets(data)

    # Summary
    print(f"\n{'=' * 60}")
    print(f"Tenant '{company_id}' created successfully!")
    print(f"{'=' * 60}")
    print(f"\nNext steps:")
    print(f"  1. Add WordPress credentials to .env ({prefix}_WP_USERNAME, {prefix}_WP_APP_PASSWORD)")
    print(f"  2. Add knowledge base files to {tenant_dir}/knowledge_base/")
    print(f"  3. Optionally customize prompts in {tenant_dir}/prompts/")
    print(f"  4. Test with: python main.py --dry-run --tenant {company_id}")

    return True


def _validate_wordpress(data):
    """Validate WordPress access."""
    try:
        prefix = data.get("credentials_env_prefix", "")
        username = os.getenv(f"{prefix}_WP_USERNAME")
        password = os.getenv(f"{prefix}_WP_APP_PASSWORD")

        if not username or not password:
            print(f"    WordPress: SKIPPED (credentials not in .env yet)")
            return

        wp_url = data["wordpress_url"].rstrip("/")
        resp = requests.get(
            f"{wp_url}/wp-json/wp/v2/users/me",
            auth=(username, password),
            timeout=10,
        )
        if resp.status_code == 200:
            print(f"    WordPress: OK (authenticated as {resp.json().get('name', 'unknown')})")
        else:
            print(f"    WordPress: FAILED (status {resp.status_code})")
    except Exception as e:
        print(f"    WordPress: ERROR ({e})")


def _validate_sheets(data):
    """Validate Google Sheets access."""
    try:
        if not os.path.exists("config/service_account.json"):
            print(f"    Sheets: SKIPPED (no service_account.json)")
            return

        from core.sheets_client import SheetsClient
        sheets = SheetsClient("config/service_account.json")
        rows = sheets.get_pending_rows(data["spreadsheet_id"])
        print(f"    Sheets: OK ({len(rows)} pending keywords)")
    except Exception as e:
        print(f"    Sheets: ERROR ({e})")


def main():
    parser = argparse.ArgumentParser(description="Add Tenant CLI")
    parser.add_argument("--non-interactive", type=str, help="JSON file with tenant config")
    parser.add_argument("--no-validate", action="store_true", help="Skip validation")
    args = parser.parse_args()

    if args.non_interactive:
        with open(args.non_interactive, 'r') as f:
            data = json.load(f)
    else:
        data = interactive_setup()

    create_tenant(data, validate=not args.no_validate)


if __name__ == "__main__":
    main()
