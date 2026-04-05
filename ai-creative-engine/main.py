"""
AI Creative Engine - Main Application

A production-ready MVP for generating branded brochures and social media
creatives using AI-powered content generation and HTML/CSS template rendering.

Run with: uvicorn main:app --reload
"""

import logging
import os
from datetime import datetime, timezone
from hashlib import sha256
from typing import Dict, List

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from config import OUTPUT_DIR, get_all_brand_keys, get_brand
from models.schemas import (
    BrandInfo,
    ErrorResponse,
    GenerateRequest,
    GenerateResponse,
    VariationResult,
)
from services.export_service import export_image, export_pdf
from services.openai_service import generate_content
from services.render_service import get_template_for_platform, render_template

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S",
)
logger = logging.getLogger(__name__)

# Initialize FastAPI app
app = FastAPI(
    title="AI Creative Engine",
    description=(
        "Generate branded brochures and social media creatives "
        "using AI-powered content generation and HTML/CSS templates."
    ),
    version="1.0.0",
    responses={
        400: {"model": ErrorResponse},
        404: {"model": ErrorResponse},
        500: {"model": ErrorResponse},
    },
)

# Ensure output directory exists
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Mount static files for serving outputs
app.mount("/outputs", StaticFiles(directory=OUTPUT_DIR), name="outputs")

# Simple in-memory cache for generated results
_cache: Dict[str, GenerateResponse] = {}


def _cache_key(request: GenerateRequest) -> str:
    """
    Generate a cache key from the request parameters.

    Args:
        request: The generation request.

    Returns:
        SHA-256 hash string as cache key.
    """
    raw = f"{request.brand}:{request.goal}:{request.platform}"
    return sha256(raw.encode()).hexdigest()


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {
        "service": "AI Creative Engine",
        "status": "running",
        "version": "1.0.0",
        "timestamp": datetime.now(timezone.utc).isoformat(),
    }


@app.get("/brands", tags=["Brands"], response_model=List[BrandInfo])
async def list_brands():
    """
    List all available brands.

    Returns:
        List of brand information objects.
    """
    brands = []
    for key in get_all_brand_keys():
        data = get_brand(key)
        if data:
            brands.append(
                BrandInfo(
                    key=key,
                    name=data["name"],
                    theme=data["theme"],
                    tone=data["tone"],
                    audience=data["audience"],
                )
            )
    return brands


@app.post(
    "/generate",
    tags=["Generation"],
    response_model=GenerateResponse,
    responses={
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Generation failed"},
    },
)
async def generate(request: GenerateRequest):
    """
    Generate branded creative content with PDF and image exports.

    This endpoint:
    1. Validates the brand
    2. Generates AI content (3 variations)
    3. Renders each variation using HTML/CSS templates
    4. Exports to PDF and image formats
    5. Returns structured content with download URLs

    Args:
        request: Generation request with brand, goal, and platform.

    Returns:
        GenerateResponse with content variations and file URLs.
    """
    # Check cache
    key = _cache_key(request)
    if key in _cache:
        logger.info("Returning cached result for key: %s", key[:12])
        return _cache[key]

    # 1. Validate brand
    brand_data = get_brand(request.brand)
    if not brand_data:
        available = ", ".join(get_all_brand_keys())
        raise HTTPException(
            status_code=400,
            detail=f"Unknown brand '{request.brand}'. Available brands: {available}",
        )

    # 2. Validate platform and get template
    try:
        template_name = get_template_for_platform(request.platform)
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))

    # 3. Generate content from AI
    logger.info(
        "Generating content for brand='%s', goal='%s', platform='%s'",
        request.brand,
        request.goal,
        request.platform,
    )

    try:
        content_variations = await generate_content(brand_data, request.goal)
    except Exception as e:
        logger.error("Content generation failed: %s", e)
        raise HTTPException(
            status_code=500,
            detail=f"Content generation failed: {e}",
        )

    # 4. Render and export each variation
    variations: List[VariationResult] = []
    all_pdf_urls: List[str] = []
    all_image_urls: List[str] = []

    for i, content in enumerate(content_variations):
        # Render HTML
        try:
            rendered_html = render_template(template_name, content, brand_data)
        except Exception as e:
            logger.error("Template rendering failed for variation %d: %s", i, e)
            raise HTTPException(
                status_code=500,
                detail=f"Template rendering failed for variation {i}: {e}",
            )

        # Export PDF
        try:
            pdf_url = export_pdf(rendered_html, request.brand, i)
        except RuntimeError as e:
            logger.error("PDF export failed for variation %d: %s", i, e)
            raise HTTPException(
                status_code=500,
                detail=f"PDF export failed for variation {i}: {e}",
            )

        # Export Image
        try:
            image_url = await export_image(rendered_html, request.brand, i)
        except RuntimeError as e:
            logger.error("Image export failed for variation %d: %s", i, e)
            raise HTTPException(
                status_code=500,
                detail=f"Image export failed for variation {i}: {e}",
            )

        variation = VariationResult(
            variation_index=i,
            content=content,
            pdf_url=pdf_url,
            image_url=image_url,
        )
        variations.append(variation)
        all_pdf_urls.append(pdf_url)
        all_image_urls.append(image_url)

    # 5. Build response
    response = GenerateResponse(
        brand=request.brand,
        goal=request.goal,
        platform=request.platform,
        variations=variations,
        pdf_urls=all_pdf_urls,
        image_urls=all_image_urls,
    )

    # Cache the result
    _cache[key] = response
    logger.info(
        "Generation complete: %d variations for brand '%s'",
        len(variations),
        request.brand,
    )

    return response


@app.delete("/cache", tags=["Admin"])
async def clear_cache():
    """Clear the in-memory result cache."""
    count = len(_cache)
    _cache.clear()
    logger.info("Cache cleared: %d entries removed", count)
    return {"message": f"Cache cleared: {count} entries removed"}
