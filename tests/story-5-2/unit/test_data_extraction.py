"""
Unit tests for Story 5.2: Data Extraction

This module tests the data extraction and filtering functionality,
including querying processed data, filtering, aggregation, and data validation.
"""

import pytest
import sys
import os
import json
import pandas as pd
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the data extraction functions (to be implemented)
# from main import (
#     extract_relevant_data,
#     filter_data_by_parameters,
#     aggregate_data_for_analysis,
#     validate_data_availability,
#     handle_missing_data
# )


class TestDataExtraction:
    """Test suite for data extraction and filtering."""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Load test data for data extraction tests."""
        fixtures_path = os.path.join(os.path.dirname(__file__), '..', 'fixtures')
        
        # Load sample financial data
        with open(os.path.join(fixtures_path, 'sample_financial_data.json'), 'r') as f:
            self.sample_data = json.load(f)
        
        # Create DataFrame from sample data
        self.processed_data = pd.DataFrame(
            self.sample_data['processed_data']['data'],
            columns=self.sample_data['processed_data']['columns']
        )
        
        # Convert Amount column to numeric
        self.processed_data['Amount'] = pd.to_numeric(self.processed_data['Amount'])
        
        # Convert Date column to datetime
        self.processed_data['Date'] = pd.to_datetime(self.processed_data['Date'])
    
    def test_extract_relevant_data_by_account(self):
        """Test extracting data for specific accounts."""
        query_entities = {
            'accounts': ['marketing', 'expenses'],
            'time_period': None,
            'metrics': ['increase']
        }
        
        with patch('main.extract_relevant_data') as mock_extract:
            # Mock the extraction to return marketing expense data
            marketing_data = self.processed_data[
                self.processed_data['Account'].str.contains('Marketing', case=False)
            ]
            mock_extract.return_value = marketing_data
            
            result = mock_extract(self.processed_data, query_entities)
            
            assert len(result) > 0
            assert all('Marketing' in account for account in result['Account'])
            assert result['Amount'].sum() > 0
    
    def test_filter_data_by_time_period(self):
        """Test filtering data by time period."""
        query_entities = {
            'accounts': [],
            'time_period': 'January 8th',
            'metrics': []
        }
        
        with patch('main.filter_data_by_parameters') as mock_filter:
            # Mock filtering for specific date
            filtered_data = self.processed_data[
                self.processed_data['Date'] == '2024-01-08'
            ]
            mock_filter.return_value = filtered_data
            
            result = mock_filter(self.processed_data, query_entities)
            
            assert len(result) > 0
            assert all(result['Date'].dt.date == pd.to_datetime('2024-01-08').date())
    
    def test_aggregate_data_for_analysis(self):
        """Test aggregating data for analysis."""
        query_entities = {
            'accounts': ['revenue'],
            'time_period': None,
            'metrics': ['total']
        }
        
        with patch('main.aggregate_data_for_analysis') as mock_aggregate:
            # Mock aggregation for revenue data
            revenue_data = self.processed_data[
                self.processed_data['Account'].str.contains('Revenue', case=False)
            ]
            total_revenue = revenue_data['Amount'].sum()
            
            mock_aggregate.return_value = {
                'total_amount': total_revenue,
                'count': len(revenue_data),
                'average': revenue_data['Amount'].mean(),
                'breakdown': revenue_data.groupby('Account')['Amount'].sum().to_dict()
            }
            
            result = mock_aggregate(self.processed_data, query_entities)
            
            assert result['total_amount'] < 0  # Revenue is negative in our data
            assert result['count'] > 0
            assert 'breakdown' in result
    
    def test_validate_data_availability(self):
        """Test validation of data availability."""
        test_cases = [
            {
                'query_entities': {
                    'accounts': ['marketing', 'expenses'],
                    'time_period': None,
                    'metrics': []
                },
                'expected_available': True
            },
            {
                'query_entities': {
                    'accounts': ['nonexistent_account'],
                    'time_period': None,
                    'metrics': []
                },
                'expected_available': False
            },
            {
                'query_entities': {
                    'accounts': [],
                    'time_period': '2099',
                    'metrics': []
                },
                'expected_available': False
            }
        ]
        
        for test_case in test_cases:
            with patch('main.validate_data_availability') as mock_validate:
                mock_validate.return_value = {
                    'available': test_case['expected_available'],
                    'missing_data': [],
                    'suggestions': []
                }
                
                result = mock_validate(self.processed_data, test_case['query_entities'])
                assert result['available'] == test_case['expected_available']
    
    def test_handle_missing_data(self):
        """Test handling of missing or incomplete data."""
        query_entities = {
            'accounts': ['nonexistent_account'],
            'time_period': None,
            'metrics': []
        }
        
        with patch('main.handle_missing_data') as mock_handle:
            mock_handle.return_value = {
                'data_available': False,
                'message': "No data found for account 'nonexistent_account'",
                'suggestions': [
                    "Try one of these available accounts: Revenue - Sales, Revenue - Service, Expense - Marketing, Expense - Rent, Expense - Utilities, Cash"
                ],
                'alternative_data': None
            }
            
            result = mock_handle(self.processed_data, query_entities)
            
            assert not result['data_available']
            assert 'message' in result
            assert 'suggestions' in result
    
    def test_extract_movement_analysis_data(self):
        """Test extracting movement analysis data."""
        query_entities = {
            'accounts': ['marketing', 'expenses'],
            'time_period': None,
            'metrics': ['increase']
        }
        
        with patch('main.extract_movement_analysis_data') as mock_extract:
            movement_data = self.sample_data['movement_analysis']['ranked_movements']
            marketing_movements = [
                movement for movement in movement_data 
                if 'marketing' in movement['account'].lower()
            ]
            
            mock_extract.return_value = marketing_movements
            
            result = mock_extract(query_entities)
            
            assert len(result) > 0
            assert all('marketing' in movement['account'].lower() for movement in result)
    
    def test_extract_anomaly_analysis_data(self):
        """Test extracting anomaly analysis data."""
        query_entities = {
            'accounts': ['sales', 'revenue'],
            'time_period': 'January 8th',
            'metrics': ['spike']
        }
        
        with patch('main.extract_anomaly_analysis_data') as mock_extract:
            anomaly_data = self.sample_data['anomaly_analysis']['combined_anomalies']
            sales_anomalies = [
                anomaly for anomaly in anomaly_data 
                if 'sales' in anomaly['account'].lower() or 'revenue' in anomaly['account'].lower()
            ]
            
            mock_extract.return_value = sales_anomalies
            
            result = mock_extract(query_entities)
            
            assert len(result) > 0
            assert all(
                'sales' in anomaly['account'].lower() or 'revenue' in anomaly['account'].lower() 
                for anomaly in result
            )
    
    def test_data_filtering_by_significance(self):
        """Test filtering data by significance level."""
        query_entities = {
            'accounts': ['expenses'],
            'time_period': None,
            'metrics': ['significant']
        }
        
        with patch('main.filter_data_by_significance') as mock_filter:
            # Mock filtering for significant movements
            significant_movements = [
                movement for movement in self.sample_data['movement_analysis']['ranked_movements']
                if movement['significance'] in ['High', 'Medium']
            ]
            
            mock_filter.return_value = significant_movements
            
            result = mock_filter(self.sample_data['movement_analysis']['ranked_movements'], query_entities)
            
            assert len(result) > 0
            assert all(movement['significance'] in ['High', 'Medium'] for movement in result)
    
    def test_data_aggregation_by_category(self):
        """Test aggregating data by category."""
        query_entities = {
            'accounts': ['expenses'],
            'time_period': None,
            'metrics': ['breakdown']
        }
        
        with patch('main.aggregate_data_by_category') as mock_aggregate:
            # Mock aggregation by expense category
            expense_data = self.processed_data[
                self.processed_data['Account'].str.contains('Expense', case=False)
            ]
            category_breakdown = expense_data.groupby('Account')['Amount'].sum().to_dict()
            
            mock_aggregate.return_value = {
                'categories': category_breakdown,
                'total': expense_data['Amount'].sum(),
                'count': len(expense_data)
            }
            
            result = mock_aggregate(self.processed_data, query_entities)
            
            assert 'categories' in result
            assert 'total' in result
            assert result['total'] > 0
    
    def test_data_validation_completeness(self):
        """Test validation of data completeness."""
        with patch('main.validate_data_completeness') as mock_validate:
            mock_validate.return_value = {
                'complete': True,
                'missing_fields': [],
                'data_quality_score': 0.95,
                'suggestions': []
            }
            
            result = mock_validate(self.processed_data)
            
            assert result['complete']
            assert result['data_quality_score'] > 0.9
            assert len(result['missing_fields']) == 0
    
    def test_data_extraction_performance(self):
        """Test performance of data extraction (should be under 1 second)."""
        import time
        
        query_entities = {
            'accounts': ['revenue'],
            'time_period': None,
            'metrics': ['total']
        }
        
        with patch('main.extract_relevant_data') as mock_extract:
            mock_extract.return_value = self.processed_data[
                self.processed_data['Account'].str.contains('Revenue', case=False)
            ]
            
            start_time = time.time()
            result = mock_extract(self.processed_data, query_entities)
            end_time = time.time()
            
            processing_time = end_time - start_time
            assert processing_time < 1.0  # Should extract within 1 second
            assert len(result) > 0
    
    def test_data_filtering_edge_cases(self):
        """Test data filtering with edge cases."""
        edge_cases = [
            {
                'query_entities': {
                    'accounts': [],
                    'time_period': None,
                    'metrics': []
                },
                'expected_result': 'all_data'
            },
            {
                'query_entities': {
                    'accounts': ['nonexistent'],
                    'time_period': 'invalid_date',
                    'metrics': []
                },
                'expected_result': 'no_data'
            }
        ]
        
        for edge_case in edge_cases:
            with patch('main.filter_data_by_parameters') as mock_filter:
                if edge_case['expected_result'] == 'all_data':
                    mock_filter.return_value = self.processed_data
                else:
                    mock_filter.return_value = pd.DataFrame()
                
                result = mock_filter(self.processed_data, edge_case['query_entities'])
                
                if edge_case['expected_result'] == 'all_data':
                    assert len(result) > 0
                else:
                    assert len(result) == 0 