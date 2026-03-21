"""TenantConfig — Loads and validates per-tenant configuration with defaults."""
import os
import yaml
from core.logger import get_logger

logger = get_logger(__name__)

TENANTS_DIR = "config/tenants"
DEFAULT_TENANT = "_default"
REQUIRED_FIELDS = ["company_id", "wordpress_url", "spreadsheet_id", "credentials_env_prefix"]


class TenantConfigError(Exception):
    """Raised when tenant configuration is invalid."""
    pass


class TenantConfig:
    """Manages per-tenant configuration with inheritance from _default."""

    def __init__(self, data):
        self._data = data

    @classmethod
    def load(cls, company_id, tenants_dir=None):
        """Load tenant config, merging with _default.

        Args:
            company_id: Tenant identifier (e.g., "mjesus").
            tenants_dir: Override tenants directory path.

        Returns:
            TenantConfig instance.

        Raises:
            TenantConfigError if config is invalid.
        """
        base_dir = tenants_dir or TENANTS_DIR
        default_path = os.path.join(base_dir, DEFAULT_TENANT, "tenant.yaml")
        tenant_path = os.path.join(base_dir, company_id, "tenant.yaml")

        # Load default
        default_data = {}
        if os.path.exists(default_path):
            with open(default_path, 'r', encoding='utf-8') as f:
                default_data = yaml.safe_load(f) or {}

        # Load tenant
        if not os.path.exists(tenant_path):
            raise TenantConfigError(
                f"Tenant config not found: {tenant_path}"
            )

        with open(tenant_path, 'r', encoding='utf-8') as f:
            tenant_data = yaml.safe_load(f) or {}

        # Deep merge: tenant overrides default
        merged = _deep_merge(default_data, tenant_data)

        # Validate required fields
        missing = [f for f in REQUIRED_FIELDS if not merged.get(f)]
        if missing:
            raise TenantConfigError(
                f"Tenant '{company_id}' missing required fields: {', '.join(missing)}"
            )

        logger.info("Loaded tenant config: %s", company_id)
        return cls(merged)

    @classmethod
    def list_all(cls, tenants_dir=None):
        """Discover all tenant IDs in the tenants directory.

        Returns:
            List of company_id strings (excludes _default).
        """
        base_dir = tenants_dir or TENANTS_DIR
        if not os.path.exists(base_dir):
            return []

        tenants = []
        for entry in sorted(os.listdir(base_dir)):
            if entry.startswith("_") or entry.startswith("."):
                continue
            tenant_yaml = os.path.join(base_dir, entry, "tenant.yaml")
            if os.path.exists(tenant_yaml):
                tenants.append(entry)

        return tenants

    @classmethod
    def from_site_config(cls, site_config):
        """Create TenantConfig from legacy sites.json entry.

        This enables backward compatibility during migration.

        Args:
            site_config: Dict from sites.json.

        Returns:
            TenantConfig instance.
        """
        data = {
            "company_id": site_config.get("company_id", "default"),
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
            "cta": site_config.get("cta", {
                "type": "whatsapp",
                "url": "",
                "text": "",
                "box_text": "",
            }),
            "agents": {
                "enabled": ["analyst", "writer", "humanizer", "editor", "visual", "growth"],
                "config": {},
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
        return cls(data)

    # --- Accessors ---

    def get(self, key, default=None):
        """Get a top-level config value."""
        return self._data.get(key, default)

    @property
    def raw_config(self):
        """Access the raw config dict."""
        return self._data

    @property
    def company_id(self):
        return self._data.get("company_id", "")

    @property
    def site_name(self):
        return self._data.get("site_name", "")

    @property
    def wordpress_url(self):
        return self._data.get("wordpress_url", "")

    @property
    def spreadsheet_id(self):
        return self._data.get("spreadsheet_id", "")

    @property
    def credentials_env_prefix(self):
        return self._data.get("credentials_env_prefix", "")

    @property
    def kb_path(self):
        """Path to tenant's knowledge_base directory."""
        return os.path.join(TENANTS_DIR, self.company_id, "knowledge_base")

    @property
    def prompts_dir(self):
        """Path to tenant's prompts directory."""
        return os.path.join(TENANTS_DIR, self.company_id, "prompts")

    def get_enabled_agents(self):
        """Return list of enabled agent names for this tenant."""
        agents = self._data.get("agents", {})
        return agents.get("enabled", ["analyst", "writer", "humanizer", "editor", "visual", "growth"])

    def get_agent_config(self, agent_name):
        """Return config dict for a specific agent."""
        agents = self._data.get("agents", {})
        config = agents.get("config", {})
        return config.get(agent_name, {})

    def get_cta(self):
        """Return CTA configuration dict."""
        return self._data.get("cta", {
            "type": "whatsapp",
            "url": "",
            "text": "",
            "box_text": "",
        })

    def get_cta_html(self, slug=""):
        """Generate CTA HTML from tenant config with optional UTM tracking.

        Args:
            slug: Article slug for conversion tracking (appended as WhatsApp text param).
        """
        cta = self.get_cta()
        cta_type = cta.get("type", "link")
        url = cta.get("url", "")
        text = cta.get("text", "Entre em contato")
        box_text = cta.get("box_text", "")

        # Add UTM tracking for WhatsApp CTA
        if cta_type == "whatsapp" and slug and url:
            # Append tracking text so we know which article generated the lead
            tracking_text = f"Vim+do+artigo+{slug}"
            separator = "&" if "?" in url else "?"
            url = f"{url}{separator}text={tracking_text}"

        btn_class = "btn-whatsapp" if cta_type == "whatsapp" else "btn-cta"

        return (
            f'<div class="cta-box">\n'
            f'   <p>{box_text}</p>\n'
            f'   <a href="{url}" class="{btn_class}" target="_blank" rel="noopener">'
            f'\u2192 {text}</a>\n'
            f'</div>'
        )

    def get_schedule(self):
        """Return schedule configuration dict."""
        return self._data.get("schedule", {
            "frequency": "twice_daily",
            "times": ["09:00", "21:00"],
            "timezone": "America/Sao_Paulo",
            "max_articles_per_run": 1,
        })

    def get_persona(self):
        """Return persona configuration dict."""
        return self._data.get("persona", {})

    def get_local_seo(self):
        """Return local SEO configuration dict."""
        return self._data.get("local_seo", {})

    def get_seo_config(self):
        """Return SEO configuration dict."""
        return self._data.get("seo", {"min_score": 40, "max_internal_links": 5})

    def to_site_config(self):
        """Convert back to legacy site_config dict for backward compatibility."""
        return {
            "company_id": self.company_id,
            "site_name": self.site_name,
            "wordpress_url": self.wordpress_url,
            "spreadsheet_id": self.spreadsheet_id,
            "credentials_env_prefix": self.credentials_env_prefix,
            "author_name": self._data.get("author_name", ""),
            "business_name": self._data.get("business_name", ""),
            "address": self._data.get("address", ""),
            "phone": self._data.get("phone", ""),
            "geo_lat": self._data.get("geo_lat", ""),
            "geo_lng": self._data.get("geo_lng", ""),
            "local_seo": self.get_local_seo(),
            "persona_prompt": self.get_persona().get("prompt", ""),
        }

    def __repr__(self):
        return f"TenantConfig(company_id='{self.company_id}')"


def _deep_merge(base, override):
    """Deep merge two dicts. Override values take precedence."""
    result = base.copy()
    for key, value in override.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _deep_merge(result[key], value)
        else:
            result[key] = value
    return result
