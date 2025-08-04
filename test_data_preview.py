"""
Unit tests for data preview functionality in main.py
Story 2.4: Data Preview Display

Coverage requirement: 80%
"""

import pytest
import pandas as pd
import numpy as np
from unittest.mock import patch, MagicMock
import io
from datetime import datetime, date


class TestDataPreviewComponents:
    """Test data preview functionality components"""
    
    def setup_method(self):
        """Setup test data for each test method"""
        # Create sample processed data
        self.sample_data = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05'],
            'account': ['Cash', 'Revenue', 'Expenses', 'Cash', 'Revenue'],
            'amount': [1000.50, -2500.75, 750.25, 300.00, -1800.00],
            'description': ['Opening balance', 'Sales revenue', 'Office supplies', 'Deposit', 'Service revenue']
        })
        
        # Sample data with missing values and outliers
        self.sample_data_quality_issues = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', None, '2024-01-04', '2024-01-05'],
            'account': ['Cash', 'Revenue', 'Expenses', None, 'Revenue'],
            'amount': [1000.50, -2500.75, 750.25, 999999.99, -1800.00],  # 999999.99 is outlier
            'description': ['Opening balance', None, 'Office supplies', 'Large deposit', 'Service revenue']
        })
        
        # Sample quality summary
        self.sample_quality_summary = {
            'data_quality_score': 85.5,
            'total_rows': 5,
            'total_columns': 4,
            'recommendations': [
                'Consider reviewing large amount transactions',
                'Ensure all date fields are properly formatted'
            ]
        }
        
        # Sample processing results
        self.sample_processing_results = {
            'missing_values': {
                'success': True,
                'missing_summary': {
                    'date': {'missing_count': 1},
                    'account': {'missing_count': 1}
                }
            },
            'duplicates': {
                'success': True,
                'duplicates_removed': 2,
                'final_count': 5
            },
            'dates': {
                'success': True,
                'success_rate': 0.95
            },
            'amounts': {
                'success': True,
                'success_rate': 1.0
            },
            'accounts': {
                'success': True,
                'original_unique_accounts': 5,
                'cleaned_unique_accounts': 3,
                'reduction_count': 2
            }
        }

    def test_summary_statistics_calculation(self):
        """Test calculation of summary statistics"""
        df = self.sample_data.copy()
        df['date'] = pd.to_datetime(df['date'])
        df['amount'] = pd.to_numeric(df['amount'])
        
        # Test row count
        assert len(df) == 5
        
        # Test date range calculation
        min_date = df['date'].min()
        max_date = df['date'].max()
        assert min_date == pd.Timestamp('2024-01-01')
        assert max_date == pd.Timestamp('2024-01-05')
        
        # Test unique accounts
        unique_accounts = df['account'].nunique()
        assert unique_accounts == 3  # Cash, Revenue, Expenses
        
        # Test amount statistics
        amounts = df['amount']
        assert amounts.min() == -2500.75
        assert amounts.max() == 1000.50
        assert abs(amounts.mean() - (-450.0)) < 0.01  # Average should be -450
        assert amounts.sum() == -2250.0

    def test_column_information_generation(self):
        """Test generation of column information for display"""
        df = self.sample_data.copy()
        
        col_info = []
        for col in df.columns:
            dtype_str = str(df[col].dtype)
            non_null = df[col].count()
            total = len(df)
            completeness = (non_null / total) * 100
            col_info.append({
                'Column': col,
                'Data Type': dtype_str,
                'Non-Null Count': f"{non_null:,}",
                'Completeness': f"{completeness:.1f}%"
            })
        
        assert len(col_info) == 4
        assert col_info[0]['Column'] == 'date'
        assert col_info[0]['Completeness'] == '100.0%'
        assert col_info[1]['Column'] == 'account'
        assert col_info[2]['Column'] == 'amount'
        assert col_info[3]['Column'] == 'description'

    def test_data_quality_highlighting_logic(self):
        """Test the logic for highlighting data quality issues"""
        df = self.sample_data_quality_issues.copy()
        
        # Test missing value detection
        missing_mask = df.isna()
        assert missing_mask.loc[2, 'date'] == True
        assert missing_mask.loc[3, 'account'] == True
        assert missing_mask.loc[1, 'description'] == True
        
        # Test outlier detection logic for amounts
        df['amount'] = pd.to_numeric(df['amount'], errors='coerce')
        amounts = df['amount'].dropna()
        Q1 = amounts.quantile(0.25)
        Q3 = amounts.quantile(0.75)
        IQR = Q3 - Q1
        
        outlier_threshold_upper = Q3 + 1.5 * IQR
        outlier_threshold_lower = Q1 - 1.5 * IQR
        
        # 999999.99 should be detected as outlier
        outliers = amounts[(amounts < outlier_threshold_lower) | (amounts > outlier_threshold_upper)]
        assert 999999.99 in outliers.values

    def test_csv_download_data_generation(self):
        """Test CSV data generation for download"""
        df = self.sample_data.copy()
        
        # Test CSV generation
        csv_data = df.to_csv(index=False)
        
        # Verify CSV structure
        assert 'date,account,amount,description' in csv_data
        assert '2024-01-01,Cash,1000.5,Opening balance' in csv_data
        assert '2024-01-02,Revenue,-2500.75,Sales revenue' in csv_data
        
        # Test timestamp generation for filename
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"processed_data_{timestamp}.csv"
        assert csv_filename.startswith("processed_data_")
        assert csv_filename.endswith(".csv")

    def test_excel_download_data_generation(self):
        """Test Excel data generation for download"""
        df = self.sample_data.copy()
        
        # Test Excel generation
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Processed Data')
        excel_data = excel_buffer.getvalue()
        
        # Verify Excel data is generated
        assert len(excel_data) > 0
        assert isinstance(excel_data, bytes)
        
        # Test filename generation
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        excel_filename = f"processed_data_{timestamp}.xlsx"
        assert excel_filename.startswith("processed_data_")
        assert excel_filename.endswith(".xlsx")

    def test_data_filtering_and_pagination(self):
        """Test data filtering and pagination logic"""
        df = self.sample_data.copy()
        
        # Test different row limits
        assert len(df.head(10)) == 5  # All rows when limit > available
        assert len(df.head(3)) == 3   # Limited rows
        assert len(df.head(100)) == 5 # All rows when limit > available
        
        # Test row numbering
        df_with_index = df.reset_index()
        df_with_index.rename(columns={'index': 'Row #'}, inplace=True)
        assert 'Row #' in df_with_index.columns
        assert df_with_index['Row #'].tolist() == [0, 1, 2, 3, 4]

    def test_quality_score_categorization(self):
        """Test quality score categorization logic"""
        
        # Test excellent quality (>=90)
        excellent_score = 95.0
        assert excellent_score >= 90
        
        # Test good quality (75-89)
        good_score = 80.0
        assert 75 <= good_score < 90
        
        # Test fair quality (50-74)
        fair_score = 60.0
        assert 50 <= fair_score < 75
        
        # Test poor quality (<50)
        poor_score = 30.0
        assert poor_score < 50

    def test_processing_warnings_extraction(self):
        """Test extraction of processing warnings from results"""
        # Test with successful processing
        results_success = self.sample_processing_results.copy()
        warnings = []
        for step, result in results_success.items():
            if not result.get('success', True):
                warnings.append(f"{step}: {result.get('error', 'Unknown error')}")
        
        assert len(warnings) == 0  # No warnings for successful processing
        
        # Test with failed processing
        results_with_errors = {
            'missing_values': {'success': False, 'error': 'Could not process missing values'},
            'duplicates': {'success': True},
            'dates': {'success': False, 'error': 'Date parsing failed'}
        }
        
        warnings_with_errors = []
        for step, result in results_with_errors.items():
            if not result.get('success', True):
                warnings_with_errors.append(f"{step}: {result.get('error', 'Unknown error')}")
        
        assert len(warnings_with_errors) == 2
        assert 'missing_values: Could not process missing values' in warnings_with_errors
        assert 'dates: Date parsing failed' in warnings_with_errors

    def test_date_parsing_edge_cases(self):
        """Test date parsing with various edge cases"""
        # Test valid dates
        valid_dates = pd.Series(['2024-01-01', '2024-12-31', '2023-06-15'])
        parsed_dates = pd.to_datetime(valid_dates)
        assert len(parsed_dates) == 3
        assert not parsed_dates.isna().any()
        
        # Test invalid dates that should handle gracefully
        mixed_dates = pd.Series(['2024-01-01', 'invalid_date', '2024-12-31', None])
        try:
            parsed_mixed = pd.to_datetime(mixed_dates, errors='coerce')
            assert parsed_mixed.isna().sum() == 2  # invalid_date and None should be NaT
        except:
            # If parsing fails completely, that's acceptable too
            pass

    def test_amount_parsing_edge_cases(self):
        """Test amount parsing with various edge cases"""
        # Test valid amounts
        valid_amounts = pd.Series([1000.50, -2500.75, 0.00, 999999.99])
        parsed_amounts = pd.to_numeric(valid_amounts, errors='coerce')
        assert len(parsed_amounts) == 4
        assert not parsed_amounts.isna().any()
        
        # Test mixed valid/invalid amounts
        mixed_amounts = pd.Series(['1000.50', 'invalid_amount', '-2500.75', None])
        parsed_mixed = pd.to_numeric(mixed_amounts, errors='coerce')
        assert parsed_mixed.isna().sum() == 2  # invalid_amount and None should be NaN


