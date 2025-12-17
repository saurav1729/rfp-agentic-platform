from typing import List, Dict, Any
import asyncio
import logging
from datetime import datetime
from app.scrappers.cpp_scraper import CPPScraper
from app.services.email_service import EmailService
from app.services.rfp_repository import RFPRepository

logger = logging.getLogger(__name__)

class DiscoveryScheduler:
    """Orchestrates continuous RFP discovery from CPP portal and Email"""
    
    def __init__(self, email_config: Dict[str, str] = None):
        self.cpp_scraper = CPPScraper()
        
        # Initialize Email Service if config is provided
        self.email_service = None
        if email_config and email_config.get('email') and email_config.get('password'):
            self.email_service = EmailService(
                email_address=email_config.get('email'),
                email_password=email_config.get('password')
            )
            
        self.rfp_repository = RFPRepository()
        self.discovered_rfps: List[Dict[str, Any]] = []
    
    async def run_discovery_cycle(self) -> List[Dict[str, Any]]:
        """
        Execute one complete discovery cycle.
        Scrapes CPP portal, checks emails, and saves to MongoDB.
        """
        logger.info("Starting RFP discovery cycle")
        
        all_rfps = []
        tasks = []
        source_map = []  

        # 1. Add Scraper Task (Uncomment when ready to use scraper)
        tasks.append(self.cpp_scraper.scrape())
        source_map.append("CPP Portal")

        # 2. Add Email Task (if enabled)
        if self.email_service:
            tasks.append(self.email_service.check_rfp_emails())
            source_map.append("Email")
        
        # If no tasks are enabled, return early
        if not tasks:
            logger.warning("No discovery sources enabled (Scraper commented out & Email not configured).")
            return []

        try:
            # Run all tasks concurrently
            results = await asyncio.gather(*tasks, return_exceptions=True)
            
            for i, result in enumerate(results):
                current_source_name = source_map[i]

                if isinstance(result, Exception):
                    logger.error(f"{current_source_name} error: {str(result)}")
                    continue
                
                if result:
                    all_rfps.extend(result)
                    logger.info(f"{current_source_name}: Found {len(result)} RFPs")
                    
                    # Save to MongoDB
                    for rfp in result:
                        try:
                            self.rfp_repository.create_rfp(rfp)
                            # Optional verbose logging:
                            # logger.info(f"  Saved: {rfp.get('title', 'Untitled')[:50]}...")
                        except Exception as e:
                            logger.error(f"Failed to save RFP '{rfp.get('title', 'Unknown')}': {str(e)}")
            
            logger.info(f"✅ Discovery cycle complete: {len(all_rfps)} total RFPs discovered")
            self.discovered_rfps = all_rfps
            return all_rfps
            
        except Exception as e:
            logger.error(f"Discovery cycle critical failure: {str(e)}")
            return []
    
    async def start_continuous_discovery(self, interval_minutes: int = 60):
        """Start continuous discovery loop"""
        
        logger.info(f"Starting continuous discovery loop (Interval: {interval_minutes}min)")
        
        while True:
            try:
                await self.run_discovery_cycle()
                logger.info(f"Sleeping for {interval_minutes} minutes...")
                await asyncio.sleep(interval_minutes * 60)
            except asyncio.CancelledError:
                logger.info("Discovery loop cancelled.")
                break
            except Exception as e:
                logger.error(f"Continuous discovery error: {str(e)}")
                await asyncio.sleep(60)  # Wait 1 min before retry on error