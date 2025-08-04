"""
Unit Tests for Story 2.3: Data Processing Pipeline
Tests all data cleaning and standardization functions with comprehensive coverage.
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime
import sys
import os

# Add the parent directory to the path so we can import from main.py
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from main import (
    clean_and_standardize_dates,
    clean_and_convert_amounts,
    standardize_account_names,
    handle_missing_values,
    remove_duplicate_transactions,
    generate_data_quality_summary,
    process_data_pipeline
)


class TestCleanAndStandardizeDates(unittest.TestCase):
    """Test the clean_and_standardize_dates function."""
    
    def setUp(self):
        """Set up test data."""
        self.df_valid = pd.DataFrame({
            'date': ['2023-01-15', '2023-02-20', '2023-03-10'],
            'amount': [100, 200, 300]
        })
        
        self.df_mixed_formats = pd.DataFrame({
            'date': ['01/15/2023', '2023-02-20', 'Mar 10, 2023', '15-04-2023'],
            'amount': [100, 200, 300, 400]
        })
        
        self.df_invalid_dates = pd.DataFrame({
            'date': ['invalid', '2023-02-30', 'not a date', '2023-13-01'],
            'amount': [100, 200, 300, 400]
        })
    
    def test_clean_dates_valid_format(self):
        """Test cleaning already valid date formats."""
        result_df, result = clean_and_standardize_dates(self.df_valid, 'date')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['valid_dates'], 3)
        self.assertEqual(result['invalid_dates'], 0)
        self.assertEqual(result['success_rate'], 1.0)
        
        # Check date format is standardized
        expected_dates = ['2023-01-15', '2023-02-20', '2023-03-10']
        self.assertEqual(result_df['date'].tolist(), expected_dates)
    
    def test_clean_dates_mixed_formats(self):
        """Test cleaning mixed date formats."""
        result_df, result = clean_and_standardize_dates(self.df_mixed_formats, 'date')
        
        self.assertTrue(result['success'])
        self.assertGreaterEqual(result['valid_dates'], 1)  # At least some dates should be valid
        
        # Valid dates should be converted to YYYY-MM-DD format
        valid_dates = result_df['date'].dropna()
        for date_str in valid_dates:
            if date_str != 'NaT':
                self.assertRegex(str(date_str), r'\d{4}-\d{2}-\d{2}')
    
    def test_clean_dates_invalid_formats(self):
        """Test handling of invalid date formats."""
        result_df, result = clean_and_standardize_dates(self.df_invalid_dates, 'date')
        
        self.assertTrue(result['success'])
        self.assertLess(result['valid_dates'], 4)  # Some dates should be invalid
        self.assertGreater(result['invalid_dates'], 0)
        self.assertLess(result['success_rate'], 1.0)
    
    def test_clean_dates_nonexistent_column(self):
        """Test handling of nonexistent date column."""
        result_df, result = clean_and_standardize_dates(self.df_valid, 'nonexistent')
        
        self.assertFalse(result['success'])
        self.assertIn('Date column not found', result['error'])
    
    def test_clean_dates_empty_dataframe(self):
        """Test handling of empty DataFrame."""
        empty_df = pd.DataFrame(columns=['date', 'amount'])
        result_df, result = clean_and_standardize_dates(empty_df, 'date')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['valid_dates'], 0)
        self.assertEqual(result['success_rate'], 0)


class TestCleanAndConvertAmounts(unittest.TestCase):
    """Test the clean_and_convert_amounts function."""
    
    def setUp(self):
        """Set up test data."""
        self.df_clean = pd.DataFrame({
            'amount': [100, 200, 300],
            'date': ['2023-01-01', '2023-01-02', '2023-01-03']
        })
        
        self.df_currency_symbols = pd.DataFrame({
            'amount': ['$100', '€200', '£300', '$1,500.50'],
            'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04']
        })
        
        self.df_negative_parentheses = pd.DataFrame({
            'amount': ['(100)', '200', '(300.50)', '$1,000'],
            'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04']
        })
        
        self.df_invalid_amounts = pd.DataFrame({
            'amount': ['not_a_number', 'abc', '$invalid', ''],
            'date': ['2023-01-01', '2023-01-02', '2023-01-03', '2023-01-04']
        })
    
    def test_clean_amounts_already_clean(self):
        """Test cleaning already clean numeric amounts."""
        result_df, result = clean_and_convert_amounts(self.df_clean, 'amount')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['valid_amounts'], 3)
        self.assertEqual(result['invalid_amounts'], 0)
        self.assertEqual(result['success_rate'], 1.0)
        
        # Check amounts are properly converted to numeric
        self.assertTrue(pd.api.types.is_numeric_dtype(result_df['amount']))
    
    def test_clean_amounts_with_currency_symbols(self):
        """Test cleaning amounts with currency symbols and commas."""
        result_df, result = clean_and_convert_amounts(self.df_currency_symbols, 'amount')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['valid_amounts'], 4)
        
        # Check specific conversions
        expected_amounts = [100.0, 200.0, 300.0, 1500.50]
        self.assertEqual(result_df['amount'].tolist(), expected_amounts)
    
    def test_clean_amounts_negative_parentheses(self):
        """Test handling of negative amounts in parentheses (accounting format)."""
        result_df, result = clean_and_convert_amounts(self.df_negative_parentheses, 'amount')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['valid_amounts'], 4)
        
        # Check negative conversion
        amounts = result_df['amount'].tolist()
        self.assertEqual(amounts[0], -100.0)  # (100) -> -100
        self.assertEqual(amounts[1], 200.0)   # 200 -> 200
        self.assertEqual(amounts[2], -300.50) # (300.50) -> -300.50
        self.assertEqual(amounts[3], 1000.0)  # $1,000 -> 1000
    
    def test_clean_amounts_invalid_values(self):
        """Test handling of invalid amount values."""
        result_df, result = clean_and_convert_amounts(self.df_invalid_amounts, 'amount')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['valid_amounts'], 0)
        self.assertEqual(result['invalid_amounts'], 4)
        self.assertEqual(result['success_rate'], 0.0)
    
    def test_clean_amounts_nonexistent_column(self):
        """Test handling of nonexistent amount column."""
        result_df, result = clean_and_convert_amounts(self.df_clean, 'nonexistent')
        
        self.assertFalse(result['success'])
        self.assertIn('Amount column not found', result['error'])


class TestStandardizeAccountNames(unittest.TestCase):
    """Test the standardize_account_names function."""
    
    def setUp(self):
        """Set up test data."""
        self.df_messy_accounts = pd.DataFrame({
            'account': ['  cash & bank  ', 'REVENUE INC', 'Expense Acct', 'bnk of america corp', 'office exp ltd'],
            'amount': [100, 200, 300, 400, 500]
        })
        
        self.df_standardizable = pd.DataFrame({
            'account': ['Cash Bnk', 'Rev Income', 'Exp Office', 'Corp Account', 'Ltd Company'],
            'amount': [100, 200, 300, 400, 500]
        })
    
    def test_standardize_account_names_basic_cleaning(self):
        """Test basic account name cleaning and standardization."""
        result_df, result = standardize_account_names(self.df_messy_accounts, 'account')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['original_unique_accounts'], 5)
        
        # Check specific standardizations
        accounts = result_df['account'].tolist()
        self.assertEqual(accounts[0], 'Cash And Bank')  # trimmed, case fixed, & -> And
        self.assertEqual(accounts[1], 'Revenue Income')  # case fixed, Inc -> Income
        self.assertEqual(accounts[2], 'Expense Account')  # case fixed, Acct -> Account
        self.assertEqual(accounts[3], 'Bank Of America Corporation')  # Bnk -> Bank, Corp -> Corporation
        self.assertEqual(accounts[4], 'Office Expense Limited')  # Exp -> Expense, Ltd -> Limited
    
    def test_standardize_account_abbreviations(self):
        """Test standardization of common abbreviations."""
        result_df, result = standardize_account_names(self.df_standardizable, 'account')
        
        self.assertTrue(result['success'])
        
        accounts = result_df['account'].tolist()
        self.assertIn('Bank', accounts[0])      # Bnk -> Bank
        self.assertIn('Revenue', accounts[1])   # Rev -> Revenue
        self.assertIn('Expense', accounts[2])   # Exp -> Expense
        self.assertIn('Corporation', accounts[3]) # Corp -> Corporation
        self.assertIn('Limited', accounts[4])   # Ltd -> Limited
    
    def test_standardize_account_nonexistent_column(self):
        """Test handling of nonexistent account column."""
        result_df, result = standardize_account_names(self.df_messy_accounts, 'nonexistent')
        
        self.assertFalse(result['success'])
        self.assertIn('Account column not found', result['error'])
    
    def test_standardize_account_reduction_count(self):
        """Test account name consolidation reduces unique count."""
        # Create data with similar account names that should be standardized
        df_similar = pd.DataFrame({
            'account': ['Cash Bank', 'cash bnk', 'CASH BNK', '  Cash Bank  '],
            'amount': [100, 200, 300, 400]
        })
        
        result_df, result = standardize_account_names(df_similar, 'account')
        
        self.assertTrue(result['success'])
        self.assertEqual(result['original_unique_accounts'], 4)
        self.assertLessEqual(result['cleaned_unique_accounts'], 4)  # Should reduce or stay same


class TestHandleMissingValues(unittest.TestCase):
    """Test the handle_missing_values function."""
    
    def setUp(self):
        """Set up test data."""
        self.df_with_missing = pd.DataFrame({
            'date': ['2023-01-01', None, '2023-01-03'],
            'amount': [100, None, 300],
            'account': ['Cash', None, 'Revenue'],
            'balance': [1000, None, 1300]
        })
        
        self.df_no_missing = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'amount': [100, 200, 300],
            'account': ['Cash', 'Bank', 'Revenue']
        })
    
    def test_handle_missing_values_with_missing_data(self):
        """Test handling missing values with appropriate strategies."""
        result_df, result = handle_missing_values(self.df_with_missing)
        
        self.assertTrue(result['success'])
        self.assertIn('missing_summary', result)
        
        # Check missing value handling strategies
        # Date columns should remain NaN
        self.assertTrue(pd.isna(result_df['date'].iloc[1]))
        
        # Amount/balance columns should be filled with 0
        self.assertEqual(result_df['amount'].iloc[1], 0)
        self.assertEqual(result_df['balance'].iloc[1], 0)
        
        # Other columns should be filled with 'Unknown'
        self.assertEqual(result_df['account'].iloc[1], 'Unknown')
    
    def test_handle_missing_values_no_missing_data(self):
        """Test handling when no missing values exist."""
        result_df, result = handle_missing_values(self.df_no_missing)
        
        self.assertTrue(result['success'])
        
        # Check that all columns have 0% missing
        for col_summary in result['missing_summary'].values():
            self.assertEqual(col_summary['missing_count'], 0)
            self.assertEqual(col_summary['missing_percentage'], 0.0)
    
    def test_handle_missing_values_summary_accuracy(self):
        """Test accuracy of missing value summary statistics."""
        result_df, result = handle_missing_values(self.df_with_missing)
        
        missing_summary = result['missing_summary']
        
        # Each column should have 1 missing value out of 3 total (33.33%)
        for col in ['date', 'amount', 'account', 'balance']:
            self.assertEqual(missing_summary[col]['missing_count'], 1)
            self.assertAlmostEqual(missing_summary[col]['missing_percentage'], 33.33, places=1)


class TestRemoveDuplicateTransactions(unittest.TestCase):
    """Test the remove_duplicate_transactions function."""
    
    def setUp(self):
        """Set up test data."""
        self.df_with_duplicates = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-01', '2023-01-02', '2023-01-01'],
            'amount': [100, 100, 200, 100],
            'account': ['Cash', 'Cash', 'Bank', 'Cash']
        })
        
        self.df_no_duplicates = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'amount': [100, 200, 300],
            'account': ['Cash', 'Bank', 'Revenue']
        })
    
    def test_remove_duplicates_with_duplicates(self):
        """Test removing duplicate transactions."""
        result_df, result = remove_duplicate_transactions(self.df_with_duplicates)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['original_count'], 4)
        self.assertEqual(result['final_count'], 2)  # Should have 2 unique rows
        self.assertEqual(result['duplicates_removed'], 2)
        
        # Check that duplicates are actually removed
        self.assertEqual(len(result_df), 2)
        self.assertEqual(len(result_df.drop_duplicates()), len(result_df))
    
    def test_remove_duplicates_no_duplicates(self):
        """Test when no duplicates exist."""
        result_df, result = remove_duplicate_transactions(self.df_no_duplicates)
        
        self.assertTrue(result['success'])
        self.assertEqual(result['original_count'], 3)
        self.assertEqual(result['final_count'], 3)
        self.assertEqual(result['duplicates_removed'], 0)


class TestGenerateDataQualitySummary(unittest.TestCase):
    """Test the generate_data_quality_summary function."""
    
    def setUp(self):
        """Set up test data."""
        self.df_good_quality = pd.DataFrame({
            'date': ['2023-01-01', '2023-01-02', '2023-01-03'],
            'amount': [100.0, 200.0, 300.0],
            'account': ['Cash', 'Bank', 'Revenue']
        })
        
        self.df_poor_quality = pd.DataFrame({
            'date': ['2023-01-01', None, 'invalid'],
            'amount': [100.0, None, 'not_a_number'],
            'account': ['Cash', None, '']
        })
        
        self.processing_results_success = {
            'dates': {'success': True, 'success_rate': 1.0},
            'amounts': {'success': True, 'success_rate': 1.0},
            'accounts': {'success': True}
        }
        
        self.processing_results_failure = {
            'dates': {'success': False, 'error': 'Date error'},
            'amounts': {'success': False, 'error': 'Amount error'}
        }
    
    def test_generate_quality_summary_good_data(self):
        """Test quality summary generation for good quality data."""
        summary = generate_data_quality_summary(self.df_good_quality, self.processing_results_success)
        
        self.assertNotIn('error', summary)
        self.assertEqual(summary['total_rows'], 3)
        self.assertEqual(summary['total_columns'], 3)
        self.assertGreaterEqual(summary['data_quality_score'], 70)  # Should be reasonably high quality
        
        # Check column info is generated
        self.assertIn('column_info', summary)
        for col in ['date', 'amount', 'account']:
            self.assertIn(col, summary['column_info'])
            col_info = summary['column_info'][col]
            self.assertEqual(col_info['completeness_rate'], 100.0)  # All data present
    
    def test_generate_quality_summary_poor_data(self):
        """Test quality summary generation for poor quality data."""
        summary = generate_data_quality_summary(self.df_poor_quality, self.processing_results_failure)
        
        self.assertNotIn('error', summary)
        self.assertEqual(summary['total_rows'], 3)
        self.assertLess(summary['data_quality_score'], 70)  # Should be low quality
        
        # Should have recommendations for improvement
        self.assertGreater(len(summary['recommendations']), 0)
    
    def test_generate_quality_summary_column_analysis(self):
        """Test detailed column analysis in quality summary."""
        summary = generate_data_quality_summary(self.df_good_quality, self.processing_results_success)
        
        # Check date column analysis
        date_info = summary['column_info']['date']
        self.assertIn('date_range', date_info)
        self.assertIsNotNone(date_info['date_range']['earliest'])
        self.assertIsNotNone(date_info['date_range']['latest'])
        
        # Check amount column analysis
        amount_info = summary['column_info']['amount']
        self.assertIn('statistics', amount_info)
        self.assertEqual(amount_info['statistics']['min'], 100.0)
        self.assertEqual(amount_info['statistics']['max'], 300.0)
        
        # Check account column analysis
        account_info = summary['column_info']['account']
        self.assertEqual(account_info['unique_values'], 3)


class TestProcessDataPipeline(unittest.TestCase):
    """Test the main process_data_pipeline function."""
    
    def setUp(self):
        """Set up test data."""
        self.df_test = pd.DataFrame({
            'transaction_date': ['01/15/2023', '02/20/2023', '01/15/2023'],  # Mixed formats, duplicate
            'description': ['  cash deposit  ', 'BANK FEE', '  cash deposit  '],
            'amount_usd': ['$1,500.00', '($25.00)', '$1,500.00']
        })
        
        self.column_mappings = {
            'date': 'transaction_date',
            'account': 'description',
            'amount': 'amount_usd'
        }
    
    def test_process_data_pipeline_full_integration(self):
        """Test the complete data processing pipeline."""
        processed_df, processing_results, quality_summary = process_data_pipeline(
            self.df_test, self.column_mappings
        )
        
        # Check that all processing steps completed
        expected_steps = ['missing_values', 'duplicates', 'dates', 'amounts', 'accounts']
        for step in expected_steps:
            self.assertIn(step, processing_results)
            if processing_results[step] is not None:
                self.assertTrue(processing_results[step]['success'])
        
        # Check processed data quality
        self.assertIsInstance(processed_df, pd.DataFrame)
        self.assertGreater(len(processed_df), 0)
        
        # Check quality summary generation
        self.assertIsInstance(quality_summary, dict)
        self.assertIn('data_quality_score', quality_summary)
        
        # Verify data transformations
        # Dates should be standardized
        if not processed_df['transaction_date'].isna().all():
            for date_val in processed_df['transaction_date'].dropna():
                self.assertRegex(str(date_val), r'\d{4}-\d{2}-\d{2}')
        
        # Amounts should be numeric
        self.assertTrue(pd.api.types.is_numeric_dtype(processed_df['amount_usd']))
        
        # Duplicates should be removed
        self.assertLessEqual(len(processed_df), len(self.df_test))
    
    def test_process_data_pipeline_missing_mappings(self):
        """Test pipeline behavior with missing column mappings."""
        incomplete_mappings = {
            'date': 'transaction_date',
            'account': None,  # Missing account mapping
            'amount': 'amount_usd'
        }
        
        processed_df, processing_results, quality_summary = process_data_pipeline(
            self.df_test, incomplete_mappings
        )
        
        # Should still process successfully with available mappings
        self.assertIn('missing_values', processing_results)
        self.assertIn('duplicates', processing_results)
        self.assertIn('dates', processing_results)
        self.assertIn('amounts', processing_results)
        # Account processing should be skipped
        self.assertNotIn('accounts', processing_results)
    
    def test_process_data_pipeline_empty_dataframe(self):
        """Test pipeline with empty DataFrame."""
        empty_df = pd.DataFrame(columns=['date', 'account', 'amount'])
        empty_mappings = {'date': 'date', 'account': 'account', 'amount': 'amount'}
        
        processed_df, processing_results, quality_summary = process_data_pipeline(
            empty_df, empty_mappings
        )
        
        # Should handle empty data gracefully
        self.assertIsInstance(processed_df, pd.DataFrame)
        self.assertIsInstance(processing_results, dict)
        self.assertIsInstance(quality_summary, dict)


if __name__ == '__main__':
    # Run all tests
    unittest.main(verbosity=2)