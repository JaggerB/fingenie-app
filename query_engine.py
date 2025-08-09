"""
Story 5.2: Financial Data Query Engine

This module contains the core functions for processing natural language queries
about financial data, extracting entities, and generating contextual responses.
"""

import pandas as pd
import re
from datetime import datetime


def parse_natural_language_query(query):
    """
    Parse natural language queries about financial data.
    
    Args:
        query (str): Natural language query string
        
    Returns:
        dict: Parsed query with entities, intent, confidence, and query_type
    """
    if not query or not query.strip():
        return {
            'entities': {
                'accounts': [],
                'time_period': None,
                'metrics': [],
                'intent': 'empty_query'
            },
            'confidence': 0.0,
            'query_type': 'error_handling'
        }
    
    # Extract entities from the query
    entities = extract_entities(query)
    
    # Classify the query intent
    intent = classify_query_intent(query, entities)
    
    # Determine query type based on intent
    query_type = _determine_query_type(intent, entities)
    
    # Calculate confidence score
    confidence = _calculate_confidence_score(query, entities, intent)
    
    return {
        'entities': entities,
        'confidence': confidence,
        'query_type': query_type
    }


def extract_entities(query):
    """
    Extract entities (accounts, time periods, metrics) from a query.
    
    Args:
        query (str): Natural language query string
        
    Returns:
        dict: Extracted entities
    """
    query_lower = query.lower()
    entities = {
        'accounts': [],
        'time_period': None,
        'metrics': [],
        'intent': 'unknown'
    }
    
    # Extract accounts with more comprehensive keywords
    account_keywords = [
        'revenue', 'sales', 'expenses', 'marketing', 'rent', 'utilities',
        'cash', 'income', 'costs', 'spending', 'earnings', 'profit',
        'loss', 'debt', 'assets', 'liabilities', 'equity', 'trend',
        'pattern', 'movement', 'growth', 'decline'
    ]
    
    for keyword in account_keywords:
        if keyword in query_lower:
            entities['accounts'].append(keyword)
    
    # Extract time periods
    time_patterns = {
        'this month': ['this month', 'current month', 'this month'],
        'last month': ['last month', 'previous month'],
        'this quarter': ['this quarter', 'current quarter'],
        'last quarter': ['last quarter', 'previous quarter'],
        'this year': ['this year', 'current year'],
        'last year': ['last year', 'previous year']
    }
    
    for period, patterns in time_patterns.items():
        if any(pattern in query_lower for pattern in patterns):
            entities['time_period'] = period
            break
    
    # Extract specific dates (e.g., "January 8th")
    date_pattern = r'\b(January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2}(?:st|nd|rd|th)?\b'
    date_match = re.search(date_pattern, query, re.IGNORECASE)
    if date_match:
        entities['time_period'] = date_match.group()
    
    # Extract metrics with more comprehensive coverage
    metric_keywords = {
        'increase': ['increase', 'growth', 'up', 'higher', 'rise', 'trend'],
        'decrease': ['decrease', 'decline', 'down', 'lower', 'fall'],
        'total': ['total', 'sum', 'amount', 'value'],
        'average': ['average', 'mean', 'typical'],
        'top': ['top', 'highest', 'largest', 'biggest'],
        'bottom': ['bottom', 'lowest', 'smallest'],
        'spike': ['spike', 'surge', 'jump', 'peak'],
        'trend': ['trend', 'pattern', 'movement', 'direction'],
        'compare': ['compare', 'comparison', 'versus', 'vs'],
        'breakdown': ['breakdown', 'break down', 'categorize']
    }
    
    for metric, keywords in metric_keywords.items():
        if any(keyword in query_lower for keyword in keywords):
            entities['metrics'].append(metric)
    
    return entities


