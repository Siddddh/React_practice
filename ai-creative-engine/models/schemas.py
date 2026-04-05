"""
Pydantic models for request/response validation.

Defines the data structures used across the AI Creative Engine API.
"""

from typing import List, Optional
from pydantic import BaseModel, Field


class GenerateRequest(BaseModel):
    """Request model for the /generate endpoint."""

    brand: str = Field(
        ...,
        description="Brand identifier key (e.g., 'luxury_homes', 'tech_startup')",
        examples=["luxury_homes"],
    )
    goal: str = Field(
        ...,
        description="The marketing goal or message to convey",
        examples=["Promote premium villas"],
    )
    platform: str = Field(
        default="brochure",
        description="Target platform: 'brochure' or 'social_post'",
        examples=["brochure"],
    )


class ContentSection(BaseModel):
    """A single content section within the creative."""

    title: str = Field(..., description="Section title")
    text: str = Field(..., description="Section body text")


class GeneratedContent(BaseModel):
    """Structured content output from OpenAI."""

    headline: str = Field(..., description="Main headline")
    subheadline: str = Field(..., description="Supporting subheadline")
    sections: List[ContentSection] = Field(
        default_factory=list, description="Content sections"
    )
    cta: str = Field(..., description="Call-to-action text")
    style: str = Field(
        default="modern", description="Visual style hint (e.g., 'luxury minimal')"
    )


class VariationResult(BaseModel):
    """Result for a single generated variation."""

    variation_index: int = Field(..., description="Variation number (0-indexed)")
    content: GeneratedContent
    pdf_url: str = Field(..., description="URL path to the generated PDF")
    image_url: str = Field(..., description="URL path to the generated image")


class GenerateResponse(BaseModel):
    """Response model for the /generate endpoint."""

    brand: str = Field(..., description="Brand identifier used")
    goal: str = Field(..., description="Marketing goal provided")
    platform: str = Field(..., description="Target platform")
    variations: List[VariationResult] = Field(
        default_factory=list, description="List of generated variations"
    )
    pdf_urls: List[str] = Field(
        default_factory=list, description="All PDF download URLs"
    )
    image_urls: List[str] = Field(
        default_factory=list, description="All image download URLs"
    )


class ErrorResponse(BaseModel):
    """Standard error response."""

    detail: str = Field(..., description="Error description")
    error_type: Optional[str] = Field(
        default=None, description="Error classification"
    )


class BrandInfo(BaseModel):
    """Brand information response model."""

    key: str
    name: str
    theme: str
    tone: str
    audience: str
