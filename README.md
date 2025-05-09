# Product Hunt Scraper and Analyzer

A Python toolkit to scrape Product Hunt launches using the GraphQL API, analyze trends, and visualize insights using Streamlit.

## Features

### Scraper
- Multiple scraping modes: date-based or top products
- Complete data collection with pagination support (scrapes ALL products)
- Collects comprehensive product metadata including descriptions, media, and engagement stats
- Outputs structured data to a CSV file
- Stealth mode with randomized delays and user agent rotation to avoid detection
- Robust error handling and retry mechanisms
- Timezone handling (UTC or PST) to match Product Hunt's timezone

### Analyzer
- Comprehensive analysis of Product Hunt data
- Topic distribution and trend identification
- Daily launch statistics and patterns
- Top product identification and metrics
- Integration with Groq LLM for advanced trend analysis
- AI and B2B/B2C trend insights
- Exports analysis to various formats (JSON, CSV)

### Visualization (Streamlit Dashboard)
- Interactive data exploration
- Topic distribution charts and treemaps
- Daily trend charts and statistics
- Top product rankings and details
- AI and B2B trend analysis
- Raw data search and filtering

## Setup

1. Clone this repository
2. Install dependencies: `pip install -r requirements.txt`
3. Create a `.env` file with your Product Hunt API credentials and Groq API key:
   ```
   # Product Hunt API Credentials
   PH_CLIENT_ID=your_client_id_here
   PH_CLIENT_SECRET=your_client_secret_here
   
   # Groq API Key for LLM Analysis
   GROQ_API_KEY=your_groq_api_key_here
   ```
4. Run the complete pipeline: `./run_ph_pipeline.sh`

## Components

### ph_scraper.py
The core scraper module that interfaces with Product Hunt's GraphQL API.

```bash
# Basic usage
python ph_scraper.py

# Scrape products from the last 7 days
python ph_scraper.py --days 7

# Scrape top products
python ph_scraper.py --mode top --periods today week month
```

### scrape_last_30_days.py
Script to scrape the last 30 days of Product Hunt data.

```bash
python scrape_last_30_days.py
```

### ph_analyzer.py
Analyzes the scraped data to identify trends, patterns, and insights.

```bash
python ph_analyzer.py
```

### streamlit_app.py
Interactive dashboard for data visualization and exploration.

```bash
streamlit run streamlit_app.py
```

### run_ph_pipeline.sh
Shell script to run the complete pipeline (scraping, analysis, visualization).

```bash
./run_ph_pipeline.sh
```

## Advanced Options

### Scraper Options
```bash
# Specify custom output file
python ph_scraper.py --output custom_filename.csv

# Disable stealth features (faster but may hit rate limits)
python ph_scraper.py --no-stealth

# Use PST timezone (Product Hunt's timezone) instead of UTC
python ph_scraper.py --use-pst

# Set maximum number of products to fetch per day/period
python ph_scraper.py --limit 200
```

### Analyzer Options
The analyzer automatically processes data from `product_hunt_30_days.csv` and saves results to the `analysis/` directory.

### Streamlit Options
```bash
# Run on a different port
streamlit run streamlit_app.py --server.port 8888

# Run in browser-less mode
streamlit run streamlit_app.py --server.headless true
```

## Timezone Handling

Product Hunt operates in Pacific Standard Time (PST). This becomes important when scraping "today's" products:

- By default, the scraper uses UTC time
- When using `--use-pst`, the scraper will use PST timezone for date calculations
- Using PST is recommended for the most accurate results since you might miss today's products if it's still the previous day in PST

## LLM Trend Analysis

The analyzer integrates with Groq LLM to provide advanced trend analysis:

- Identifies trending categories and emerging product types
- Analyzes B2B vs B2C product trends
- Highlights AI-related trends and use cases
- Identifies patterns in successful products

To use this feature, you need to provide a valid Groq API key in the `.env` file:
```
GROQ_API_KEY=your_groq_api_key_here
```

## Getting Product Hunt API Credentials

1. Go to [Product Hunt Developers](https://api.producthunt.com/v2/docs)
2. Create an account if you don't have one
3. Create a new application
4. Get the Client ID and Client Secret
5. Add them to your `.env` file 