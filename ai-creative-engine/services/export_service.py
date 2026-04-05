"""
Export service for converting rendered HTML to PDF and image formats.

Uses WeasyPrint for PDF generation and Playwright for image screenshots.
"""

import logging
import os
from datetime import datetime, timezone

from config import OUTPUT_DIR

logger = logging.getLogger(__name__)


def _ensure_output_dir(brand_key: str) -> str:
    """
    Ensure the output directory exists for a given brand.

    Args:
        brand_key: Brand identifier for directory naming.

    Returns:
        Absolute path to the brand's output directory.
    """
    brand_dir = os.path.join(OUTPUT_DIR, brand_key)
    os.makedirs(brand_dir, exist_ok=True)
    return brand_dir


def _generate_filename(brand_key: str, variation_index: int, extension: str) -> str:
    """
    Generate a unique filename based on brand, timestamp, and variation.

    Args:
        brand_key: Brand identifier.
        variation_index: Index of the variation.
        extension: File extension (e.g., 'pdf', 'png').

    Returns:
        Tuple of (absolute file path, relative URL path).
    """
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d_%H%M%S")
    filename = f"{timestamp}_v{variation_index}.{extension}"
    brand_dir = _ensure_output_dir(brand_key)
    filepath = os.path.join(brand_dir, filename)
    url_path = f"/outputs/{brand_key}/{filename}"
    return filepath, url_path


def export_pdf(html_content: str, brand_key: str, variation_index: int) -> str:
    """
    Export rendered HTML content to a PDF file.

    Uses WeasyPrint for high-quality PDF rendering.

    Args:
        html_content: Rendered HTML string.
        brand_key: Brand identifier for output organization.
        variation_index: Variation number for filename.

    Returns:
        URL path to the generated PDF file.

    Raises:
        RuntimeError: If PDF generation fails.
    """
    filepath, url_path = _generate_filename(brand_key, variation_index, "pdf")

    try:
        from weasyprint import HTML as WeasyHTML

        WeasyHTML(string=html_content).write_pdf(filepath)
        logger.info("PDF exported: %s", filepath)
        return url_path
    except ImportError:
        logger.warning(
            "WeasyPrint not installed. Falling back to saving raw HTML as PDF placeholder."
        )
        # Fallback: save HTML with .pdf extension for development
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        logger.info("HTML placeholder saved as PDF: %s", filepath)
        return url_path
    except Exception as e:
        logger.error("PDF export failed: %s", e)
        raise RuntimeError(f"PDF export failed: {e}") from e


async def export_image(
    html_content: str, brand_key: str, variation_index: int
) -> str:
    """
    Export rendered HTML content to a PNG image using Playwright.

    Args:
        html_content: Rendered HTML string.
        brand_key: Brand identifier for output organization.
        variation_index: Variation number for filename.

    Returns:
        URL path to the generated image file.

    Raises:
        RuntimeError: If image export fails.
    """
    filepath, url_path = _generate_filename(brand_key, variation_index, "png")

    try:
        from playwright.async_api import async_playwright

        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=True)
            page = await browser.new_page(viewport={"width": 1200, "height": 1600})
            await page.set_content(html_content, wait_until="networkidle")
            await page.screenshot(path=filepath, full_page=True)
            await browser.close()

        logger.info("Image exported: %s", filepath)
        return url_path
    except ImportError:
        logger.warning(
            "Playwright not installed. Falling back to HTML placeholder for image."
        )
        html_filepath = filepath.replace(".png", ".html")
        with open(html_filepath, "w", encoding="utf-8") as f:
            f.write(html_content)
        fallback_url = url_path.replace(".png", ".html")
        logger.info("HTML placeholder saved as image fallback: %s", html_filepath)
        return fallback_url
    except Exception as e:
        logger.error("Image export failed: %s", e)
        raise RuntimeError(f"Image export failed: {e}") from e
