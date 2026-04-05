"""
OpenAI service for generating structured creative content.

Handles communication with the OpenAI API, prompt construction,
and safe JSON parsing of responses.
"""

import json
import logging
from typing import Any, Dict, List

import openai

from config import OPENAI_API_KEY, OPENAI_MODEL, NUM_VARIATIONS
from models.schemas import GeneratedContent

logger = logging.getLogger(__name__)


def _build_system_prompt(brand_data: Dict[str, Any]) -> str:
    """
    Build the system prompt with brand context.

    Args:
        brand_data: Brand configuration dictionary.

    Returns:
        System prompt string for OpenAI.
    """
    return (
        "You are an expert marketing copywriter and creative director. "
        f"You are creating content for the brand '{brand_data['name']}'. "
        f"The brand tone is: {brand_data['tone']}. "
        f"The target audience is: {brand_data['audience']}. "
        f"The visual style should complement a {brand_data['theme']} theme. "
        "You must respond ONLY with valid JSON. No markdown, no code fences, no extra text."
    )


def _build_user_prompt(goal: str, num_variations: int) -> str:
    """
    Build the user prompt requesting structured content.

    Args:
        goal: The marketing goal to achieve.
        num_variations: Number of content variations to generate.

    Returns:
        User prompt string.
    """
    return (
        f"Generate {num_variations} unique creative content variations for this goal: '{goal}'.\n\n"
        "Return a JSON array where each element has this exact structure:\n"
        "{\n"
        '  "headline": "A compelling headline",\n'
        '  "subheadline": "A supporting subheadline",\n'
        '  "sections": [\n'
        '    {"title": "Section Title", "text": "Section body text"}\n'
        "  ],\n"
        '  "cta": "Call to action text",\n'
        '  "style": "visual style description"\n'
        "}\n\n"
        "Requirements:\n"
        "- Each variation must be distinct in messaging and approach\n"
        "- Include 2-3 sections per variation\n"
        "- Make headlines punchy and memorable\n"
        "- CTAs should be action-oriented\n"
        "- Return ONLY the JSON array, nothing else"
    )


def _parse_content_response(raw_response: str) -> List[Dict[str, Any]]:
    """
    Safely parse the OpenAI response into structured content.

    Handles common JSON parsing issues including markdown code fences.

    Args:
        raw_response: Raw string response from OpenAI.

    Returns:
        List of content dictionaries.

    Raises:
        ValueError: If the response cannot be parsed as valid JSON.
    """
    cleaned = raw_response.strip()

    # Remove markdown code fences if present
    if cleaned.startswith("```"):
        lines = cleaned.split("\n")
        # Remove first line (```json or ```) and last line (```)
        lines = [line for line in lines if not line.strip().startswith("```")]
        cleaned = "\n".join(lines).strip()

    try:
        parsed = json.loads(cleaned)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse OpenAI response as JSON: %s", e)
        logger.debug("Raw response: %s", raw_response[:500])
        raise ValueError(f"Failed to parse AI response as JSON: {e}") from e

    # Ensure we have a list
    if isinstance(parsed, dict):
        parsed = [parsed]

    if not isinstance(parsed, list):
        raise ValueError("AI response is not a JSON array or object")

    return parsed


async def generate_content(
    brand_data: Dict[str, Any], goal: str
) -> List[GeneratedContent]:
    """
    Generate creative content variations using OpenAI.

    Args:
        brand_data: Brand configuration dictionary.
        goal: The marketing goal to achieve.

    Returns:
        List of GeneratedContent objects (one per variation).

    Raises:
        openai.APIError: If the OpenAI API call fails.
        ValueError: If the response cannot be parsed.
    """
    if not OPENAI_API_KEY:
        logger.warning("No OpenAI API key configured; returning fallback content.")
        return _generate_fallback_content(brand_data, goal)

    client = openai.AsyncOpenAI(api_key=OPENAI_API_KEY)

    system_prompt = _build_system_prompt(brand_data)
    user_prompt = _build_user_prompt(goal, NUM_VARIATIONS)

    logger.info(
        "Requesting %d variations from OpenAI for brand '%s'",
        NUM_VARIATIONS,
        brand_data["name"],
    )

    try:
        response = await client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
            temperature=0.8,
            max_tokens=2000,
        )
    except openai.APIError as e:
        logger.error("OpenAI API error: %s", e)
        raise

    raw_content = response.choices[0].message.content or ""
    parsed_list = _parse_content_response(raw_content)

    results: List[GeneratedContent] = []
    for i, item in enumerate(parsed_list[:NUM_VARIATIONS]):
        try:
            content = GeneratedContent(**item)
            results.append(content)
        except Exception as e:
            logger.warning("Variation %d failed validation: %s", i, e)
            continue

    if not results:
        logger.warning("No valid variations parsed; using fallback content.")
        return _generate_fallback_content(brand_data, goal)

    return results


def _generate_fallback_content(
    brand_data: Dict[str, Any], goal: str
) -> List[GeneratedContent]:
    """
    Generate fallback content when OpenAI is unavailable or fails.

    Provides deterministic placeholder content for testing and development.

    Args:
        brand_data: Brand configuration dictionary.
        goal: The marketing goal.

    Returns:
        List of GeneratedContent with fallback values.
    """
    variations = []
    style_options = ["luxury minimal", "bold modern", "clean corporate"]

    for i in range(NUM_VARIATIONS):
        variations.append(
            GeneratedContent(
                headline=f"{brand_data['name']}: Variation {i + 1}",
                subheadline=f"Crafted to {goal.lower()}",
                sections=[
                    {
                        "title": "Our Vision",
                        "text": (
                            f"At {brand_data['name']}, we believe in delivering "
                            "exceptional quality that exceeds expectations."
                        ),
                    },
                    {
                        "title": "What Sets Us Apart",
                        "text": (
                            "Our commitment to excellence drives every decision we make, "
                            "ensuring unparalleled results for our clients."
                        ),
                    },
                    {
                        "title": "The Experience",
                        "text": (
                            "Discover a new standard of quality that transforms "
                            "the ordinary into the extraordinary."
                        ),
                    },
                ],
                cta=f"Discover {brand_data['name']} Today",
                style=style_options[i % len(style_options)],
            )
        )

    return variations
