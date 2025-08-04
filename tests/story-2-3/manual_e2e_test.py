"""
Manual E2E Test for Story 2.3: Data Processing Pipeline
This script tests the complete Streamlit interface functionality manually.
"""

import pandas as pd
import sys
import os
from io import StringIO, BytesIO

# Add the parent directory to the path so we can import from main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import (
    validate_data_structure,
    process_data_pipeline,
    detect_column_mappings
)

def create_test_csv_files():
    """Create test CSV files for manual testing."""
    
    # Test Case 1: Mixed date formats and currency symbols
    mixed_data = """Transaction Date,Description,Amount USD
01/15/2023,Cash Deposit from Client,"$1,500.00"
2023-02-20,Office Supplies Purchase,($125.50)
Mar 10 2023,Bank Service Fee,"$25.00"
15-04-2023,Rent Payment,"$2,000"
2023-05-15,Salary Payment,"5,000.00"
invalid_date,Insurance Premium,"$300"
"""
    
    with open('test_mixed_formats.csv', 'w') as f:
        f.write(mixed_data)
    
    # Test Case 2: Financial Statement Format
    financial_statement = """Account Name,Dec 2023,Nov 2023,Oct 2023,Sep 2023
Cash & Bank,"$10,000.00","$8,500.00","$7,200.00","$6,800.00"
Accounts Receivable,"$15,000.00","$12,000.00","$14,000.00","$13,500.00"
Revenue Income,"$25,000.00","$22,000.00","$21,000.00","$20,000.00"
Office Expenses,"$(3,500.00)","$(3,200.00)","$(2,800.00)","$(2,900.00)"
Salary Expense,"$(8,000.00)","$(8,000.00)","$(8,000.00)","$(8,000.00)"
"""
    
    with open('test_financial_statement.csv', 'w') as f:
        f.write(financial_statement)
    
    # Test Case 3: Inconsistent account names
    inconsistent_accounts = """Date,Account Name,Amount
2023-01-15,cash & bank,1500.00
2023-01-16,CASH & BANK,(-125.50)
2023-01-17,Cash Bnk,800.00
2023-01-18,office exp,(-250.00)
2023-01-19,Office Expense,(-300.00)
2023-01-20,revenue inc,2500.00
2023-01-21,Revenue Income,1800.00
"""
    
    with open('test_inconsistent_accounts.csv', 'w') as f:
        f.write(inconsistent_accounts)
    
    # Test Case 4: Missing values
    missing_values = """Date,Description,Amount
2023-01-01,Cash Deposit,1000.00
,Office Supplies,
2023-01-03,,500.00
2023-01-04,Bank Fee,25.00
,Unknown Transaction,
"""
    
    with open('test_missing_values.csv', 'w') as f:
        f.write(missing_values)
    
    print("✅ Test CSV files created:")
    print("- test_mixed_formats.csv")
    print("- test_financial_statement.csv") 
    print("- test_inconsistent_accounts.csv")
    print("- test_missing_values.csv")