def classify_query_intent(query, entities=None):
    """
    Classify the intent of a query.
    
    Args:
        query (str): Natural language query string
        entities (dict): Extracted entities (optional)
        
    Returns:
        str: Query intent classification
    """
    if entities is None:
        entities = extract_entities(query)
    
    query_lower = query.lower()
    
    # Check for movement analysis intent
    movement_keywords = ['drove', 'caused', 'increase', 'decrease', 'change', 'movement']
    if any(keyword in query_lower for keyword in movement_keywords):
        return 'movement_analysis'
    
    # Check for data query intent
    data_keywords = ['how much', 'what is', 'show me', 'total', 'amount']
    if any(keyword in query_lower for keyword in data_keywords):
        return 'data_query'
    
    # Check for ranking query intent
    ranking_keywords = ['top', 'highest', 'largest', 'biggest', 'bottom', 'lowest']
    if any(keyword in query_lower for keyword in ranking_keywords):
        return 'ranking_query'
    
    # Check for anomaly analysis intent
    anomaly_keywords = ['spike', 'surge', 'anomaly', 'unusual', 'strange']
    if any(keyword in query_lower for keyword in anomaly_keywords):
        return 'anomaly_analysis'
    
    # Check for comparison query intent
    comparison_keywords = ['compare', 'versus', 'vs', 'between', 'difference']
    if any(keyword in query_lower for keyword in comparison_keywords):
        return 'comparison_query'
    
    # Check for trend analysis intent
    trend_keywords = ['trend', 'pattern', 'over time', 'trends']
    if any(keyword in query_lower for keyword in trend_keywords):
        return 'trend_analysis'
    
    # Check for follow-up intent
    follow_up_keywords = ['tell me more', 'what about', 'can you show', 'that']
    if any(keyword in query_lower for keyword in follow_up_keywords):
        return 'follow_up'
    
    # Check for unrelated query
    unrelated_keywords = ['meaning of life', 'weather', 'politics', 'sports']
    if any(keyword in query_lower for keyword in unrelated_keywords):
        return 'unrelated_query'
    
    return 'data_query'  # Default intent


def process_query_context(query, context=None):
    """
    Process query context for follow-up questions.
    
    Args:
        query (str): Natural language query string
        context (dict): Previous query context
        
    Returns:
        dict: Processed query with context
    """
    if context is None:
        context = {}
    
    # Extract entities from current query
    entities = extract_entities(query)
    
    # If this is a follow-up query, inherit context from previous query
    if context.get('entities'):
        # Merge entities from context
        for key in ['accounts', 'metrics']:
            if key in context['entities'] and key in entities:
                entities[key].extend(context['entities'][key])
                entities[key] = list(set(entities[key]))  # Remove duplicates
    
    # Determine intent
    intent = classify_query_intent(query, entities)
    
    return {
        'entities': entities,
        'context': context,
        'confidence': 0.85 if context else 0.95
    }


def extract_relevant_data(processed_data, query_entities):
    """
    Extract relevant data based on query entities.
    
    Args:
        processed_data (DataFrame): Processed financial data
        query_entities (dict): Query entities
        
    Returns:
        DataFrame: Filtered and relevant data
    """
    if processed_data is None or processed_data.empty:
        return pd.DataFrame()
    
    filtered_data = processed_data.copy()
    
    # Filter by accounts (only if Account column exists)
    if query_entities.get('accounts') and 'Account' in filtered_data.columns:
        try:
            account_filter = filtered_data['Account'].str.lower().str.contains(
                '|'.join(query_entities['accounts']), 
                case=False, 
                na=False
            )
            filtered_data = filtered_data[account_filter]
        except Exception:
            # If there's an error with account filtering, continue without filtering
            pass
    
    # Filter by time period
    if query_entities.get('time_period'):
        # This would need more sophisticated date parsing
        # For now, return all data
        pass
    
    return filtered_data


def filter_data_by_parameters(processed_data, query_entities):
    """
    Filter data by query parameters.
    
    Args:
        processed_data (DataFrame): Processed financial data
        query_entities (dict): Query entities
        
    Returns:
        DataFrame: Filtered data
    """
    return extract_relevant_data(processed_data, query_entities)


