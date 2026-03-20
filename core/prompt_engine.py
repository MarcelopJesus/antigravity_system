"""PromptEngine — Renders Jinja2 prompt templates with tenant config inheritance."""
import os
from jinja2 import Environment, FileSystemLoader, ChoiceLoader, TemplateNotFound, Undefined
from core.logger import get_logger

logger = get_logger(__name__)

TENANTS_DIR = "config/tenants"
DEFAULT_PROMPTS = os.path.join(TENANTS_DIR, "_default", "prompts")


class PromptEngine:
    """Renders prompt templates with Jinja2 and tenant-level inheritance.

    Lookup order:
    1. config/tenants/{company_id}/prompts/{agent}.txt
    2. config/tenants/_default/prompts/{agent}.txt
    """

    def __init__(self, tenant_config=None, tenants_dir=None):
        """
        Args:
            tenant_config: TenantConfig instance (provides persona, CTA, etc.).
            tenants_dir: Override tenants directory path.
        """
        self.tenant_config = tenant_config
        base_dir = tenants_dir or TENANTS_DIR

        # Build Jinja2 loaders with priority: tenant > _default
        loaders = []
        if tenant_config:
            tenant_prompts = os.path.join(base_dir, tenant_config.company_id, "prompts")
            if os.path.exists(tenant_prompts):
                loaders.append(FileSystemLoader(tenant_prompts))

        default_prompts = os.path.join(base_dir, "_default", "prompts")
        if os.path.exists(default_prompts):
            loaders.append(FileSystemLoader(default_prompts))

        if not loaders:
            logger.warning("No prompt directories found. PromptEngine will use empty templates.")
            loaders.append(FileSystemLoader("."))

        self.env = Environment(
            loader=ChoiceLoader(loaders),
            keep_trailing_newline=True,
            undefined=_SilentUndefined,
        )

    def render(self, agent_name, context=None):
        """Render a prompt template for the given agent.

        Args:
            agent_name: Agent name (e.g., "analyst", "writer").
            context: Dict of variables to inject (keyword, outline, etc.).

        Returns:
            Rendered prompt string.
        """
        template_name = f"{agent_name}.txt"
        ctx = self._build_context(context)

        try:
            template = self.env.get_template(template_name)
            rendered = template.render(**ctx)
            logger.debug("Rendered prompt '%s' for tenant '%s' (%d chars)",
                        agent_name,
                        self.tenant_config.company_id if self.tenant_config else "none",
                        len(rendered))
            return rendered
        except TemplateNotFound:
            logger.warning("Prompt template '%s' not found. Returning empty string.", template_name)
            return ""

    def _build_context(self, extra_context=None):
        """Build template context from tenant config + extra variables."""
        ctx = {}

        if self.tenant_config:
            ctx["persona"] = self.tenant_config.get_persona()
            ctx["cta"] = self.tenant_config.get_cta()
            ctx["cta_html"] = self.tenant_config.get_cta_html()
            ctx["local_seo"] = self.tenant_config.get_local_seo()
            ctx["company_id"] = self.tenant_config.company_id
            ctx["site_name"] = self.tenant_config.site_name

            # Build local_seo_section for prompts that use it
            local_seo = self.tenant_config.get_local_seo()
            if local_seo and local_seo.get("primary_location"):
                ctx["local_seo_section"] = self._build_local_seo_section(local_seo)
            else:
                ctx["local_seo_section"] = ""

        if extra_context:
            ctx.update(extra_context)

        return ctx

    def _build_local_seo_section(self, local_seo):
        """Build the local SEO prompt section."""
        location = local_seo.get("primary_location", "")
        neighborhood = local_seo.get("neighborhood", "")
        city = local_seo.get("city", "")
        keywords = local_seo.get("local_keywords", [])

        section = f"\nSEO LOCAL ({location}):\n"
        section += f"- Mencione naturalmente a localização: {neighborhood}, {city}\n"
        if keywords:
            section += f"- Keywords locais para incluir: {', '.join(keywords)}\n"
        return section

    def has_template(self, agent_name):
        """Check if a template exists for the given agent."""
        try:
            self.env.get_template(f"{agent_name}.txt")
            return True
        except TemplateNotFound:
            return False


class _SilentUndefined(Undefined):
    """Jinja2 undefined that returns empty string instead of raising."""

    def __str__(self):
        return ""

    def __iter__(self):
        return iter([])

    def __bool__(self):
        return False

    def __getattr__(self, name):
        return _SilentUndefined()
