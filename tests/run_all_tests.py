#!/usr/bin/env python3

import os
import sys
import subprocess
import time

def run_test(test_script, description):
    print(f"\n{'='*80}")
    print(f"RUNNING TEST: {description}")
    print(f"{'='*80}")
    
    start_time = time.time()
    
    result = subprocess.run(['python', test_script], capture_output=True, text=True)
    
    elapsed = time.time() - start_time
    
    print(result.stdout)
    
    if result.returncode == 0:
        print(f"\n✅ PASSED: {description} ({elapsed:.2f}s)")
        return True
    else:
        print(f"\n❌ FAILED: {description} ({elapsed:.2f}s)")
        if result.stderr:
            print(f"Error details:\n{result.stderr}")
        return False

def main():
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
    
    for description, result in results.items():
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status}: {description}")
    
    print(f"\nPassed {passed} of {total} tests ({passed/total*100:.1f}%)")
    
    if passed == total:
        print("\n🎉 All tests passed! 🎉")
        return 0
    else:
        print("\n⚠️ Some tests failed. Please review the output above. ⚠️")
        return 1

if __name__ == "__main__":
    sys.exit(main()) 