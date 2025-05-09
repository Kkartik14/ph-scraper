#!/usr/bin/env python3
"""
Product Hunt Scraper - Fetches product data using GraphQL API with anti-detection features
"""

import os
import sys
import json
import time
import argparse
import datetime
import random
import logging
from typing import Dict, List, Any, Optional, Union

import requests
import pandas as pd
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ph_scraper.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger("PHScraper")

# Load environment variables
load_dotenv()

# Constants
API_URL = "https://api.producthunt.com/v2/api/graphql"
API_DOMAIN = "api.producthunt.com"
DEFAULT_OUTPUT_FILE = "product_hunt_data.csv"
MAX_RETRIES = 3
RETRY_DELAY = 2  # seconds

# API Authentication credentials
CLIENT_ID = os.getenv("PH_CLIENT_ID")
CLIENT_SECRET = os.getenv("PH_CLIENT_SECRET")

# User agents for rotation
USER_AGENTS = [
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.1 Safari/605.1.15",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36 Edg/96.0.1054.62",
    "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/96.0.4664.110 Safari/537.36",
]

class ProductHuntScraper:
    """Product Hunt scraper using GraphQL API with anti-detection features"""

    def __init__(self, use_stealth: bool = True):
        """
        Initialize the scraper
        
        Args:
            use_stealth: Whether to use stealth features like delays and user agent rotation
        """
        self.access_token = None
        self.token_expiry = 0
        self.use_stealth = use_stealth
        self.headers = {
            "Accept": "application/json",
            "Content-Type": "application/json",
        }
        self.last_request_time = 0
        
        if self.use_stealth:
            logger.info("Stealth features ENABLED - requests will be spaced out and appear more natural")
        else:
            logger.info("Stealth features DISABLED - requests will be made at regular intervals")

    def _get_random_user_agent(self) -> str:
        """Get a random user agent string"""
        return random.choice(USER_AGENTS)
    
    def _prepare_headers(self) -> Dict[str, str]:
        """Prepare headers with anti-detection features"""
        headers = self.headers.copy()
        
        if self.use_stealth:
            # Rotate user agent
            headers["User-Agent"] = self._get_random_user_agent()
            
            # Add common browser headers
            headers.update({
                "Accept-Language": "en-US,en;q=0.9",
                "DNT": "1",
                "Connection": "keep-alive"
            })
            
            # Sometimes add a referer
            if random.random() < 0.3:
                headers["Referer"] = "https://www.producthunt.com/"
        
        return headers
    
    def _delay_request(self) -> None:
        """Add variable delay between requests to appear human-like"""
        if not self.use_stealth:
            return
            
        # Calculate delay based on time since last request
        now = time.time()
        elapsed = now - self.last_request_time
        
        # Random delay between 1-4 seconds
        delay = random.uniform(1.0, 4.0)
        
        # Only sleep if not enough time has passed naturally
        if elapsed < delay:
            sleep_time = delay - elapsed
            logger.info(f"Waiting {sleep_time:.2f}s before next request")
            time.sleep(sleep_time)
            
        self.last_request_time = time.time()

    def authenticate(self) -> bool:
        """
        Authenticate with the Product Hunt API using client credentials
        
        Returns:
            True if authentication successful, False otherwise
        """
        # Check if we already have a valid token
        if self.access_token and time.time() < self.token_expiry:
            return True

        if not CLIENT_ID or not CLIENT_SECRET:
            logger.error("Missing API credentials. Please set PH_CLIENT_ID and PH_CLIENT_SECRET in .env file")
            return False
            
        auth_url = "https://api.producthunt.com/v2/oauth/token"
        payload = {
            "client_id": CLIENT_ID,
            "client_secret": CLIENT_SECRET,
            "grant_type": "client_credentials",
        }

        try:
            # Apply delay and get headers
            self._delay_request()
            headers = self._prepare_headers()
            
            # Make the request
            response = requests.post(auth_url, json=payload, headers=headers)
            response.raise_for_status()
            
            # Process the response
            data = response.json()
            
            # Check if the response contains the access token
            if "access_token" not in data:
                logger.error(f"Authentication failed: No access token in response: {data}")
                return False
                
            self.access_token = data["access_token"]
            
            # Set expiry - if expires_in is not provided, default to 2 hours (7200 seconds)
            expires_in = data.get("expires_in", 7200)
            self.token_expiry = time.time() + (expires_in * 0.9)
            self.headers["Authorization"] = f"Bearer {self.access_token}"
            
            logger.info("Successfully authenticated with Product Hunt API")
            return True

        except requests.exceptions.RequestException as e:
            logger.error(f"Authentication failed: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error during authentication: {str(e)}")
            return False

    def get_posts_by_date(self, date_str: str) -> List[Dict[str, Any]]:
        """
        Fetch posts from Product Hunt by date
        
        Args:
            date_str: ISO format date string (YYYY-MM-DD)
            
        Returns:
            List of posts data
        """
        # Ensure we have a valid token
        if not self.authenticate():
            logger.error("Authentication failed. Cannot fetch posts.")
            return []

        # Create date range for the query (entire day)
        date_obj = datetime.datetime.fromisoformat(date_str)
        next_day = date_obj + datetime.timedelta(days=1)
        
        logger.info(f"Fetching posts for {date_str}")
        
        # GraphQL query for posts - updated to match current API schema
        query = """
        query getPosts($after: DateTime!, $before: DateTime!) {
          posts(postedAfter: $after, postedBefore: $before, first: 50) {
            edges {
              node {
                id
                name
                tagline
                description
                url
                website
                votesCount
                commentsCount
                createdAt
                topics {
                  edges {
                    node {
                      name
                    }
                  }
                }
                thumbnail {
                  url
                }
                media {
                  url
                  type
                }
                makers {
                  id
                  name
                  username
                  profileImage
                }
              }
            }
          }
        }
        """

        variables = {
            "after": f"{date_str}T00:00:00Z",
            "before": f"{next_day.strftime('%Y-%m-%d')}T00:00:00Z",
        }

        payload = {"query": query, "variables": variables}
        
        # Implement retry logic with exponential backoff
        for attempt in range(MAX_RETRIES):
            try:
                # Apply delay and get headers
                self._delay_request()
                headers = self._prepare_headers()
                
                # Make the request
                response = requests.post(API_URL, json=payload, headers=headers)
                response.raise_for_status()
                data = response.json()
                
                # Check for GraphQL errors
                if "errors" in data:
                    logger.error(f"API returned errors: {data['errors']}")
                    if attempt < MAX_RETRIES - 1:
                        # Calculate backoff delay
                        delay = (RETRY_DELAY * (2 ** attempt)) * random.uniform(0.8, 1.2)
                        logger.info(f"Retrying in {delay:.2f}s (attempt {attempt+1}/{MAX_RETRIES})")
                        time.sleep(delay)
                        continue
                    return []
                
                # Check if data structure is valid
                if not data or "data" not in data or "posts" not in data["data"] or "edges" not in data["data"]["posts"]:
                    logger.error(f"Unexpected API response structure for {date_str}")
                    if attempt < MAX_RETRIES - 1:
                        delay = (RETRY_DELAY * (2 ** attempt)) * random.uniform(0.8, 1.2)
                        logger.info(f"Retrying in {delay:.2f}s (attempt {attempt+1}/{MAX_RETRIES})")
                        time.sleep(delay)
                        continue
                    return []
                
                # Extract posts from response
                posts = [edge["node"] for edge in data["data"]["posts"]["edges"]]
                logger.info(f"Successfully fetched {len(posts)} posts for {date_str}")
                
                # Occasionally simulate a user pausing
                if self.use_stealth and random.random() < 0.15:
                    pause_time = random.uniform(3.0, 8.0)
                    logger.info(f"Taking a short pause for {pause_time:.2f}s")
                    time.sleep(pause_time)
                
                return posts
                
            except requests.exceptions.RequestException as e:
                logger.error(f"Request failed (attempt {attempt+1}/{MAX_RETRIES}): {str(e)}")
                if attempt < MAX_RETRIES - 1:
                    # Calculate backoff delay
                    delay = (RETRY_DELAY * (2 ** attempt)) * random.uniform(0.8, 1.2)
                    logger.info(f"Retrying in {delay:.2f}s")
                    time.sleep(delay)
                else:
                    logger.error(f"Failed to fetch posts for {date_str} after {MAX_RETRIES} attempts")
                    return []

    def process_post_data(self, posts: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Process raw post data into structured format for export"""
        processed_posts = []
        
        for post in posts:
            # Extract topic names
            topics = [
                edge["node"]["name"] 
                for edge in post.get("topics", {}).get("edges", [])
            ]
            
            # Extract maker usernames (updated schema)
            makers = []
            for maker in post.get("makers", []):
                if maker.get("username"):
                    makers.append(maker.get("username"))
            
            # Extract media URLs by type
            media_items = post.get("media", [])
            gallery_images = [
                item["url"] for item in media_items 
                if item.get("type") == "image"
            ]
            videos = [
                item["url"] for item in media_items 
                if item.get("type") == "video"
            ]
            
            # Create structured post data
            processed_post = {
                "Product Name": post.get("name", ""),
                "Tagline": post.get("tagline", ""),
                "Description": post.get("description", ""),
                "Product URL": post.get("url", ""),
                "Website URL": post.get("website", ""),  # Updated from websiteUrl to website
                "Upvotes": post.get("votesCount", 0),
                "Comments Count": post.get("commentsCount", 0),
                "Launch Date": post.get("createdAt", "").split("T")[0] if post.get("createdAt") else "",
                "Topics": ", ".join(topics),
                "Thumbnail Image URL": post.get("thumbnail", {}).get("url", ""),
                "Gallery Image URLs": ", ".join(gallery_images),
                "Demo Video URL": ", ".join(videos),
                "Makers": ", ".join(makers)
            }
            
            processed_posts.append(processed_post)
            
        return processed_posts

    def scrape_recent_days(self, days: int = 3) -> List[Dict[str, Any]]:
        """
        Scrape posts from the past N days
        
        Args:
            days: Number of days to scrape (default: 3)
            
        Returns:
            Combined list of processed posts
        """
        all_posts = []
        today = datetime.datetime.now().date()
        
        # Add some randomization to day order for more natural pattern
        day_order = list(range(days))
        if self.use_stealth:
            random.shuffle(day_order)
        
        for i in day_order:
            date = today - datetime.timedelta(days=i)
            date_str = date.isoformat()
            
            day_label = "Today"
            if i == 1:
                day_label = "Yesterday"
            elif i == 2:
                day_label = "Day before yesterday"
            else:
                day_label = f"{i} days ago"
                
            logger.info(f"Scraping posts for {day_label} ({date_str})...")
            
            # Get posts for this date
            posts = self.get_posts_by_date(date_str)
            
            # Process the posts
            processed_posts = self.process_post_data(posts)
            all_posts.extend(processed_posts)
            
            # Add a delay between days to avoid triggering rate limits
            if i < days - 1 and self.use_stealth:
                delay = random.uniform(2.0, 5.0)
                logger.info(f"Waiting {delay:.2f}s before fetching next day")
                time.sleep(delay)
        
        return all_posts

    def export_to_csv(self, posts: List[Dict[str, Any]], output_file: str) -> bool:
        """
        Export posts data to CSV file
        
        Args:
            posts: List of post data
            output_file: Output file path
            
        Returns:
            True if export successful, False otherwise
        """
        if not posts:
            logger.warning("No data to export")
            return False
            
        try:
            df = pd.DataFrame(posts)
            df.to_csv(output_file, index=False)
            logger.info(f"Exported {len(posts)} products to {output_file}")
            return True
        except Exception as e:
            logger.error(f"Error exporting to CSV: {str(e)}")
            return False


def main():
    """Main function to run the scraper"""
    parser = argparse.ArgumentParser(description="Product Hunt Scraper")
    parser.add_argument(
        "--output", 
        default=DEFAULT_OUTPUT_FILE,
        help=f"Output CSV file (default: {DEFAULT_OUTPUT_FILE})"
    )
    parser.add_argument(
        "--days", 
        type=int, 
        default=3,
        help="Number of days to scrape (default: 3)"
    )
    parser.add_argument(
        "--no-stealth", 
        action="store_true",
        help="Disable stealth features (no delays, no user agent rotation)"
    )
    args = parser.parse_args()
    
    try:
        # Create scraper
        scraper = ProductHuntScraper(use_stealth=not args.no_stealth)
        
        # Scrape data
        posts = scraper.scrape_recent_days(args.days)
        
        # Export data
        if posts:
            if scraper.export_to_csv(posts, args.output):
                logger.info(f"Scraping completed successfully! Data saved to {args.output}")
            else:
                logger.error("Failed to export data")
                return 1
        else:
            logger.warning("No products found during the specified period")
            
    except KeyboardInterrupt:
        logger.info("Scraping interrupted by user")
        return 130
    except Exception as e:
        logger.error(f"Error: {str(e)}", exc_info=True)
        return 1
        
    return 0


if __name__ == "__main__":
    exit(main()) 