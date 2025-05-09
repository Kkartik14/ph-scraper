#!/usr/bin/env python3
"""
Streamlit app for Product Hunt trends visualization
"""

import os
import json
import pandas as pd
import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
from typing import Dict, List, Any
import sys
import time
from ph_scraper import ProductHuntScraper
from ph_analyzer import ProductHuntAnalyzer
import logging

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("streamlit_app.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("StreamlitApp")

# Set page configuration
st.set_page_config(
    page_title="Product Hunt Trends Analyzer",
    page_icon="🚀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Apply custom styling
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        color: #FF6154;
        font-weight: 800;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #46484c;
        font-weight: 600;
    }
    .highlight {
        color: #FF6154;
        font-weight: 600;
    }
    .card {
        padding: 1.5rem;
        border-radius: 0.5rem;
        background-color: #f8f9fa;
        box-shadow: 0 0.125rem 0.25rem rgba(0, 0, 0, 0.075);
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Default CSV filename
DEFAULT_CSV_FILENAME = "product_hunt_data.csv"

def load_analysis_data(base_dir: str = "analysis") -> Dict[str, Any]:
    """
    Load analysis data from files
    
    Args:
        base_dir: Directory containing analysis files
        
    Returns:
        Dictionary with loaded analysis data
    """
    data = {}
    
    # Check if directory exists
    if not os.path.exists(base_dir):
        st.error(f"Analysis directory '{base_dir}' not found. Please run the analyzer first.")
        return data
    
    # Load basic stats
    basic_stats_path = os.path.join(base_dir, "basic_stats.json")
    if os.path.exists(basic_stats_path):
        with open(basic_stats_path) as f:
            data["basic_stats"] = json.load(f)
    
    # Load topic analysis
    topic_path = os.path.join(base_dir, "topic_analysis.json")
    if os.path.exists(topic_path):
        with open(topic_path) as f:
            data["topics"] = json.load(f)
    
    # Load daily trends
    daily_path = os.path.join(base_dir, "daily_trends.csv")
    if os.path.exists(daily_path):
        data["daily"] = pd.read_csv(daily_path)
        
        # Check for date column and convert to datetime
        date_col = None
        if "date" in data["daily"].columns:
            date_col = "date"
        elif "index" in data["daily"].columns:
            date_col = "index"
            # Rename index to date for consistency
            data["daily"] = data["daily"].rename(columns={"index": "date"})
            
        # Convert date column to datetime if found
        if date_col:
            data["daily"][date_col] = pd.to_datetime(data["daily"][date_col])
    
    # Load top products
    top_path = os.path.join(base_dir, "top_products.csv")
    if os.path.exists(top_path):
        data["top_products"] = pd.read_csv(top_path)
        # Convert date column to datetime
        if "Launch Date" in data["top_products"].columns:
            data["top_products"]["Launch Date"] = pd.to_datetime(data["top_products"]["Launch Date"])
    
    # Load LLM analysis
    llm_path = os.path.join(base_dir, "llm_trend_analysis.json")
    if os.path.exists(llm_path):
        with open(llm_path) as f:
            data["llm_analysis"] = json.load(f)
    
    return data

def load_raw_data(file_path: str = DEFAULT_CSV_FILENAME) -> pd.DataFrame:
    """
    Load raw Product Hunt data from CSV
    
    Args:
        file_path: Path to CSV file
        
    Returns:
        DataFrame with product data
    """
    if not os.path.exists(file_path):
        return pd.DataFrame()
    
    df = pd.read_csv(file_path)
    
    # Convert Launch Date to datetime
    if "Launch Date" in df.columns:
        df["Launch Date"] = pd.to_datetime(df["Launch Date"])
    
    return df

def display_header():
    """Display the app header and introduction"""
    st.markdown('<p class="main-header">Product Hunt Trends Analyzer 🚀</p>', unsafe_allow_html=True)
    st.markdown("""
    This dashboard allows you to scrape Product Hunt data, visualize trends and patterns,
    identify popular categories, emerging trends, and analyze successful product characteristics.
    """)
    st.markdown("---")

def display_sidebar_controls():
    """Display sidebar controls and filters"""
    st.sidebar.header("📊 Dashboard Controls")
    
    view_options = [
        "Data Collection",
        "Raw CSV Data",
        "Overview",
        "Topic Analysis",
        "Daily Trends",
        "Top Products",
        "AI & B2B Trends (LLM Analysis)"
    ]
    
    selected_view = st.sidebar.radio("Select View", view_options)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Data Info")
    
    # Get CSV file info if it exists
    if os.path.exists(DEFAULT_CSV_FILENAME):
        file_stats = os.stat(DEFAULT_CSV_FILENAME)
        file_size = file_stats.st_size / 1024  # Convert to KB
        modified_time = datetime.fromtimestamp(file_stats.st_mtime)
        
        st.sidebar.markdown(f"**Data file:** {DEFAULT_CSV_FILENAME}")
        st.sidebar.markdown(f"**Size:** {file_size:.2f} KB")
        st.sidebar.markdown(f"**Last updated:** {modified_time.strftime('%Y-%m-%d %H:%M')}")
        
        # Try to get row count
        try:
            df = pd.read_csv(DEFAULT_CSV_FILENAME)
            st.sidebar.markdown(f"**Products:** {len(df)} items")
        except:
            pass
    else:
        st.sidebar.warning("No data file found. Please collect data first.")
    
    st.sidebar.markdown("---")
    
    return selected_view

def run_scraper(days: int, use_pst: bool, output_file: str, stealth: bool, max_per_day: int):
    """Run the Product Hunt scraper"""
    with st.spinner(f"Scraping Product Hunt data for the last {days} days..."):
        # Create progress bar
        progress_bar = st.progress(0)
        
        # Initialize scraper
        scraper = ProductHuntScraper(use_stealth=stealth)
        
        # Scrape data
        posts = scraper.scrape_recent_days(days=days, use_pst=use_pst, limit=max_per_day)
        
        # Update progress bar to 75%
        progress_bar.progress(75)
        
        # Export to CSV
        success = False
        if posts:
            success = scraper.export_to_csv(posts, output_file)
            if success:
                st.success(f"Successfully scraped {len(posts)} products over {days} days. Data saved to {output_file}.")
            else:
                st.error("Failed to export data to CSV.")
        else:
            st.warning("No data was retrieved. Please check your API credentials.")
        
        # Complete progress bar
        progress_bar.progress(100)
        
        return success

def run_analyzer(input_file: str):
    """Run the Product Hunt analyzer"""
    with st.spinner("Analyzing Product Hunt data..."):
        # Create progress bar
        progress_bar = st.progress(0)
        
        # Ensure the analysis directory exists
        os.makedirs("analysis", exist_ok=True)
        
        # Initialize analyzer
        analyzer = ProductHuntAnalyzer(data_file=input_file)
        
        # Load data
        if not analyzer.load_data():
            st.error("Failed to load data from CSV.")
            return False
        
        progress_bar.progress(25)
        
        # Run analysis
        analyzer.analyze_basic_stats()
        progress_bar.progress(40)
        
        analyzer.analyze_topics()
        progress_bar.progress(55)
        
        analyzer.analyze_daily_trends()
        progress_bar.progress(70)
        
        analyzer.get_top_products()
        progress_bar.progress(85)
        
        # Try LLM analysis if possible
        if analyzer.groq_client is None:
            st.info("Skipping LLM analysis since GROQ_API_KEY is not configured. All other analyses will still work.")
        else:
            try:
                analyzer.analyze_with_llm()
            except Exception as e:
                st.warning(f"LLM analysis failed: {str(e)}. Make sure your GROQ_API_KEY is set correctly.")
        
        progress_bar.progress(95)
        
        # Save analysis
        success = analyzer.save_analysis()
        
        progress_bar.progress(100)
        
        if success:
            st.success("Analysis completed successfully!")
        else:
            st.error("Failed to save analysis results.")
        
        return success

def display_data_collection():
    """Display the data collection interface"""
    st.markdown('<p class="sub-header">Data Collection</p>', unsafe_allow_html=True)
    
    st.write("Collect data from Product Hunt by specifying how many days to scrape.")
    
    # Collection parameters
    with st.form("scraper_form"):
        days = st.slider("Number of days to scrape", min_value=1, max_value=90, value=30, help="Number of days to go back from today")
        
        col1, col2 = st.columns(2)
        
        with col1:
            use_pst = st.checkbox("Use PST timezone (Product Hunt's timezone)", value=True, 
                                 help="Enable this to use PST timezone for date calculations")
            stealth = st.checkbox("Use stealth mode", value=True, 
                                 help="Enable randomized delays and user agent rotation to avoid detection")
        
        with col2:
            max_per_day = st.number_input("Max products per day (0 = unlimited)", min_value=0, value=0, 
                                         help="Limit the number of products to fetch per day. 0 means no limit.")
            output_file = st.text_input("Output filename", value=DEFAULT_CSV_FILENAME, 
                                       help="Name of the CSV file to save the data to")
        
        submit_button = st.form_submit_button("Start Scraping")
        
        if submit_button:
            # Check file existence and ask for confirmation if it exists
            if os.path.exists(output_file):
                st.warning(f"File {output_file} already exists.")
                col1, col2 = st.columns(2)
                with col1:
                    if st.button("Overwrite Existing File"):
                        run_scraper(days, use_pst, output_file, stealth, max_per_day)
                with col2:
                    if st.button("Cancel"):
                        st.info("Scraping cancelled. Please choose a different filename.")
            else:
                run_scraper(days, use_pst, output_file, stealth, max_per_day)
    
    # Analysis section
    st.markdown("---")
    st.markdown("### 📊 Run Analysis")
    st.write("After collecting the data, you can run the analyzer to generate insights.")
    
    csv_files = [f for f in os.listdir() if f.endswith('.csv')]
    
    if not csv_files:
        st.warning("No CSV files found. Please scrape data first.")
    else:
        with st.form("analyzer_form"):
            input_file = st.selectbox("Select CSV file to analyze", csv_files, 
                                     index=csv_files.index(DEFAULT_CSV_FILENAME) if DEFAULT_CSV_FILENAME in csv_files else 0)
            
            analyze_button = st.form_submit_button("Run Analysis")
            
            if analyze_button:
                run_analyzer(input_file)

def display_raw_csv_data(csv_file: str = DEFAULT_CSV_FILENAME):
    """Display the raw CSV data"""
    st.markdown('<p class="sub-header">Raw CSV Data</p>', unsafe_allow_html=True)
    
    # List available CSV files
    csv_files = [f for f in os.listdir() if f.endswith('.csv')]
    
    if not csv_files:
        st.warning("No CSV files found. Please collect data first.")
        return
    
    # Select file
    selected_file = st.selectbox("Select CSV file to view", csv_files,
                               index=csv_files.index(csv_file) if csv_file in csv_files else 0)
    
    # Load and display data
    if os.path.exists(selected_file):
        df = pd.read_csv(selected_file)
        
        # File stats
        st.markdown("### File Information")
        file_stats = os.stat(selected_file)
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Products", len(df))
        
        with col2:
            st.metric("File Size", f"{file_stats.st_size / 1024:.2f} KB")
        
        with col3:
            modified_time = datetime.fromtimestamp(file_stats.st_mtime)
            st.metric("Last Modified", modified_time.strftime("%Y-%m-%d"))
        
        # Search and filter options
        st.markdown("### Search and Filter")
        
        search_term = st.text_input("Search in all text fields", "")
        
        # Filter dataframe based on search term
        if search_term:
            filtered_df = df[df.astype(str).apply(lambda row: any(search_term.lower() in str(val).lower() for val in row), axis=1)]
        else:
            filtered_df = df
        
        # Sort options
        sort_col = st.selectbox("Sort by", df.columns.tolist(), 
                               index=df.columns.get_loc("Upvotes") if "Upvotes" in df.columns else 0)
        sort_ascending = st.checkbox("Ascending order", value=False)
        
        # Apply sorting
        if sort_col in filtered_df.columns:
            filtered_df = filtered_df.sort_values(by=sort_col, ascending=sort_ascending)
        
        # Display data
        st.markdown(f"### Data Preview ({len(filtered_df)} products)")
        st.dataframe(filtered_df)
        
        # Download options
        st.download_button(
            label="Download Filtered Data as CSV",
            data=filtered_df.to_csv(index=False).encode('utf-8'),
            file_name=f"filtered_{selected_file}",
            mime="text/csv"
        )
    else:
        st.error(f"File {selected_file} not found.")

def display_overview(data: Dict[str, Any]):
    """Display overview with key metrics and statistics"""
    st.markdown('<p class="sub-header">Overview</p>', unsafe_allow_html=True)
    
    if "basic_stats" not in data:
        st.warning("Basic statistics not available. Please run the analyzer.")
        return
    
    stats = data["basic_stats"]
    
    # Create metrics row
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Total Products", stats.get("total_products", "N/A"))
    
    with col2:
        st.metric("Avg. Upvotes", stats.get("upvotes", {}).get("average", "N/A"))
    
    with col3:
        st.metric("Max Upvotes", stats.get("upvotes", {}).get("max", "N/A"))
    
    with col4:
        date_range = stats.get("date_range", {})
        days = date_range.get("days", "N/A")
        st.metric("Days Analyzed", days)
    
    # Most popular product
    st.markdown("### 🏆 Most Popular Product")
    st.markdown(f"**{stats.get('upvotes', {}).get('max_product', 'N/A')}** with {stats.get('upvotes', {}).get('max', 'N/A')} upvotes")
    
    # Date range info
    st.markdown("### 📅 Date Range")
    date_range = stats.get("date_range", {})
    st.markdown(f"From **{date_range.get('start', 'N/A')}** to **{date_range.get('end', 'N/A')}**")
    
    # Display top topics if available
    if "topics" in data:
        st.markdown("### 🔝 Top 10 Topics")
        
        topics = data["topics"]
        top_topics = dict(list(topics.items())[:10])
        
        # Create horizontal bar chart
        fig = px.bar(
            x=list(top_topics.values()),
            y=list(top_topics.keys()),
            orientation='h',
            labels={'x': 'Number of Products', 'y': 'Topic'},
            title='Top 10 Topics by Frequency',
            color=list(top_topics.values()),
            color_continuous_scale=px.colors.sequential.Reds
        )
        fig.update_layout(height=500)
        st.plotly_chart(fig, use_container_width=True)

def display_topic_analysis(data: Dict[str, Any]):
    """Display detailed topic analysis"""
    st.markdown('<p class="sub-header">Topic Analysis</p>', unsafe_allow_html=True)
    
    if "topics" not in data:
        st.warning("Topic analysis not available. Please run the analyzer.")
        return
    
    topics = data["topics"]
    
    # Create topic distribution chart
    st.markdown("### Topic Distribution")
    
    # Take top 20 topics for visualization
    top_topics = dict(list(topics.items())[:20])
    
    fig = px.bar(
        x=list(top_topics.keys()),
        y=list(top_topics.values()),
        labels={'x': 'Topic', 'y': 'Number of Products'},
        title='Top 20 Topics by Frequency',
        color=list(top_topics.values()),
        color_continuous_scale=px.colors.sequential.Reds
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)
    
    # Create topic heatmap/treemap
    st.markdown("### Topic Importance Map")
    
    fig = px.treemap(
        names=list(top_topics.keys()),
        values=list(top_topics.values()),
        title='Topic Importance Treemap',
        color=list(top_topics.values()),
        color_continuous_scale=px.colors.sequential.Reds
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Add table with all topics
    st.markdown("### All Topics")
    
    # Convert to DataFrame for display
    topics_df = pd.DataFrame({
        "Topic": list(topics.keys()),
        "Count": list(topics.values())
    })
    
    st.dataframe(topics_df, height=400, use_container_width=True)

def display_daily_trends(data: Dict[str, Any]):
    """Display daily trends analysis"""
    st.markdown('<p class="sub-header">Daily Trends</p>', unsafe_allow_html=True)
    
    if "daily" not in data:
        st.warning("Daily trends data not available. Please run the analyzer.")
        return
    
    daily_data = data["daily"]
    
    # Determine which date column is available
    date_column = None
    if "date" in daily_data.columns:
        date_column = "date"
    elif "Launch Date" in daily_data.columns:
        date_column = "Launch Date"
    else:
        # Try to find a date column by checking data types
        for col in daily_data.columns:
            if pd.api.types.is_datetime64_any_dtype(daily_data[col]):
                date_column = col
                break
    
    if date_column is None:
        st.error("No date column found in the daily trends data.")
        st.dataframe(daily_data)  # Show the data for debugging
        return
    
    # Create daily products count chart
    st.markdown("### Daily Product Launch Count")
    
    fig = px.line(
        daily_data,
        x=date_column,
        y="products_count",
        labels={date_column: "Date", "products_count": "Number of Products"},
        title="Daily Product Launches",
        markers=True
    )
    st.plotly_chart(fig, use_container_width=True)
    
    # Create daily upvotes chart
    st.markdown("### Daily Upvote Statistics")
    
    # Create multiple metrics in the same chart
    fig = go.Figure()
    
    # Add total upvotes line
    fig.add_trace(go.Scatter(
        x=daily_data[date_column],
        y=daily_data["total_upvotes"],
        mode="lines+markers",
        name="Total Upvotes",
        line=dict(color="#FF6154", width=3)
    ))
    
    # Add average upvotes line
    fig.add_trace(go.Scatter(
        x=daily_data[date_column],
        y=daily_data["avg_upvotes"],
        mode="lines+markers",
        name="Avg Upvotes per Product",
        line=dict(color="#5A85FF", width=2, dash="dash")
    ))
    
    fig.update_layout(
        title="Daily Upvote Trends",
        xaxis_title="Date",
        yaxis_title="Upvotes",
        legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=1
        )
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Show daily details in a table
    st.markdown("### Daily Metrics")
    st.dataframe(daily_data, height=400, use_container_width=True)

def display_top_products(data: Dict[str, Any]):
    """Display top products analysis"""
    st.markdown('<p class="sub-header">Top Products</p>', unsafe_allow_html=True)
    
    if "top_products" not in data:
        st.warning("Top products data not available. Please run the analyzer.")
        return
    
    top_products = data["top_products"]
    
    # Create top products chart
    st.markdown("### Top 10 Products by Upvotes")
    
    # Take top 10 for visualization
    top_10 = top_products.head(10)
    
    fig = px.bar(
        top_10,
        y="Product Name",
        x="Upvotes",
        orientation='h',
        color="Upvotes",
        color_continuous_scale=px.colors.sequential.Reds,
        hover_data=["Tagline", "Comments Count", "Launch Date"]
    )
    
    fig.update_layout(
        title="Top 10 Products by Upvotes",
        xaxis_title="Upvotes",
        yaxis_title="Product"
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display interactive table with top products
    st.markdown("### Top Products Details")
    
    # Format dates for display
    top_products["Launch Date"] = top_products["Launch Date"].dt.strftime("%Y-%m-%d")
    
    # Add clickable links
    top_products["Website"] = top_products["Website URL"].apply(
        lambda x: f'<a href="{x}" target="_blank">🔗 Visit</a>' if pd.notnull(x) else ""
    )
    
    # Display table with selected columns
    display_cols = ["Product Name", "Tagline", "Launch Date", "Upvotes", "Comments Count", "Topics", "Website"]
    st.write(top_products[display_cols].to_html(escape=False, index=False), unsafe_allow_html=True)

def display_llm_analysis(data: Dict[str, Any]):
    """Display LLM trend analysis for AI and B2B trends"""
    st.markdown('<p class="sub-header">AI & B2B Trends (LLM Analysis)</p>', unsafe_allow_html=True)
    
    if "llm_analysis" not in data:
        st.warning("LLM analysis not available. Please run the analyzer with GROQ_API_KEY configured.")
        return
    
    analysis = data["llm_analysis"]
    
    # Check if we have structured analysis or raw text
    if "raw_analysis" in analysis:
        st.markdown("### Trend Analysis")
        st.write(analysis["raw_analysis"])
        return
    
    # Display trending categories
    if "trending_categories" in analysis:
        st.markdown("### 🔥 Top Trending Categories")
        st.markdown(analysis["trending_categories"])
    
    # Display emerging categories
    if "emerging_categories" in analysis:
        st.markdown("### 📈 Emerging Categories")
        st.markdown(analysis["emerging_categories"])
    
    # Display product patterns
    if "product_patterns" in analysis:
        st.markdown("### 🔍 Product Success Patterns")
        st.markdown(analysis["product_patterns"])
    
    # Display B2B trends
    if "b2b_trends" in analysis:
        st.markdown("### 🏢 B2B Trends")
        st.markdown(analysis["b2b_trends"])
    
    # Display B2C trends
    if "b2c_trends" in analysis:
        st.markdown("### 👤 B2C Trends")
        st.markdown(analysis["b2c_trends"])
    
    # Display AI trends
    if "ai_trends" in analysis:
        st.markdown("### 🤖 AI Trends")
        st.markdown(analysis["ai_trends"])

def main():
    """Main function to run the Streamlit app"""
    # Display header
    display_header()
    
    # Display sidebar and get selected view
    selected_view = display_sidebar_controls()
    
    # Load analysis data
    analysis_data = {}
    if selected_view not in ["Data Collection", "Raw CSV Data"]:
        analysis_data = load_analysis_data()
    
    # Load raw data if needed
    raw_df = pd.DataFrame()
    if selected_view == "Raw CSV Data":
        raw_df = load_raw_data()
    
    # Display selected view
    if selected_view == "Data Collection":
        display_data_collection()
    
    elif selected_view == "Overview":
        display_overview(analysis_data)
    
    elif selected_view == "Topic Analysis":
        display_topic_analysis(analysis_data)
    
    elif selected_view == "Daily Trends":
        display_daily_trends(analysis_data)
    
    elif selected_view == "Top Products":
        display_top_products(analysis_data)
    
    elif selected_view == "AI & B2B Trends (LLM Analysis)":
        display_llm_analysis(analysis_data)
    
    elif selected_view == "Raw CSV Data":
        display_raw_csv_data()

if __name__ == "__main__":
    main() 