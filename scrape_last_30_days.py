#!/usr/bin/env python3
"""
Script to scrape Product Hunt data for the last 30 days
"""

import os
import logging
from ph_scraper import ProductHuntScraper

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("scrape_30_days.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PH30DayScraper")

def main():
    """Scrape Product Hunt data for the last 30 days"""
    output_file = "product_hunt_30_days.csv"
    
    logger.info("Starting 30-day Product Hunt scraper")
    
    # Initialize scraper with stealth mode
    scraper = ProductHuntScraper(use_stealth=True)
    
    # Scrape data for the last 30 days using PST timezone (Product Hunt's timezone)
    logger.info("Scraping last 30 days of Product Hunt data...")
    posts = scraper.scrape_recent_days(days=30, use_pst=True, limit=0)  # Limit 0 means no limit
    
    # Export to CSV
    if posts:
        if scraper.export_to_csv(posts, output_file):
            logger.info(f"Successfully scraped {len(posts)} products over 30 days")
            logger.info(f"Data saved to {output_file}")
        else:
            logger.error("Failed to export data to CSV")
            return 1
    else:
        logger.warning("No data was retrieved")
        return 1
    
    return 0

if __name__ == "__main__":
    exit(main()) 