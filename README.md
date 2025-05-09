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
- **Data Collection**: Configure and run the scraper directly from the UI
- **Raw CSV Data View**: Explore, filter, and download the raw data
- Interactive data exploration
- Topic distribution charts and treemaps
- Daily trend charts and statistics
- Top product rankings and details
- AI and B2B trend analysis

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
4. Run the application: `./run_ph_pipeline.sh` or directly with `streamlit run streamlit_app.py`

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

### ph_analyzer.py
Analyzes the scraped data to identify trends, patterns, and insights.

```bash
python ph_analyzer.py
```

### streamlit_app.py
Interactive dashboard for data collection, visualization, and exploration.

```bash
streamlit run streamlit_app.py
```

### run_ph_pipeline.sh
Shell script to start the Streamlit app.

```bash
./run_ph_pipeline.sh
```

## Using the Application

### Data Collection
1. Launch the application and navigate to the "Data Collection" view
2. Configure the scraping parameters:
   - Number of days to scrape
   - Timezone settings
   - Stealth mode options
   - Output filename
3. Click "Start Scraping" to begin data collection
4. After collection completes, you can run analysis directly from the same page

### Raw CSV Data
- View, filter, and sort the collected raw data
- Search through all fields
- Download filtered results as CSV

### Analysis Views
After running the analyzer, explore different views:
- Overview (key metrics and statistics)
- Topic Analysis (distribution and trends)
- Daily Trends (charts and patterns)
- Top Products (rankings and details)
- AI & B2B Trends (LLM-powered insights)

## Advanced Options

### Scraper Options
All scraper options are configurable from the Streamlit UI:
- Number of days to scrape (1-90)
- PST timezone toggle 
- Stealth mode toggle
- Maximum products per day
- Custom output filename

### Analyzer Options
The analyzer is integrated directly into the Streamlit app and will process any CSV file you select.

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
- When enabling "Use PST timezone" in the UI, the scraper will use PST timezone for date calculations
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