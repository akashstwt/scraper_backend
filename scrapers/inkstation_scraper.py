"""
Scraper for inkstation.com.au
"""
import requests
from bs4 import BeautifulSoup
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.request_utils import make_request, random_delay, safe_extract_text, clean_price


def scrape_inkstation(oem_code):
    """
    Scrape product information from inkstation.com.au
    
    Args:
        oem_code (str): OEM product code to search for
        
    Returns:
        dict or None: Product information or None if not found
    """
    url = f"https://www.inkstation.com.au/search?keywords={oem_code}"
    
    try:
        response = make_request(url)
        
        if not response:
            return {
                "OEM_CODE": oem_code,
                "Title": "Not Found",
                "Price": "N/A",
                "Website": "InkStation",
                "Status": "Not Available",
                "URL": url
            }
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # Try multiple possible selectors (websites change their HTML)
        product = None
        selectors = [
            {"tag": "div", "class_": "product-item"},
            {"tag": "div", "class_": "product"},
            {"tag": "article", "class_": "product-item"},
            {"tag": "div", "class_": "productCard"}
        ]
        
        for selector in selectors:
            product = soup.find(selector["tag"], class_=selector["class_"])
            if product:
                break
        
        if not product:
            # Try to find any product-related div
            product = soup.find("div", class_=lambda x: x and "product" in x.lower())
        
        if not product:
            return {
                "OEM_CODE": oem_code,
                "Title": "Not Found",
                "Price": "N/A",
                "Website": "InkStation",
                "Status": "Not Available",
                "URL": url
            }
        
        # Extract title - try multiple selectors
        title = None
        title_selectors = [
            product.find("a", class_=lambda x: x and "title" in x.lower()),
            product.find("h2"),
            product.find("h3"),
            product.find("a", class_=lambda x: x and "name" in x.lower())
        ]
        
        for title_elem in title_selectors:
            if title_elem:
                title = safe_extract_text(title_elem)
                if title != "N/A":
                    break
        
        # Extract price - try multiple selectors
        price = None
        price_selectors = [
            product.find("span", class_=lambda x: x and "price" in x.lower()),
            product.find("div", class_=lambda x: x and "price" in x.lower()),
            product.find("p", class_=lambda x: x and "price" in x.lower())
        ]
        
        for price_elem in price_selectors:
            if price_elem:
                price = clean_price(safe_extract_text(price_elem))
                if price != "N/A":
                    break
        
        # Check availability
        stock_elem = product.find(string=lambda x: x and ("stock" in x.lower() or "available" in x.lower()))
        status = "Available" if not stock_elem or "out" not in str(stock_elem).lower() else "Out of Stock"
        
        # Add delay to avoid rate limiting
        random_delay(1, 3)
        
        return {
            "OEM_CODE": oem_code,
            "Title": title if title else "N/A",
            "Price": price if price else "N/A",
            "Website": "InkStation",
            "Status": status,
            "URL": url
        }
        
    except Exception as e:
        print(f"❌ Error scraping InkStation for {oem_code}: {e}")
        return {
            "OEM_CODE": oem_code,
            "Title": "Error",
            "Price": "N/A",
            "Website": "InkStation",
            "Status": "Error",
            "URL": url
        }


# Test function
if __name__ == "__main__":
    test_code = "WBP03"
    result = scrape_inkstation(test_code)
    print(f"\n🧪 Test result for {test_code}:")
    for key, value in result.items():
        print(f"  {key}: {value}")
