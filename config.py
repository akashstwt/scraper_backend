"""
Configuration file for the price comparison scraper.
Edit these settings to customize the scraper's behavior.
"""

# ============================================================
# FILE PATHS
# ============================================================

# Input Excel file containing OEM codes
INPUT_FILE = "data/oem_codes.xlsx"

# Output Excel file for results
OUTPUT_FILE = "data/price_comparison.xlsx"


# ============================================================
# SCRAPING SETTINGS
# ============================================================

# Maximum number of OEM codes to process (None = all codes)
# Useful for testing with a subset of data
BATCH_SIZE = None  # Set to a number like 10 for testing

# Delay between requests (in seconds)
MIN_DELAY = 1  # Minimum delay
MAX_DELAY = 3  # Maximum delay

# Request timeout (in seconds)
REQUEST_TIMEOUT = 10

# Maximum retry attempts for failed requests
MAX_RETRIES = 3


# ============================================================
# WEBSITE SCRAPERS
# ============================================================

# Enable/disable specific scrapers
# Set to False to skip a particular website
ENABLE_INKSTATION = True
ENABLE_INKDEPOT = True
ENABLE_CARTRIDGESTORE = True


# ============================================================
# ADVANCED SETTINGS
# ============================================================

# Use Selenium for JavaScript-heavy sites (requires selenium installed)
USE_SELENIUM = False

# Save HTML for debugging (creates debug files)
DEBUG_SAVE_HTML = False

# Verbose logging (show more detailed output)
VERBOSE_LOGGING = False

# Number of parallel workers (for concurrent scraping)
# WARNING: Higher values may trigger rate limiting
MAX_WORKERS = 1  # Set to 3-5 for parallel scraping


# ============================================================
# EXCEL OUTPUT SETTINGS
# ============================================================

# Include summary sheet in output Excel
INCLUDE_SUMMARY_SHEET = True

# Include timestamp in output filename
ADD_TIMESTAMP_TO_OUTPUT = False  # If True, output will be like "results_2024-01-15.xlsx"


# ============================================================
# USER AGENTS (Randomly selected for each request)
# ============================================================

USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
]


# ============================================================
# WEBSITE-SPECIFIC SETTINGS
# ============================================================

# InkStation settings
INKSTATION_URL_TEMPLATE = "https://www.inkstation.com.au/search?keywords={oem_code}"

# InkDepot settings  
INKDEPOT_URL_TEMPLATE = "https://www.inkdepot.com.au/search?q={oem_code}"

# CartridgeStore settings
CARTRIDGESTORE_URL_TEMPLATE = "https://www.cartridgestore.com.au/search?q={oem_code}"


# ============================================================
# NOTES
# ============================================================
"""
TIPS FOR CUSTOMIZATION:

1. Testing Mode:
   Set BATCH_SIZE = 10 to test with first 10 codes only

2. Speed vs Safety:
   - Lower delays = faster but risky (may get blocked)
   - Higher delays = slower but safer

3. Parallel Scraping:
   Set MAX_WORKERS = 3-5 for faster scraping
   WARNING: May trigger rate limiting on some sites

4. Debugging:
   Set DEBUG_SAVE_HTML = True to save HTML files for inspection
   Set VERBOSE_LOGGING = True for detailed output

5. Selenium Mode:
   Set USE_SELENIUM = True for JavaScript-heavy sites
   Requires: pip install selenium webdriver-manager
"""
