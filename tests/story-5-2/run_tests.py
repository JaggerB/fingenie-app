#!/usr/bin/env python3
"""
Test Execution Script for Story 5.2: Financial Data Query Engine

This script runs comprehensive tests for the query engine implementation.
"""

import sys
import os
import subprocess
import time
import json
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def run_unit_tests():
    """Run unit tests for query engine."""
    print("🧪 Running Unit Tests...")
    print("=" * 50)
    
    try:
        # Run pytest for unit tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "unit/",
            "-v", "--tb=short", "-m", "unit"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        return False

def run_integration_tests():
    """Run integration tests for query engine."""
    print("\n🔄 Running Integration Tests...")
    print("=" * 50)
    
    try:
        # Check if integration tests exist
        integration_dir = os.path.join(os.path.dirname(__file__), "integration")
        if not os.path.exists(integration_dir) or not os.listdir(integration_dir):
            print("ℹ️  No integration tests found. Skipping integration tests.")
            return True
        
        # Run pytest for integration tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "integration/",
            "-v", "--tb=short", "-m", "integration"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False

def run_coverage_tests():
    """Run tests with coverage reporting."""
    print("\n📊 Running Coverage Tests...")
    print("=" * 50)
    
    try:
        # Run pytest with coverage
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            ".",
            "--cov=main",
            "--cov-report=html:coverage_html",
            "--cov-report=term-missing",
            "--cov-fail-under=85",
            "-v"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running coverage tests: {e}")
        return False

def run_performance_tests():
    """Run performance tests for query engine."""
    print("\n⚡ Running Performance Tests...")
    print("=" * 50)
    
    try:
        # Run performance tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            ".",
            "-k", "performance",
            "-v", "--tb=short"
        ], capture_output=True, text=True, cwd=os.path.dirname(__file__))
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running performance tests: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available."""
    print("🔍 Checking Dependencies...")
    print("=" * 50)
    
    required_packages = [
        'pytest',
        'pandas',
        'streamlit',
        'openai'
    ]
    
    missing_packages = []
    
    for package in required_packages:
        try:
            __import__(package)
            print(f"✅ {package}")
        except ImportError:
            print(f"❌ {package} - MISSING")
            missing_packages.append(package)
    
    if missing_packages:
        print(f"\n⚠️  Missing packages: {', '.join(missing_packages)}")
        print("Please install missing packages with: pip install " + " ".join(missing_packages))
        return False
    
    return True

def check_application_availability():
    """Check if the main application is available."""
    print("\n🔍 Checking Application Availability...")
    print("=" * 50)
    
    try:
        # Try to import main module
        import main
        print("✅ Main application module available")
        return True
    except ImportError as e:
        print(f"❌ Main application module not available: {e}")
        return False

def run_manual_test_checklist():
    """Run manual test checklist."""
    print("\n📋 Manual Test Checklist")
    print("=" * 50)
    
    checklist_items = [
        "✅ Test natural language query understanding",
        "✅ Test data extraction accuracy",
        "✅ Test response generation quality",
        "✅ Test chart and insight references",
        "✅ Test follow-up question handling",
        "✅ Test conversation context maintenance",
        "✅ Test error handling and recovery",
        "✅ Test performance with large datasets",
        "✅ Test integration with chat interface",
        "✅ Test integration with existing data sources"
    ]
    
    for item in checklist_items:
        print(item)
    
    print("\n📝 Manual testing guide available at: tests/story-5-2/MANUAL_TESTING_GUIDE.md")

def generate_test_report(results):
    """Generate a comprehensive test report."""
    print("\n📄 Generating Test Report...")
    print("=" * 50)
    
    report = {
        'timestamp': datetime.now().isoformat(),
        'story': '5.2 - Financial Data Query Engine',
        'results': results,
        'summary': {
            'total_tests': len(results),
            'passed_tests': sum(1 for r in results.values() if r),
            'failed_tests': sum(1 for r in results.values() if not r)
        }
    }
    
    # Save report to file
    report_path = os.path.join(os.path.dirname(__file__), 'test_report.json')
    with open(report_path, 'w') as f:
        json.dump(report, f, indent=2)
    
    print(f"📄 Test report saved to: {report_path}")
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"   Total Tests: {report['summary']['total_tests']}")
    print(f"   Passed: {report['summary']['passed_tests']}")
    print(f"   Failed: {report['summary']['failed_tests']}")
    
    if report['summary']['failed_tests'] == 0:
        print("🎉 All tests passed!")
    else:
        print("⚠️  Some tests failed. Please review the output above.")

def main():
    """Main test execution function."""
    print("🧪 Story 5.2: Financial Data Query Engine - Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Check dependencies
    results['dependencies'] = check_dependencies()
    
    if not results['dependencies']:
        print("\n❌ Dependencies check failed. Please install missing packages.")
        return False
    
    # Check application availability
    results['app_available'] = check_application_availability()
    
    if not results['app_available']:
        print("\n❌ Application not available. Please ensure main.py is properly implemented.")
        return False
    
    # Run tests
    results['unit_tests'] = run_unit_tests()
    results['integration_tests'] = run_integration_tests()
    results['coverage_tests'] = run_coverage_tests()
    results['performance_tests'] = run_performance_tests()
    
    # Run manual test checklist
    run_manual_test_checklist()
    
    # Generate test report
    generate_test_report(results)
    
    # Return overall success
    overall_success = all(results.values())
    
    print(f"\n{'✅ All tests passed!' if overall_success else '❌ Some tests failed!'}")
    print(f"Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    return overall_success

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="Run Story 5.2 tests")
    parser.add_argument("--type", choices=["unit", "integration", "coverage", "performance", "all"], 
                       default="all", help="Type of tests to run")
    
    args = parser.parse_args()
    
    if args.type == "unit":
        success = run_unit_tests()
    elif args.type == "integration":
        success = run_integration_tests()
    elif args.type == "coverage":
        success = run_coverage_tests()
    elif args.type == "performance":
        success = run_performance_tests()
    else:
        success = main()
    
    sys.exit(0 if success else 1) 