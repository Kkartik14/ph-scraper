#!/usr/bin/env python3

import os
import sys
from dotenv import load_dotenv

load_dotenv()

def test_groq_client():
    print("\n=== Testing Groq Client Initialization ===\n")
    
    groq_api_key = os.getenv("GROQ_API_KEY")
    
    if not groq_api_key:
        print("ERROR: GROQ_API_KEY not found in environment.")
        return False
    
    print(f"API Key found: {groq_api_key[:5]}...{groq_api_key[-5:]}")
    print(f"API Key length: {len(groq_api_key)}")
    
    if '%' in groq_api_key:
        print("WARNING: Found '%' character in GROQ_API_KEY - attempting to URL decode it.")
        import urllib.parse
        groq_api_key = urllib.parse.unquote(groq_api_key)
        print(f"Cleaned API Key: {groq_api_key[:5]}...{groq_api_key[-5:]}")
        print(f"Cleaned API Key length: {len(groq_api_key)}")
    
    methods = [
        "direct_import",
        "client_import", 
        "manual_httpclient"
    ]
    
    success = False
    
    for method in methods:
        print(f"\n--- Testing method: {method} ---")
        
        try:
            if method == "direct_import":
                print("Trying: from groq import Groq")
                from groq import Groq
                client = Groq(api_key=groq_api_key)
                print("SUCCESS: Client initialized with direct import!")
                success = True
                
            elif method == "client_import":
                print("Trying: from groq.client import Groq")
                from groq.client import Groq
                client = Groq(api_key=groq_api_key)
                print("SUCCESS: Client initialized with client import!")
                success = True
                
            elif method == "manual_httpclient":
                print("Trying manual HTTP client approach")
                import httpx
                from groq import Groq
                http_client = httpx.Client()
                try:
                    client = Groq(api_key=groq_api_key, http_client=http_client)
                    print("SUCCESS: Client initialized with manual HTTP client!")
                    success = True
                except Exception as e:
                    print(f"FAILED: Manual HTTP client approach: {str(e)}")
            
            if success:
                print("\nTesting API call...")
                try:
                    models = client.models.list()
                    print(f"API call successful! Available models: {[m.id for m in models.data]}")
                except Exception as e:
                    print(f"API call failed: {str(e)}")
                break
                
        except Exception as e:
            print(f"FAILED: {str(e)}")
    
    if not success:
        print("\nAll initialization methods failed.")
    
    return success

if __name__ == "__main__":
    if test_groq_client():
        print("\nOverall test: SUCCESS")
        sys.exit(0)
    else:
        print("\nOverall test: FAILED")
        sys.exit(1) 