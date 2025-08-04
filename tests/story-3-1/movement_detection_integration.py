"""
Integration tests for Story 3.1: Movement Detection Engine
Tests the complete movement detection workflow with real data scenarios.

This integration test verifies:
1. End-to-end movement detection pipeline
2. Integration with data processing from Epic 2
3. Session state management
4. UI data flow and results persistence
5. Real-world data scenarios and edge cases
"""

import unittest
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import sys
import os

# Add the parent directory to the path to import main module
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from main import (
    run_movement_detection_engine,
    process_data_pipeline,
    detect_column_mappings,
    validate_data_structure
)


class TestMovementDetectionIntegration(unittest.TestCase):
    """Integration tests for movement detection engine with realistic data scenarios."""
    
    def setUp(self):
        """Set up realistic financial data scenarios for integration testing."""
        
        # Scenario 1: Real P&L data with significant movements
        self.pnl_data = pd.DataFrame({
            'Date': [
                '2023-01-31', '2023-02-28', '2023-03-31', '2023-04-30', '2023-05-31', '2023-06-30',
                '2023-07-31', '2023-08-31', '2023-09-30', '2023-10-31', '2023-11-30', '2023-12-31',
                '2024-01-31', '2024-02-29', '2024-03-31', '2024-04-30', '2024-05-31', '2024-06-30'
            ],
            'Account': [
                'Sales Revenue', 'Sales Revenue', 'Sales Revenue', 'Sales Revenue', 'Sales Revenue', 'Sales Revenue',
                'Sales Revenue', 'Sales Revenue', 'Sales Revenue', 'Sales Revenue', 'Sales Revenue', 'Sales Revenue',
                'Sales Revenue', 'Sales Revenue', 'Sales Revenue', 'Sales Revenue', 'Sales Revenue', 'Sales Revenue'
            ],
            'Amount': [
                500000, 520000, 580000, 600000, 650000, 700000,
                750000, 780000, 820000, 850000, 900000, 950000,
                550000, 620000, 680000, 720000, 800000, 850000  # YoY increases
            ]
        })
        
        # Add expense data with significant movements
        expense_data = pd.DataFrame({
            'Date': [
                '2023-01-31', '2023-02-28', '2023-03-31', '2023-04-30', '2023-05-31', '2023-06-30',
                '2023-07-31', '2023-08-31', '2023-09-30', '2023-10-31', '2023-11-30', '2023-12-31',
                '2024-01-31', '2024-02-29', '2024-03-31', '2024-04-30', '2024-05-31', '2024-06-30'
            ],
            'Account': [
                'Marketing Expense', 'Marketing Expense', 'Marketing Expense', 'Marketing Expense', 'Marketing Expense', 'Marketing Expense',
                'Marketing Expense', 'Marketing Expense', 'Marketing Expense', 'Marketing Expense', 'Marketing Expense', 'Marketing Expense',
                'Marketing Expense', 'Marketing Expense', 'Marketing Expense', 'Marketing Expense', 'Marketing Expense', 'Marketing Expense'
            ],
            'Amount': [
                -50000, -52000, -48000, -55000, -60000, -65000,
                -70000, -75000, -80000, -120000, -130000, -140000,  # Big jump in Oct-Dec
                -60000, -65000, -58000, -70000, -80000, -90000  # Higher than prior year
            ]
        })
        
        # Combine revenue and expense data
        self.pnl_data = pd.concat([self.pnl_data, expense_data], ignore_index=True)
        
        # Scenario 2: Financial statement with new accounts
        self.new_account_data = pd.DataFrame({
            'Date': [
                '2023-10-31', '2023-11-30', '2023-12-31',  # New account starting Oct 2023
                '2024-01-31', '2024-02-29', '2024-03-31'
            ],
            'Account': [
                'New Product Line', 'New Product Line', 'New Product Line',
                'New Product Line', 'New Product Line', 'New Product Line'
            ],
            'Amount': [
                25000, 30000, 35000, 40000, 45000, 50000
            ]
        })
        
        # Scenario 3: Discontinued account data
        self.discontinued_data = pd.DataFrame({
            'Date': [
                '2023-01-31', '2023-02-28', '2023-03-31', '2023-04-30',  # Account active until Apr
                '2024-01-31', '2024-02-29', '2024-03-31', '2024-04-30'   # Different account same periods
            ],
            'Account': [
                'Old Product Line', 'Old Product Line', 'Old Product Line', 'Old Product Line',
                'Continuing Product', 'Continuing Product', 'Continuing Product', 'Continuing Product'
            ],
            'Amount': [
                15000, 18000, 20000, 22000,
                25000, 28000, 30000, 32000
            ]
        })
        
        # Combine all scenarios for comprehensive test
        self.comprehensive_data = pd.concat([
            self.pnl_data, 
            self.new_account_data, 
            self.discontinued_data
        ], ignore_index=True)
        
        # Scenario 4: Edge case data (zeros, negatives, extreme values)
        self.edge_case_data = pd.DataFrame({
            'Date': [
                '2023-01-31', '2023-02-28', '2023-03-31',
                '2023-01-31', '2023-02-28', '2023-03-31',
                '2023-01-31', '2023-02-28', '2023-03-31'
            ],
            'Account': [
                'Zero Account', 'Zero Account', 'Zero Account',
                'Extreme Growth', 'Extreme Growth', 'Extreme Growth',
                'Volatile Account', 'Volatile Account', 'Volatile Account'
            ],
            'Amount': [
                0, 0, 1000,  # Goes from 0 to 1000 (should handle division by zero)
                1000, 50000, 100000,  # Extreme growth
                10000, -5000, 15000  # Volatile swings
            ]
        })
    
    def test_complete_movement_detection_workflow(self):
        """Test the complete movement detection workflow from raw data to insights."""
        
        # Step 1: Validate that data processing pipeline integration works
        column_mappings = detect_column_mappings(self.comprehensive_data)
        self.assertIsNotNone(column_mappings['date'])
        self.assertIsNotNone(column_mappings['account'])
        self.assertIsNotNone(column_mappings['amount'])
        
        # Step 2: Process data through the pipeline (simulating Epic 2 completion)
        processed_df, processing_results, quality_summary = process_data_pipeline(
            self.comprehensive_data, column_mappings
        )
        
        self.assertIsNotNone(processed_df)
        self.assertTrue(processing_results['missing_values']['success'])
        self.assertGreater(quality_summary['data_quality_score'], 50)  # Should have decent quality
        
        # Step 3: Run movement detection engine
        movement_results = run_movement_detection_engine(processed_df)
        
        # Verify successful execution
        self.assertTrue(movement_results['success'])
        self.assertEqual(len(movement_results['errors']), 0)
        
        # Step 4: Verify all components were created
        self.assertIsNotNone(movement_results['monthly_summary'])
        self.assertIsNotNone(movement_results['mom_movements'])
        self.assertIsNotNone(movement_results['yoy_movements'])
        
        # Step 5: Verify significant movements were detected
        if movement_results['significant_movements'] is not None:
            significant_movements = movement_results['significant_movements']
            self.assertGreater(len(significant_movements), 0)
            
            # Should have both MoM and YoY movements
            movement_types = significant_movements['movement_type'].unique()
            self.assertIn('MoM', movement_types)
            
            # Should have significance levels assigned
            self.assertIn('significance', significant_movements.columns)
            significance_levels = significant_movements['significance'].unique()
            self.assertTrue(any(level in ['Medium', 'High', 'Critical'] for level in significance_levels))
        
        # Step 6: Verify account flags were detected
        account_flags = movement_results['account_flags']
        self.assertIsInstance(account_flags, list)
        
        # Should detect new accounts
        flag_types = [flag['flag_type'] for flag in account_flags] if account_flags else []
        self.assertIn('New', flag_types)  # New Product Line should be flagged
    
    def test_yoy_movement_detection_accuracy(self):
        """Test that year-over-year movements are accurately detected and calculated."""
        
        # Create specific YoY test data
        yoy_test_data = pd.DataFrame({
            'Date': [
                '2023-01-31', '2023-02-28', '2023-03-31',
                '2024-01-31', '2024-02-29', '2024-03-31'
            ],
            'Account': [
                'YoY Test', 'YoY Test', 'YoY Test',
                'YoY Test', 'YoY Test', 'YoY Test'
            ],
            'Amount': [
                100000, 110000, 120000,  # 2023 values
                120000, 143000, 150000   # 2024 values: 20%, 30%, 25% increases
            ]
        })
        
        movement_results = run_movement_detection_engine(yoy_test_data)
        
        self.assertTrue(movement_results['success'])
        
        # Check YoY movements specifically
        yoy_movements = movement_results['yoy_movements']
        self.assertIsNotNone(yoy_movements)
        self.assertGreater(len(yoy_movements), 0)
        
        # Verify percentage calculations
        for _, movement in yoy_movements.iterrows():
            self.assertEqual(movement['movement_type'], 'YoY')
            self.assertGreater(abs(movement['percentage_change']), 15)  # Should exceed YoY threshold
        
        # Check that significant movements were flagged
        significant_movements = movement_results['significant_movements']
        if significant_movements is not None:
            yoy_significant = significant_movements[significant_movements['movement_type'] == 'YoY']
            self.assertGreater(len(yoy_significant), 0)
    
    def test_mom_movement_detection_accuracy(self):
        """Test that month-over-month movements are accurately detected."""
        
        # Create MoM test data with clear movements
        mom_test_data = pd.DataFrame({
            'Date': [
                '2024-01-31', '2024-02-29', '2024-03-31', '2024-04-30'
            ],
            'Account': [
                'MoM Test', 'MoM Test', 'MoM Test', 'MoM Test'
            ],
            'Amount': [
                100000, 85000, 120000, 95000  # -15%, +41%, -21% changes
            ]
        })
        
        movement_results = run_movement_detection_engine(mom_test_data)
        
        self.assertTrue(movement_results['success'])
        
        # Check MoM movements
        mom_movements = movement_results['mom_movements']
        self.assertIsNotNone(mom_movements)
        self.assertGreater(len(mom_movements), 0)
        
        # Should detect 3 movements (Feb vs Jan, Mar vs Feb, Apr vs Mar)
        self.assertEqual(len(mom_movements), 3)
        
        # Verify significant movements above 10% threshold
        significant_movements = movement_results['significant_movements']
        if significant_movements is not None:
            mom_significant = significant_movements[significant_movements['movement_type'] == 'MoM']
            # All 3 movements should be above 10% threshold
            self.assertEqual(len(mom_significant), 3)
    
    def test_edge_cases_handling(self):
        """Test handling of edge cases like zero values, extreme changes, etc."""
        
        movement_results = run_movement_detection_engine(self.edge_case_data)
        
        # Should handle edge cases gracefully
        self.assertTrue(movement_results['success'])
        self.assertEqual(len(movement_results['errors']), 0)
        
        # Should not crash on division by zero
        mom_movements = movement_results['mom_movements']
        if mom_movements is not None and len(mom_movements) > 0:
            # Check that percentage changes are finite (not NaN or infinite)
            self.assertTrue(all(np.isfinite(mom_movements['percentage_change'])))
            self.assertTrue(all(np.isfinite(mom_movements['absolute_change'])))
    
    def test_materiality_ranking_integration(self):
        """Test that materiality ranking works correctly in the integrated system."""
        
        movement_results = run_movement_detection_engine(self.comprehensive_data)
        
        self.assertTrue(movement_results['success'])
        
        ranked_movements = movement_results['ranked_movements']
        if ranked_movements is not None and len(ranked_movements) > 0:
            # Check ranking is applied
            self.assertIn('rank', ranked_movements.columns)
            self.assertIn('materiality_score', ranked_movements.columns)
            
            # Verify ranking order (highest materiality score should be rank 1)
            self.assertEqual(ranked_movements.iloc[0]['rank'], 1)
            
            # Verify scores are descending
            scores = ranked_movements['materiality_score'].tolist()
            self.assertEqual(scores, sorted(scores, reverse=True))
            
            # Should have ranking statistics
            ranking_stats = movement_results['summary_stats']['ranking']
            self.assertTrue(ranking_stats['success'])
            self.assertEqual(ranking_stats['total_movements'], len(ranked_movements))
    
    def test_session_state_data_structure(self):
        """Test that movement detection results are properly structured for session state storage."""
        
        movement_results = run_movement_detection_engine(self.comprehensive_data)
        
        # Verify all required keys are present for UI integration
        required_keys = [
            'success', 'monthly_summary', 'mom_movements', 'yoy_movements',
            'significant_movements', 'account_flags', 'ranked_movements', 'summary_stats'
        ]
        
        for key in required_keys:
            self.assertIn(key, movement_results)
        
        # Verify summary stats structure
        summary_stats = movement_results['summary_stats']
        expected_stat_keys = ['monthly_summary', 'mom_movements', 'yoy_movements']
        
        for key in expected_stat_keys:
            if key in summary_stats:
                self.assertIn('success', summary_stats[key])
    
    def test_performance_with_large_dataset(self):
        """Test performance and stability with larger datasets."""
        
        # Generate larger dataset (simulate 2 years of daily data for 20 accounts)
        dates = pd.date_range(start='2023-01-01', end='2024-12-31', freq='D')
        accounts = [f'Account_{i:02d}' for i in range(1, 21)]
        
        large_data = []
        for account in accounts:
            for date in dates:
                # Generate realistic amounts with some variation
                base_amount = np.random.normal(10000, 2000)
                large_data.append({
                    'Date': date.strftime('%Y-%m-%d'),
                    'Account': account,
                    'Amount': max(0, base_amount)  # Ensure positive amounts
                })
        
        large_df = pd.DataFrame(large_data)
        
        # Should handle large datasets without errors
        movement_results = run_movement_detection_engine(large_df)
        
        self.assertTrue(movement_results['success'])
        self.assertEqual(len(movement_results['errors']), 0)
        
        # Should process all accounts
        monthly_stats = movement_results['summary_stats']['monthly_summary']
        self.assertEqual(monthly_stats['accounts_processed'], 20)
    
    def test_data_validation_integration(self):
        """Test integration with data validation from Epic 2."""
        
        # Test with various data formats that should be handled by the pipeline
        test_cases = [
            # Case 1: Different date formats
            pd.DataFrame({
                'Date': ['01/31/2023', '02/28/2023', '03/31/2023'],
                'Account': ['Test', 'Test', 'Test'],
                'Amount': [1000, 1100, 1200]
            }),
            
            # Case 2: Different amount formats
            pd.DataFrame({
                'Date': ['2023-01-31', '2023-02-28', '2023-03-31'],
                'Account': ['Test', 'Test', 'Test'],
                'Amount': ['$1,000.00', '$1,100.00', '$1,200.00']
            }),
            
            # Case 3: Mixed case account names
            pd.DataFrame({
                'Date': ['2023-01-31', '2023-02-28', '2023-03-31'],
                'Account': ['test account', 'TEST ACCOUNT', 'Test Account'],
                'Amount': [1000, 1100, 1200]
            })
        ]
        
        for i, test_data in enumerate(test_cases):
            with self.subTest(case=i):
                # Should be handled by data processing pipeline
                column_mappings = detect_column_mappings(test_data)
                processed_df, _, _ = process_data_pipeline(test_data, column_mappings)
                
                # Movement detection should work on processed data
                movement_results = run_movement_detection_engine(processed_df)
                self.assertTrue(movement_results['success'], f"Failed on test case {i}")


