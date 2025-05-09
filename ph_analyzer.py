#!/usr/bin/env python3
"""
Product Hunt Data Analyzer - Analyzes trends and patterns in Product Hunt data using Groq LLM
"""

import os
import json
import logging
import pandas as pd
import numpy as np  # Add numpy import
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Tuple
from collections import Counter
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("ph_analyzer.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("PHAnalyzer")

# Load environment variables
load_dotenv()

# Custom JSON encoder to handle numpy types
class NumpyEncoder(json.JSONEncoder):
    """JSON encoder that handles numpy data types"""
    def default(self, obj):
        if isinstance(obj, np.integer):
            return int(obj)
        if isinstance(obj, np.floating):
            return float(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)

class ProductHuntAnalyzer:
    """Analyzes Product Hunt data to identify trends and patterns"""
    
    def __init__(self, data_file: str):
        """
        Initialize the analyzer
        
        Args:
            data_file: Path to CSV file containing Product Hunt data
        """
        self.data_file = data_file
        self.df = None
        self.topics_count = None
        self.daily_stats = None
        self.top_products = None
        self.trend_analysis = None
        
        # Initialize Groq client for LLM analysis
        groq_api_key = os.getenv("GROQ_API_KEY")
        
        # Clean the API key if it has URL-encoded characters
        if groq_api_key and '%' in groq_api_key:
            import urllib.parse
            try:
                groq_api_key = urllib.parse.unquote(groq_api_key)
                logger.info("Cleaned GROQ_API_KEY to remove URL encoding")
            except Exception as e:
                logger.error(f"Failed to clean GROQ_API_KEY: {str(e)}")
            
        if not groq_api_key:
            logger.warning("GROQ_API_KEY not found in environment. LLM analysis will not be available.")
            self.groq_client = None
        else:
            try:
                # Using the successful approach with manual HTTP client to avoid the proxies issue
                import httpx
                from groq import Groq
                http_client = httpx.Client()
                self.groq_client = Groq(api_key=groq_api_key, http_client=http_client)
                logger.info("Groq client initialized successfully")
            except Exception as e:
                logger.error(f"Failed to initialize Groq client: {str(e)}")
                self.groq_client = None
        
    def load_data(self) -> bool:
        """
        Load and preprocess the data from CSV
        
        Returns:
            True if data loaded successfully, False otherwise
        """
        try:
            logger.info(f"Loading data from {self.data_file}")
            self.df = pd.read_csv(self.data_file)
            
            # Convert Launch Date to datetime
            self.df['Launch Date'] = pd.to_datetime(self.df['Launch Date'])
            
            # Convert numeric columns
            self.df['Upvotes'] = pd.to_numeric(self.df['Upvotes'], errors='coerce').fillna(0).astype(int)
            self.df['Comments Count'] = pd.to_numeric(self.df['Comments Count'], errors='coerce').fillna(0).astype(int)
            
            # Create Topic Lists
            self.df['Topic List'] = self.df['Topics'].str.split(', ')
            
            logger.info(f"Successfully loaded {len(self.df)} products")
            return True
        except Exception as e:
            logger.error(f"Error loading data: {str(e)}")
            return False
            
    def analyze_basic_stats(self) -> Dict[str, Any]:
        """
        Calculate basic statistics about the dataset
        
        Returns:
            Dictionary with basic statistics
        """
        if self.df is None:
            return {}
            
        total_products = len(self.df)
        date_range = (self.df['Launch Date'].min(), self.df['Launch Date'].max())
        avg_upvotes = self.df['Upvotes'].mean()
        median_upvotes = self.df['Upvotes'].median()
        max_upvotes = self.df['Upvotes'].max()
        max_upvote_product = self.df.loc[self.df['Upvotes'].idxmax()]['Product Name']
        
        stats = {
            "total_products": total_products,
            "date_range": {
                "start": date_range[0].strftime("%Y-%m-%d"),
                "end": date_range[1].strftime("%Y-%m-%d"),
                "days": (date_range[1] - date_range[0]).days + 1
            },
            "upvotes": {
                "average": round(avg_upvotes, 2),
                "median": median_upvotes,
                "max": max_upvotes,
                "max_product": max_upvote_product
            }
        }
        
        logger.info(f"Basic stats calculated for {total_products} products")
        return stats
    
    def analyze_topics(self) -> Dict[str, int]:
        """
        Analyze the distribution of topics/categories
        
        Returns:
            Dictionary with topic counts
        """
        if self.df is None:
            return {}
            
        # Extract all topics
        all_topics = []
        for topics_list in self.df['Topic List'].dropna():
            if isinstance(topics_list, list):
                all_topics.extend(topics_list)
        
        # Count occurrences
        topic_counts = Counter(all_topics)
        
        # Sort by count (descending)
        sorted_topics = dict(sorted(topic_counts.items(), key=lambda x: x[1], reverse=True))
        
        self.topics_count = sorted_topics
        logger.info(f"Analyzed {len(sorted_topics)} unique topics")
        
        return sorted_topics
    
    def analyze_daily_trends(self) -> pd.DataFrame:
        """
        Analyze daily launch trends
        
        Returns:
            DataFrame with daily stats
        """
        if self.df is None:
            return pd.DataFrame()
            
        # Group by launch date
        daily = self.df.groupby(self.df['Launch Date'].dt.date).agg({
            'Product Name': 'count',
            'Upvotes': ['sum', 'mean', 'median', 'max'],
            'Comments Count': ['sum', 'mean']
        })
        
        # Flatten the column hierarchy
        daily.columns = ['_'.join(col).strip() for col in daily.columns.values]
        
        # Rename columns for clarity
        daily = daily.rename(columns={
            'Product Name_count': 'products_count',
            'Upvotes_sum': 'total_upvotes',
            'Upvotes_mean': 'avg_upvotes',
            'Upvotes_median': 'median_upvotes',
            'Upvotes_max': 'max_upvotes',
            'Comments Count_sum': 'total_comments',
            'Comments Count_mean': 'avg_comments'
        })
        
        # Reset index to make date a column
        daily = daily.reset_index().rename(columns={'index': 'date'})
        
        self.daily_stats = daily
        logger.info(f"Analyzed daily trends across {len(daily)} days")
        
        return daily
    
    def get_top_products(self, n: int = 20) -> pd.DataFrame:
        """
        Get the top N products by upvotes
        
        Args:
            n: Number of top products to return
            
        Returns:
            DataFrame with top N products
        """
        if self.df is None:
            return pd.DataFrame()
            
        # Select relevant columns and sort by upvotes
        top = self.df[['Product Name', 'Tagline', 'Launch Date', 'Upvotes', 'Comments Count', 'Topics', 'Website URL']]
        top = top.sort_values('Upvotes', ascending=False).head(n).reset_index(drop=True)
        
        self.top_products = top
        logger.info(f"Extracted top {n} products by upvotes")
        
        return top
    
    def analyze_with_llm(self) -> Dict[str, Any]:
        """
        Use Groq LLM to analyze trends and patterns in the data
        
        Returns:
            Dictionary with LLM analysis results
        """
        if self.df is None or self.groq_client is None:
            return {"error": "Data not loaded or Groq API key not configured"}
            
        logger.info("Starting LLM analysis of Product Hunt data")
        
        # Prepare data for LLM analysis
        topics_data = dict(list(self.topics_count.items())[:30])  # Top 30 topics
        top_products_data = self.top_products[['Product Name', 'Tagline', 'Upvotes', 'Topics']].head(20).to_dict(orient='records')
        
        # Create prompt for trend analysis
        prompt = f"""
        Analyze the following Product Hunt data to identify key trends, categories that are booming, and patterns:
        
        TOPICS BY FREQUENCY (top 30):
        {json.dumps(topics_data, indent=2)}
        
        TOP PRODUCTS (by upvotes):
        {json.dumps(top_products_data, indent=2)}
        
        Please analyze this data and provide:
        1. What are the top 5 trending categories/industries right now?
        2. For each trending category, what specific product types are popular?
        3. Which categories appear to be emerging or growing fastest?
        4. Are there any interesting patterns in the most successful products?
        5. What types of B2B vs B2C products are trending?
        6. Identify any AI-related trends and popular use cases.
        
        Format your response as a structured JSON with the following keys:
        "trending_categories", "emerging_categories", "product_patterns", "b2b_trends", "b2c_trends", "ai_trends"
        
        Your analysis should be concise but insightful, focusing on clear patterns in the data.
        """
        
        try:
            # Call Groq LLM API with the latest client structure
            try:
                # Try with llama3-70b-8192 first
                completion = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a data analyst specializing in tech industry trends."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama3-70b-8192",
                    temperature=0.1,
                    max_tokens=2000
                )
            except Exception as model_error:
                logger.warning(f"Failed with model llama3-70b-8192: {str(model_error)}. Trying fallback model.")
                # Try with llama3-8b-8192 as fallback
                completion = self.groq_client.chat.completions.create(
                    messages=[
                        {"role": "system", "content": "You are a data analyst specializing in tech industry trends."},
                        {"role": "user", "content": prompt}
                    ],
                    model="llama3-8b-8192",
                    temperature=0.1,
                    max_tokens=2000
                )
            
            # Extract the response text
            response_text = completion.choices[0].message.content
            
            # Try to parse as JSON
            try:
                start_idx = response_text.find('{')
                end_idx = response_text.rfind('}') + 1
                if start_idx >= 0 and end_idx > start_idx:
                    json_str = response_text[start_idx:end_idx]
                    analysis = json.loads(json_str)
                else:
                    # If no JSON found, use the whole text
                    analysis = {"raw_analysis": response_text}
            except json.JSONDecodeError:
                # If JSON parsing fails, return the raw text
                analysis = {"raw_analysis": response_text}
            
            self.trend_analysis = analysis
            logger.info("LLM analysis completed successfully")
            
            return analysis
            
        except Exception as e:
            logger.error(f"Error during LLM analysis: {str(e)}")
            return {"error": str(e)}
    
    def save_analysis(self, output_dir: str = "analysis") -> bool:
        """
        Save all analysis results to files
        
        Args:
            output_dir: Directory to save analysis files
            
        Returns:
            True if successful, False otherwise
        """
        if self.df is None:
            return False
            
        try:
            # Create output directory if it doesn't exist
            os.makedirs(output_dir, exist_ok=True)
            
            # Save basic stats
            basic_stats = self.analyze_basic_stats()
            with open(f"{output_dir}/basic_stats.json", "w") as f:
                json.dump(basic_stats, f, indent=2, cls=NumpyEncoder)
            
            # Save topic analysis
            if self.topics_count is None:
                self.analyze_topics()
            with open(f"{output_dir}/topic_analysis.json", "w") as f:
                json.dump(self.topics_count, f, indent=2, cls=NumpyEncoder)
            
            # Save daily trends
            if self.daily_stats is None:
                self.analyze_daily_trends()
            self.daily_stats.to_csv(f"{output_dir}/daily_trends.csv", index=False)
            
            # Save top products
            if self.top_products is None:
                self.get_top_products()
            self.top_products.to_csv(f"{output_dir}/top_products.csv", index=False)
            
            # Save LLM analysis if available
            if hasattr(self, 'trend_analysis') and self.trend_analysis:
                with open(f"{output_dir}/llm_trend_analysis.json", "w") as f:
                    json.dump(self.trend_analysis, f, indent=2, cls=NumpyEncoder)
            else:
                # Create a default/empty trend analysis to avoid missing file errors
                default_analysis = {
                    "error": "LLM analysis not available",
                    "trending_categories": "No data available",
                    "emerging_categories": "No data available",
                    "product_patterns": "No data available",
                    "b2b_trends": "No data available",
                    "b2c_trends": "No data available",
                    "ai_trends": "No data available"
                }
                with open(f"{output_dir}/llm_trend_analysis.json", "w") as f:
                    json.dump(default_analysis, f, indent=2)
            
            logger.info(f"Analysis results saved to {output_dir}/ directory")
            return True
            
        except Exception as e:
            logger.error(f"Error saving analysis: {str(e)}")
            return False


def main():
    """Run analysis on Product Hunt data"""
    data_file = "product_hunt_30_days.csv"
    
    logger.info("Starting Product Hunt data analysis")
    
    # Initialize analyzer
    analyzer = ProductHuntAnalyzer(data_file)
    
    # Load data
    if not analyzer.load_data():
        logger.error(f"Failed to load data from {data_file}")
        return 1
    
    # Run basic analyses
    analyzer.analyze_basic_stats()
    analyzer.analyze_topics()
    analyzer.analyze_daily_trends()
    analyzer.get_top_products()
    
    # Run LLM analysis if GROQ_API_KEY is available
    if analyzer.groq_client:
        analyzer.analyze_with_llm()
    
    # Save all analysis results
    analyzer.save_analysis()
    
    logger.info("Analysis completed successfully")
    return 0

if __name__ == "__main__":
    exit(main()) 