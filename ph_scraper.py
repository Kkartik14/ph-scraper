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
from typing import Dict, List, Any, Optional, Union, Tuple
import pytz

import requests
import pandas as pd
from dotenv import load_dotenv

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", "ph_scraper.log")),
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

    def get_posts_by_date(self, date_str: str, limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch posts from Product Hunt by date
        
        Args:
            date_str: ISO format date string (YYYY-MM-DD)
            limit: Maximum number of posts to fetch
            
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
        
        logger.info(f"Fetching posts for {date_str} (from {date_str}T00:00:00Z to {next_day.strftime('%Y-%m-%d')}T00:00:00Z)")
        
        # GraphQL query for posts - updated to match current API schema and handle pagination
        query = """
        query getPosts($after: DateTime!, $before: DateTime!, $first: Int!, $cursor: String) {
          posts(postedAfter: $after, postedBefore: $before, first: $first, after: $cursor) {
            pageInfo {
              endCursor
              hasNextPage
            }
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
            "first": 50  # Max number of items per page
        }

        all_posts = []
        has_next_page = True
        cursor = None
        
        # Implement pagination to get all posts
        while has_next_page and (len(all_posts) < limit or limit <= 0):
            if cursor:
                variables["cursor"] = cursor
                
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
                        return all_posts
                    
                    # Check if data structure is valid
                    if not data or "data" not in data or "posts" not in data["data"] or "edges" not in data["data"]["posts"]:
                        logger.error(f"Unexpected API response structure for {date_str}")
                        if attempt < MAX_RETRIES - 1:
                            delay = (RETRY_DELAY * (2 ** attempt)) * random.uniform(0.8, 1.2)
                            logger.info(f"Retrying in {delay:.2f}s (attempt {attempt+1}/{MAX_RETRIES})")
                            time.sleep(delay)
                            continue
                        return all_posts
                    
                    # Extract pagination info
                    page_info = data["data"]["posts"].get("pageInfo", {})
                    has_next_page = page_info.get("hasNextPage", False)
                    cursor = page_info.get("endCursor", None)
                    
                    # Extract posts from response
                    posts = [edge["node"] for edge in data["data"]["posts"]["edges"]]
                    all_posts.extend(posts)
                    
                    logger.info(f"Fetched {len(posts)} posts (total: {len(all_posts)})")
                    
                    # Occasionally simulate a user pausing
                    if self.use_stealth and random.random() < 0.15:
                        pause_time = random.uniform(3.0, 8.0)
                        logger.info(f"Taking a short pause for {pause_time:.2f}s")
                        time.sleep(pause_time)
                    
                    # Break the retry loop since we got a successful response
                    break
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request failed (attempt {attempt+1}/{MAX_RETRIES}): {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        # Calculate backoff delay
                        delay = (RETRY_DELAY * (2 ** attempt)) * random.uniform(0.8, 1.2)
                        logger.info(f"Retrying in {delay:.2f}s")
                        time.sleep(delay)
                    else:
                        logger.error(f"Failed to fetch posts for {date_str} after {MAX_RETRIES} attempts")
                        return all_posts
            
            # Check if we've reached the limit
            if 0 < limit <= len(all_posts):
                logger.info(f"Reached post limit of {limit}")
                break
                
            # If we have next page, we need to continue pagination
            if has_next_page:
                logger.info(f"Fetching next page with cursor: {cursor}")
            else:
                logger.info(f"No more pages to fetch")
        
        logger.info(f"Successfully fetched {len(all_posts)} posts for {date_str}")
        return all_posts

    def get_top_posts(self, time_period: str = "today", limit: int = 50) -> List[Dict[str, Any]]:
        """
        Fetch top posts from Product Hunt based on time period
        
        Args:
            time_period: Time period to fetch posts for (today, yesterday, week, month)
            limit: Maximum number of posts to fetch
            
        Returns:
            List of posts data
        """
        # Ensure we have a valid token
        if not self.authenticate():
            logger.error("Authentication failed. Cannot fetch posts.")
            return []
            
        # Define the query for top posts based on time period
        # For top posts, we'll use the appropriate filter and sort by votes
        query = """
        query getTopPosts($first: Int!, $cursor: String) {
          posts(order: VOTES, first: $first, after: $cursor) {
            pageInfo {
              endCursor
              hasNextPage
            }
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
        
        # For today/yesterday, use date filtering instead
        if time_period.lower() in ["today", "yesterday"]:
            # Get today's date
            if time_period.lower() == "today":
                # Get today's date in PST (Product Hunt's timezone)
                now_utc = datetime.datetime.now(pytz.UTC)
                now_pst = now_utc.astimezone(pytz.timezone('US/Pacific'))
                date_str = now_pst.date().isoformat()
                logger.info(f"Fetching today's top posts for PST date: {date_str}")
                return self.get_posts_by_date(date_str, limit=limit)
            else:  # yesterday
                # Get yesterday's date in PST
                now_utc = datetime.datetime.now(pytz.UTC)
                now_pst = now_utc.astimezone(pytz.timezone('US/Pacific'))
                yesterday = now_pst.date() - datetime.timedelta(days=1)
                date_str = yesterday.isoformat()
                logger.info(f"Fetching yesterday's top posts for PST date: {date_str}")
                return self.get_posts_by_date(date_str, limit=limit)
                
        # For week/month/all_time, we need to modify the query to filter by created date
        if time_period.lower() == "week":
            # Get posts from the last 7 days
            now_utc = datetime.datetime.now(pytz.UTC)
            now_pst = now_utc.astimezone(pytz.timezone('US/Pacific'))
            week_ago = now_pst.date() - datetime.timedelta(days=7)
            
            query = """
            query getWeekPosts($after: DateTime!, $first: Int!, $cursor: String) {
              posts(postedAfter: $after, order: VOTES, first: $first, after: $cursor) {
                pageInfo {
                  endCursor
                  hasNextPage
                }
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
                "after": f"{week_ago.isoformat()}T00:00:00Z",
                "first": 50  # Max number of items per page
            }
            
            logger.info(f"Fetching top posts for the last week (after {week_ago.isoformat()})")
            
        elif time_period.lower() == "month":
            # Get posts from the last 30 days
            now_utc = datetime.datetime.now(pytz.UTC)
            now_pst = now_utc.astimezone(pytz.timezone('US/Pacific'))
            month_ago = now_pst.date() - datetime.timedelta(days=30)
            
            query = """
            query getMonthPosts($after: DateTime!, $first: Int!, $cursor: String) {
              posts(postedAfter: $after, order: VOTES, first: $first, after: $cursor) {
                pageInfo {
                  endCursor
                  hasNextPage
                }
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
                "after": f"{month_ago.isoformat()}T00:00:00Z",
                "first": 50  # Max number of items per page
            }
            
            logger.info(f"Fetching top posts for the last month (after {month_ago.isoformat()})")
            
        else:  # all_time or any other value
            # For all-time, just sort by votes without date filtering
            variables = {
                "first": 50  # Max number of items per page
            }
            
            logger.info(f"Fetching all-time top posts")
        
        all_posts = []
        has_next_page = True
        cursor = None
        
        # Implement pagination to get all posts
        while has_next_page and (len(all_posts) < limit or limit <= 0):
            if cursor:
                variables["cursor"] = cursor
                
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
                        return all_posts
                        
                    # Check if data structure is valid
                    if not data or "data" not in data or "posts" not in data["data"] or "edges" not in data["data"]["posts"]:
                        logger.error(f"Unexpected API response structure for top posts")
                        if attempt < MAX_RETRIES - 1:
                            delay = (RETRY_DELAY * (2 ** attempt)) * random.uniform(0.8, 1.2)
                            logger.info(f"Retrying in {delay:.2f}s (attempt {attempt+1}/{MAX_RETRIES})")
                            time.sleep(delay)
                            continue
                        return all_posts
                    
                    # Extract pagination info
                    page_info = data["data"]["posts"].get("pageInfo", {})
                    has_next_page = page_info.get("hasNextPage", False)
                    cursor = page_info.get("endCursor", None)
                    
                    # Extract posts from response
                    posts = [edge["node"] for edge in data["data"]["posts"]["edges"]]
                    all_posts.extend(posts)
                    
                    logger.info(f"Fetched {len(posts)} top posts (total: {len(all_posts)})")
                    
                    # Occasionally simulate a user pausing
                    if self.use_stealth and random.random() < 0.15:
                        pause_time = random.uniform(3.0, 8.0)
                        logger.info(f"Taking a short pause for {pause_time:.2f}s")
                        time.sleep(pause_time)
                    
                    # Break the retry loop since we got a successful response
                    break
                    
                except requests.exceptions.RequestException as e:
                    logger.error(f"Request failed (attempt {attempt+1}/{MAX_RETRIES}): {str(e)}")
                    if attempt < MAX_RETRIES - 1:
                        # Calculate backoff delay
                        delay = (RETRY_DELAY * (2 ** attempt)) * random.uniform(0.8, 1.2)
                        logger.info(f"Retrying in {delay:.2f}s")
                        time.sleep(delay)
                    else:
                        logger.error(f"Failed to fetch top posts after {MAX_RETRIES} attempts")
                        return all_posts
            
            # Check if we've reached the limit
            if 0 < limit <= len(all_posts):
                logger.info(f"Reached post limit of {limit}")
                break
                
            # If we have next page, we need to continue pagination
            if has_next_page and cursor:
                logger.info(f"Fetching next page with cursor: {cursor}")
            else:
                logger.info(f"No more pages to fetch")
        
        logger.info(f"Successfully fetched {len(all_posts)} top posts for {time_period}")
        return all_posts

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

    def scrape_recent_days(self, days: int = 3, use_pst: bool = False, limit: int = 100) -> List[Dict[str, Any]]:
        """
        Scrape posts from the past N days
        
        Args:
            days: Number of days to scrape (default: 3)
            use_pst: Whether to use PST timezone for date calculations
            limit: Maximum number of posts to fetch per day
            
        Returns:
            Combined list of processed posts
        """
        all_posts = []
        
        # Calculate the start date based on the timezone preference
        if use_pst:
            # Use PST (Product Hunt's timezone)
            now_utc = datetime.datetime.now(pytz.UTC)
            now_pst = now_utc.astimezone(pytz.timezone('US/Pacific'))
            today = now_pst.date()
            logger.info(f"Using PST date: {today.isoformat()} for calculations")
        else:
            # Use UTC
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
            posts = self.get_posts_by_date(date_str, limit=limit)
            
            # Process the posts
            processed_posts = self.process_post_data(posts)
            all_posts.extend(processed_posts)
            
            # Add a delay between days to avoid triggering rate limits
            if i < days - 1 and self.use_stealth:
                delay = random.uniform(2.0, 5.0)
                logger.info(f"Waiting {delay:.2f}s before fetching next day")
                time.sleep(delay)
        
        return all_posts

    def scrape_top_posts(self, time_periods: List[str] = ["today"], limit: int = 100) -> List[Dict[str, Any]]:
        """
        Scrape top posts based on different time periods
        
        Args:
            time_periods: List of time periods to fetch (today, yesterday, week, month, all_time)
            limit: Maximum number of posts to fetch per time period
            
        Returns:
            Combined list of processed posts
        """
        all_posts = []
        
        for period in time_periods:
            logger.info(f"Scraping top posts for {period}...")
            
            # Get top posts for this time period
            posts = self.get_top_posts(period, limit=limit)
            
            # Process the posts
            processed_posts = self.process_post_data(posts)
            all_posts.extend(processed_posts)
            
            # Add a delay between time periods to avoid triggering rate limits
            if period != time_periods[-1] and self.use_stealth:
                delay = random.uniform(2.0, 5.0)
                logger.info(f"Waiting {delay:.2f}s before fetching next time period")
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
    parser.add_argument(
        "--use-pst",
        action="store_true",
        help="Use PST timezone (Product Hunt's timezone) instead of UTC"
    )
    parser.add_argument(
        "--mode",
        choices=["date", "top"],
        default="date",
        help="Scraping mode: date-based or top posts"
    )
    parser.add_argument(
        "--periods",
        nargs="+",
        default=["today"],
        choices=["today", "yesterday", "week", "month", "all_time"],
        help="Time periods for top posts mode (can specify multiple)"
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=100,
        help="Maximum number of posts to fetch per day/period"
    )
    args = parser.parse_args()
    
    try:
        # Create scraper
        scraper = ProductHuntScraper(use_stealth=not args.no_stealth)
        
        # Get timezone info if requested
        if args.use_pst:
            now_utc = datetime.datetime.now(pytz.UTC)
            now_pst = now_utc.astimezone(pytz.timezone('US/Pacific'))
            logger.info(f"Current time (UTC): {now_utc}")
            logger.info(f"Current time (PST/Product Hunt timezone): {now_pst}")
            logger.info(f"Using PST timezone for date calculations")
        
        # Scrape data based on mode
        if args.mode == "date":
            logger.info(f"Running in date-based mode for {args.days} days with limit {args.limit} posts per day")
            posts = scraper.scrape_recent_days(args.days, use_pst=args.use_pst, limit=args.limit)
        else:  # top mode
            logger.info(f"Running in top posts mode for periods: {', '.join(args.periods)} with limit {args.limit} posts per period")
            posts = scraper.scrape_top_posts(args.periods, limit=args.limit)
        
        # Export data
        if posts:
            if scraper.export_to_csv(posts, args.output):
                logger.info(f"Scraping completed successfully! Data saved to {args.output}")
                logger.info(f"Total posts scraped: {len(posts)}")
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