def test_data_processing_pipeline(filename):
    """Test the data processing pipeline with a specific file."""
    print(f"\n🧪 Testing Data Processing Pipeline: {filename}")
    print("=" * 60)
    
    try:
        # Read the CSV file
        df = pd.read_csv(filename)
        print(f"📊 Original data shape: {df.shape}")
        print(f"📋 Original columns: {list(df.columns)}")
        
        # Step 1: Validate data structure
        print("\n1️⃣ Data Structure Validation")
        validation_results = validate_data_structure(df)
        
        if validation_results['overall_valid']:
            print("✅ Data structure validation PASSED")
            mappings = validation_results['mappings']
            print(f"   📍 Date column: {mappings['date']}")
            print(f"   📍 Account column: {mappings['account']}")
            print(f"   📍 Amount column: {mappings['amount']}")
            
            # Check for conversion info
            if validation_results.get('conversion_info', {}).get('was_converted'):
                print("🔄 Financial statement format detected and converted")
                conv_stats = validation_results['conversion_info']['conversion_stats']
                print(f"   📈 Converted from {conv_stats['original_shape']} to {conv_stats['converted_shape']}")
                print(f"   🏦 Found {conv_stats['accounts_found']} accounts across {conv_stats['periods_found']} periods")
            
        else:
            print("❌ Data structure validation FAILED")
            for col_type, validation in validation_results['validations'].items():
                if not validation['valid']:
                    print(f"   ❌ {col_type.title()}: {validation['error']}")
                    if validation['sample']:
                        print(f"      Sample: {validation['sample'][:3]}")
            return
        
        # Get the validated DataFrame (could be converted)
        working_df = validation_results.get('converted_df', df)
        
        # Step 2: Process through data pipeline
        print("\n2️⃣ Data Processing Pipeline")
        processed_df, processing_results, quality_summary = process_data_pipeline(
            working_df, mappings
        )
        
        print(f"📊 Processed data shape: {processed_df.shape}")
        
        # Step 3: Display processing results
        print("\n3️⃣ Processing Results")
        
        for step_name, result in processing_results.items():
            if result['success']:
                print(f"   ✅ {step_name.replace('_', ' ').title()}")
                
                if step_name == 'duplicates' and result.get('duplicates_removed', 0) > 0:
                    print(f"      🔄 Removed {result['duplicates_removed']} duplicate transactions")
                
                if step_name == 'dates' and 'success_rate' in result:
                    print(f"      📅 Date standardization: {result['success_rate']*100:.1f}% success rate")
                
                if step_name == 'amounts' and 'success_rate' in result:
                    print(f"      💰 Amount conversion: {result['success_rate']*100:.1f}% success rate")
                    
                if step_name == 'accounts' and result.get('reduction_count', 0) > 0:
                    print(f"      🏷️  Account standardization: {result['original_unique_accounts']} → {result['cleaned_unique_accounts']} unique accounts")
                    
                if step_name == 'missing_values':
                    total_missing = sum(info['missing_count'] for info in result['missing_summary'].values())
                    print(f"      📋 Handled {total_missing} missing values")
            else:
                print(f"   ❌ {step_name.replace('_', ' ').title()}: {result.get('error', 'Unknown error')}")
        
        # Step 4: Quality Summary
        print("\n4️⃣ Data Quality Summary")
        if 'error' not in quality_summary:
            quality_score = quality_summary['data_quality_score']
            
            if quality_score >= 90:
                print(f"   🎉 EXCELLENT Quality Score: {quality_score:.1f}/100")
            elif quality_score >= 75:
                print(f"   ✅ GOOD Quality Score: {quality_score:.1f}/100")
            elif quality_score >= 50:
                print(f"   ⚠️  FAIR Quality Score: {quality_score:.1f}/100")
            else:
                print(f"   ❌ POOR Quality Score: {quality_score:.1f}/100")
            
            print(f"   📊 Total rows: {quality_summary['total_rows']}")
            print(f"   📋 Total columns: {quality_summary['total_columns']}")
            
            # Show recommendations
            if quality_summary['recommendations']:
                print("   💡 Recommendations:")
                for rec in quality_summary['recommendations']:
                    print(f"      • {rec}")
        else:
            print(f"   ❌ Quality summary error: {quality_summary['error']}")
        
        # Step 5: Show sample of processed data
        print("\n5️⃣ Sample Processed Data (First 5 rows)")
        pd.set_option('display.max_columns', None)
        pd.set_option('display.width', None)
        print(processed_df.head())
        
        print(f"\n✅ SUCCESS: {filename} processed successfully!")
        
    except Exception as e:
        print(f"❌ ERROR processing {filename}: {str(e)}")
        import traceback
        traceback.print_exc()

def run_manual_e2e_tests():
    """Run the complete manual E2E test suite."""
    print("🧪 Story 2.3: Data Processing Pipeline - Manual E2E Tests")
    print("=" * 70)
    
    # Create test files
    create_test_csv_files()
    
    # Test each scenario
    test_files = [
        'test_mixed_formats.csv',
        'test_financial_statement.csv',
        'test_inconsistent_accounts.csv',
        'test_missing_values.csv'
    ]
    
    results = []
    for test_file in test_files:
        try:
            test_data_processing_pipeline(test_file)
            results.append(f"✅ {test_file}")
        except Exception as e:
            results.append(f"❌ {test_file}: {str(e)}")
    
    # Summary
    print("\n" + "=" * 70)
    print("📋 TEST SUMMARY")
    print("=" * 70)
    
    for result in results:
        print(result)
    
    passed_tests = len([r for r in results if r.startswith("✅")])
    total_tests = len(results)
    
    print(f"\n🎯 OVERALL RESULT: {passed_tests}/{total_tests} tests passed")
    
    if passed_tests == total_tests:
        print("🎉 ALL TESTS PASSED! Story 2.3 data processing pipeline is working correctly.")
    else:
        print("⚠️  Some tests failed. Review the errors above.")
    
    # Cleanup test files
    import os
    for test_file in test_files:
        try:
            os.remove(test_file)
        except:
            pass
    print("\n🧹 Test files cleaned up.")

if __name__ == '__main__':
    run_manual_e2e_tests()