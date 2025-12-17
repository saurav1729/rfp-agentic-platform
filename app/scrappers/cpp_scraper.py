import asyncio
import logging
from typing import List, Dict, Any
from datetime import datetime
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from .base_scrapper import BaseScraper

logger = logging.getLogger(__name__)

class CPPScraper(BaseScraper):
    def __init__(self):
        super().__init__("India CPPP")
        self.search_url = "https://eprocure.gov.in/eprocure/app"
    async def scrape(self) -> List[Dict[str, Any]]:
        loop = asyncio.get_running_loop()
        try:
            return await loop.run_in_executor(self.executor, self._scrape_sync)
        except Exception as e:
            logger.error(f"CPPP Scraping failed: {str(e)}")
            return []

    def _scrape_sync(self) -> List[Dict[str, Any]]:
        rfps = []
        driver = self._get_selenium_driver()
        if not driver: return []
        try:
            logger.info(f"Navigating to CPPP: {self.search_url}")
            driver.get(self.search_url)
            wait = WebDriverWait(driver, 30)
            try:
                close_btn = wait.until(EC.element_to_be_clickable((By.ID, "alertclose")))
                close_btn.click()
                logger.info("Closed CPPP Popup")
            except:
                pass 
            wait.until(EC.presence_of_element_located((By.CSS_SELECTOR, "tr[id^='informal']")))

            rows = driver.find_elements(By.CSS_SELECTOR, "tr[id^='informal']")
            logger.info(f"Found {len(rows)} tender rows on CPPP")

            tender_links = []

            for row in rows[:5]:
                try:
                    cols = row.find_elements(By.TAG_NAME, "td")
                    if len(cols) < 4: continue

                   
                    
                    link_el = cols[0].find_element(By.TAG_NAME, "a")
                    title = link_el.text.strip()
                    url = link_el.get_attribute("href")
                    ref_no = cols[1].text.strip()
                    closing_date_raw = cols[2].text.strip()

                    tender_links.append({
                        "url": url,
                        "title": title,
                        "ref_no": ref_no,
                        "closing_date": closing_date_raw
                    })
                    print(tender_links)
                except Exception as e:
                    continue

            for item in tender_links:
                try:
                    driver.get(item['url'])
                    details = self._parse_detail_page(driver)
                    full_rfp = {
                        'title': item['title'],
                        'source_url': item['url'],
                        'external_id': item['ref_no'], # Use Ref No as ID
                        'deadline': self._parse_indian_date(item['closing_date']),
                        **details
                    }
                    
                    rfps.append(self.normalize_rfp(full_rfp))

                    import time
                    time.sleep(1.5)

                except Exception as e:
                    logger.error(f"Error scraping detail {item['url']}: {e}")

        except Exception as e:
            logger.error(f"CPPP Sync Error: {e}")
        finally:
            self.close_driver()
            
        return rfps

    def _parse_detail_page(self, driver) -> Dict[str, Any]:
        """Scrapes the 'Basic Details' table from the detail view"""
        data = {}
        try:
            # Wait for the detail table 'tablebg'
            WebDriverWait(driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "tablebg"))
            )
            
            # Find all caption/field pairs
            captions = driver.find_elements(By.CLASS_NAME, "td_caption")
            fields = driver.find_elements(By.CLASS_NAME, "td_field")
            
            # They usually map 1-to-1 in visual order, but HTML structure varies.
            # A safer way is to find the row and get pairs.
            rows = driver.find_elements(By.CSS_SELECTOR, ".tablebg tr")
            
            for row in rows:
                cells = row.find_elements(By.TAG_NAME, "td")
                # Iterate in pairs: Caption -> Field
                for i in range(0, len(cells) - 1):
                    if "td_caption" in cells[i].get_attribute("class"):
                        key = cells[i].text.strip().replace(":", "")
                        # The value is usually the next cell
                        val = cells[i+1].text.strip()
                        if key and val:
                            data[key] = val
                            
        except Exception:
            pass # Return whatever we found so far

        # Map CPPP fields to our schema
        return {
            'agency': data.get("Organisation Chain", "Government of India"),
            'description': f"Tender Type: {data.get('Tender Type', 'N/A')} | Category: {data.get('Tender Category', 'N/A')} | Ref: {data.get('Tender Reference Number', '')}",
            'posted_date': datetime.now(), # Placeholder as 'Published Date' is hard to parse reliably
            'raw_data': data
        }

    def _parse_indian_date(self, date_str: str):
        """Parse '13-Dec-2025 06:55 PM'"""
        if not date_str: return None
        try:
            return datetime.strptime(date_str, "%d-%b-%Y %I:%M %p")
        except:
            return None
