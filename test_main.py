"""
Unit tests for movement detection engine functions in main.py
Tests for Story 3.1: Movement Detection Engine

Coverage requirement: 80%
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from unittest.mock import patch, Mock

# Import functions from main.py
from main import (
    calculate_monthly_summaries,
    calculate_mom_movements,
    calculate_yoy_movements,
    apply_movement_thresholds,
    detect_new_and_discontinued_accounts,
    rank_movements_by_significance,
    run_movement_detection_engine
)


class TestMovementDetectionEngine(unittest.TestCase):
    """Test suite for movement detection engine functions."""
    
    def setUp(self):
        """Set up test data for movement detection tests."""
        # Create sample financial data for testing
        self.sample_data = pd.DataFrame({
            'date': [
                '2022-01-01', '2022-01-15', '2022-02-01', '2022-02-15',
                '2022-03-01', '2022-03-15', '2023-01-01', '2023-01-15',
                '2023-02-01', '2023-02-15', '2023-03-01', '2023-03-15'
            ],
            'account': [
                'Revenue', 'Revenue', 'Revenue', 'Revenue',
                'Revenue', 'Revenue', 'Revenue', 'Revenue',
                'Revenue', 'Revenue', 'Revenue', 'Revenue'
            ],
            'amount': [
                10000, 5000, 12000, 6000, 15000, 7500, 11000, 5500,
                18000, 9000, 20000, 10000
            ]
        })
        
        # Create sample data with multiple accounts
        self.multi_account_data = pd.DataFrame({
            'date': [
                '2022-01-01', '2022-02-01', '2022-03-01', '2023-01-01', '2023-02-01', '2023-03-01',
                '2022-01-01', '2022-02-01', '2022-03-01', '2023-01-01', '2023-02-01', '2023-03-01'
            ],
            'account': [
                'Revenue', 'Revenue', 'Revenue', 'Revenue', 'Revenue', 'Revenue',
                'Expenses', 'Expenses', 'Expenses', 'Expenses', 'Expenses', 'Expenses'
            ],
            'amount': [
                100000, 110000, 120000, 120000, 140000, 150000,
                50000, 55000, 60000, 70000, 80000, 85000
            ]
        })
        
        # Create sample monthly summary data
        self.sample_monthly_summary = pd.DataFrame({
            'account': ['Revenue', 'Revenue', 'Revenue', 'Revenue'],
            'year_month': pd.to_datetime(['2022-01', '2022-02', '2022-03', '2023-01']).to_period('M'),
            'amount': [15000, 18000, 22500, 16500],
            'date': pd.to_datetime(['2022-01-31', '2022-02-28', '2022-03-31', '2023-01-31']),
            'year': [2022, 2022, 2022, 2023],
            'month': [1, 2, 3, 1]
        })
    
    def test_calculate_monthly_summaries_success(self):
        """Test successful calculation of monthly summaries."""
        result, stats = calculate_monthly_summaries(self.sample_data)
        
        self.assertIsNotNone(result)
        self.assertTrue(stats['success'])
        self.assertGreater(stats['accounts_processed'], 0)
        self.assertGreater(stats['periods_processed'], 0)
        self.assertIn('amount', result.columns)
        self.assertIn('account', result.columns)
        self.assertIn('year_month', result.columns)
    
    def test_calculate_monthly_summaries_missing_columns(self):
        """Test monthly summaries with missing required columns."""
        invalid_data = pd.DataFrame({
            'invalid_date': ['2022-01-01'],
            'invalid_account': ['Test'],
            'invalid_amount': [1000]
        })
        
        result, stats = calculate_monthly_summaries(invalid_data)
        
        self.assertIsNone(result)
        self.assertFalse(stats['success'])
        self.assertIn('missing', stats['error'])
    
    def test_calculate_mom_movements_success(self):
        """Test successful MoM movement calculations."""
        result, stats = calculate_mom_movements(self.sample_monthly_summary)
        
        self.assertIsNotNone(result)
        self.assertTrue(stats['success'])
        self.assertGreater(stats['total_movements'], 0)
        self.assertIn('percentage_change', result.columns)
        self.assertIn('absolute_change', result.columns)
        self.assertIn('movement_type', result.columns)
        
        # Verify movement type is MoM
        self.assertTrue(all(result['movement_type'] == 'MoM'))
    
    def test_calculate_mom_movements_empty_data(self):
        """Test MoM movements with empty data."""
        empty_data = pd.DataFrame(columns=['account', 'year_month', 'amount', 'date', 'year', 'month'])
        result, stats = calculate_mom_movements(empty_data)
        
        self.assertIsNotNone(result)
        self.assertTrue(stats['success'])
        self.assertEqual(len(result), 0)
    
    def test_calculate_yoy_movements_success(self):
        """Test successful YoY movement calculations."""
        # Create data spanning multiple years
        yoy_data = pd.DataFrame({
            'account': ['Revenue', 'Revenue', 'Revenue', 'Revenue'],
            'year_month': pd.to_datetime(['2022-01', '2022-02', '2023-01', '2023-02']).to_period('M'),
            'amount': [10000, 12000, 11000, 15000],
            'date': pd.to_datetime(['2022-01-31', '2022-02-28', '2023-01-31', '2023-02-28']),
            'year': [2022, 2022, 2023, 2023],
            'month': [1, 2, 1, 2]
        })
        
        result, stats = calculate_yoy_movements(yoy_data)
        
        self.assertIsNotNone(result)
        self.assertTrue(stats['success'])
        self.assertIn('movement_type', result.columns)
        
        # Verify movement type is YoY
        if len(result) > 0:
            self.assertTrue(all(result['movement_type'] == 'YoY'))
    
    def test_apply_movement_thresholds_success(self):
        """Test threshold application to movements."""
        # Create sample movements data
        movements_data = pd.DataFrame({
            'account': ['Account1', 'Account2', 'Account3'],
            'movement_type': ['MoM', 'MoM', 'YoY'],
            'percentage_change': [15.0, 5.0, 20.0],  # Only first and third should be flagged
            'absolute_change': [1500, 500, 2000],
            'current_period': ['2022-02', '2022-02', '2022-02'],
            'previous_period': ['2022-01', '2022-01', '2021-02'],
            'current_amount': [11500, 10500, 12000],
            'previous_amount': [10000, 10000, 10000]
        })
        
        result, stats = apply_movement_thresholds(movements_data, mom_threshold=10.0, yoy_threshold=15.0)
        
        self.assertIsNotNone(result)
        self.assertTrue(stats['success'])
        self.assertEqual(stats['mom_threshold_applied'], 10.0)
        self.assertEqual(stats['yoy_threshold_applied'], 15.0)
        
        # Should have 2 significant movements (15% MoM and 20% YoY)
        self.assertEqual(len(result), 2)
        self.assertIn('significance', result.columns)
        self.assertIn('materiality_score', result.columns)
    
    def test_apply_movement_thresholds_empty_data(self):
        """Test threshold application with empty movements data."""
        result, stats = apply_movement_thresholds(None)
        
        self.assertIsNone(result)
        self.assertFalse(stats['success'])
    
    def test_detect_new_and_discontinued_accounts_success(self):
        """Test detection of new and discontinued accounts."""
        # Create sample data with various account patterns
        current_date = pd.Timestamp.now()
        test_data = pd.DataFrame({
            'account': ['New Account', 'Old Account', 'Normal Account'],
            'date': [
                current_date - timedelta(days=30),  # New account (1 month ago)
                current_date - timedelta(days=90),  # Discontinued (3 months ago)
                current_date - timedelta(days=10)   # Normal account
            ]
        })
        
        # Create multiple entries per account to simulate monthly summary
        expanded_data = []
        for _, row in test_data.iterrows():
            for i in range(1, 4):  # Create 3 months of data for each
                expanded_data.append({
                    'account': row['account'],
                    'date': row['date'] - timedelta(days=30 * i),
                    'amount': 1000 * i
                })
        
        monthly_summary = pd.DataFrame(expanded_data)
        
        result, stats = detect_new_and_discontinued_accounts(monthly_summary)
        
        self.assertTrue(stats['success'])
        self.assertGreater(stats['total_accounts_analyzed'], 0)
        self.assertIsInstance(result, list)
    
    def test_detect_new_and_discontinued_accounts_empty_data(self):
        """Test account detection with empty data."""
        result, stats = detect_new_and_discontinued_accounts(None)
        
        self.assertEqual(result, [])
        self.assertFalse(stats['success'])
    
    def test_rank_movements_by_significance_success(self):
        """Test ranking of movements by significance."""
        # Create sample movements with materiality scores
        movements_data = pd.DataFrame({
            'account': ['Account1', 'Account2', 'Account3'],
            'percentage_change': [25.0, 15.0, 35.0],
            'absolute_change': [2500, 1500, 3500],
            'materiality_score': [75.0, 50.0, 90.0],
            'significance': ['High', 'Medium', 'Critical'],
            'movement_type': ['MoM', 'MoM', 'YoY']
        })
        
        result, stats = rank_movements_by_significance(movements_data)
        
        self.assertIsNotNone(result)
        self.assertTrue(stats['success'])
        self.assertEqual(len(result), 3)
        self.assertIn('rank', result.columns)
        
        # Check that highest materiality score is ranked first
        self.assertEqual(result.iloc[0]['rank'], 1)
        self.assertEqual(result.iloc[0]['materiality_score'], 90.0)
        
        # Verify ranking statistics
        self.assertEqual(stats['critical_movements'], 1)
        self.assertEqual(stats['high_movements'], 1)
        self.assertEqual(stats['medium_movements'], 1)
    
    def test_rank_movements_by_significance_empty_data(self):
        """Test ranking with empty movements data."""
        result, stats = rank_movements_by_significance(None)
        
        self.assertIsNone(result)
        self.assertFalse(stats['success'])
    
    def test_run_movement_detection_engine_success(self):
        """Test complete movement detection engine execution."""
        result = run_movement_detection_engine(self.multi_account_data)
        
        self.assertTrue(result['success'])
        self.assertIsNotNone(result['monthly_summary'])
        self.assertIn('summary_stats', result)
        self.assertEqual(len(result['errors']), 0)
        
        # Check that monthly summary was created
        self.assertTrue(result['summary_stats']['monthly_summary']['success'])
    
    def test_run_movement_detection_engine_invalid_data(self):
        """Test movement detection engine with invalid data."""
        invalid_data = pd.DataFrame({
            'wrong_column': ['value1', 'value2'],
            'another_wrong': [1, 2]
        })
        
        result = run_movement_detection_engine(invalid_data)
        
        self.assertFalse(result['success'])
        self.assertGreater(len(result['errors']), 0)
    
    def test_percentage_change_calculation_zero_division(self):
        """Test percentage change calculation with zero previous values."""
        # Create movements with zero previous amount
        monthly_data = pd.DataFrame({
            'account': ['Test Account', 'Test Account'],
            'year_month': pd.to_datetime(['2022-01', '2022-02']).to_period('M'),
            'amount': [0, 1000],  # Previous = 0, Current = 1000
            'date': pd.to_datetime(['2022-01-31', '2022-02-28']),
            'year': [2022, 2022],
            'month': [1, 2]
        })
        
        result, stats = calculate_mom_movements(monthly_data)
        
        self.assertTrue(stats['success'])
        self.assertEqual(len(result), 1)
        
        # Should handle zero division gracefully
        self.assertIsNotNone(result.iloc[0]['percentage_change'])
        self.assertFalse(np.isnan(result.iloc[0]['percentage_change']))
    
    def test_movement_type_consistency(self):
        """Test that movement types are correctly assigned."""
        # Test MoM movements
        mom_result, _ = calculate_mom_movements(self.sample_monthly_summary)
        if len(mom_result) > 0:
            self.assertTrue(all(mom_result['movement_type'] == 'MoM'))
        
        # Test YoY movements
        yoy_data = pd.DataFrame({
            'account': ['Revenue', 'Revenue'],
            'year_month': pd.to_datetime(['2022-01', '2023-01']).to_period('M'),
            'amount': [10000, 12000],
            'date': pd.to_datetime(['2022-01-31', '2023-01-31']),
            'year': [2022, 2023],
            'month': [1, 1]
        })
        
        yoy_result, _ = calculate_yoy_movements(yoy_data)
        if len(yoy_result) > 0:
            self.assertTrue(all(yoy_result['movement_type'] == 'YoY'))
    
    def test_significance_levels(self):
        """Test that significance levels are correctly assigned based on thresholds."""
        movements_data = pd.DataFrame({
            'account': ['Low', 'Medium', 'High', 'Critical'],
            'movement_type': ['MoM', 'MoM', 'MoM', 'MoM'],
            'percentage_change': [5.0, 12.0, 25.0, 35.0],  # 10% threshold
            'absolute_change': [500, 1200, 2500, 3500],
            'current_period': ['2022-02'] * 4,
            'previous_period': ['2022-01'] * 4,
            'current_amount': [10500, 11200, 12500, 13500],
            'previous_amount': [10000] * 4
        })
        
        result, _ = apply_movement_thresholds(movements_data, mom_threshold=10.0)
        
        # Should only have movements above threshold (12%, 25%, 35%)
        self.assertEqual(len(result), 3)
        
        # Check significance levels
        significance_counts = result['significance'].value_counts()
        self.assertIn('Medium', significance_counts)  # 12% (1x threshold)
        self.assertIn('High', significance_counts)    # 25% (2x threshold)
        self.assertIn('Critical', significance_counts) # 35% (3x threshold)


class TestMovementDetectionHelpers(unittest.TestCase):
    """Additional tests for helper functions and edge cases."""
    
    def test_materiality_score_calculation(self):
        """Test materiality score calculation combines percentage and absolute impact."""
        movements_data = pd.DataFrame({
            'account': ['High %', 'High $'],
            'movement_type': ['MoM', 'MoM'],
            'percentage_change': [50.0, 15.0],  # High percentage vs low percentage
            'absolute_change': [1000, 10000],   # Low absolute vs high absolute
            'current_period': ['2022-02', '2022-02'],
            'previous_period': ['2022-01', '2022-01'],
            'current_amount': [3000, 20000],
            'previous_amount': [2000, 10000]
        })
        
        result, _ = apply_movement_thresholds(movements_data, mom_threshold=10.0)
        
        self.assertEqual(len(result), 2)
        self.assertIn('materiality_score', result.columns)
        self.assertIn('abs_score', result.columns)
        
        # Both should have materiality scores that reflect the combination
        self.assertTrue(all(result['materiality_score'] > 0))
    
    def test_data_type_handling(self):
        """Test handling of different data types in input."""
        # Test with string dates
        string_date_data = pd.DataFrame({
            'date': ['2022-01-01', '2022-02-01', '2022-03-01'],
            'account': ['Test', 'Test', 'Test'],
            'amount': ['1000', '1100', '1200']  # String amounts
        })
        
        result, stats = calculate_monthly_summaries(string_date_data)
        
        # Should handle string dates and amounts
        self.assertTrue(stats['success'])
        self.assertIsNotNone(result)


if __name__ == '__main__':
    # Run tests with detailed output
    unittest.main(verbosity=2)