class TestMovementDetectionManualE2E(unittest.TestCase):
    """Manual E2E test scenarios as specified in the story requirements."""
    
    def setUp(self):
        """Set up data for manual E2E test scenarios."""
        
        # Multiple months dataset
        self.multi_month_data = pd.DataFrame({
            'Date': [
                '2023-01-31', '2023-02-28', '2023-03-31', '2023-04-30',
                '2023-05-31', '2023-06-30', '2023-07-31', '2023-08-31'
            ],
            'Account': ['Sales'] * 8,
            'Amount': [100000, 85000, 120000, 95000, 110000, 140000, 130000, 160000]
        })
        
        # Multi-year dataset
        self.multi_year_data = pd.DataFrame({
            'Date': [
                '2022-01-31', '2022-02-28', '2022-03-31',
                '2023-01-31', '2023-02-28', '2023-03-31',
                '2024-01-31', '2024-02-29', '2024-03-31'
            ],
            'Account': ['Revenue'] * 9,
            'Amount': [100000, 110000, 120000, 120000, 140000, 150000, 150000, 180000, 200000]
        })
        
        # Dataset with new accounts
        self.new_account_data = pd.DataFrame({
            'Date': [
                '2023-10-31', '2023-11-30', '2023-12-31',
                '2024-01-31', '2024-02-29', '2024-03-31'
            ],
            'Account': ['Existing Product'] * 3 + ['New Product Launch'] * 3,
            'Amount': [50000, 52000, 55000, 0, 10000, 25000]
        })
        
        # Dataset missing historical data
        self.limited_history_data = pd.DataFrame({
            'Date': ['2024-02-29', '2024-03-31'],
            'Account': ['Limited History Account'] * 2,
            'Amount': [75000, 82000]
        })
    
    def test_manual_e2e_mom_detection(self):
        """Manual E2E Test: Upload dataset with multiple months and verify MoM detection."""
        
        movement_results = run_movement_detection_engine(self.multi_month_data)
        
        # Should successfully detect MoM movements
        self.assertTrue(movement_results['success'])
        
        mom_movements = movement_results['mom_movements']
        self.assertIsNotNone(mom_movements)
        self.assertGreater(len(mom_movements), 0)
        
        # Should have 7 MoM comparisons (8 months - 1)
        self.assertEqual(len(mom_movements), 7)
        
        # Verify significant movements are detected (changes > 10%)
        significant_movements = movement_results['significant_movements']
        if significant_movements is not None:
            mom_significant = significant_movements[significant_movements['movement_type'] == 'MoM']
            # Should detect several significant MoM changes
            self.assertGreater(len(mom_significant), 3)
    
    def test_manual_e2e_yoy_detection(self):
        """Manual E2E Test: Upload dataset spanning multiple years and verify YoY detection."""
        
        movement_results = run_movement_detection_engine(self.multi_year_data)
        
        # Should successfully process multi-year data
        self.assertTrue(movement_results['success'])
        
        yoy_movements = movement_results['yoy_movements']
        self.assertIsNotNone(yoy_movements)
        
        # Should detect YoY movements
        if len(yoy_movements) > 0:
            # All movements should be YoY type
            self.assertTrue(all(yoy_movements['movement_type'] == 'YoY'))
            
            # Should have meaningful percentage changes
            significant_yoy = yoy_movements[abs(yoy_movements['percentage_change']) >= 15]
            self.assertGreater(len(significant_yoy), 0)
    
    def test_manual_e2e_new_account_flagging(self):
        """Manual E2E Test: Dataset with new accounts and verify flagging."""
        
        movement_results = run_movement_detection_engine(self.new_account_data)
        
        self.assertTrue(movement_results['success'])
        
        # Should detect account flags
        account_flags = movement_results['account_flags']
        self.assertIsInstance(account_flags, list)
        self.assertGreater(len(account_flags), 0)
        
        # Should flag new account
        flag_types = [flag['flag_type'] for flag in account_flags]
        flagged_accounts = [flag['account'] for flag in account_flags]
        
        # New Product Launch should be flagged as new
        self.assertIn('New Product Launch', flagged_accounts)
    
    def test_manual_e2e_missing_historical_data(self):
        """Manual E2E Test: Dataset missing historical data and verify graceful handling."""
        
        movement_results = run_movement_detection_engine(self.limited_history_data)
        
        # Should handle limited data gracefully
        self.assertTrue(movement_results['success'])
        
        # Should flag insufficient history
        account_flags = movement_results['account_flags']
        flag_types = [flag['flag_type'] for flag in account_flags] if account_flags else []
        
        # Should identify insufficient history
        self.assertIn('Insufficient History', flag_types)
    
    def test_manual_e2e_movement_ranking_priority(self):
        """Manual E2E Test: Verify movement ranking prioritizes most significant changes."""
        
        # Create data with clearly different significance levels
        test_data = pd.DataFrame({
            'Date': [
                '2024-01-31', '2024-02-29', '2024-03-31',
                '2024-01-31', '2024-02-29', '2024-03-31',
                '2024-01-31', '2024-02-29', '2024-03-31'
            ],
            'Account': [
                'High Impact', 'High Impact', 'High Impact',
                'Medium Impact', 'Medium Impact', 'Medium Impact',
                'Low Impact', 'Low Impact', 'Low Impact'
            ],
            'Amount': [
                100000, 150000, 200000,  # 50% and 33% increases
                50000, 60000, 70000,     # 20% and 17% increases  
                10000, 11000, 12000      # 10% and 9% increases
            ]
        })
        
        movement_results = run_movement_detection_engine(test_data)
        
        self.assertTrue(movement_results['success'])
        
        ranked_movements = movement_results['ranked_movements']
        if ranked_movements is not None and len(ranked_movements) > 0:
            # Top ranked movement should have highest materiality score
            top_movement = ranked_movements.iloc[0]
            self.assertEqual(top_movement['rank'], 1)
            
            # Should prioritize high impact movements
            self.assertEqual(top_movement['account'], 'High Impact')
            
            # Verify ranking descends by materiality score
            scores = ranked_movements['materiality_score'].tolist()
            self.assertEqual(scores, sorted(scores, reverse=True))


if __name__ == '__main__':
    # Set up test suite
    loader = unittest.TestLoader()
    suite = unittest.TestSuite()
    
    # Add test classes
    suite.addTests(loader.loadTestsFromTestCase(TestMovementDetectionIntegration))
    suite.addTests(loader.loadTestsFromTestCase(TestMovementDetectionManualE2E))
    
    # Run tests with detailed output
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    
    # Print summary
    print(f"\n{'='*60}")
    print(f"INTEGRATION TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Tests run: {result.testsRun}")
    print(f"Failures: {len(result.failures)}")
    print(f"Errors: {len(result.errors)}")
    print(f"Success rate: {((result.testsRun - len(result.failures) - len(result.errors)) / result.testsRun * 100):.1f}%")
    
    if result.failures:
        print(f"\nFAILURES:")
        for test, traceback in result.failures:
            print(f"- {test}")
    
    if result.errors:
        print(f"\nERRORS:")
        for test, traceback in result.errors:
            print(f"- {test}")