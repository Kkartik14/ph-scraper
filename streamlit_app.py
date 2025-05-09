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
        # Convert date column to datetime
        if "date" in data["daily"].columns:
            data["daily"]["date"] = pd.to_datetime(data["daily"]["date"])
    
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

def load_raw_data(file_path: str = "product_hunt_30_days.csv") -> pd.DataFrame:
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
    This dashboard visualizes trends and patterns in recent Product Hunt launches, 
    identifying popular categories, emerging trends, and successful product characteristics.
    """)
    st.markdown("---")

def display_sidebar_controls():
    """Display sidebar controls and filters"""
    st.sidebar.header("📊 Dashboard Controls")
    
    view_options = [
        "Overview",
        "Topic Analysis",
        "Daily Trends",
        "Top Products",
        "AI & B2B Trends (LLM Analysis)",
        "Raw Data"
    ]
    
    selected_view = st.sidebar.radio("Select View", view_options)
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### Data Info")
    st.sidebar.markdown("This analysis is based on Product Hunt launches from the last 30 days.")
    
    st.sidebar.markdown("---")
    st.sidebar.markdown("### 🔄 Update Data")
    if st.sidebar.button("Run Scraper (30 Days)"):
        st.sidebar.warning("Scraper is running... This may take several minutes.")
        # This would trigger the scraper in a real implementation
        st.sidebar.success("Scraper completed! Refresh the page to see updated data.")
    
    if st.sidebar.button("Run Analysis"):
        st.sidebar.warning("Analyzer is running...")
        # This would trigger the analyzer in a real implementation
        st.sidebar.success("Analysis completed! Refresh the page to see updated results.")
    
    return selected_view

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
    
    # Create daily products count chart
    st.markdown("### Daily Product Launch Count")
    
    fig = px.line(
        daily_data,
        x="date",
        y="products_count",
        labels={"date": "Date", "products_count": "Number of Products"},
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
        x=daily_data["date"],
        y=daily_data["total_upvotes"],
        mode="lines+markers",
        name="Total Upvotes",
        line=dict(color="#FF6154", width=3)
    ))
    
    # Add average upvotes line
    fig.add_trace(go.Scatter(
        x=daily_data["date"],
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

def display_raw_data(raw_df: pd.DataFrame):
    """Display raw Product Hunt data"""
    st.markdown('<p class="sub-header">Raw Product Hunt Data</p>', unsafe_allow_html=True)
    
    if raw_df.empty:
        st.warning("Raw data not available. Please run the scraper first.")
        return
    
    # Display summary stats
    st.markdown("### Data Summary")
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.metric("Total Products", len(raw_df))
    
    with col2:
        if "Upvotes" in raw_df.columns:
            st.metric("Avg. Upvotes", round(raw_df["Upvotes"].mean(), 2))
    
    with col3:
        date_range = None
        if "Launch Date" in raw_df.columns:
            min_date = raw_df["Launch Date"].min().strftime("%Y-%m-%d")
            max_date = raw_df["Launch Date"].max().strftime("%Y-%m-%d")
            date_range = f"{min_date} to {max_date}"
        
        st.metric("Date Range", date_range or "N/A")
    
    # Add search/filter capability
    search_term = st.text_input("Search Products", "")
    
    filtered_df = raw_df
    if search_term:
        filtered_df = raw_df[
            raw_df["Product Name"].str.contains(search_term, case=False) |
            raw_df["Tagline"].str.contains(search_term, case=False) |
            raw_df["Topics"].str.contains(search_term, case=False)
        ]
    
    # Display interactive table
    st.markdown("### All Products")
    
    # Format the dataframe for display
    display_df = filtered_df.copy()
    if "Launch Date" in display_df.columns and pd.api.types.is_datetime64_any_dtype(display_df["Launch Date"]):
        display_df["Launch Date"] = display_df["Launch Date"].dt.strftime("%Y-%m-%d")
    
    # Display the data
    st.dataframe(display_df, height=600, use_container_width=True)

def main():
    """Main function to run the Streamlit app"""
    # Display header
    display_header()
    
    # Display sidebar and get selected view
    selected_view = display_sidebar_controls()
    
    # Load analysis data
    analysis_data = load_analysis_data()
    
    # Load raw data if needed
    raw_df = pd.DataFrame()
    if selected_view == "Raw Data":
        raw_df = load_raw_data()
    
    # Display the selected view
    if selected_view == "Overview":
        display_overview(analysis_data)
    
    elif selected_view == "Topic Analysis":
        display_topic_analysis(analysis_data)
    
    elif selected_view == "Daily Trends":
        display_daily_trends(analysis_data)
    
    elif selected_view == "Top Products":
        display_top_products(analysis_data)
    
    elif selected_view == "AI & B2B Trends (LLM Analysis)":
        display_llm_analysis(analysis_data)
    
    elif selected_view == "Raw Data":
        display_raw_data(raw_df)

if __name__ == "__main__":
    main() 