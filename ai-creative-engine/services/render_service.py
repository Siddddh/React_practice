"""
Template rendering service using Jinja2.

Handles rendering of HTML templates with brand and content data.
"""

import logging
import os
from typing import Any, Dict

from jinja2 import Environment, FileSystemLoader, TemplateNotFound

from config import TEMPLATE_DIR, STATIC_DIR
from models.schemas import GeneratedContent

logger = logging.getLogger(__name__)

# Initialize Jinja2 environment
_env = Environment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=True,
)


def render_template(
    template_name: str,
    content: GeneratedContent,
    brand_data: Dict[str, Any],
) -> str:
    """
    Render an HTML template with content and brand data.

    Args:
        template_name: Name of the template file (e.g., 'brochure.html').
        content: Generated content to inject into the template.
        brand_data: Brand configuration for styling.

    Returns:
        Rendered HTML string.

    Raises:
        TemplateNotFound: If the specified template does not exist.
        Exception: If template rendering fails.
    """
    try:
        template = _env.get_template(template_name)
    except TemplateNotFound:
        logger.error("Template not found: %s", template_name)
        raise

    # Read CSS content for inline embedding
    css_content = _load_css()

    context = {
        "content": content,
        "brand": brand_data,
        "colors": brand_data.get("colors", {}),
        "font": brand_data.get("font", "sans-serif"),
        "font_body": brand_data.get("font_body", "sans-serif"),
        "theme": brand_data.get("theme", "modern"),
        "css": css_content,
        "static_dir": STATIC_DIR,
    }

    try:
        rendered = template.render(**context)
        logger.info(
            "Rendered template '%s' for brand '%s'",
            template_name,
            brand_data.get("name", "unknown"),
        )
        return rendered
    except Exception as e:
        logger.error("Template rendering failed for '%s': %s", template_name, e)
        raise


def _load_css() -> str:
    """
    Load the main CSS stylesheet content.

    Returns:
        CSS content as a string, or empty string if file not found.
    """
    css_path = os.path.join(STATIC_DIR, "styles.css")
    try:
        with open(css_path, "r", encoding="utf-8") as f:
            return f.read()
    except FileNotFoundError:
        logger.warning("CSS file not found at %s", css_path)
        return ""


def get_template_for_platform(platform: str) -> str:
    """
    Map a platform name to its corresponding template file.

    Args:
        platform: Platform identifier ('brochure' or 'social_post').

    Returns:
        Template filename.

    Raises:
        ValueError: If the platform is not supported.
    """
    templates = {
        "brochure": "brochure.html",
        "social_post": "social_post.html",
    }

    template_name = templates.get(platform)
    if not template_name:
        supported = ", ".join(templates.keys())
        raise ValueError(
            f"Unsupported platform '{platform}'. Supported: {supported}"
        )

    return template_name
