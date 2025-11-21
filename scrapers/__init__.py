"""
Scrapers package - Contains individual scrapers for each website.
"""
from .inkstation_scraper import scrape_inkstation
from .inkdepot_scraper import scrape_inkdepot
from .hottoner_scraper import scrape_hottoner

__all__ = [
    'scrape_inkstation',
    'scrape_inkdepot',
    'scrape_hottoner'
]
