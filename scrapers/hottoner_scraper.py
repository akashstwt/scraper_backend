"""
Scraper for HotToner.com.au
"""
import requests
from bs4 import BeautifulSoup
import sys
import os

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from utils.request_utils import make_request, random_delay, safe_extract_text, clean_price


def scrape_hottoner(oem_code):
    """
    Scrape product information from HotToner.com.au
    
    Args:
        oem_code (str): OEM product code to search for
        
    Returns:
        dict or None: Product information or None if not found
    """
    url = f"https://www.hottoner.com.au/index.php?route=product/search&filter_cartridge={oem_code}"
    
    try:
        # HotToner seems to have issues with make_request, use direct requests
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.5",
            "Connection": "keep-alive",
        }
        response = requests.get(url, headers=headers, timeout=15)
        
        if response.status_code != 200:
            return {
                "OEM_CODE": oem_code,
                "Title": "Not Found",
                "Price": "N/A",
                "Website": "HotToner",
                "Status": "Not Available",
                "URL": url
            }
        
        soup = BeautifulSoup(response.text, "html.parser")
        
        # HotToner has two possible page types:
        # 1. Product detail page (single product - redirects directly)
        # 2. Search results page (multiple products - shows table)
        
        # Check for product detail page first
        product_info_div = soup.find('div', class_='product-info')
        
        if product_info_div:
            # CASE 1: Product detail page (single product)
            # Extract title from h1 tag
            title = "N/A"
            h1_title = soup.find('h1')
            if h1_title:
                title = safe_extract_text(h1_title)
            
            # Extract price from div.price > span.price-new
            price = "N/A"
            price_div = soup.find('div', class_='price')
            if price_div:
                price_span = price_div.find('span', class_='price-new')
                if price_span:
                    price_text = safe_extract_text(price_span)
                    price = clean_price(price_text)
            
            # Extract availability status
            status = "Available"
            availability_text = soup.find(string=lambda x: x and 'Availability:' in str(x))
            if availability_text:
                parent = availability_text.find_parent()
                if parent:
                    stock_text = safe_extract_text(parent)
                    if 'InStock' in stock_text:
                        status = "In Stock"
                    elif 'OutOfStock' in stock_text or 'Out of Stock' in stock_text:
                        status = "Out of Stock"
            
            # Check for "Out of Stock" indicator
            outofstock_div = soup.find('div', class_='OutofStock')
            if outofstock_div:
                status = "Out of Stock"
        
        else:
            # CASE 2: Search results page (multiple products in table)
            product_list = soup.find('div', class_='product-list')
            
            if not product_list:
                # Product not found
                return {
                    "OEM_CODE": oem_code,
                    "Title": "Not Found",
                    "Price": "N/A",
                    "Website": "HotToner",
                    "Status": "Not Available",
                    "URL": url
                }
            
            # Find first product (li element with table inside)
            product_li = product_list.find('li')
            
            if not product_li:
                return {
                    "OEM_CODE": oem_code,
                    "Title": "Not Found",
                    "Price": "N/A",
                    "Website": "HotToner",
                    "Status": "Not Available",
                    "URL": url
                }
            
            # Extract title from td.pl-name
            title = "N/A"
            title_cell = product_li.find('td', class_='pl-name')
            if title_cell:
                title_link = title_cell.find('a')
                if title_link:
                    title = safe_extract_text(title_link)
            
            # Extract price from td.pl-our-price
            price = "N/A"
            price_cell = product_li.find('td', class_='pl-our-price')
            if price_cell:
                price_text = safe_extract_text(price_cell)
                price = clean_price(price_text)
            
            # Extract availability status
            status = "Available"
            stock_indicator = product_li.find(string=lambda x: x and 'InStock' in str(x))
            if stock_indicator:
                status = "In Stock"
            elif product_li.find(string=lambda x: x and ('OutOfStock' in str(x) or 'out of stock' in str(x).lower())):
                status = "Out of Stock"
        
        # Add delay to avoid rate limiting
        random_delay(1, 3)
        
        return {
            "OEM_CODE": oem_code,
            "Title": title,
            "Price": price,
            "Website": "HotToner",
            "Status": status,
            "URL": url
        }
        
    except Exception as e:
        print(f"❌ Error scraping HotToner for {oem_code}: {e}")
        return {
            "OEM_CODE": oem_code,
            "Title": "Error",
            "Price": "N/A",
            "Website": "HotToner",
            "Status": "Error",
            "URL": url
        }


# Test function
if __name__ == "__main__":
    import os
    os.environ['DEBUG_HOTTONER'] = '1'  # Enable HTML saving
    
    test_code = "A0XPWY1"
    print(f"Testing HotToner scraper with {test_code}...\n")
    result = scrape_hottoner(test_code)
    print(f"\n🧪 Test result for {test_code}:")
    for key, value in result.items():
        print(f"  {key}: {value}")
