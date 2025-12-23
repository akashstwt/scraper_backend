from dotenv import load_dotenv
load_dotenv()

from .inkstation_scraper import scrape_inkstation
from .hottoner_scraper import scrape_hottoner

__all__ = [
    'scrape_inkstation',
    'scrape_hottoner'
]
