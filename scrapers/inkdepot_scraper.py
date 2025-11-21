"""
Scraper for inkdepot.com.au
"""
import requests
from bs4 import BeautifulSoup
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.request_utils import make_request, random_delay, safe_extract_text, clean_price


def scrape_inkdepot(oem_code):
    """
    Scrape product information from inkdepot.com.au
    
    Args:
        oem_code (str): OEM product code to search for
        
    Returns:
        dict or None: Product information or None if not found
    """
    # Try multiple URL patterns as different sites use different search formats
    url_patterns = [
        f"https://www.inkdepot.com.au/search?q={oem_code}",
        f"https://www.inkdepot.com.au/search?keywords={oem_code}",
        f"https://www.inkdepot.com.au/catalogsearch/result/?q={oem_code}"
    ]
    
    url = url_patterns[0]  # Use the first pattern
    
    try:
        response = make_request(url)
        
        if not response:
            return {
                "OEM_CODE": oem_code,
                "Title": "Not Found",
                "Price": "N/A",
                "Website": "InkDepot",
                "Status": "Not Available",
                "URL": url
            }
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Try multiple possible selectors
        product = None
        selectors = [
            {"tag": "div", "class_": "product-item"},
            {"tag": "div", "class_": "product"},
            {"tag": "li", "class_": "item"},
            {"tag": "div", "class_": "product-card"}
        ]
        
        for selector in selectors:
            product = soup.find(selector["tag"], class_=selector["class_"])
            if product:
                break
        
        if not product:
            # Try to find any product-related element
            product = soup.find(["div", "li", "article"], class_=lambda x: x and "product" in x.lower())
        
        if not product:
            return {
                "OEM_CODE": oem_code,
                "Title": "Not Found",
                "Price": "N/A",
                "Website": "InkDepot",
                "Status": "Not Available",
                "URL": url
            }
        
        # Extract title
        title = None
        title_selectors = [
            product.find("a", class_=lambda x: x and ("title" in x.lower() or "name" in x.lower())),
            product.find("h2"),
            product.find("h3"),
            product.find("h4")
        ]
        
        for title_elem in title_selectors:
            if title_elem:
                title = safe_extract_text(title_elem)
                if title != "N/A":
                    break
        
        # Extract price
        price = None
        price_selectors = [
            product.find("span", class_=lambda x: x and "price" in x.lower()),
            product.find("div", class_=lambda x: x and "price" in x.lower()),
            product.find("p", class_=lambda x: x and "price" in x.lower()),
            product.find(string=lambda x: x and "$" in str(x))
        ]
        
        for price_elem in price_selectors:
            if price_elem:
                price = clean_price(safe_extract_text(price_elem) if hasattr(price_elem, 'text') else str(price_elem))
                if price != "N/A":
                    break
        
        # Check availability
        stock_indicators = product.find_all(string=lambda x: x and any(
            keyword in x.lower() for keyword in ["stock", "available", "in stock", "out of stock"]
        ))
        status = "Available"
        for indicator in stock_indicators:
            if "out" in indicator.lower():
                status = "Out of Stock"
                break
        
        # Add delay to avoid rate limiting
        random_delay(1, 3)
        
        return {
            "OEM_CODE": oem_code,
            "Title": title if title else "N/A",
            "Price": price if price else "N/A",
            "Website": "InkDepot",
            "Status": status,
            "URL": url
        }
        
    except Exception as e:
        print(f"❌ Error scraping InkDepot for {oem_code}: {e}")
        return {
            "OEM_CODE": oem_code,
            "Title": "Error",
            "Price": "N/A",
            "Website": "InkDepot",
            "Status": "Error",
            "URL": url
        }


# Test function
if __name__ == "__main__":
    test_code = "CB540A"
    result = scrape_inkdepot(test_code)
    print(f"\n🧪 Test result for {test_code}:")
    for key, value in result.items():
        print(f"  {key}: {value}")
