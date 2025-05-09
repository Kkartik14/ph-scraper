#!/usr/bin/env python3

import os
import sys
from ph_analyzer import ProductHuntAnalyzer

def test_analyzer_init():
    print("\n=== Testing ProductHuntAnalyzer Initialization ===\n")
    
    sample_file = "product_hunt_data.csv"
    if not os.path.exists(sample_file):
        print(f"Warning: {sample_file} not found. Please use an existing CSV file.")
        return False
    
    analyzer = ProductHuntAnalyzer(data_file=sample_file)
    
    if analyzer.groq_client is None:
        print("ERROR: Groq client was not initialized.")
        return False
    else:
        print("SUCCESS: Groq client was initialized successfully!")
        
        try:
            print("\nTesting Groq API call...")
            models = analyzer.groq_client.models.list()
            print(f"API call successful! Available models: {[m.id for m in models.data][:5]} (showing first 5)")
            
            print("\nTesting LLM analysis capability...")
            if analyzer.load_data():
                print("Successfully loaded data")
                
                analyzer.analyze_basic_stats()
                analyzer.analyze_topics()
                analyzer.analyze_daily_trends()
                analyzer.get_top_products()
                
                result = analyzer.analyze_with_llm()
                if "error" in result:
                    print(f"LLM analysis returned an error: {result['error']}")
                    return False
                else:
                    print("LLM analysis completed successfully!")
                    return True
            else:
                print(f"Failed to load data from {sample_file}")
                return False
                
        except Exception as e:
            print(f"ERROR: API call failed: {str(e)}")
            return False
    
    return True

if __name__ == "__main__":
    if test_analyzer_init():
        print("\nOverall test: SUCCESS")
        sys.exit(0)
    else:
        print("\nOverall test: FAILED")
        sys.exit(1) 