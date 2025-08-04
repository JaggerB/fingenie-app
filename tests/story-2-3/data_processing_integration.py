"""
Integration Tests for Story 2.3: Data Processing Pipeline
Tests the complete end-to-end data processing workflow with realistic data scenarios.
"""

import unittest
import pandas as pd
import numpy as np
import sys
import os
from io import StringIO

# Add the parent directory to the path so we can import from main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import (
    validate_data_structure,
    detect_financial_statement_format,
    convert_financial_statement_to_long_format,
    process_data_pipeline,
    detect_column_mappings
)


class TestDataProcessingIntegration(unittest.TestCase):
    """Integration tests for the complete data processing workflow."""
    
    def setUp(self):
        """Set up realistic test datasets."""
        
        # Realistic transaction data with various issues
        self.messy_transaction_csv = """Transaction Date,Description,Amount,Account Type
01/15/2023,Cash Deposit from Customer,$1500.00,Revenue
2023-02-20,Office Supplies Purchase,(125.50),Expense
Mar 10 2023,Bank Service Fee,($25.00),Bank Exp
01/15/2023,Cash Deposit from Customer,$1500.00,Revenue
2023-04-01,Unknown Transaction,$0.00,Unknown
invalid_date,Rent Payment,$2000.00,Expense Acct
2023-05-15,Salary Payment,$5000,Expense Inc
""".strip()
        
        # Financial statement format (wide format)
        self.financial_statement_csv = """Account,Dec-22,Nov-22,Oct-22,Sep-22
Cash and Bank,"$10,000","$8,500","$7,200","$6,800"
Accounts Receivable,"$15,000","$12,000","$14,000","$13,500"
Revenue Income,"$25,000","$22,000","$21,000","$20,000"
Office Expenses,"$(3,500)","$(3,200)","$(2,800)","$(2,900)"
Salary Expense,"$(8,000)","$(8,000)","$(8,000)","$(8,000)"
""".strip()
        
        # Clean data for baseline testing
        self.clean_transaction_csv = """Date,Account,Amount
2023-01-15,Cash Revenue,1500.00
2023-02-20,Office Expense,125.50
2023-03-10,Bank Fee,25.00
2023-04-01,Rent Expense,2000.00
""".strip()
    
    def test_messy_transaction_data_complete_workflow(self):
        """Test complete workflow with messy real-world transaction data."""
        # Load the messy data
        df = pd.read_csv(StringIO(self.messy_transaction_csv))
        
        # Step 1: Validate data structure
        validation_results = validate_data_structure(df)
        
        # Should detect column mappings
        self.assertTrue(validation_results['overall_valid'])
        self.assertIsNotNone(validation_results['mappings']['date'])
        self.assertIsNotNone(validation_results['mappings']['account'])
        self.assertIsNotNone(validation_results['mappings']['amount'])
        
        # Step 2: Process through complete pipeline
        processed_df, processing_results, quality_summary = process_data_pipeline(
            df, validation_results['mappings']
        )
        
        # Verify all processing steps completed successfully
        expected_steps = ['missing_values', 'duplicates', 'dates', 'amounts', 'accounts']
        for step in expected_steps:
            self.assertIn(step, processing_results)
            self.assertTrue(processing_results[step]['success'], f"Step {step} failed")
        
        # Verify data quality improvements
        # 1. Duplicates should be removed
        original_rows = len(df)
        processed_rows = len(processed_df)
        self.assertLessEqual(processed_rows, original_rows)
        self.assertGreater(processing_results['duplicates']['duplicates_removed'], 0)
        
        # 2. Dates should be standardized to YYYY-MM-DD format
        date_col = validation_results['mappings']['date']
        valid_dates = processed_df[date_col].dropna()
        for date_val in valid_dates:
            self.assertRegex(str(date_val), r'\d{4}-\d{2}-\d{2}')
        
        # 3. Amounts should be converted to numeric
        amount_col = validation_results['mappings']['amount']
        self.assertTrue(pd.api.types.is_numeric_dtype(processed_df[amount_col]))
        
        # 4. Account names should be cleaned and standardized
        account_col = validation_results['mappings']['account']
        account_names = processed_df[account_col].dropna().tolist()
        
        # Check that standardization rules were applied
        standardized_terms = ['Revenue', 'Expense', 'Account', 'Income', 'Bank']
        has_standardized = any(
            any(term in account for term in standardized_terms)
            for account in account_names
        )
        self.assertTrue(has_standardized, "Account names should be standardized")
        
        # 5. Missing values should be handled appropriately
        missing_handling = processing_results['missing_values']['missing_summary']
        self.assertIsInstance(missing_handling, dict)
        
        # Verify quality summary is comprehensive
        self.assertIn('data_quality_score', quality_summary)
        self.assertIn('column_info', quality_summary)
        self.assertIn('recommendations', quality_summary)
        
        quality_score = quality_summary['data_quality_score']
        self.assertGreaterEqual(quality_score, 0)
        self.assertLessEqual(quality_score, 100)
        
        print(f"Integration Test - Messy Data Quality Score: {quality_score:.1f}/100")
    
    def test_financial_statement_conversion_workflow(self):
        """Test complete workflow with financial statement format conversion."""
        # Load financial statement data
        df = pd.read_csv(StringIO(self.financial_statement_csv))
        
        # Step 1: Detect financial statement format
        fs_detection = detect_financial_statement_format(df)
        self.assertTrue(fs_detection['is_financial_statement'])
        
        # Step 2: Convert to long format
        converted_df = convert_financial_statement_to_long_format(df, fs_detection)
        self.assertIsNotNone(converted_df)
        self.assertIn('Date', converted_df.columns)
        self.assertIn('Account', converted_df.columns)
        self.assertIn('Amount', converted_df.columns)
        
        # Verify conversion results
        self.assertGreater(len(converted_df), 0)
        self.assertEqual(len(converted_df.columns), 3)
        
        # Step 3: Validate converted structure
        validation_results = validate_data_structure(df)  # This will trigger conversion internally
        self.assertTrue(validation_results.get('conversion_info', {}).get('was_converted', False))
        
        # Step 4: Process converted data through pipeline
        if validation_results['overall_valid']:
            processed_df, processing_results, quality_summary = process_data_pipeline(
                converted_df, validation_results['mappings']
            )
            
            # Verify processing success
            self.assertIsInstance(processed_df, pd.DataFrame)
            self.assertGreater(len(processed_df), 0)
            
            # Check that amounts are properly numeric (including negatives)
            amounts = processed_df[validation_results['mappings']['amount']]
            self.assertTrue(pd.api.types.is_numeric_dtype(amounts))
            
            # Should have both positive and negative amounts from financial statement
            self.assertTrue((amounts > 0).any(), "Should have positive amounts")
            self.assertTrue((amounts < 0).any(), "Should have negative amounts")
            
            print(f"Integration Test - Financial Statement Quality Score: {quality_summary['data_quality_score']:.1f}/100")
    
    def test_clean_data_baseline_workflow(self):
        """Test workflow with clean data to establish baseline performance."""
        # Load clean data
        df = pd.read_csv(StringIO(self.clean_transaction_csv))
        
        # Step 1: Validate structure
        validation_results = validate_data_structure(df)
        self.assertTrue(validation_results['overall_valid'])
        
        # Step 2: Process through pipeline
        processed_df, processing_results, quality_summary = process_data_pipeline(
            df, validation_results['mappings']
        )
        
        # With clean data, processing should be highly successful
        for step, result in processing_results.items():
            if result and 'success' in result:
                self.assertTrue(result['success'], f"Clean data processing failed at step: {step}")
            
            # Check success rates where applicable
            if result and 'success_rate' in result:
                self.assertGreaterEqual(result['success_rate'], 0.9, f"Low success rate at step: {step}")
        
        # Quality score should be very high for clean data
        quality_score = quality_summary['data_quality_score']
        self.assertGreaterEqual(quality_score, 80, "Clean data should have high quality score")
        
        # No duplicates should be removed from clean data
        self.assertEqual(processing_results['duplicates']['duplicates_removed'], 0)
        
        # All dates should be successfully processed
        if 'dates' in processing_results and processing_results['dates']['success']:
            self.assertEqual(processing_results['dates']['success_rate'], 1.0)
        
        print(f"Integration Test - Clean Data Quality Score: {quality_score:.1f}/100")
    
    def test_edge_cases_and_error_handling(self):
        """Test integration workflow with edge cases and error conditions."""
        
        # Test 1: Empty DataFrame
        empty_df = pd.DataFrame()
        try:
            validation_results = validate_data_structure(empty_df)
            self.assertFalse(validation_results['overall_valid'])
        except Exception as e:
            self.fail(f"Empty DataFrame should be handled gracefully: {e}")
        
        # Test 2: DataFrame with only headers, no data
        headers_only_df = pd.DataFrame(columns=['Date', 'Account', 'Amount'])
        try:
            validation_results = validate_data_structure(headers_only_df)
            processed_df, processing_results, quality_summary = process_data_pipeline(
                headers_only_df, {'date': 'Date', 'account': 'Account', 'amount': 'Amount'}
            )
            self.assertEqual(len(processed_df), 0)
            self.assertIn('data_quality_score', quality_summary)
        except Exception as e:
            self.fail(f"Headers-only DataFrame should be handled gracefully: {e}")
        
        # Test 3: DataFrame with completely invalid data
        invalid_data_csv = """Date,Account,Amount
not_a_date,12345,not_a_number
also_not_date,67890,also_not_number
still_not_date,54321,still_not_number"""
        
        invalid_df = pd.read_csv(StringIO(invalid_data_csv))
        try:
            processed_df, processing_results, quality_summary = process_data_pipeline(
                invalid_df, {'date': 'Date', 'account': 'Account', 'amount': 'Amount'}
            )
            
            # Should complete without errors but with low quality scores
            self.assertIsInstance(quality_summary, dict)
            self.assertLess(quality_summary['data_quality_score'], 70)
            
            # Should have recommendations for data quality improvement
            self.assertGreater(len(quality_summary['recommendations']), 0)
        except Exception as e:
            self.fail(f"Invalid data should be handled gracefully: {e}")
    
    def test_data_volume_and_performance(self):
        """Test integration workflow with larger datasets for performance validation."""
        
        # Generate larger dataset
        dates = pd.date_range('2022-01-01', '2023-12-31', freq='D')
        accounts = ['Revenue', 'Expense', 'Bank Fee', 'Office Cost', 'Salary']
        
        large_data = []
        for i, date in enumerate(dates):
            account = accounts[i % len(accounts)]
            amount = np.random.uniform(100, 5000) * (1 if 'Revenue' in account else -1)
            large_data.append({
                'transaction_date': date.strftime('%Y-%m-%d'),
                'account_name': account,
                'amount_value': amount
            })
        
        large_df = pd.DataFrame(large_data)
        
        # Add some duplicates and missing values for realism
        large_df = pd.concat([large_df, large_df.head(50)])  # Add duplicates
        large_df.loc[large_df.sample(20).index, 'account_name'] = None  # Add missing values
        
        print(f"Testing with dataset size: {len(large_df)} rows")
        
        # Process through complete workflow
        import time
        start_time = time.time()
        
        validation_results = validate_data_structure(large_df)
        processed_df, processing_results, quality_summary = process_data_pipeline(
            large_df, validation_results['mappings']
        )
        
        end_time = time.time()
        processing_time = end_time - start_time
        
        print(f"Large dataset processing time: {processing_time:.2f} seconds")
        
        # Verify results
        self.assertIsInstance(processed_df, pd.DataFrame)
        self.assertGreater(len(processed_df), 0)
        self.assertIn('data_quality_score', quality_summary)
        
        # Performance should be reasonable (less than 30 seconds for ~800 rows)
        self.assertLess(processing_time, 30, "Processing should complete in reasonable time")
        
        # Duplicates should be detected and removed
        self.assertGreater(processing_results['duplicates']['duplicates_removed'], 0)


