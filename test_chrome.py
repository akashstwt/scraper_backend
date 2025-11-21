"""Test ChromeDriver setup"""
import sys
sys.path.append('.')

try:
    print("Testing ChromeDriver setup...")
    from scrapers.selenium_scraper import SeleniumScraper
    
    print("Creating SeleniumScraper instance...")
    scraper = SeleniumScraper(headless=False)
    
    print("Setting up driver...")
    scraper.setup_driver()
    
    print("✅ ChromeDriver setup successful!")
    print("✅ Browser should open now...")
    
    # Test a simple navigation
    scraper.driver.get("https://www.google.com")
    print("✅ Navigation successful!")
    
    # Close
    scraper.close()
    print("✅ Test complete!")
    
except Exception as e:
    print(f"❌ Error: {e}")
    import traceback
    traceback.print_exc()
