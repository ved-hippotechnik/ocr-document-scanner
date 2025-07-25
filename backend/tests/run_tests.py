#!/usr/bin/env python3
"""
Test runner for the OCR Document Scanner application
"""
import unittest
import sys
import os
import time
from io import StringIO

# Add the backend directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

# Import test modules
from test_auth import TestAuth
from test_cache import TestMemoryCache, TestMemoryCacheManager, TestRedisCache, TestOCRCache, TestUnifiedCache
from test_api import TestAPIEndpoints, TestAsyncEndpoints


class ColoredTextTestResult(unittest.TextTestResult):
    """Custom test result class with colored output"""
    
    def __init__(self, stream, descriptions, verbosity):
        super().__init__(stream, descriptions, verbosity)
        self.success_count = 0
        
    def addSuccess(self, test):
        super().addSuccess(test)
        self.success_count += 1
        if self.verbosity > 1:
            self.stream.write(f"\033[92m✓ {test._testMethodName}\033[0m\n")
            
    def addError(self, test, err):
        super().addError(test, err)
        if self.verbosity > 1:
            self.stream.write(f"\033[91m✗ {test._testMethodName} (ERROR)\033[0m\n")
            
    def addFailure(self, test, err):
        super().addFailure(test, err)
        if self.verbosity > 1:
            self.stream.write(f"\033[91m✗ {test._testMethodName} (FAILED)\033[0m\n")
            
    def addSkip(self, test, reason):
        super().addSkip(test, reason)
        if self.verbosity > 1:
            self.stream.write(f"\033[93m~ {test._testMethodName} (SKIPPED)\033[0m\n")


class TestRunner:
    """Enhanced test runner with detailed reporting"""
    
    def __init__(self, verbosity=2):
        self.verbosity = verbosity
        self.start_time = None
        self.end_time = None
        
    def run_test_suite(self, test_suite, suite_name):
        """Run a test suite and return results"""
        print(f"\n{'='*60}")
        print(f"🧪 Running {suite_name}")
        print(f"{'='*60}")
        
        runner = unittest.TextTestRunner(
            stream=sys.stdout,
            verbosity=self.verbosity,
            resultclass=ColoredTextTestResult
        )
        
        result = runner.run(test_suite)
        
        # Print summary
        print(f"\n📊 {suite_name} Results:")
        print(f"   ✅ Tests run: {result.testsRun}")
        print(f"   ✅ Successes: {result.success_count}")
        print(f"   ❌ Failures: {len(result.failures)}")
        print(f"   💥 Errors: {len(result.errors)}")
        print(f"   ⏭️  Skipped: {len(result.skipped)}")
        
        # Print failure details
        if result.failures:
            print(f"\n❌ Failure Details:")
            for test, traceback in result.failures:
                print(f"   - {test}: {traceback.split('AssertionError: ')[-1].strip()}")
        
        # Print error details
        if result.errors:
            print(f"\n💥 Error Details:")
            for test, traceback in result.errors:
                print(f"   - {test}: {traceback.split('\\n')[-2].strip()}")
        
        return result
    
    def run_all_tests(self):
        """Run all test suites"""
        self.start_time = time.time()
        
        print("\n🚀 Starting OCR Document Scanner Test Suite")
        print("="*80)
        
        # Define test suites
        test_suites = [
            (unittest.TestLoader().loadTestsFromTestCase(TestAuth), "Authentication Tests"),
            (unittest.TestLoader().loadTestsFromTestCase(TestMemoryCache), "Memory Cache Tests"),
            (unittest.TestLoader().loadTestsFromTestCase(TestMemoryCacheManager), "Memory Cache Manager Tests"),
            (unittest.TestLoader().loadTestsFromTestCase(TestRedisCache), "Redis Cache Tests"),
            (unittest.TestLoader().loadTestsFromTestCase(TestOCRCache), "OCR Cache Tests"),
            (unittest.TestLoader().loadTestsFromTestCase(TestUnifiedCache), "Unified Cache Tests"),
            (unittest.TestLoader().loadTestsFromTestCase(TestAPIEndpoints), "API Endpoint Tests"),
            (unittest.TestLoader().loadTestsFromTestCase(TestAsyncEndpoints), "Async Endpoint Tests"),
        ]
        
        # Run each test suite
        all_results = []
        for suite, name in test_suites:
            result = self.run_test_suite(suite, name)
            all_results.append((name, result))
        
        self.end_time = time.time()
        
        # Print overall summary
        self.print_overall_summary(all_results)
        
        # Return overall success status
        return all(result.wasSuccessful() for _, result in all_results)
    
    def print_overall_summary(self, results):
        """Print overall test summary"""
        print("\n" + "="*80)
        print("📈 OVERALL TEST SUMMARY")
        print("="*80)
        
        total_tests = sum(result.testsRun for _, result in results)
        total_successes = sum(getattr(result, 'success_count', 0) for _, result in results)
        total_failures = sum(len(result.failures) for _, result in results)
        total_errors = sum(len(result.errors) for _, result in results)
        total_skipped = sum(len(result.skipped) for _, result in results)
        
        print(f"🎯 Total Tests: {total_tests}")
        print(f"✅ Successes: {total_successes}")
        print(f"❌ Failures: {total_failures}")
        print(f"💥 Errors: {total_errors}")
        print(f"⏭️  Skipped: {total_skipped}")
        
        success_rate = (total_successes / total_tests * 100) if total_tests > 0 else 0
        print(f"📊 Success Rate: {success_rate:.1f}%")
        
        duration = self.end_time - self.start_time
        print(f"⏱️  Duration: {duration:.2f} seconds")
        
        # Print suite-by-suite results
        print(f"\n📋 Suite Results:")
        for name, result in results:
            status = "✅ PASS" if result.wasSuccessful() else "❌ FAIL"
            print(f"   {status} {name}: {result.testsRun} tests")
        
        # Overall status
        overall_success = all(result.wasSuccessful() for _, result in results)
        if overall_success:
            print(f"\n🎉 ALL TESTS PASSED! 🎉")
        else:
            print(f"\n⚠️  SOME TESTS FAILED ⚠️")
        
        print("="*80)