class TestColumnMappingDetection(unittest.TestCase):
    """Test automatic column mapping detection in various scenarios."""
    
    def test_standard_column_names(self):
        """Test detection with standard column names."""
        df = pd.DataFrame({
            'Date': ['2023-01-01'],
            'Description': ['Test'],
            'Amount': [100]
        })
        
        mappings = detect_column_mappings(df)
        
        self.assertEqual(mappings['date'], 'Date')
        self.assertEqual(mappings['account'], 'Description') 
        self.assertEqual(mappings['amount'], 'Amount')
    
    def test_alternative_column_names(self):
        """Test detection with alternative column names."""
        df = pd.DataFrame({
            'transaction_date': ['2023-01-01'],
            'account_name': ['Test'],
            'dollar_amount': [100]
        })
        
        mappings = detect_column_mappings(df)
        
        self.assertEqual(mappings['date'], 'transaction_date')
        self.assertEqual(mappings['account'], 'account_name')
        self.assertEqual(mappings['amount'], 'dollar_amount')
    
    def test_financial_terms_detection(self):
        """Test detection with financial-specific terms."""
        df = pd.DataFrame({
            'posting_date': ['2023-01-01'],
            'expense_category': ['Test'],
            'credit_amount': [100]
        })
        
        mappings = detect_column_mappings(df)
        
        self.assertEqual(mappings['date'], 'posting_date')
        self.assertEqual(mappings['account'], 'expense_category')
        self.assertEqual(mappings['amount'], 'credit_amount')


if __name__ == '__main__':
    # Run integration tests with detailed output
    unittest.main(verbosity=2)