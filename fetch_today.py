#!/usr/bin/env python3
"""
Fetch today's Product Hunt launches with detailed logging
"""

import datetime
import pytz
from ph_scraper import ProductHuntScraper, logger

def main():
    # Get current date in multiple timezones
    now_utc = datetime.datetime.now(pytz.UTC)
    now_pst = now_utc.astimezone(pytz.timezone('US/Pacific'))
    
    today_utc = now_utc.date().isoformat()
    today_pst = now_pst.date().isoformat()
    
    logger.info(f"Current time (UTC): {now_utc}")
    logger.info(f"Current time (PST/Product Hunt timezone): {now_pst}")
    logger.info(f"Fetching products for today (UTC): {today_utc}")
    
    # Initialize scraper
    scraper = ProductHuntScraper(use_stealth=True)
    
    # Get posts for today (UTC)
    posts = scraper.get_posts_by_date(today_utc)
    
    if not posts:
        logger.warning(f"No products found for today (UTC): {today_utc}")
        logger.info("Possible reasons:")
        logger.info("1. It's too early in the day and no products have been launched yet")
        logger.info("2. Product Hunt typically launches products based on PST timezone")
        logger.info("3. The API might have rate limits or other restrictions")
        
        # If UTC and PST dates are different, try PST date
        if today_utc != today_pst:
            logger.info(f"Trying with PST date: {today_pst}")
            posts = scraper.get_posts_by_date(today_pst)
            
            if not posts:
                logger.warning(f"No products found for today (PST): {today_pst}")
                return
    
    # Process the posts
    processed_posts = scraper.process_post_data(posts)
    
    # Export to CSV
    output_file = f"products_today.csv"
    if scraper.export_to_csv(processed_posts, output_file):
        logger.info(f"Successfully exported {len(processed_posts)} products to {output_file}")
    else:
        logger.error("Failed to export data")

if __name__ == "__main__":
    main() 