#!/usr/bin/env python3
"""
Fetch yesterday's Product Hunt launches
"""

import datetime
from ph_scraper import ProductHuntScraper, logger

def main():
    # Calculate yesterday's date
    yesterday = (datetime.datetime.now() - datetime.timedelta(days=1)).date()
    yesterday_str = yesterday.isoformat()
    
    logger.info(f"Explicitly fetching products for yesterday: {yesterday_str}")
    
    # Initialize scraper
    scraper = ProductHuntScraper(use_stealth=True)
    
    # Get posts for yesterday
    posts = scraper.get_posts_by_date(yesterday_str)
    
    if not posts:
        logger.warning(f"No products found for {yesterday_str}")
        return
        
    # Process the posts
    processed_posts = scraper.process_post_data(posts)
    
    # Export to CSV
    output_file = f"products_{yesterday_str}.csv"
    if scraper.export_to_csv(processed_posts, output_file):
        logger.info(f"Successfully exported {len(processed_posts)} products to {output_file}")
    else:
        logger.error("Failed to export data")

if __name__ == "__main__":
    main() 