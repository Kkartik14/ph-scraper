# Product Hunt Scraper

A Python tool to automatically scrape Product Hunt launches using the GraphQL API with anti-detection features.

## Features

- Date-based scraping of product launches from any specified number of days
- Collects comprehensive product metadata including descriptions, media, and engagement stats
- Outputs structured data to a CSV file
- Stealth mode with randomized delays and user agent rotation to avoid detection
- Robust error handling and retry mechanisms

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your Product Hunt API credentials:
   ```
   PH_CLIENT_ID=your_client_id
   PH_CLIENT_SECRET=your_client_secret
   ```
4. Run the scraper: `python ph_scraper.py`

## Output

The scraper generates a CSV file (`product_hunt_data.csv`) with the following columns:

- Product Name
- Tagline
- Description
- Product URL
- Website URL
- Upvotes
- Comments Count
- Launch Date
- Topics (categories/tags)
- Thumbnail Image URL
- Gallery Image URLs
- Demo Video URL
- Makers (usernames)

## Stealth Features

To avoid triggering rate limits and detection mechanisms, the scraper includes stealth features:

- Variable delays between requests
- User agent rotation
- Exponential backoff when encountering errors
- Randomized request patterns
- Simulated browsing pauses

## Usage

```bash
# Run the scraper with default settings (3 days)
python ph_scraper.py

# Scrape more days
python ph_scraper.py --days 7

# Specify custom output file
python ph_scraper.py --output custom_filename.csv

# Disable stealth features (faster but may hit rate limits)
python ph_scraper.py --no-stealth
```

## Getting Product Hunt API Credentials

1. Go to [Product Hunt Developers](https://api.producthunt.com/v2/docs)
2. Create an account if you don't have one
3. Create a new application
4. Get the Client ID and Client Secret
5. Add them to your `.env` file 