def run_specific_test(test_class, test_method=None):
    """Run a specific test class or method"""
    if test_method:
        suite = unittest.TestSuite()
        suite.addTest(test_class(test_method))
    else:
        suite = unittest.TestLoader().loadTestsFromTestCase(test_class)
    
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    return result.wasSuccessful()


def main():
    """Main test runner function"""
    import argparse
    
    parser = argparse.ArgumentParser(description='Run OCR Document Scanner tests')
    parser.add_argument('--verbose', '-v', action='store_true', help='Verbose output')
    parser.add_argument('--test', '-t', help='Run specific test class or method')
    parser.add_argument('--coverage', '-c', action='store_true', help='Run with coverage report')
    parser.add_argument('--fast', '-f', action='store_true', help='Run only fast tests')
    
    args = parser.parse_args()
    
    # Set verbosity
    verbosity = 2 if args.verbose else 1
    
    # Run specific test if requested
    if args.test:
        test_parts = args.test.split('.')
        if len(test_parts) == 1:
            # Test class
            test_class = globals().get(test_parts[0])
            if test_class:
                success = run_specific_test(test_class)
                sys.exit(0 if success else 1)
            else:
                print(f"Test class '{test_parts[0]}' not found")
                sys.exit(1)
        elif len(test_parts) == 2:
            # Test method
            test_class = globals().get(test_parts[0])
            if test_class:
                success = run_specific_test(test_class, test_parts[1])
                sys.exit(0 if success else 1)
            else:
                print(f"Test class '{test_parts[0]}' not found")
                sys.exit(1)
    
    # Run with coverage if requested
    if args.coverage:
        try:
            import coverage
            cov = coverage.Coverage()
            cov.start()
            
            # Run tests
            runner = TestRunner(verbosity)
            success = runner.run_all_tests()
            
            # Stop coverage and report
            cov.stop()
            cov.save()
            
            print("\n📊 COVERAGE REPORT")
            print("="*50)
            cov.report()
            
            # Generate HTML report
            cov.html_report(directory='coverage_html')
            print(f"\n📁 HTML coverage report generated in 'coverage_html' directory")
            
        except ImportError:
            print("Coverage not available. Install with: pip install coverage")
            success = False
    else:
        # Run all tests normally
        runner = TestRunner(verbosity)
        success = runner.run_all_tests()
    
    # Exit with appropriate code
    sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()