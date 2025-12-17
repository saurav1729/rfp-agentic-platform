from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import asyncio
from concurrent.futures import ThreadPoolExecutor
from selenium import webdriver
from selenium.webdriver.chrome.options import Options

logger = logging.getLogger(__name__)

class BaseScraper(ABC):
    """Base class for all RFP portal web scrapers"""
    
    def __init__(self, name: str):
        self.name = name
        self.timeout = 30
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/115.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.9',
            'Referer': 'https://www.google.com/',
        }
        self.driver = None
        # Dedicated thread pool for blocking Selenium operations
        self.executor = ThreadPoolExecutor(max_workers=1)
    
    def _get_selenium_driver(self):
        """Initialize Stealth Selenium WebDriver"""
        if self.driver is None:
            chrome_options = Options()
            
            # --- HEADLESS MODE TOGGLE ---
            # Uncomment the line below to run in background (Production)
            # chrome_options.add_argument("--headless=new") 
            
            # --- STEALTH & STABILITY SETTINGS ---
            chrome_options.add_argument("--no-sandbox")
            chrome_options.add_argument("--disable-dev-shm-usage")
            chrome_options.add_argument("--disable-gpu")
            chrome_options.add_argument("--window-size=1920,1080")
            chrome_options.add_argument("--start-maximized")
            
            # Anti-detection flags
            chrome_options.add_argument("--disable-blink-features=AutomationControlled")
            chrome_options.add_experimental_option("excludeSwitches", ["enable-automation"])
            chrome_options.add_experimental_option('useAutomationExtension', False)
            chrome_options.add_argument(f"user-agent={self.headers['User-Agent']}")
            
            try:
                self.driver = webdriver.Chrome(options=chrome_options)
                
                # Execute CDP command to hide webdriver property
                self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                    "source": """
                        Object.defineProperty(navigator, 'webdriver', {
                            get: () => undefined
                        })
                    """
                })
                
            except Exception as e:
                logger.warning(f"Selenium driver initialization failed: {str(e)}")
                return None
        
        return self.driver
    
    def close_driver(self):
        """Close Selenium driver safely"""
        if self.driver:
            try:
                self.driver.quit()
            except Exception as e:
                logger.warning(f"Error closing driver: {str(e)}")
            finally:
                self.driver = None

    def __del__(self):
        """Destructor to ensure driver is killed if object is garbage collected"""
        self.close_driver()
    
    @abstractmethod
    async def scrape(self) -> List[Dict[str, Any]]:
        """Scrape RFPs from portal (Must be non-blocking)"""
        pass
    
    def normalize_rfp(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Normalize RFP data to common format"""
        return {
            'title': data.get('title', 'Untitled Opportunity'),
            'description': data.get('description', ''),
            'source': self.name,
            'source_url': data.get('source_url', ''),
            'posted_date': data.get('posted_date'),
            'deadline': data.get('deadline'),
            'budget_min': data.get('budget_min'),
            'budget_max': data.get('budget_max'),
            'agency': data.get('agency', 'Unknown'),
            'keywords': data.get('keywords', []),
            'external_id': data.get('external_id', ''),
            'raw_data': data.get('raw_data', {}),
            'discovered_at': datetime.utcnow()
        }

    def _extract_budget(self, text: str) -> tuple:
        import re
        if not text: return None, None
        budget_pattern = r'\$?([\d,]+(?:\.\d{2})?)\s*(?:to|-|–)?\s*\$?([\d,]+(?:\.\d{2})?)?'
        matches = re.findall(budget_pattern, text)
        if matches:
            try:
                min_val = float(matches[0][0].replace(',', '')) if matches[0][0] else None
                max_val = float(matches[0][1].replace(',', '')) if len(matches[0]) > 1 and matches[0][1] else min_val
                return min_val, max_val
            except:
                pass
        return None, None