"""
Configuration module for the AI Creative Engine.

Contains brand definitions, application settings, and OpenAI configuration.
"""

import os
from typing import Dict, Any

# OpenAI Configuration
OPENAI_API_KEY: str = os.getenv("OPENAI_API_KEY", "")
OPENAI_MODEL: str = os.getenv("OPENAI_MODEL", "gpt-4")

# Application Settings
OUTPUT_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "outputs")
TEMPLATE_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "templates")
STATIC_DIR: str = os.path.join(os.path.dirname(os.path.abspath(__file__)), "static")

# Number of variations to generate per request
NUM_VARIATIONS: int = 3

# Brand System
BRANDS: Dict[str, Dict[str, Any]] = {
    "luxury_homes": {
        "name": "Luxury Homes",
        "colors": {
            "primary": "#1a1a2e",
            "secondary": "#e94560",
            "background": "#f5f0eb",
            "text": "#16213e",
            "accent": "#c9a96e",
        },
        "font": "Playfair Display",
        "font_body": "Lato",
        "tone": "elegant, sophisticated, exclusive",
        "audience": "High-net-worth individuals looking for premium properties",
        "theme": "luxury",
    },
    "tech_startup": {
        "name": "Tech Startup",
        "colors": {
            "primary": "#6c5ce7",
            "secondary": "#00cec9",
            "background": "#ffffff",
            "text": "#2d3436",
            "accent": "#fd79a8",
        },
        "font": "Inter",
        "font_body": "Inter",
        "tone": "innovative, bold, forward-thinking",
        "audience": "Tech-savvy professionals and early adopters",
        "theme": "modern",
    },
    "corporate_finance": {
        "name": "Corporate Finance",
        "colors": {
            "primary": "#0a3d62",
            "secondary": "#3c6382",
            "background": "#f8f9fa",
            "text": "#1e272e",
            "accent": "#f6b93b",
        },
        "font": "Merriweather",
        "font_body": "Open Sans",
        "tone": "professional, trustworthy, authoritative",
        "audience": "Business executives and financial decision-makers",
        "theme": "corporate",
    },
    "eco_brand": {
        "name": "Eco Brand",
        "colors": {
            "primary": "#2d6a4f",
            "secondary": "#52b788",
            "background": "#f0f7f4",
            "text": "#1b4332",
            "accent": "#95d5b2",
        },
        "font": "Nunito",
        "font_body": "Nunito",
        "tone": "warm, sustainable, community-driven",
        "audience": "Eco-conscious consumers and sustainability advocates",
        "theme": "modern",
    },
}


def get_brand(brand_key: str) -> Dict[str, Any] | None:
    """
    Retrieve brand configuration by key.

    Args:
        brand_key: The identifier for the brand.

    Returns:
        Brand configuration dictionary, or None if not found.
    """
    return BRANDS.get(brand_key)


def get_all_brand_keys() -> list[str]:
    """
    Get a list of all available brand keys.

    Returns:
        List of brand identifier strings.
    """
    return list(BRANDS.keys())
