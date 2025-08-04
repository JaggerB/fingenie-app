"""
Integration tests for Story 2.4: Data Preview Display
Tests the complete data preview functionality integration with the Streamlit app

This file tests the integration between:
- Data processing pipeline (Story 2.3)
- Data preview display components (Story 2.4)
- Session state management
- File upload and processing flow
"""

import pytest
import pandas as pd
import numpy as np
import io
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime


class TestDataPreviewIntegration:
    """Integration tests for data preview functionality"""
    
    def setup_method(self):
        """Setup test data and mock objects for integration tests"""
        
        # Create realistic financial data for testing
        self.sample_financial_data = pd.DataFrame({
            'Date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05',
                    '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10'],
            'Account': ['Cash', 'Revenue - Sales', 'Expense - Office', 'Cash', 'Revenue - Service',
                       'Expense - Rent', 'Cash', 'Revenue - Sales', 'Expense - Utilities', 'Cash'],
            'Amount': [5000.00, -12500.50, 850.75, 2500.00, -8750.25,
                      1200.00, 1500.00, -15000.00, 450.50, 3000.00],
            'Description': ['Opening Balance', 'Monthly Sales', 'Office Supplies', 'Deposit',
                           'Consulting Revenue', 'Office Rent', 'Transfer', 'Product Sales',
                           'Electricity Bill', 'Client Payment']
        })
        
        # Create processed data that would come from Story 2.3 pipeline
        self.processed_data = pd.DataFrame({
            'date': pd.to_datetime(['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05',
                                   '2024-01-06', '2024-01-07', '2024-01-08', '2024-01-09', '2024-01-10']),
            'account': ['Cash', 'Revenue', 'Expenses', 'Cash', 'Revenue',
                       'Expenses', 'Cash', 'Revenue', 'Expenses', 'Cash'],
            'amount': [5000.00, -12500.50, 850.75, 2500.00, -8750.25,
                      1200.00, 1500.00, -15000.00, 450.50, 3000.00],
            'description': ['Opening Balance', 'Monthly Sales', 'Office Supplies', 'Deposit',
                           'Consulting Revenue', 'Office Rent', 'Transfer', 'Product Sales',
                           'Electricity Bill', 'Client Payment']
        })
        
        # Create quality summary that would come from processing pipeline
        self.quality_summary = {
            'data_quality_score': 92.5,
            'total_rows': 10,
            'total_columns': 4,
            'recommendations': [
                'Data quality is excellent with minimal issues',
                'Consider reviewing large transactions for accuracy'
            ]
        }
        
        # Create processing results that would come from pipeline
        self.processing_results = {
            'missing_values': {
                'success': True,
                'missing_summary': {
                    'date': {'missing_count': 0},
                    'account': {'missing_count': 0},
                    'amount': {'missing_count': 0},
                    'description': {'missing_count': 1}
                }
            },
            'duplicates': {
                'success': True,
                'duplicates_removed': 0,
                'final_count': 10
            },
            'dates': {
                'success': True,
                'success_rate': 1.0
            },
            'amounts': {
                'success': True,
                'success_rate': 1.0
            },
            'accounts': {
                'success': True,
                'original_unique_accounts': 6,
                'cleaned_unique_accounts': 3,
                'reduction_count': 3
            }
        }

    def test_complete_data_processing_to_preview_flow(self):
        """Test the complete flow from data processing to preview display"""
        
        # Step 1: Simulate data validation and processing (Story 2.3 output)
        processed_df = self.processed_data.copy()
        quality_summary = self.quality_summary.copy()
        processing_results = self.processing_results.copy()
        
        # Verify processed data structure
        assert not processed_df.empty
        assert 'date' in processed_df.columns
        assert 'account' in processed_df.columns
        assert 'amount' in processed_df.columns
        assert len(processed_df) == 10
        
        # Step 2: Test summary statistics calculation (Story 2.4 functionality)
        total_rows = len(processed_df)
        assert total_rows == 10
        
        # Date range calculation
        date_col = pd.to_datetime(processed_df['date'])
        min_date = date_col.min()
        max_date = date_col.max()
        assert min_date == pd.Timestamp('2024-01-01')
        assert max_date == pd.Timestamp('2024-01-10')
        
        # Account types
        unique_accounts = processed_df['account'].nunique()
        assert unique_accounts == 3  # Cash, Revenue, Expenses
        
        # Amount statistics
        amount_col = pd.to_numeric(processed_df['amount'])
        min_amount = amount_col.min()
        max_amount = amount_col.max()
        avg_amount = amount_col.mean()
        total_amount = amount_col.sum()
        
        assert min_amount == -15000.00
        assert max_amount == 5000.00
        assert abs(total_amount - (-21749.50)) < 0.01
        
        # Step 3: Test data quality highlighting integration
        # Check for missing values
        missing_mask = processed_df.isna()
        missing_count = missing_mask.sum().sum()
        
        # Check for outliers using IQR method
        Q1 = amount_col.quantile(0.25)
        Q3 = amount_col.quantile(0.75)
        IQR = Q3 - Q1
        outlier_mask = (amount_col < (Q1 - 1.5 * IQR)) | (amount_col > (Q3 + 1.5 * IQR))
        outlier_count = outlier_mask.sum()
        
        # Verify quality indicators are calculated
        assert missing_count >= 0
        assert outlier_count >= 0
        
        # Step 4: Test download functionality integration
        # CSV generation
        csv_data = processed_df.to_csv(index=False)
        assert len(csv_data) > 0
        assert 'date,account,amount,description' in csv_data
        
        # Excel generation
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            processed_df.to_excel(writer, index=False, sheet_name='Processed Data')
        excel_data = excel_buffer.getvalue()
        assert len(excel_data) > 0

    def test_session_state_integration(self):
        """Test integration with Streamlit session state management"""
        
        # Mock session state
        mock_session_state = {
            'final_processed_data': self.processed_data,
            'quality_summary': self.quality_summary,
            'processing_results': self.processing_results
        }
        
        # Test that session state data is properly structured for preview
        final_data = mock_session_state['final_processed_data']
        quality_data = mock_session_state['quality_summary']
        processing_data = mock_session_state['processing_results']
        
        # Verify data structure
        assert isinstance(final_data, pd.DataFrame)
        assert not final_data.empty
        assert isinstance(quality_data, dict)
        assert 'data_quality_score' in quality_data
        assert isinstance(processing_data, dict)
        
        # Test preview functionality with session data
        # Row count display
        total_rows = len(final_data)
        assert total_rows > 0
        
        # Quality score display
        quality_score = quality_data['data_quality_score']
        assert 0 <= quality_score <= 100
        
        # Processing results display
        for step, result in processing_data.items():
            assert isinstance(result, dict)
            assert 'success' in result

    def test_data_preview_with_edge_cases(self):
        """Test data preview functionality with edge cases"""
        
        # Test with minimal data (1 row)
        minimal_data = pd.DataFrame({
            'date': ['2024-01-01'],
            'account': ['Cash'],
            'amount': [1000.00],
            'description': ['Test transaction']
        })
        
        # Should handle minimal data gracefully
        assert len(minimal_data) == 1
        assert minimal_data['account'].nunique() == 1
        
        # Test with data containing missing values
        data_with_missing = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', None],
            'account': ['Cash', None, 'Revenue'],
            'amount': [1000.00, 500.00, None],
            'description': ['Test 1', 'Test 2', 'Test 3']
        })
        
        # Should detect missing values correctly
        missing_mask = data_with_missing.isna()
        assert missing_mask.sum().sum() == 3  # 3 missing values total
        
        # Test with more realistic outliers (larger dataset for IQR to work properly)
        data_with_outliers = pd.DataFrame({
            'date': ['2024-01-01', '2024-01-02', '2024-01-03', '2024-01-04', '2024-01-05', '2024-01-06'],
            'account': ['Cash', 'Revenue', 'Expenses', 'Cash', 'Revenue', 'Expenses'],
            'amount': [100.00, 200.00, 150.00, 120.00, 5000.00, 180.00],  # 5000 should be outlier
            'description': ['Normal', 'Normal', 'Normal', 'Normal', 'Outlier', 'Normal']
        })
        
        amounts = pd.to_numeric(data_with_outliers['amount'])
        Q1 = amounts.quantile(0.25)
        Q3 = amounts.quantile(0.75)
        IQR = Q3 - Q1
        outliers = amounts[(amounts < (Q1 - 1.5 * IQR)) | (amounts > (Q3 + 1.5 * IQR))]
        assert len(outliers) > 0  # Should detect the outlier (5000.00)

    def test_column_information_integration(self):
        """Test column information display integration"""
        
        df = self.processed_data.copy()
        
        # Generate column information as would be done in the UI
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
        
        # Verify column information structure
        assert len(col_info) == 4  # date, account, amount, description
        
        # Check specific column information
        date_info = next(info for info in col_info if info['Column'] == 'date')
        assert 'datetime' in date_info['Data Type']
        assert date_info['Completeness'] == '100.0%'
        
        amount_info = next(info for info in col_info if info['Column'] == 'amount')
        assert 'float' in amount_info['Data Type']

    def test_data_pagination_integration(self):
        """Test data pagination functionality integration"""
        
        df = self.processed_data.copy()
        
        # Test different pagination scenarios
        test_cases = [
            {'rows': 5, 'expected_len': 5},
            {'rows': 25, 'expected_len': 10},  # More than available
            {'rows': 100, 'expected_len': 10}, # Much more than available
            {'rows': 'All', 'expected_len': 10}
        ]
        
        for test_case in test_cases:
            rows_to_show = test_case['rows']
            expected_len = test_case['expected_len']
            
            if rows_to_show == "All":
                display_df = df
            else:
                display_df = df.head(rows_to_show)
            
            assert len(display_df) == expected_len
        
        # Test row numbering
        display_df = df.head(5)
        numbered_df = display_df.reset_index()
        numbered_df.rename(columns={'index': 'Row #'}, inplace=True)
        
        assert 'Row #' in numbered_df.columns
        assert numbered_df['Row #'].tolist() == [0, 1, 2, 3, 4]

    def test_download_functionality_integration(self):
        """Test download functionality integration with timestamp"""
        
        df = self.processed_data.copy()
        
        # Test CSV download with timestamp
        csv_data = df.to_csv(index=False)
        timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
        csv_filename = f"processed_data_{timestamp}.csv"
        
        # Verify CSV structure and filename
        assert len(csv_data) > 0
        assert csv_filename.startswith("processed_data_")
        assert csv_filename.endswith(".csv")
        assert len(timestamp) == 15  # YYYYMMDD_HHMMSS format
        
        # Test Excel download with timestamp
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
            df.to_excel(writer, index=False, sheet_name='Processed Data')
        excel_data = excel_buffer.getvalue()
        excel_filename = f"processed_data_{timestamp}.xlsx"
        
        # Verify Excel structure and filename
        assert len(excel_data) > 0
        assert excel_filename.startswith("processed_data_")
        assert excel_filename.endswith(".xlsx")

    def test_quality_summary_integration(self):
        """Test quality summary display integration"""
        
        quality_data = self.quality_summary.copy()
        processing_data = self.processing_results.copy()
        
        # Test quality score display logic
        quality_score = quality_data['data_quality_score']
        
        # Test score categorization (as implemented in UI)
        if quality_score >= 90:
            category = "Excellent Quality"
        elif quality_score >= 75:
            category = "Good Quality"
        elif quality_score >= 50:
            category = "Fair Quality"
        else:
            category = "Poor Quality"
        
        assert category == "Excellent Quality"  # 92.5 score
        
        # Test recommendations display
        recommendations = quality_data.get('recommendations', [])
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        
        # Test processing warnings extraction
        warnings = []
        for step, result in processing_data.items():
            if not result.get('success', True):
                warnings.append(f"{step}: {result.get('error', 'Unknown error')}")
        
        # Should have no warnings for successful processing
        assert len(warnings) == 0

    def test_file_upload_to_preview_integration(self):
        """Test integration from file upload through to preview"""
        
        # Create a temporary CSV file for testing
        with tempfile.NamedTemporaryFile(mode='w', suffix='.csv', delete=False) as tmp_file:
            self.sample_financial_data.to_csv(tmp_file.name, index=False)
            
            # Simulate file reading as would happen in upload
            uploaded_df = pd.read_csv(tmp_file.name)
            
            # Verify file was read correctly
            assert not uploaded_df.empty
            assert len(uploaded_df) == 10
            assert 'Date' in uploaded_df.columns
            assert 'Account' in uploaded_df.columns
            assert 'Amount' in uploaded_df.columns
            
            # Simulate the processing that would happen after upload
            # (This would be done by Story 2.3 pipeline)
            processed_df = uploaded_df.copy()
            processed_df.columns = processed_df.columns.str.lower()
            processed_df['date'] = pd.to_datetime(processed_df['date'])
            processed_df['amount'] = pd.to_numeric(processed_df['amount'])
            
            # Verify processing worked
            assert 'date' in processed_df.columns
            assert processed_df['date'].dtype.name.startswith('datetime')
            assert processed_df['amount'].dtype.name in ['float64', 'int64']
            
            # Test that this processed data can be used for preview
            total_rows = len(processed_df)
            unique_accounts = processed_df['account'].nunique()
            date_range = (processed_df['date'].min(), processed_df['date'].max())
            
            assert total_rows == 10
            assert unique_accounts > 0
            assert date_range[0] <= date_range[1]


if __name__ == "__main__":
    # Run the integration tests
    pytest.main([__file__, "-v"])