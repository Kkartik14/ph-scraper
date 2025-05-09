#!/usr/bin/env python3

import os
import sys
import time
from ph_scraper import ProductHuntScraper
from ph_analyzer import ProductHuntAnalyzer

def test_full_pipeline():
    print("\n=== Testing Full Product Hunt Pipeline ===\n")
    
    # Step 1: Test Scraper
    print("Step 1: Testing scraper")
    
    output_file = "test_product_hunt_data.csv"
    days = 2
    
    scraper = ProductHuntScraper(use_stealth=False)  # Set to False for faster testing
    
    posts = scraper.scrape_recent_days(days=days, use_pst=True, limit=5)  # Limit to 5 products per day for testing
    
    if not posts:
        print("ERROR: Failed to scrape any posts.")
        return False
    
    print(f"SUCCESS: Scraped {len(posts)} posts from the last {days} days.")
    
    if not scraper.export_to_csv(posts, output_file):
        print(f"ERROR: Failed to export scraped data to {output_file}")
        return False
    
    print(f"SUCCESS: Saved scraped data to {output_file}")
    
    # Step 2: Test Analyzer
    print("\nStep 2: Testing analyzer")
    
    analyzer = ProductHuntAnalyzer(data_file=output_file)
    
    if not analyzer.load_data():
        print(f"ERROR: Failed to load data from {output_file}")
        return False
    
    print(f"SUCCESS: Loaded {len(analyzer.df)} products from {output_file}")
    
    analyzer.analyze_basic_stats()
    analyzer.analyze_topics()
    analyzer.analyze_daily_trends()
    analyzer.get_top_products()
    
    if analyzer.groq_client:
        print("Testing LLM analysis...")
        try:
            analyzer.analyze_with_llm()
            print("SUCCESS: LLM analysis completed.")
        except Exception as e:
            print(f"WARNING: LLM analysis failed: {str(e)}")
    else:
        print("WARNING: Skipping LLM analysis as Groq client is not initialized.")
    
    output_dir = "test_analysis"
    if not analyzer.save_analysis(output_dir):
        print(f"ERROR: Failed to save analysis results to {output_dir}")
        return False
    
    print(f"SUCCESS: Saved analysis results to {output_dir} directory")
    
    # Clean up test files
    cleanup_test_files(output_file, output_dir)
    
    return True

def cleanup_test_files(csv_file, analysis_dir):
    print("\nCleaning up test files...")
    
    try:
        if os.path.exists(csv_file):
            os.remove(csv_file)
            print(f"Removed {csv_file}")
        
        if os.path.exists(analysis_dir):
            for file in os.listdir(analysis_dir):
                os.remove(os.path.join(analysis_dir, file))
            os.rmdir(analysis_dir)
            print(f"Removed {analysis_dir} directory")
    except Exception as e:
        print(f"WARNING: Error during cleanup: {str(e)}")

if __name__ == "__main__":
    if test_full_pipeline():
        print("\nOverall pipeline test: SUCCESS")
        sys.exit(0)
    else:
        print("\nOverall pipeline test: FAILED")
        sys.exit(1) 