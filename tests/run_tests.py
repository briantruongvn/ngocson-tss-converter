"""
Test runner for TSS Converter Web Application
Runs all tests and provides comprehensive reporting
"""

import sys
import unittest
import time
from pathlib import Path
from io import StringIO

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

def run_all_tests():
    """Run all tests and provide detailed reporting"""
    print("🧪 TSS Converter Test Suite")
    print("=" * 50)
    
    # Discover and load all tests
    test_dir = Path(__file__).parent
    loader = unittest.TestLoader()
    suite = loader.discover(test_dir, pattern='test_*.py')
    
    # Run tests with detailed output
    stream = StringIO()
    runner = unittest.TextTestRunner(
        stream=stream,
        verbosity=2,
        failfast=False,
        buffer=True
    )
    
    start_time = time.time()
    result = runner.run(suite)
    end_time = time.time()
    
    # Print results
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Skipped: {len(result.skipped) if hasattr(result, 'skipped') else 0}")
    print(f"Execution time: {end_time - start_time:.2f} seconds")
    print()
    
    # Print detailed output
    print("Test Output:")
    print("-" * 30)
    print(stream.getvalue())
    
    # Print failures and errors
    if result.failures:
        print("\n❌ FAILURES:")
        print("=" * 30)
        for test, traceback in result.failures:
            print(f"\nFAILED: {test}")
            print(traceback)
    
    if result.errors:
        print("\n💥 ERRORS:")
        print("=" * 30)
        for test, traceback in result.errors:
            print(f"\nERROR: {test}")
            print(traceback)
    
    # Summary
    print("\n" + "=" * 50)
    if result.wasSuccessful():
        print("✅ All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

def run_security_tests():
    """Run only security-related tests"""
    print("🔒 Security Tests")
    print("=" * 30)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test_security')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

def run_pipeline_tests():
    """Run only pipeline-related tests"""
    print("⚙️ Pipeline Tests")
    print("=" * 30)
    
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromName('test_pipeline')
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="TSS Converter Test Runner")
    parser.add_argument(
        "--suite", 
        choices=["all", "security", "pipeline"], 
        default="all",
        help="Test suite to run"
    )
    
    args = parser.parse_args()
    
    if args.suite == "security":
        success = run_security_tests()
    elif args.suite == "pipeline":
        success = run_pipeline_tests()
    else:
        success = run_all_tests()
    
    sys.exit(0 if success else 1)