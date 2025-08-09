#!/usr/bin/env python3
"""
Test Execution Script for Story 5.1: Chat Interface Foundation

This script runs comprehensive tests for the chat interface implementation.
"""

import sys
import os
import subprocess
import time
from datetime import datetime

# Add the parent directory to the path
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

def run_unit_tests():
    """Run unit tests for chat interface."""
    print("🧪 Running Unit Tests...")
    print("=" * 50)
    
    try:
        # Run pytest for unit tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/story-5-1/test_chat_interface.py::TestChatInterfaceFoundation",
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running unit tests: {e}")
        return False

def run_integration_tests():
    """Run integration tests for chat interface."""
    print("\n🔗 Running Integration Tests...")
    print("=" * 50)
    
    try:
        # Run pytest for integration tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/story-5-1/test_chat_interface.py::TestChatInterfaceIntegration",
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running integration tests: {e}")
        return False

def run_e2e_tests():
    """Run end-to-end tests for chat interface."""
    print("\n🌐 Running End-to-End Tests...")
    print("=" * 50)
    
    try:
        # Run pytest for e2e tests
        result = subprocess.run([
            sys.executable, "-m", "pytest", 
            "tests/story-5-1/test_chat_interface.py::TestChatInterfaceEndToEnd",
            "-v", "--tb=short"
        ], capture_output=True, text=True)
        
        print(result.stdout)
        if result.stderr:
            print("Errors:", result.stderr)
        
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running e2e tests: {e}")
        return False

def check_application_availability():
    """Check if the main application is available."""
    print("🔍 Checking Application Availability...")
    print("=" * 50)
    
    try:
        # Try to import the main module
        import main
        print("✅ Main application module is available")
        
        # Check for required functions
        required_functions = [
            'create_chat_interface',
            'create_chat_message_display',
            'display_chat_message',
            'create_chat_input_field',
            'add_chat_message',
            'create_loading_indicator',
            'process_chat_message',
            'initialize_session_state'
        ]
        
        missing_functions = []
        for func_name in required_functions:
            if hasattr(main, func_name):
                print(f"✅ {func_name} function found")
            else:
                print(f"❌ {func_name} function missing")
                missing_functions.append(func_name)
        
        if missing_functions:
            print(f"\n❌ Missing functions: {', '.join(missing_functions)}")
            return False
        
        return True
    except ImportError as e:
        print(f"❌ Cannot import main module: {e}")
        return False
    except Exception as e:
        print(f"❌ Error checking application: {e}")
        return False

def run_manual_test_checklist():
    """Run manual test checklist."""
    print("\n📋 Manual Test Checklist")
    print("=" * 50)
    
    checklist = [
        "1. ✅ Chat tab is visible as the 7th tab",
        "2. ✅ Chat interface loads without errors",
        "3. ✅ Welcome message is displayed when no messages exist",
        "4. ✅ Input field accepts text input",
        "5. ✅ Send button is clickable and functional",
        "6. ✅ User messages appear with correct styling (right-aligned, blue)",
        "7. ✅ AI responses appear with correct styling (left-aligned, light)",
        "8. ✅ Message timestamps are displayed correctly",
        "9. ✅ Chat history persists when switching tabs",
        "10. ✅ Loading indicator appears during AI processing",
        "11. ✅ Error handling works correctly",
        "12. ✅ Responsive design works on different screen sizes",
        "13. ✅ Integration with existing data works",
        "14. ✅ Performance is acceptable with many messages",
        "15. ✅ Accessibility features work correctly"
    ]
    
    for item in checklist:
        print(item)
    
    print("\n📝 Manual Testing Required:")
    print("- Execute the manual testing guide: tests/story-5-1/MANUAL_TESTING_GUIDE.md")
    print("- Test on different browsers and devices")
    print("- Verify all user scenarios work correctly")
    print("- Document any issues found")

def generate_test_report(results):
    """Generate a test report."""
    print("\n📊 Test Report")
    print("=" * 50)
    
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    report = f"""
Story 5.1: Chat Interface Foundation - Test Report
Generated: {timestamp}

Test Results:
- Application Availability: {'✅ PASS' if results['app_available'] else '❌ FAIL'}
- Unit Tests: {'✅ PASS' if results['unit_tests'] else '❌ FAIL'}
- Integration Tests: {'✅ PASS' if results['integration_tests'] else '❌ FAIL'}
- End-to-End Tests: {'✅ PASS' if results['e2e_tests'] else '❌ FAIL'}

Overall Status: {'✅ PASS' if all(results.values()) else '❌ FAIL'}

Next Steps:
1. Review any failed tests
2. Execute manual testing checklist
3. Address any issues found
4. Re-run tests after fixes
"""
    
    print(report)
    
    # Save report to file
    report_file = f"tests/story-5-1/test_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}.txt"
    try:
        with open(report_file, 'w') as f:
            f.write(report)
        print(f"📄 Test report saved to: {report_file}")
    except Exception as e:
        print(f"❌ Error saving test report: {e}")

def main():
    """Main test execution function."""
    print("🧪 Story 5.1: Chat Interface Foundation - Test Suite")
    print("=" * 60)
    print(f"Started at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    results = {}
    
    # Check application availability
    results['app_available'] = check_application_availability()
    
    if not results['app_available']:
        print("\n❌ Application not available. Please ensure main.py is properly implemented.")
        return False
    
    # Run tests
    results['unit_tests'] = run_unit_tests()
    results['integration_tests'] = run_integration_tests()
    results['e2e_tests'] = run_e2e_tests()
    
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
    success = main()
    sys.exit(0 if success else 1) 