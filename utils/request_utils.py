"""
HTTP request utilities with retry logic and rate limiting.
"""
import requests
import random
import time
from typing import Optional


def get_random_user_agent():
    """
    Return a random user agent to avoid detection.
    
    Returns:
        str: A user agent string
    """
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:120.0) Gecko/20100101 Firefox/120.0",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.1 Safari/605.1.15"
    ]
    return random.choice(user_agents)


def get_headers():
    """
    Generate headers for HTTP requests.
    
    Returns:
        dict: Request headers
    """
    return {
        "User-Agent": get_random_user_agent(),
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }


def make_request(url, max_retries=3, timeout=10):
    """
    Make an HTTP GET request with retry logic.
    
    Args:
        url (str): URL to request
        max_retries (int): Maximum number of retry attempts
        timeout (int): Request timeout in seconds
        
    Returns:
        requests.Response or None: Response object if successful, None otherwise
    """
    for attempt in range(max_retries):
        try:
            response = requests.get(
                url, 
                headers=get_headers(), 
                timeout=timeout,
                allow_redirects=True
            )
            
            if response.status_code == 200:
                return response
            elif response.status_code == 404:
                # Product not found - don't retry
                return None
            elif response.status_code == 429:
                # Too many requests - wait longer
                wait_time = (attempt + 1) * 5
                print(f"⚠️  Rate limited. Waiting {wait_time}s before retry...")
                time.sleep(wait_time)
            else:
                print(f"⚠️  HTTP {response.status_code} for {url}")
                
        except requests.exceptions.Timeout:
            print(f"⏱️  Timeout on attempt {attempt + 1}/{max_retries}")
        except requests.exceptions.ConnectionError:
            print(f"🔌 Connection error on attempt {attempt + 1}/{max_retries}")
        except Exception as e:
            print(f"❌ Error: {e}")
        
        # Wait before retry (except on last attempt)
        if attempt < max_retries - 1:
            time.sleep(random.uniform(2, 4))
    
    return None


def random_delay(min_seconds=1, max_seconds=3):
    """
    Add a random delay to avoid detection and rate limiting.
    
    Args:
        min_seconds (float): Minimum delay in seconds
        max_seconds (float): Maximum delay in seconds
    """
    delay = random.uniform(min_seconds, max_seconds)
    time.sleep(delay)


def safe_extract_text(element, default="N/A"):
    """
    Safely extract text from a BeautifulSoup element.
    
    Args:
        element: BeautifulSoup element
        default (str): Default value if extraction fails
        
    Returns:
        str: Extracted text or default value
    """
    try:
        if element:
            return element.text.strip()
        return default
    except:
        return default


def clean_price(price_text):
    """
    Clean and standardize price text.
    
    Args:
        price_text (str): Raw price text
        
    Returns:
        str: Cleaned price string
    """
    if not price_text or price_text == "N/A":
        return "N/A"
    
    # Remove extra whitespace
    price_text = price_text.strip()
    
    # Extract price using common patterns
    import re
    price_match = re.search(r'\$[\d,]+\.?\d*', price_text)
    if price_match:
        return price_match.group(0)
    
    return price_text
