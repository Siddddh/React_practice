from __future__ import annotations

import argparse
import asyncio
import logging
from typing import List

from config import load_config
from enricher import enrich_with_pdl
from lead_saver import clean_and_deduplicate, save_leads_to_csv
from parser import extract_linkedin_urls
from scraper import scrape_profiles
from search_agent import generate_queries, search_google


def _configure_logging(verbose: bool) -> None:
    """
    Configure application-wide logging.

    Args:
        verbose: If True, use DEBUG log level, otherwise INFO.
    """
    level = logging.DEBUG if verbose else logging.INFO
    logging.basicConfig(
        level=level,
        format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    )


def parse_args() -> argparse.Namespace:
    """
    Parse command line arguments for the lead generation script.

    Returns:
        argparse.Namespace with parsed arguments.
    """
    parser = argparse.ArgumentParser(
        description="LinkedIn Lead Generation Agent using Google + SerpAPI."
    )
    parser.add_argument(
        "--job-titles",
        nargs="*",
        help="Optional list of job titles (for generated LinkedIn queries).",
    )
    parser.add_argument(
        "--locations",
        nargs="*",
        help="Optional list of locations (for generated LinkedIn queries).",
    )
    parser.add_argument(
        "--queries",
        nargs="*",
        help=(
            "Optional list of full Google queries to use directly. "
            "Example: site:linkedin.com/in \"broadcast engineer\" Dubai"
        ),
    )
    parser.add_argument(
        "--output",
        default=None,
        help="Optional output CSV path (default: value from config).",
    )
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose logging.",
    )
    return parser.parse_args()


async def run_async(
    job_titles: List[str],
    locations: List[str],
    output_csv: str,
    queries: List[str] | None = None,
) -> None:
    """
    Execute the full lead generation workflow asynchronously.

    Args:
        job_titles: List of job titles to search for.
        locations: List of locations to target.
        output_csv: Path to the output CSV file.
    """
    config = load_config()
    search_cfg = config.search
    pdl_api_key = getattr(config, "pdl_api_key", None)

    if job_titles:
        config.job_titles = job_titles
    if locations:
        config.locations = locations
    if output_csv:
        config.output_csv = output_csv

    logger = logging.getLogger(__name__)

    # 1. Query Generator (or use raw queries if supplied)
    if queries:
        # Use the exact queries the user typed.
        active_queries = [q for q in queries if q.strip()]
        logger.info("Using %d user-supplied Google queries", len(active_queries))
    elif config.job_titles or config.locations:
        logger.info(
            "Starting lead generation for titles=%s, locations=%s",
            config.job_titles,
            config.locations,
        )
        active_queries = generate_queries(config.job_titles, config.locations)
        logger.info("Generated %d search queries", len(active_queries))
    else:
        logger.info("No queries provided on CLI; entering interactive query mode.")
        print(
            "Enter Google search queries exactly as you would type them.\n"
            "Example: site:linkedin.com/in \"John Smith\" \"broadcast engineer\" Mumbai\n"
            "Press ENTER on an empty line when you are done.\n"
        )
        active_queries = []
        while True:
            line = input("> ").strip()
            if not line:
                break
            active_queries.append(line)
        logger.info("Collected %d interactive queries", len(active_queries))

    # 2. Google Search + 3. LinkedIn URL Extractor
    all_profile_urls: List[str] = []
    for q in active_queries:
        try:
            organic_results = search_google(q, search_cfg)
        except RuntimeError as exc:
            logging.getLogger(__name__).error("Search failed for query '%s': %s", q, exc)
            continue
        urls = extract_linkedin_urls(organic_results)
        all_profile_urls.extend(urls)

    if not all_profile_urls:
        logging.getLogger(__name__).warning("No LinkedIn profile URLs found. Exiting.")
        return

    # 4. Enrichment / Profile Scraper
    if pdl_api_key:
        logging.getLogger(__name__).info("Using People Data Labs enrichment for profiles.")
        leads = enrich_with_pdl(all_profile_urls, pdl_api_key)
    else:
        logging.getLogger(__name__).info(
            "No PDL_API_KEY configured; falling back to Playwright scraping."
        )
        leads = await scrape_profiles(all_profile_urls, search_cfg)

    # 5. Data Cleaner
    df = clean_and_deduplicate(leads)

    # 6. Lead Export
    save_leads_to_csv(df, config.output_csv)


def main() -> None:
    """
    Entry point for the command-line interface.
    """
    args = parse_args()
    _configure_logging(args.verbose)

    try:
        asyncio.run(
            run_async(
                job_titles=args.job_titles or [],
                locations=args.locations or [],
                output_csv=args.output or "",
                queries=args.queries or None,
            )
        )
    except KeyboardInterrupt:
        logging.getLogger(__name__).warning("Interrupted by user, shutting down.")


if __name__ == "__main__":
    main()

