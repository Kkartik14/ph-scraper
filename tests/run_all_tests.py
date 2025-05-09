#!/usr/bin/env python3

import os
import sys
import subprocess
import time
import logging
from datetime import datetime

# Ensure logs directory exists
os.makedirs("logs", exist_ok=True)

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(os.path.join("logs", "test_results.log")),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger("TestRunner")

def run_test(test_script, description):
    logger.info(f"Starting test: {description}")
    print(f"\n{'='*80}")
    print(f"RUNNING TEST: {description}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    result = subprocess.run(['python', test_script], capture_output=True, text=True)
    
    elapsed = time.time() - start_time
    
    print(result.stdout)
    
    if result.returncode == 0:
        status_msg = f"✅ PASSED: {description} ({elapsed:.2f}s)"
        logger.info(status_msg)
        print(f"\n{status_msg}")
        return True
    else:
        status_msg = f"❌ FAILED: {description} ({elapsed:.2f}s)"
        logger.error(status_msg)
        print(f"\n{status_msg}")
        if result.stderr:
            logger.error(f"Error details: {result.stderr}")
            print(f"Error details:\n{result.stderr}")
        return False

def main():
    logger.info(f"=== Starting test suite at {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} ===")
    print("\n" + "="*80)
    print("PRODUCT HUNT SCRAPER & ANALYZER TEST SUITE")
    print("="*80 + "\n")
    
    # Get all test files
    test_files = [
        ("tests/test_groq_client.py", "Groq Client Initialization Test"),
        ("tests/test_analyzer.py", "Product Hunt Analyzer Test"),
        ("tests/test_full_pipeline.py", "Full Pipeline Integration Test")
    ]
    
    # Run each test
    results = {}
    
    for test_file, description in test_files:
        results[description] = run_test(test_file, description)
    
    # Print summary
    print("\n" + "="*80)
    print("TEST SUMMARY")
    print("="*80)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    summary_line = f"Passed {passed} of {total} tests ({passed/total*100:.1f}%)"
    logger.info(summary_line)
    
    for description, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {description}")
    
    print(f"\n{summary_line}")
    
    if passed == total:
        success_msg = "🎉 All tests passed! 🎉"
        logger.info(success_msg)
        print(f"\n{success_msg}")
        return 0
    else:
        failure_msg = "⚠️ Some tests failed. Please review the output above. ⚠️"
        logger.warning(failure_msg)
        print(f"\n{failure_msg}")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 