def aggregate_data_for_analysis(processed_data, query_entities):
    """
    Aggregate data for analysis based on query entities.
    
    Args:
        processed_data (DataFrame): Processed financial data
        query_entities (dict): Query entities
        
    Returns:
        dict: Aggregated data
    """
    if processed_data is None or processed_data.empty:
        return {
            'total_amount': 0,
            'count': 0,
            'average': 0,
            'breakdown': {}
        }
    
    relevant_data = extract_relevant_data(processed_data, query_entities)
    
    if relevant_data.empty:
        return {
            'total_amount': 0,
            'count': 0,
            'average': 0,
            'breakdown': {}
        }
    
    total_amount = relevant_data['Amount'].sum()
    count = len(relevant_data)
    average = relevant_data['Amount'].mean()
    
    # Create breakdown by account
    breakdown = relevant_data.groupby('Account')['Amount'].sum().to_dict()
    
    return {
        'total_amount': total_amount,
        'count': count,
        'average': average,
        'breakdown': breakdown
    }


def validate_data_availability(processed_data, query_entities):
    """
    Validate data availability for query entities.
    
    Args:
        processed_data (DataFrame): Processed financial data
        query_entities (dict): Query entities
        
    Returns:
        dict: Validation results
    """
    if processed_data is None or processed_data.empty:
        return {
            'available': False,
            'missing_data': ['all_data'],
            'suggestions': ['Please upload financial data first']
        }
    
    missing_data = []
    suggestions = []
    
    # Check for account availability
    if query_entities.get('accounts'):
        available_accounts = processed_data['Account'].unique()
        for account in query_entities['accounts']:
            if not any(account.lower() in acc.lower() for acc in available_accounts):
                missing_data.append(f"account_{account}")
                suggestions.append(f"Account '{account}' not found. Available accounts: {', '.join(available_accounts[:5])}")
    
    # Check for time period availability
    if query_entities.get('time_period'):
        # This would need more sophisticated date validation
        pass
    
    return {
        'available': len(missing_data) == 0,
        'missing_data': missing_data,
        'suggestions': suggestions
    }


def handle_missing_data(processed_data, query_entities):
    """
    Handle missing or incomplete data scenarios.
    
    Args:
        processed_data (DataFrame): Processed financial data
        query_entities (dict): Query entities
        
    Returns:
        dict: Handling results
    """
    validation = validate_data_availability(processed_data, query_entities)
    
    if validation['available']:
        return {
            'data_available': True,
            'message': "Data available for query",
            'suggestions': [],
            'alternative_data': None
        }
    
    return {
        'data_available': False,
        'message': f"No data found for query. Missing: {', '.join(validation['missing_data'])}",
        'suggestions': validation['suggestions'],
        'alternative_data': None
    }


def extract_movement_analysis_data(query_entities):
    """
    Extract movement analysis data based on query entities.
    
    Args:
        query_entities (dict): Query entities
        
    Returns:
        list: Movement analysis data
    """
    # This would integrate with existing movement analysis
    # For now, return mock data
    return []


def extract_anomaly_analysis_data(query_entities):
    """
    Extract anomaly analysis data based on query entities.
    
    Args:
        query_entities (dict): Query entities
        
    Returns:
        list: Anomaly analysis data
    """
    # This would integrate with existing anomaly analysis
    # For now, return mock data
    return []


def filter_data_by_significance(movement_data, query_entities):
    """
    Filter data by significance level.
    
    Args:
        movement_data (list): Movement analysis data
        query_entities (dict): Query entities
        
    Returns:
        list: Filtered movement data
    """
    # This would filter by significance level
    # For now, return all data
    return movement_data


