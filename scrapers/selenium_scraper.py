"""
Selenium-based scraper for websites with Cloudflare/CAPTCHA protection.
This uses a real browser to bypass anti-bot measures.
"""
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
import time
import random


class SeleniumScraper:
    """Browser-based scraper that can handle JavaScript and CAPTCHA"""
    
    def __init__(self, headless=False):
        """
        Initialize the Selenium scraper
        
        Args:
            headless (bool): If True, browser runs in background. 
                           Set to False to see browser and solve CAPTCHA manually if needed.
        """
        self.driver = None
        self.headless = headless
        self.cloudflare_solved = False  # Track if we've already solved Cloudflare
        self.request_count = 0  # Track number of requests
        
    def setup_driver(self):
        """Setup Chrome driver - browser will stay open for manual CAPTCHA solving"""
        options = Options()
        
        # Don't close browser automatically
        options.add_experimental_option("detach", True)
        
        # Stealth options
        options.add_argument('--disable-blink-features=AutomationControlled')
        options.add_experimental_option("excludeSwitches", ["enable-automation"])
        options.add_experimental_option('useAutomationExtension', False)
        
        # Basic options
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        
        # Headless mode (MUST be False to solve CAPTCHA manually)
        if self.headless:
            print("⚠️  Headless mode disabled - CAPTCHA requires manual interaction")
        
        # Setup ChromeDriver
        service = Service(ChromeDriverManager().install())
        driver = webdriver.Chrome(service=service, options=options)
        
        self.driver = driver
        return driver
    
    def wait_for_cloudflare(self, timeout=120):
        """
        Wait for Cloudflare challenge - YOU NEED TO SOLVE IT MANUALLY
        The browser will stay open - click the checkbox when it appears
        """
        print("\n" + "="*60)
        print("⚠️  CLOUDFLARE DETECTED - MANUAL ACTION REQUIRED!")
        print("="*60)
        print("Please solve the Cloudflare challenge in the browser window:")
        print("1. Look for the checkbox that says 'Verify you are human'")
        print("2. Click it")
        print("3. Wait for the page to load")
        print("4. The script will continue automatically\n")
        
        # Wait for page content to appear (indicating challenge is solved)
        for i in range(timeout):
            try:
                page_source = self.driver.page_source.lower()
                
                # Check if we have actual product content (challenge solved)
                if any(indicator in page_source for indicator in ['product', 'search', 'add to cart', '$']):
                    print("\n✅ Challenge solved! Page loaded successfully!")
                    time.sleep(3)
                    return True
                
                # Progress indicator
                if i % 10 == 0 and i > 0:
                    print(f"⏳ Waiting for you to solve the challenge... ({i}s elapsed)")
                
                time.sleep(1)
            except:
                time.sleep(1)
        
        print("\n⚠️ Timeout - proceeding anyway...")
        return False
    
    def scrape_inkstation(self, oem_code):
        """
        Scrape InkStation using Selenium
        
        Args:
            oem_code (str): Product code to search
            
        Returns:
            dict: Product information
        """
        url = f"https://www.inkstation.com.au/search?keywords={oem_code}"
        
        try:
            if not self.driver:
                self.setup_driver()
            
            self.request_count += 1
            print(f"🌐 Loading {url}")
            self.driver.get(url)
            
            # Only wait for Cloudflare on first request or if we detect it again
            if not self.cloudflare_solved:
                self.wait_for_cloudflare(timeout=120)
                self.cloudflare_solved = True  # Mark as solved for subsequent requests
                print("✅ Cloudflare session established - subsequent requests will be faster!")
            else:
                # Just wait for page to load (much faster)
                time.sleep(3)
                print("⚡ Using existing Cloudflare session (no CAPTCHA needed)")
            
            # Additional wait for dynamic content
            print("⏳ Waiting for page to fully render...")
            time.sleep(5)  # Reduced from 8 seconds since no CAPTCHA
            
            # Scroll to trigger lazy loading
            self.driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
            time.sleep(2)
            self.driver.execute_script("window.scrollTo(0, 0);")
            time.sleep(2)
            
            # Try to find product elements
            try:
                # Wait for page content to load (more flexible)
                WebDriverWait(self.driver, 15).until(
                    lambda d: d.execute_script("return document.readyState") == "complete"
                )
                
                # Get page source for BeautifulSoup parsing (more reliable)
                from bs4 import BeautifulSoup
                soup = BeautifulSoup(self.driver.page_source, 'html.parser')
                
                # InkStation specific: Find product card
                # Try multiple possible container structures
                product = None
                
                # Method 1: Look for InkStation-specific product listing containers
                # Common patterns: product-item, product-card, search-result-item, etc.
                selectors = [
                    {'class_': 'product-item'},
                    {'class_': 'product-card'},
                    {'class_': 'search-result'},
                    {'class_': 'item'},
                    {'attrs': {'data-product-id': True}},
                    {'attrs': {'data-product': True}},
                ]
                
                for selector in selectors:
                    products = soup.find_all('div', **selector)
                    if not products:
                        products = soup.find_all('article', **selector)
                    if not products:
                        products = soup.find_all('li', **selector)
                    
                    if products:
                        # Found potential products, verify they have price
                        for p in products:
                            if p.find(string=lambda x: x and '$' in str(x)):
                                product = p
                                print(f"✅ Found product using selector: {selector}")
                                break
                    if product:
                        break
                
                # Method 2: Generic fallback - find any div/article containing price
                if not product:
                    all_containers = soup.find_all(['div', 'article', 'li'])
                    for container in all_containers:
                        # Check if has price and product-like attributes
                        has_price = container.find(string=lambda x: x and '$' in str(x))
                        has_link = container.find('a', href=True)
                        has_image = container.find('img')
                        
                        # Product should have at least price and link
                        if has_price and has_link:
                            product = container
                            print(f"✅ Found product using fallback detection")
                            break
                
                if not product:
                    print(f"⚠️  No product found for {oem_code}")
                    return {
                        "OEM_CODE": oem_code,
                        "Title": "Not Found",
                        "Price": "N/A",
                        "Website": "InkStation",
                        "Status": "Not Available",
                        "URL": url
                    }
                
                print(f"✅ Product card found for {oem_code}")
                
                # Extract title - look for heading or product link text
                title = "N/A"
                if hasattr(product, 'find'):  # BeautifulSoup
                    # Try to find title in multiple ways
                    title_elem = (product.find("h2") or product.find("h3") or product.find("h4") or
                                product.find("a", href=lambda x: x and 'product' in str(x).lower()) or
                                product.find("a", class_=lambda x: x and any(t in str(x).lower() for t in ['title', 'name', 'product'])))
                    if title_elem:
                        title = title_elem.get_text(strip=True)
                    # If still not found, look for any link with substantial text
                    if title == "N/A":
                        links = product.find_all('a')
                        for link in links:
                            text = link.get_text(strip=True)
                            if len(text) > 10 and '$' not in text:  # Avoid price links
                                title = text
                                break
                
                # Extract price - look for $ symbol
                price = "N/A"
                if hasattr(product, 'find'):  # BeautifulSoup
                    # Find any element with $ in text
                    import re
                    price_elem = product.find(string=lambda x: x and '$' in str(x))
                    if price_elem:
                        # Extract price from text
                        price_match = re.search(r'\$[\d,]+\.?\d*', str(price_elem))
                        if price_match:
                            price = price_match.group(0)
                    
                    # If not found, try price-specific elements
                    if price == "N/A":
                        price_elems = product.find_all(['span', 'div', 'p'], 
                            class_=lambda x: x and 'price' in str(x).lower())
                        for elem in price_elems:
                            text = elem.get_text(strip=True)
                            price_match = re.search(r'\$[\d,]+\.?\d*', text)
                            if price_match:
                                price = price_match.group(0)
                                break
                
                # Check availability
                page_source = self.driver.page_source.lower()
                status = "Available"
                if "out of stock" in page_source or "not available" in page_source:
                    status = "Out of Stock"
                
                return {
                    "OEM_CODE": oem_code,
                    "Title": title,
                    "Price": price,
                    "Website": "InkStation",
                    "Status": status,
                    "URL": url
                }
                
            except Exception as e:
                print(f"⚠️  Error parsing page for {oem_code}: {e}")
                return {
                    "OEM_CODE": oem_code,
                    "Title": "Error",
                    "Price": "N/A",
                    "Website": "InkStation",
                    "Status": "Error",
                    "URL": url
                }
        
        except Exception as e:
            print(f"❌ Error loading page for {oem_code}: {e}")
            return {
                "OEM_CODE": oem_code,
                "Title": "Error",
                "Price": "N/A",
                "Website": "InkStation",
                "Status": "Error",
                "URL": url
            }
    
    def close(self):
        """Close the browser"""
        if self.driver:
            self.driver.quit()
            self.driver = None


# Test function
if __name__ == "__main__":
    scraper = SeleniumScraper(headless=False)  # Set to False to see browser
    
    try:
        result = scraper.scrape_inkstation("WBP03")
        print("\n🧪 Test Result:")
        for key, value in result.items():
            print(f"  {key}: {value}")
    finally:
        scraper.close()
