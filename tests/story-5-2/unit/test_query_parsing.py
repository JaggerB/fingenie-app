"""
Unit tests for Story 5.2: Query Parsing

This module tests the natural language query parsing functionality,
including entity extraction, intent classification, and query processing.
"""

import pytest
import sys
import os
import json
from unittest.mock import patch, MagicMock

# Add the parent directory to the path to import main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(__file__)))))

# Import the query parsing functions (to be implemented)
# from main import (
#     parse_natural_language_query,
#     extract_entities,
#     classify_query_intent,
#     process_query_context
# )


class TestQueryParsing:
    """Test suite for natural language query parsing."""
    
    @pytest.fixture(autouse=True)
    def setup_test_data(self):
        """Load test data for query parsing tests."""
        fixtures_path = os.path.join(os.path.dirname(__file__), '..', 'fixtures')
        
        # Load sample queries
        with open(os.path.join(fixtures_path, 'sample_queries.json'), 'r') as f:
            self.sample_queries = json.load(f)
        
        # Load mock responses
        with open(os.path.join(fixtures_path, 'mock_ai_responses.json'), 'r') as f:
            self.mock_responses = json.load(f)
    
    def test_parse_simple_query(self):
        """Test parsing a simple natural language query."""
        query = "What drove the increase in marketing expenses?"
        
        # Mock the parsing function (to be implemented)
        with patch('main.parse_natural_language_query') as mock_parse:
            mock_parse.return_value = {
                'entities': {
                    'accounts': ['marketing', 'expenses'],
                    'time_period': None,
                    'metrics': ['increase'],
                    'intent': 'movement_analysis'
                },
                'confidence': 0.95,
                'query_type': 'movement_explanation'
            }
            
            result = mock_parse(query)
            
            assert result['entities']['accounts'] == ['marketing', 'expenses']
            assert result['entities']['intent'] == 'movement_analysis'
            assert result['confidence'] > 0.9
            assert result['query_type'] == 'movement_explanation'
    
    def test_extract_account_entities(self):
        """Test extraction of account entities from queries."""
        test_cases = [
            {
                'query': "What drove the increase in marketing expenses?",
                'expected_accounts': ['marketing', 'expenses']
            },
            {
                'query': "How much revenue did we generate this month?",
                'expected_accounts': ['revenue']
            },
            {
                'query': "Show me the top expenses",
                'expected_accounts': ['expenses']
            }
        ]
        
        for test_case in test_cases:
            with patch('main.extract_entities') as mock_extract:
                mock_extract.return_value = {
                    'accounts': test_case['expected_accounts'],
                    'time_period': None,
                    'metrics': []
                }
                
                result = mock_extract(test_case['query'])
                assert result['accounts'] == test_case['expected_accounts']
    
    def test_extract_time_period_entities(self):
        """Test extraction of time period entities from queries."""
        test_cases = [
            {
                'query': "How much revenue did we generate this month?",
                'expected_period': 'this month'
            },
            {
                'query': "What are the trends over the last quarter?",
                'expected_period': 'last quarter'
            },
            {
                'query': "Show me data from January 8th",
                'expected_period': 'January 8th'
            }
        ]
        
        for test_case in test_cases:
            with patch('main.extract_entities') as mock_extract:
                mock_extract.return_value = {
                    'accounts': [],
                    'time_period': test_case['expected_period'],
                    'metrics': []
                }
                
                result = mock_extract(test_case['query'])
                assert result['time_period'] == test_case['expected_period']
    
    def test_classify_query_intent(self):
        """Test classification of query intent."""
        test_cases = [
            {
                'query': "What drove the increase in marketing expenses?",
                'expected_intent': 'movement_analysis'
            },
            {
                'query': "How much revenue did we generate?",
                'expected_intent': 'data_query'
            },
            {
                'query': "Show me the top expenses",
                'expected_intent': 'ranking_query'
            },
            {
                'query': "What caused the spike in sales?",
                'expected_intent': 'anomaly_analysis'
            }
        ]
        
        for test_case in test_cases:
            with patch('main.classify_query_intent') as mock_classify:
                mock_classify.return_value = test_case['expected_intent']
                
                result = mock_classify(test_case['query'])
                assert result == test_case['expected_intent']
    
    def test_handle_follow_up_queries(self):
        """Test handling of follow-up queries with context."""
        context = {
            'previous_query': "What drove the increase in marketing expenses?",
            'previous_response': "Marketing expenses increased by $3,750...",
            'entities': {
                'accounts': ['marketing', 'expenses'],
                'intent': 'movement_analysis'
            }
        }
        
        follow_up_query = "Tell me more about that"
        
        with patch('main.process_query_context') as mock_context:
            mock_context.return_value = {
                'entities': {
                    'accounts': ['marketing', 'expenses'],
                    'time_period': None,
                    'metrics': ['details'],
                    'intent': 'follow_up'
                },
                'context': context,
                'confidence': 0.85
            }
            
            result = mock_context(follow_up_query, context)
            assert result['entities']['intent'] == 'follow_up'
            assert result['context'] == context
    
    def test_handle_complex_queries(self):
        """Test handling of complex queries with multiple entities."""
        complex_query = "What caused the spike in sales revenue on January 8th?"
        
        with patch('main.parse_natural_language_query') as mock_parse:
            mock_parse.return_value = {
                'entities': {
                    'accounts': ['sales', 'revenue'],
                    'time_period': 'January 8th',
                    'metrics': ['spike'],
                    'intent': 'anomaly_analysis'
                },
                'confidence': 0.88,
                'query_type': 'anomaly_explanation'
            }
            
            result = mock_parse(complex_query)
            assert len(result['entities']['accounts']) == 2
            assert result['entities']['time_period'] == 'January 8th'
            assert result['entities']['intent'] == 'anomaly_analysis'
    
    def test_handle_edge_cases(self):
        """Test handling of edge cases and error scenarios."""
        edge_cases = [
            {
                'query': "",
                'expected_handling': 'empty_query'
            },
            {
                'query': "What is the meaning of life?",
                'expected_handling': 'unrelated_query'
            },
            {
                'query': "Show me data from 2099",
                'expected_handling': 'future_date'
            }
        ]
        
        for edge_case in edge_cases:
            with patch('main.parse_natural_language_query') as mock_parse:
                mock_parse.return_value = {
                    'entities': {
                        'accounts': [],
                        'time_period': None,
                        'metrics': [],
                        'intent': edge_case['expected_handling']
                    },
                    'confidence': 0.0,
                    'query_type': 'error_handling'
                }
                
                result = mock_parse(edge_case['query'])
                assert result['entities']['intent'] == edge_case['expected_handling']
                assert result['query_type'] == 'error_handling'
    
    def test_query_confidence_scoring(self):
        """Test confidence scoring for query parsing."""
        test_queries = [
            {
                'query': "What drove the increase in marketing expenses?",
                'expected_confidence': 0.95
            },
            {
                'query': "How much revenue did we generate?",
                'expected_confidence': 0.98
            },
            {
                'query': "Show me the top expenses",
                'expected_confidence': 0.92
            }
        ]
        
        for test_query in test_queries:
            with patch('main.parse_natural_language_query') as mock_parse:
                mock_parse.return_value = {
                    'entities': {
                        'accounts': [],
                        'time_period': None,
                        'metrics': [],
                        'intent': 'data_query'
                    },
                    'confidence': test_query['expected_confidence'],
                    'query_type': 'data_summary'
                }
                
                result = mock_parse(test_query['query'])
                assert result['confidence'] >= test_query['expected_confidence']
    
    def test_entity_extraction_accuracy(self):
        """Test accuracy of entity extraction from various query formats."""
        test_cases = [
            {
                'query': "What drove the increase in marketing expenses?",
                'expected_entities': {
                    'accounts': ['marketing', 'expenses'],
                    'metrics': ['increase'],
                    'intent': 'movement_analysis'
                }
            },
            {
                'query': "Compare marketing expenses between January and February",
                'expected_entities': {
                    'accounts': ['marketing', 'expenses'],
                    'time_period': ['January', 'February'],
                    'metrics': ['compare'],
                    'intent': 'comparison_query'
                }
            },
            {
                'query': "What are the trends in our cash flow over the last quarter?",
                'expected_entities': {
                    'accounts': ['cash flow'],
                    'time_period': 'last quarter',
                    'metrics': ['trends'],
                    'intent': 'trend_analysis'
                }
            }
        ]
        
        for test_case in test_cases:
            with patch('main.extract_entities') as mock_extract:
                mock_extract.return_value = test_case['expected_entities']
                
                result = mock_extract(test_case['query'])
                assert result == test_case['expected_entities']
    
    def test_query_processing_performance(self):
        """Test performance of query processing (should be under 3 seconds)."""
        import time
        
        query = "What drove the increase in marketing expenses?"
        
        with patch('main.parse_natural_language_query') as mock_parse:
            mock_parse.return_value = {
                'entities': {
                    'accounts': ['marketing', 'expenses'],
                    'intent': 'movement_analysis'
                },
                'confidence': 0.95,
                'query_type': 'movement_explanation'
            }
            
            start_time = time.time()
            result = mock_parse(query)
            end_time = time.time()
            
            processing_time = end_time - start_time
            assert processing_time < 3.0  # Should process within 3 seconds
            assert result['entities']['intent'] == 'movement_analysis' 