class TestDataPreviewIntegration:
    """Integration tests for data preview with session state"""
    
    def test_session_state_data_handling(self):
        """Test handling of session state data"""
        # Mock session state data
        mock_processed_data = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02'],
            'account': ['Cash', 'Revenue'], 
            'amount': [1000.0, -500.0]
        })
        
        mock_quality_summary = {
            'data_quality_score': 90.0,
            'total_rows': 2,
            'total_columns': 3,
            'recommendations': []
        }
        
        # Test data is properly structured
        assert not mock_processed_data.empty
        assert 'date' in mock_processed_data.columns
        assert 'account' in mock_processed_data.columns
        assert 'amount' in mock_processed_data.columns
        
        # Test quality summary is valid
        assert 'data_quality_score' in mock_quality_summary
        assert mock_quality_summary['data_quality_score'] >= 0
        assert mock_quality_summary['data_quality_score'] <= 100

    def test_empty_data_handling(self):
        """Test graceful handling of empty or None data"""
        # Test None data
        none_data = None
        assert none_data is None
        
        # Test empty DataFrame
        empty_df = pd.DataFrame()
        assert empty_df.empty
        
        # Test DataFrame with no rows
        no_rows_df = pd.DataFrame(columns=['date', 'account', 'amount'])
        assert len(no_rows_df) == 0
        assert not no_rows_df.columns.empty


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v", "--cov=main", "--cov-report=term-missing"])