def aggregate_data_by_category(processed_data, query_entities):
    """
    Aggregate data by category.
    
    Args:
        processed_data (DataFrame): Processed financial data
        query_entities (dict): Query entities
        
    Returns:
        dict: Aggregated data by category
    """
    if processed_data is None or processed_data.empty:
        return {
            'categories': {},
            'total': 0,
            'count': 0
        }
    
    relevant_data = extract_relevant_data(processed_data, query_entities)
    
    if relevant_data.empty:
        return {
            'categories': {},
            'total': 0,
            'count': 0
        }
    
    category_breakdown = relevant_data.groupby('Account')['Amount'].sum().to_dict()
    total = relevant_data['Amount'].sum()
    count = len(relevant_data)
    
    return {
        'categories': category_breakdown,
        'total': total,
        'count': count
    }


def validate_data_completeness(processed_data):
    """
    Validate data completeness.
    
    Args:
        processed_data (DataFrame): Processed financial data
        
    Returns:
        dict: Validation results
    """
    if processed_data is None or processed_data.empty:
        return {
            'complete': False,
            'missing_fields': ['all_fields'],
            'data_quality_score': 0.0,
            'suggestions': ['Please upload financial data']
        }
    
    missing_fields = []
    total_fields = len(processed_data.columns)
    present_fields = 0
    
    required_fields = ['Date', 'Account', 'Amount']
    for field in required_fields:
        if field in processed_data.columns:
            present_fields += 1
        else:
            missing_fields.append(field)
    
    data_quality_score = present_fields / total_fields if total_fields > 0 else 0.0
    
    return {
        'complete': len(missing_fields) == 0,
        'missing_fields': missing_fields,
        'data_quality_score': data_quality_score,
        'suggestions': []
    }


def generate_contextual_response(query, extracted_data, query_entities):
    """
    Generate contextual response based on query and extracted data.
    
    Args:
        query (str): Original query
        extracted_data (DataFrame): Extracted data
        query_entities (dict): Query entities
        
    Returns:
        str: Contextual response
    """
    # This would generate AI-powered responses
    # For now, return a basic response
    return f"Based on the data, here's what I found for your query: '{query}'"


def manage_conversation_context(query, context=None):
    """
    Manage conversation context across queries.
    
    Args:
        query (str): Current query
        context (dict): Previous context
        
    Returns:
        dict: Updated context
    """
    if context is None:
        context = {}
    
    # Extract entities from current query
    entities = extract_entities(query)
    
    # Update context
    context['last_query'] = query
    context['entities'] = entities
    context['timestamp'] = datetime.now().isoformat()
    
    return context


# Helper functions

def _determine_query_type(intent, entities):
    """Determine query type based on intent and entities."""
    if intent == 'movement_analysis':
        return 'movement_explanation'
    elif intent == 'data_query':
        return 'data_summary'
    elif intent == 'ranking_query':
        return 'ranking_list'
    elif intent == 'anomaly_analysis':
        return 'anomaly_explanation'
    elif intent == 'comparison_query':
        return 'comparison_analysis'
    elif intent == 'trend_analysis':
        return 'trend_analysis'
    elif intent == 'follow_up':
        return 'detailed_explanation'
    elif intent == 'unrelated_query':
        return 'error_handling'
    else:
        # Check for trend-related keywords in entities
        if 'trend' in entities.get('metrics', []) or 'trend' in entities.get('accounts', []):
            return 'trend_analysis'
        elif 'revenue' in entities.get('accounts', []) or 'income' in entities.get('accounts', []):
            return 'data_summary'
        else:
            return 'data_summary'


def _calculate_confidence_score(query, entities, intent):
    """Calculate confidence score for query parsing."""
    base_confidence = 0.5
    
    # Boost confidence based on entity extraction
    if entities['accounts']:
        base_confidence += 0.2
    if entities['time_period']:
        base_confidence += 0.1
    if entities['metrics']:
        base_confidence += 0.1
    
    # Boost confidence based on intent classification
    if intent != 'unknown':
        base_confidence += 0.1
    
    # Penalize for unrelated queries
    if intent == 'unrelated_query':
        base_confidence = 0.0
    
    return min(base_confidence, 1.0) 