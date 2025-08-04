"""
FinGenie - AI-Powered Financial Assistant
Basic Streamlit App Foundation

This module provides the core Streamlit application structure with multi-tab layout
for financial data processing, insights generation, visualizations, and forecasting.
"""

import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime
import re
import os
import time
from openai import OpenAI


# OpenAI Client Configuration for Story 3.2
def get_openai_client():
    """
    Get OpenAI client with API key from environment.
    Returns None if API key is not configured.
    """
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        return None
    
    try:
        return OpenAI(api_key=api_key)
    except Exception as e:
        st.error(f"Failed to initialize OpenAI client: {str(e)}")
        return None


def call_openai_with_retry(client, messages, model="gpt-4o", max_retries=3, base_delay=1):
    """
    Call OpenAI API with exponential backoff retry logic and rate limiting.
    
    Args:
        client: OpenAI client instance
        messages: List of message objects for the API
        model: Model to use (default: gpt-4o)
        max_retries: Maximum number of retry attempts
        base_delay: Base delay for exponential backoff
    
    Returns:
        tuple: (success: bool, response: str or error_message: str)
    """
    if not client:
        return False, "OpenAI client not configured. Please set OPENAI_API_KEY environment variable."
    
    for attempt in range(max_retries + 1):
        try:
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                temperature=0.3,  # Consistent tone for financial commentary
                max_tokens=1000,  # Reasonable limit for commentary
                timeout=30  # 30 second timeout
            )
            
            if response.choices and response.choices[0].message:
                return True, response.choices[0].message.content
            else:
                return False, "No response content received from OpenAI"
                
        except Exception as e:
            error_msg = str(e)
            
            # Check for rate limiting
            if "rate_limit" in error_msg.lower() or "429" in error_msg:
                if attempt < max_retries:
                    delay = base_delay * (2 ** attempt)  # Exponential backoff
                    time.sleep(delay)
                    continue
                else:
                    return False, f"Rate limit exceeded after {max_retries} retries: {error_msg}"
            
            # Check for API errors that shouldn't be retried
            elif "invalid_api_key" in error_msg.lower() or "401" in error_msg:
                return False, f"Invalid API key: {error_msg}"
            
            # Other errors - retry if attempts remaining
            elif attempt < max_retries:
                delay = base_delay * (2 ** attempt)
                time.sleep(delay)
                continue
            else:
                return False, f"API call failed after {max_retries} retries: {error_msg}"
    
    return False, "Unexpected error in API retry logic"


def get_cached_commentary(cache_key):
    """
    Get cached commentary from session state.
    
    Args:
        cache_key: Unique identifier for the cached content
    
    Returns:
        str or None: Cached commentary if exists, None otherwise
    """
    if 'commentary_cache' not in st.session_state:
        st.session_state.commentary_cache = {}
    
    return st.session_state.commentary_cache.get(cache_key)


def cache_commentary(cache_key, commentary):
    """
    Cache commentary in session state.
    
    Args:
        cache_key: Unique identifier for the content
        commentary: Commentary text to cache
    """
    if 'commentary_cache' not in st.session_state:
        st.session_state.commentary_cache = {}
    
    st.session_state.commentary_cache[cache_key] = commentary


def create_movement_analysis_prompt(movement_data, context_data=None):
    """
    Create base prompt template for movement analysis with management pack tone.
    
    Args:
        movement_data: Dictionary containing movement details
        context_data: Optional context about account history and trends
    
    Returns:
        list: Messages for OpenAI API
    """
    # Extract movement details
    account = movement_data.get('account', 'Unknown Account')
    percentage_change = movement_data.get('percentage_change', 0)
    absolute_change = movement_data.get('absolute_change', 0)
    current_amount = movement_data.get('current_amount', 0)
    previous_amount = movement_data.get('previous_amount', 0)
    movement_type = movement_data.get('movement_type', 'MoM')
    significance = movement_data.get('significance', 'Medium')
    
    # Format currency values
    def format_currency(amount):
        return f"${amount:,.0f}" if abs(amount) >= 1000 else f"${amount:.2f}"
    
    # Build context string
    context_str = ""
    if context_data:
        context_str = f"\n\nAdditional Context:\n{context_data}"
    
    system_prompt = """You are a senior financial analyst providing executive-level commentary for monthly management reports. Your analysis should be:

- Concise and executive-ready (2-3 sentences max)
- Focused on business implications, not just numbers
- Professional tone suitable for CFO/executive review
- Include potential business drivers when appropriate
- Avoid overly technical language

Format your response as clear, actionable commentary that a finance team can present to executives."""

    user_prompt = f"""Analyze this financial movement and provide executive commentary:

Account: {account}
Movement Type: {movement_type}
Change: {percentage_change:+.1f}% ({format_currency(absolute_change)})
Current Period: {format_currency(current_amount)}
Previous Period: {format_currency(previous_amount)}
Significance Level: {significance}
{context_str}

Provide a brief executive summary explaining what changed and potential business drivers."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


def create_business_driver_prompt(movement_data, account_type=None):
    """
    Create focused prompt for business driver suggestions.
    
    Args:
        movement_data: Dictionary containing movement details
        account_type: Type of account (revenue, expense, asset, etc.)
    
    Returns:
        list: Messages for OpenAI API focusing on business drivers
    """
    account = movement_data.get('account', 'Unknown Account')
    percentage_change = movement_data.get('percentage_change', 0)
    movement_type = movement_data.get('movement_type', 'MoM')
    
    # Determine likely account type from name if not provided
    if not account_type:
        account_lower = account.lower()
        if any(term in account_lower for term in ['revenue', 'sales', 'income']):
            account_type = 'revenue'
        elif any(term in account_lower for term in ['expense', 'cost', 'operating']):
            account_type = 'expense'
        elif any(term in account_lower for term in ['asset', 'cash', 'inventory']):
            account_type = 'asset'
        elif any(term in account_lower for term in ['liability', 'payable']):
            account_type = 'liability'
        else:
            account_type = 'general'
    
    direction = "increase" if percentage_change > 0 else "decrease"
    
    system_prompt = f"""You are a financial analyst specializing in business driver analysis. Suggest 2-3 realistic business drivers that could explain a {direction} in this {account_type} account. Be specific and practical."""

    user_prompt = f"""Account: {account}
Movement: {percentage_change:+.1f}% {movement_type} {direction}

What are the most likely business drivers for this change? Focus on actionable insights for management."""

    return [
        {"role": "system", "content": system_prompt},
        {"role": "user", "content": user_prompt}
    ]


def extract_movement_data_from_session():
    """
    Extract movement data from session state (st.session_state.movement_analysis).
    
    Returns:
        dict: Movement analysis data or None if not available
    """
    if 'movement_analysis' not in st.session_state:
        return None
    
    movement_data = st.session_state.movement_analysis
    if not movement_data or not movement_data.get('success', False):
        return None
    
    return movement_data


def build_account_context_string(account_name, movement_data):
    """
    Build context strings with account history and trends.
    
    Args:
        account_name: Name of the account to analyze
        movement_data: Movement analysis data from session state
    
    Returns:
        str: Context string with account history and trends
    """
    if not movement_data:
        return ""
    
    context_parts = []
    
    # Get account flags for this account
    account_flags = movement_data.get('account_flags', [])
    account_flag = None
    for flag in account_flags:
        if flag.get('account') == account_name:
            account_flag = flag
            break
    
    if account_flag:
        flag_type = account_flag.get('flag_type', '')
        if flag_type == 'New':
            context_parts.append(f"This is a new account with limited historical data ({account_flag.get('months_active', 0)} months active).")
        elif flag_type == 'Discontinued':
            context_parts.append(f"This account shows no recent activity (last activity {account_flag.get('months_since_last', 0):.1f} months ago).")
        elif flag_type == 'Insufficient History':
            context_parts.append(f"Limited historical data available ({account_flag.get('months_active', 0)} months).")
    
    # Get summary statistics
    summary_stats = movement_data.get('summary_stats', {})
    monthly_stats = summary_stats.get('monthly_summary', {})
    if monthly_stats.get('success'):
        total_accounts = monthly_stats.get('accounts_processed', 0)
        context_parts.append(f"Analysis covers {total_accounts} accounts across {monthly_stats.get('periods_processed', 0)} time periods.")
    
    return " ".join(context_parts) if context_parts else ""


def calculate_materiality_metrics(movement_data):
    """
    Calculate materiality metrics for prompt context.
    
    Args:
        movement_data: Movement analysis data from session state
    
    Returns:
        dict: Materiality metrics and context
    """
    if not movement_data or not movement_data.get('ranked_movements') is not None:
        return {}
    
    ranked_movements = movement_data['ranked_movements']
    
    if len(ranked_movements) == 0:
        return {}
    
    # Calculate materiality context
    total_movements = len(ranked_movements)
    significance_counts = ranked_movements['significance'].value_counts().to_dict()
    
    # Get top movement score for reference
    top_score = ranked_movements.iloc[0]['materiality_score'] if len(ranked_movements) > 0 else 0
    avg_score = ranked_movements['materiality_score'].mean()
    
    return {
        'total_movements': total_movements,
        'critical_count': significance_counts.get('Critical', 0),
        'high_count': significance_counts.get('High', 0),
        'medium_count': significance_counts.get('Medium', 0),
        'low_count': significance_counts.get('Low', 0),
        'top_materiality_score': top_score,
        'avg_materiality_score': avg_score
    }


def handle_multiple_time_periods(movement_data, account_name):
    """
    Handle multiple time periods and comparison data for context.
    
    Args:
        movement_data: Movement analysis data from session state
        account_name: Name of the account to analyze
    
    Returns:
        str: Context string with time period information
    """
    if not movement_data:
        return ""
    
    context_parts = []
    
    # Check both MoM and YoY movements for this account
    mom_movements = movement_data.get('mom_movements')
    yoy_movements = movement_data.get('yoy_movements')
    
    account_mom_count = 0
    account_yoy_count = 0
    
    if mom_movements is not None:
        account_mom_count = len(mom_movements[mom_movements['account'] == account_name])
    
    if yoy_movements is not None:
        account_yoy_count = len(yoy_movements[yoy_movements['account'] == account_name])
    
    if account_mom_count > 0:
        context_parts.append(f"{account_mom_count} month-over-month movements")
    
    if account_yoy_count > 0:
        context_parts.append(f"{account_yoy_count} year-over-year movements")
    
    if context_parts:
        return f"Historical analysis shows {' and '.join(context_parts)} for this account."
    
    return ""


def format_currency_value(amount, currency_symbol="$"):
    """
    Format currency values with appropriate precision and thousands separators.
    
    Args:
        amount: Numeric amount to format
        currency_symbol: Currency symbol to use (default: $)
    
    Returns:
        str: Formatted currency string
    """
    if abs(amount) >= 1000000:
        return f"{currency_symbol}{amount/1000000:.1f}M"
    elif abs(amount) >= 1000:
        return f"{currency_symbol}{amount/1000:.0f}K"
    else:
        return f"{currency_symbol}{amount:.2f}"


def format_percentage_change(percentage):
    """
    Format percentage changes with appropriate precision and color indicators.
    
    Args:
        percentage: Percentage change value
    
    Returns:
        str: Formatted percentage string
    """
    if percentage > 0:
        return f"+{percentage:.1f}%"
    else:
        return f"{percentage:.1f}%"


def create_executive_summary_template(movement_data, commentary_text):
    """
    Create structured summary template for executive presentation.
    
    Args:
        movement_data: Dictionary containing movement details
        commentary_text: Generated commentary from GPT
    
    Returns:
        str: Formatted executive summary with markdown
    """
    account = movement_data.get('account', 'Unknown Account')
    percentage_change = movement_data.get('percentage_change', 0)
    absolute_change = movement_data.get('absolute_change', 0)
    current_amount = movement_data.get('current_amount', 0)
    movement_type = movement_data.get('movement_type', 'MoM')
    significance = movement_data.get('significance', 'Medium')
    
    # Determine significance emoji
    significance_emoji = {
        'Critical': '🚨',
        'High': '⚠️',
        'Medium': '📊',
        'Low': '📈'
    }.get(significance, '📊')
    
    # Format the summary
    summary_parts = [
        f"### {significance_emoji} {account}",
        f"**{movement_type} Change:** {format_percentage_change(percentage_change)} ({format_currency_value(absolute_change)})",
        f"**Current Value:** {format_currency_value(current_amount)}",
        f"**Significance:** {significance}",
        "",
        "**Executive Commentary:**",
        commentary_text,
        ""
    ]
    
    return "\n".join(summary_parts)


def format_commentary_for_streamlit(commentary_text, movement_data):
    """
    Add markdown formatting for Streamlit display with consistent styling.
    
    Args:
        commentary_text: Raw commentary text from GPT
        movement_data: Movement details for context
    
    Returns:
        str: Markdown-formatted commentary for Streamlit
    """
    if not commentary_text:
        return "No commentary available."
    
    # Clean up the commentary text
    cleaned_text = commentary_text.strip()
    
    # Add proper markdown formatting
    formatted_parts = [
        f"**Analysis:** {cleaned_text}",
        "",
        f"*Based on {movement_data.get('movement_type', 'MoM')} analysis with {movement_data.get('significance', 'Medium').lower()} significance.*"
    ]
    
    return "\n".join(formatted_parts)


def create_multiple_movements_summary(movements_list, commentary_dict):
    """
    Create structured summary for multiple movements with consistent formatting.
    
    Args:
        movements_list: List of movement data dictionaries
        commentary_dict: Dictionary mapping movement keys to commentary text
    
    Returns:
        str: Formatted summary for multiple movements
    """
    if not movements_list:
        return "No significant movements to report."
    
    summary_parts = [
        "## 📋 Executive Summary - Significant Financial Movements",
        "",
        f"**Total Movements Analyzed:** {len(movements_list)}",
        ""
    ]
    
    # Group by significance
    by_significance = {}
    for movement in movements_list:
        sig = movement.get('significance', 'Medium')
        if sig not in by_significance:
            by_significance[sig] = []
        by_significance[sig].append(movement)
    
    # Display in order of importance
    for significance in ['Critical', 'High', 'Medium', 'Low']:
        if significance in by_significance:
            movements = by_significance[significance]
            summary_parts.append(f"### {significance} Items ({len(movements)})")
            summary_parts.append("")
            
            for movement in movements[:3]:  # Limit to top 3 per category
                account = movement.get('account', 'Unknown')
                movement_key = f"{account}_{movement.get('movement_type', 'MoM')}"
                commentary = commentary_dict.get(movement_key, "Analysis pending...")
                
                movement_summary = create_executive_summary_template(movement, commentary)
                summary_parts.append(movement_summary)
            
            summary_parts.append("---")
            summary_parts.append("")
    
    return "\n".join(summary_parts)


def generate_fallback_commentary(movement_data, error_message=None):
    """
    Generate fallback commentary when OpenAI API fails.
    
    Args:
        movement_data: Dictionary containing movement details
        error_message: Optional error message for debugging
    
    Returns:
        str: Fallback commentary based on movement data
    """
    account = movement_data.get('account', 'Unknown Account')
    percentage_change = movement_data.get('percentage_change', 0)
    absolute_change = movement_data.get('absolute_change', 0)
    movement_type = movement_data.get('movement_type', 'MoM')
    significance = movement_data.get('significance', 'Medium')
    
    # Generate basic analysis without AI
    direction = "increased" if percentage_change > 0 else "decreased"
    magnitude = "significantly" if abs(percentage_change) > 20 else "moderately" if abs(percentage_change) > 10 else "slightly"
    
    fallback_text = f"{account} {direction} {magnitude} by {abs(percentage_change):.1f}% ({movement_type}), " \
                   f"representing a {format_currency_value(abs(absolute_change))} change. " \
                   f"This movement has been flagged as {significance.lower()} significance and warrants management review."
    
    if error_message:
        fallback_text += f"\n\n*Note: AI analysis temporarily unavailable. Basic analysis provided.*"
    
    return fallback_text


def log_api_failure(error_message, movement_data=None):
    """
    Log API failures for debugging purposes.
    
    Args:
        error_message: Error message from the API call
        movement_data: Optional movement data context
    """
    import logging
    
    # Configure logging if not already done
    logging.basicConfig(level=logging.ERROR)
    logger = logging.getLogger(__name__)
    
    log_entry = f"OpenAI API failure: {error_message}"
    if movement_data:
        account = movement_data.get('account', 'Unknown')
        log_entry += f" | Account: {account}"
    
    logger.error(log_entry)


def display_user_friendly_error(error_type="api_error"):
    """
    Display user-friendly error messages in Streamlit.
    
    Args:
        error_type: Type of error (api_error, rate_limit, invalid_key, etc.)
    """
    error_messages = {
        'api_error': "⚠️ AI commentary temporarily unavailable. Using basic analysis instead.",
        'rate_limit': "⏱️ API usage limit reached. Please try again in a few minutes.",
        'invalid_key': "🔑 OpenAI API key configuration issue. Please contact your administrator.",
        'network_error': "🌐 Network connectivity issue. Please check your internet connection.",
        'timeout': "⏰ AI analysis timed out. Using fallback commentary instead."
    }
    
    message = error_messages.get(error_type, "❌ Commentary generation encountered an error.")
    st.warning(message)


def generate_movement_commentary(movement_data, use_cache=True):
    """
    Generate AI commentary for a movement with fallback handling.
    
    Args:
        movement_data: Dictionary containing movement details
        use_cache: Whether to use cached commentary if available
    
    Returns:
        tuple: (success: bool, commentary: str)
    """
    # Create cache key
    account = movement_data.get('account', 'Unknown')
    movement_type = movement_data.get('movement_type', 'MoM')
    percentage_change = movement_data.get('percentage_change', 0)
    cache_key = f"commentary_{account}_{movement_type}_{percentage_change:.1f}"
    
    # Check cache first if enabled
    if use_cache:
        cached_commentary = get_cached_commentary(cache_key)
        if cached_commentary:
            return True, cached_commentary
    
    # Get OpenAI client
    client = get_openai_client()
    
    # Extract additional context
    movement_analysis = extract_movement_data_from_session()
    context_string = build_account_context_string(account, movement_analysis)
    time_period_context = handle_multiple_time_periods(movement_analysis, account)
    
    # Combine context
    full_context = f"{context_string} {time_period_context}".strip()
    
    # Generate prompt
    messages = create_movement_analysis_prompt(movement_data, full_context if full_context else None)
    
    # Try to get AI commentary
    success, response = call_openai_with_retry(client, messages)
    
    if success:
        # Cache the successful response
        cache_commentary(cache_key, response)
        return True, response
    else:
        # Log the failure and generate fallback
        log_api_failure(response, movement_data)
        
        # Determine error type for user display
        error_type = "api_error"
        if "rate_limit" in response.lower():
            error_type = "rate_limit"
        elif "invalid_api_key" in response.lower():
            error_type = "invalid_key"
        elif "timeout" in response.lower():
            error_type = "timeout"
        
        # Generate fallback commentary
        fallback_commentary = generate_fallback_commentary(movement_data, response)
        
        return False, fallback_commentary


def initialize_commentary_session_state():
    """
    Initialize commentary-related session state variables.
    """
    if 'generated_commentary' not in st.session_state:
        st.session_state.generated_commentary = {}
    
    if 'commentary_generation_status' not in st.session_state:
        st.session_state.commentary_generation_status = 'not_started'


def clean_and_standardize_dates(df, date_col):
    """
    Clean and standardize date column to YYYY-MM-DD format.
    """
    if date_col not in df.columns:
        return df, {'success': False, 'error': 'Date column not found'}
    
    try:
        # Create a copy to avoid modifying original
        df_copy = df.copy()
        original_count = len(df_copy)
        
        # Convert to datetime with flexible parsing
        df_copy[date_col] = pd.to_datetime(df_copy[date_col], errors='coerce')
        
        # Count how many dates were successfully parsed
        valid_dates = df_copy[date_col].notna().sum()
        invalid_dates = original_count - valid_dates
        
        # Convert to standard YYYY-MM-DD string format
        df_copy[date_col] = df_copy[date_col].dt.strftime('%Y-%m-%d')
        
        return df_copy, {
            'success': True,
            'valid_dates': valid_dates,
            'invalid_dates': invalid_dates,
            'success_rate': valid_dates / original_count if original_count > 0 else 0
        }
        
    except Exception as e:
        return df, {'success': False, 'error': f'Date processing error: {str(e)}'}


def clean_and_convert_amounts(df, amount_col):
    """
    Clean amount column and convert to numeric values.
    """
    if amount_col not in df.columns:
        return df, {'success': False, 'error': 'Amount column not found'}
    
    try:
        df_copy = df.copy()
        original_count = len(df_copy)
        
        # Clean amount values - remove currency symbols, commas, spaces
        df_copy[amount_col] = df_copy[amount_col].astype(str)
        
        # Remove common currency symbols and formatting
        df_copy[amount_col] = df_copy[amount_col].str.replace('$', '', regex=False)
        df_copy[amount_col] = df_copy[amount_col].str.replace(',', '', regex=False)
        df_copy[amount_col] = df_copy[amount_col].str.replace(' ', '', regex=False)
        df_copy[amount_col] = df_copy[amount_col].str.replace('€', '', regex=False)
        df_copy[amount_col] = df_copy[amount_col].str.replace('£', '', regex=False)
        
        # Handle parentheses for negative numbers (accounting format)
        df_copy[amount_col] = df_copy[amount_col].str.replace(r'\((.*)\)', r'-\1', regex=True)
        
        # Convert to numeric
        df_copy[amount_col] = pd.to_numeric(df_copy[amount_col], errors='coerce')
        
        # Count successful conversions
        valid_amounts = df_copy[amount_col].notna().sum()
        invalid_amounts = original_count - valid_amounts
        
        return df_copy, {
            'success': True,
            'valid_amounts': valid_amounts,
            'invalid_amounts': invalid_amounts,
            'success_rate': valid_amounts / original_count if original_count > 0 else 0
        }
        
    except Exception as e:
        return df, {'success': False, 'error': f'Amount processing error: {str(e)}'}


def standardize_account_names(df, account_col):
    """
    Clean and standardize account names for consistency.
    """
    if account_col not in df.columns:
        return df, {'success': False, 'error': 'Account column not found'}
    
    try:
        df_copy = df.copy()
        original_accounts = df_copy[account_col].unique()
        
        # Clean account names
        df_copy[account_col] = df_copy[account_col].astype(str)
        
        # Trim whitespace and normalize case
        df_copy[account_col] = df_copy[account_col].str.strip()
        df_copy[account_col] = df_copy[account_col].str.title()
        
        # Remove extra spaces
        df_copy[account_col] = df_copy[account_col].str.replace(r'\s+', ' ', regex=True)
        
        # Basic standardization rules
        standardization_rules = {
            r'\bBnk\b': 'Bank',
            r'\bAcct\b': 'Account',
            r'\bRev\b': 'Revenue',
            r'\bExp\b': 'Expense',
            r'\bInc\b': 'Income',
            r'\s&\s': ' And ',
            r'\bCorp\b': 'Corporation',
            r'\bLtd\b': 'Limited',
            r'\bCo\b': 'Company'
        }
        
        for pattern, replacement in standardization_rules.items():
            df_copy[account_col] = df_copy[account_col].str.replace(pattern, replacement, regex=True)
        
        cleaned_accounts = df_copy[account_col].unique()
        
        return df_copy, {
            'success': True,
            'original_unique_accounts': len(original_accounts),
            'cleaned_unique_accounts': len(cleaned_accounts),
            'reduction_count': len(original_accounts) - len(cleaned_accounts)
        }
        
    except Exception as e:
        return df, {'success': False, 'error': f'Account standardization error: {str(e)}'}


def handle_missing_values(df):
    """
    Handle missing values with appropriate strategies.
    """
    try:
        df_copy = df.copy()
        missing_summary = {}
        
        for col in df_copy.columns:
            missing_count = df_copy[col].isnull().sum()
            missing_summary[col] = {
                'missing_count': missing_count,
                'missing_percentage': (missing_count / len(df_copy)) * 100 if len(df_copy) > 0 else 0
            }
            
                    # Handle missing values based on column type
            if missing_count > 0:
                if col.lower() in ['date'] or 'date' in col.lower():
                    # For date columns, we'll leave NaN as is - they can be filtered out
                    pass
                elif col.lower() in ['amount', 'value', 'balance'] or any(word in col.lower() for word in ['amount', 'value', 'balance']):
                    # For amount columns, fill with 0
                    df_copy[col] = df_copy[col].fillna(0)
                else:
                    # For other columns (like account names), fill with 'Unknown'
                    df_copy[col] = df_copy[col].fillna('Unknown')
        
        return df_copy, {
            'success': True,
            'missing_summary': missing_summary
        }
        
    except Exception as e:
        return df, {'success': False, 'error': f'Missing value handling error: {str(e)}'}


def remove_duplicate_transactions(df):
    """
    Remove duplicate transactions based on all columns.
    """
    try:
        df_copy = df.copy()
        original_count = len(df_copy)
        
        # Remove exact duplicates
        df_copy = df_copy.drop_duplicates()
        
        after_removal_count = len(df_copy)
        duplicates_removed = original_count - after_removal_count
        
        return df_copy, {
            'success': True,
            'original_count': original_count,
            'final_count': after_removal_count,
            'duplicates_removed': duplicates_removed
        }
        
    except Exception as e:
        return df, {'success': False, 'error': f'Duplicate removal error: {str(e)}'}


def generate_data_quality_summary(df, processing_results):
    """
    Generate comprehensive data quality summary and metrics.
    """
    try:
        summary = {
            'total_rows': len(df),
            'total_columns': len(df.columns),
            'processing_results': processing_results,
            'data_quality_score': 0.0,
            'column_info': {},
            'recommendations': []
        }
        
        # Analyze each column
        for col in df.columns:
            col_info = {
                'data_type': str(df[col].dtype),
                'non_null_count': df[col].notna().sum(),
                'null_count': df[col].isnull().sum(),
                'completeness_rate': (df[col].notna().sum() / len(df)) * 100 if len(df) > 0 else 0
            }
            
            # Add specific info for different column types
            if col.lower() in ['date'] or 'date' in col.lower():
                if df[col].notna().sum() > 0:
                    valid_dates = pd.to_datetime(df[col], errors='coerce').notna().sum()
                    col_info['valid_dates'] = valid_dates
                    col_info['date_range'] = {
                        'earliest': str(pd.to_datetime(df[col], errors='coerce').min()) if valid_dates > 0 else None,
                        'latest': str(pd.to_datetime(df[col], errors='coerce').max()) if valid_dates > 0 else None
                    }
            
            elif pd.api.types.is_numeric_dtype(df[col]) or col.lower() in ['amount', 'value', 'balance']:
                if df[col].notna().sum() > 0:
                    numeric_col = pd.to_numeric(df[col], errors='coerce')
                    col_info['statistics'] = {
                        'min': float(numeric_col.min()) if pd.notna(numeric_col.min()) else None,
                        'max': float(numeric_col.max()) if pd.notna(numeric_col.max()) else None,
                        'mean': float(numeric_col.mean()) if pd.notna(numeric_col.mean()) else None,
                        'zero_values': (numeric_col == 0).sum()
                    }
            
            else:  # String/categorical columns
                if df[col].notna().sum() > 0:
                    col_info['unique_values'] = df[col].nunique()
                    col_info['most_common'] = df[col].value_counts().head(3).to_dict()
            
            summary['column_info'][col] = col_info
        
        # Calculate overall data quality score
        scores = []
        
        # Completeness score (average across all columns)
        completeness_scores = [info['completeness_rate'] for info in summary['column_info'].values()]
        avg_completeness = sum(completeness_scores) / len(completeness_scores) if completeness_scores else 0
        scores.append(avg_completeness)
        
        # Processing success score
        processing_success_count = sum(1 for result in processing_results.values() if result.get('success', False))
        processing_score = (processing_success_count / len(processing_results)) * 100 if processing_results else 100
        scores.append(processing_score)
        
        # Data volume score (penalize very small datasets)
        volume_score = min(100, (len(df) / 5) * 100) if len(df) > 0 else 0
        scores.append(volume_score)
        
        summary['data_quality_score'] = sum(scores) / len(scores) if scores else 0
        
        # Generate recommendations
        if avg_completeness < 90:
            summary['recommendations'].append("Consider cleaning missing values - some columns have low completeness")
        
        if len(df) < 10:
            summary['recommendations'].append("Dataset is very small - results may not be statistically significant")
        
        if processing_success_count < len(processing_results):
            summary['recommendations'].append("Some data processing steps failed - review data format")
        
        return summary
        
    except Exception as e:
        return {'error': f'Quality summary generation error: {str(e)}'}


def process_data_pipeline(df, column_mappings):
    """
    Main data processing pipeline that orchestrates all cleaning steps.
    """
    processing_results = {}
    processed_df = df.copy()
    
    # Step 1: Handle missing values first
    processed_df, missing_result = handle_missing_values(processed_df)
    processing_results['missing_values'] = missing_result
    
    # Step 2: Remove duplicates
    processed_df, duplicate_result = remove_duplicate_transactions(processed_df)
    processing_results['duplicates'] = duplicate_result
    
    # Step 3: Clean and standardize dates
    if 'date' in column_mappings and column_mappings['date']:
        processed_df, date_result = clean_and_standardize_dates(processed_df, column_mappings['date'])
        processing_results['dates'] = date_result
    
    # Step 4: Clean and convert amounts
    if 'amount' in column_mappings and column_mappings['amount']:
        processed_df, amount_result = clean_and_convert_amounts(processed_df, column_mappings['amount'])
        processing_results['amounts'] = amount_result
    
    # Step 5: Standardize account names
    if 'account' in column_mappings and column_mappings['account']:
        processed_df, account_result = standardize_account_names(processed_df, column_mappings['account'])
        processing_results['accounts'] = account_result
    
    # Step 6: Generate quality summary
    quality_summary = generate_data_quality_summary(processed_df, processing_results)
    
    return processed_df, processing_results, quality_summary


def calculate_monthly_summaries(df):
    """
    Calculate monthly summaries for each account.
    Groups data by account and month to prepare for movement analysis.
    """
    try:
        # Ensure we have the required columns (check both lowercase and title case)
        required_cols = {'date': None, 'account': None, 'amount': None}
        for col in df.columns:
            col_lower = col.lower()
            if col_lower in required_cols:
                required_cols[col_lower] = col
        
        if not all(col is not None for col in required_cols.values()):
            return None, {'success': False, 'error': 'Required columns (date, account, amount) missing'}
        
        # Convert date column to datetime for processing
        df_copy = df.copy()
        date_col = required_cols['date']
        account_col = required_cols['account']
        amount_col = required_cols['amount']
        
        df_copy['date'] = pd.to_datetime(df_copy[date_col])
        df_copy['account'] = df_copy[account_col]
        df_copy['amount'] = df_copy[amount_col]
        
        # Create year-month period column
        df_copy['year_month'] = df_copy['date'].dt.to_period('M')
        
        # Group by account and month, sum amounts
        monthly_summary = df_copy.groupby(['account', 'year_month']).agg({
            'amount': 'sum',
            'date': 'max'  # Keep latest date in the month for reference
        }).reset_index()
        
        # Convert period back to datetime for easier manipulation
        monthly_summary['date'] = monthly_summary['year_month'].dt.start_time
        monthly_summary['year'] = monthly_summary['year_month'].dt.year
        monthly_summary['month'] = monthly_summary['year_month'].dt.month
        
        return monthly_summary, {
            'success': True,
            'accounts_processed': len(monthly_summary['account'].unique()),
            'periods_processed': len(monthly_summary['year_month'].unique()),
            'total_records': len(monthly_summary)
        }
        
    except Exception as e:
        return None, {'success': False, 'error': f'Monthly summary calculation error: {str(e)}'}


def calculate_mom_movements(monthly_summary):
    """
    Calculate month-over-month movements for each account.
    """
    try:
        movements = []
        
        # Sort by account and date
        sorted_data = monthly_summary.sort_values(['account', 'date'])
        
        # Calculate MoM changes for each account
        for account in sorted_data['account'].unique():
            account_data = sorted_data[sorted_data['account'] == account].copy()
            account_data = account_data.sort_values('date')
            
            # Calculate period-over-period changes
            for i in range(1, len(account_data)):
                current_row = account_data.iloc[i]
                previous_row = account_data.iloc[i-1]
                
                current_amount = current_row['amount']
                previous_amount = previous_row['amount']
                
                # Calculate percentage change
                if previous_amount != 0:
                    pct_change = ((current_amount - previous_amount) / abs(previous_amount)) * 100
                else:
                    # Handle division by zero - if previous was 0, this is new activity
                    pct_change = 100.0 if current_amount > 0 else -100.0 if current_amount < 0 else 0.0
                
                # Calculate absolute change
                abs_change = current_amount - previous_amount
                
                movements.append({
                    'account': account,
                    'current_period': current_row['year_month'],
                    'current_date': current_row['date'],
                    'current_amount': current_amount,
                    'previous_period': previous_row['year_month'],
                    'previous_amount': previous_amount,
                    'percentage_change': pct_change,
                    'absolute_change': abs_change,
                    'movement_type': 'MoM'
                })
        
        movements_df = pd.DataFrame(movements)
        
        return movements_df, {
            'success': True,
            'total_movements': len(movements),
            'accounts_analyzed': len(movements_df['account'].unique()) if len(movements) > 0 else 0
        }
        
    except Exception as e:
        return None, {'success': False, 'error': f'MoM calculation error: {str(e)}'}


def calculate_yoy_movements(monthly_summary):
    """
    Calculate year-over-year movements for each account.
    """
    try:
        movements = []
        
        # Sort by account and date
        sorted_data = monthly_summary.sort_values(['account', 'date'])
        
        # Calculate YoY changes for each account
        for account in sorted_data['account'].unique():
            account_data = sorted_data[sorted_data['account'] == account].copy()
            
            # Group by month to compare same months across years
            for month in range(1, 13):
                month_data = account_data[account_data['month'] == month].sort_values('year')
                
                # Calculate year-over-year changes
                for i in range(1, len(month_data)):
                    current_row = month_data.iloc[i]
                    previous_year_row = month_data.iloc[i-1]
                    
                    # Only compare if it's exactly one year apart
                    if current_row['year'] - previous_year_row['year'] == 1:
                        current_amount = current_row['amount']
                        previous_amount = previous_year_row['amount']
                        
                        # Calculate percentage change
                        if previous_amount != 0:
                            pct_change = ((current_amount - previous_amount) / abs(previous_amount)) * 100
                        else:
                            pct_change = 100.0 if current_amount > 0 else -100.0 if current_amount < 0 else 0.0
                        
                        # Calculate absolute change
                        abs_change = current_amount - previous_amount
                        
                        movements.append({
                            'account': account,
                            'current_period': current_row['year_month'],
                            'current_date': current_row['date'],
                            'current_amount': current_amount,
                            'previous_period': previous_year_row['year_month'],
                            'previous_amount': previous_amount,
                            'percentage_change': pct_change,
                            'absolute_change': abs_change,
                            'movement_type': 'YoY'
                        })
        
        movements_df = pd.DataFrame(movements)
        
        return movements_df, {
            'success': True,
            'total_movements': len(movements),
            'accounts_analyzed': len(movements_df['account'].unique()) if len(movements) > 0 else 0
        }
        
    except Exception as e:
        return None, {'success': False, 'error': f'YoY calculation error: {str(e)}'}


def apply_movement_thresholds(movements_df, mom_threshold=10.0, yoy_threshold=15.0):
    """
    Apply threshold-based flagging to identify significant movements.
    """
    try:
        if movements_df is None or len(movements_df) == 0:
            return None, {'success': False, 'error': 'No movements to analyze'}
        
        flagged_movements = movements_df.copy()
        
        # Apply thresholds based on movement type
        def get_significance_flag(row):
            threshold = mom_threshold if row['movement_type'] == 'MoM' else yoy_threshold
            abs_pct_change = abs(row['percentage_change'])
            
            if abs_pct_change >= threshold * 3:  # 3x threshold
                return 'Critical'
            elif abs_pct_change >= threshold * 2:  # 2x threshold
                return 'High'
            elif abs_pct_change >= threshold:  # 1x threshold
                return 'Medium'
            else:
                return 'Low'
        
        # Apply significance flagging
        flagged_movements['significance'] = flagged_movements.apply(get_significance_flag, axis=1)
        
        # Filter to only significant movements (above threshold)
        significant_movements = flagged_movements[
            ((flagged_movements['movement_type'] == 'MoM') & (abs(flagged_movements['percentage_change']) >= mom_threshold)) |
            ((flagged_movements['movement_type'] == 'YoY') & (abs(flagged_movements['percentage_change']) >= yoy_threshold))
        ].copy()
        
        # Add materiality scoring (combination of percentage and absolute impact)
        if len(significant_movements) > 0:
            # Normalize absolute values for scoring
            max_abs_change = abs(significant_movements['absolute_change']).max()
            if max_abs_change > 0:
                significant_movements['abs_score'] = abs(significant_movements['absolute_change']) / max_abs_change * 100
            else:
                significant_movements['abs_score'] = 0
            
            # Combine percentage and absolute scores
            significant_movements['materiality_score'] = (
                abs(significant_movements['percentage_change']) * 0.6 + 
                significant_movements['abs_score'] * 0.4
            )
        
        return significant_movements, {
            'success': True,
            'total_movements_analyzed': len(flagged_movements),
            'significant_movements_found': len(significant_movements),
            'mom_threshold_applied': mom_threshold,
            'yoy_threshold_applied': yoy_threshold
        }
        
    except Exception as e:
        return None, {'success': False, 'error': f'Threshold application error: {str(e)}'}


def detect_new_and_discontinued_accounts(monthly_summary):
    """
    Detect accounts that are new (no historical data) or discontinued (no recent data).
    """
    try:
        if monthly_summary is None or len(monthly_summary) == 0:
            return [], {'success': False, 'error': 'No data to analyze'}
        
        account_flags = []
        current_date = monthly_summary['date'].max()
        earliest_date = monthly_summary['date'].min()
        
        # Analysis for each account
        for account in monthly_summary['account'].unique():
            account_data = monthly_summary[monthly_summary['account'] == account]
            
            account_start = account_data['date'].min()
            account_end = account_data['date'].max()
            
            # Calculate months of data availability
            months_active = len(account_data)
            
            # Flag new accounts (started recently)
            months_since_start = (current_date - account_start).days / 30.44  # Average days per month
            is_new = months_since_start <= 2  # New if started within last 2 months
            
            # Flag discontinued accounts (no recent activity)
            months_since_last = (current_date - account_end).days / 30.44
            is_discontinued = months_since_last > 2  # Discontinued if no activity for 2+ months
            
            # Flag accounts with insufficient history for meaningful analysis
            insufficient_history = months_active < 3  # Less than 3 months of data
            
            if is_new or is_discontinued or insufficient_history:
                account_flags.append({
                    'account': account,
                    'flag_type': 'New' if is_new else 'Discontinued' if is_discontinued else 'Insufficient History',
                    'months_active': months_active,
                    'start_date': account_start,
                    'end_date': account_end,
                    'months_since_start': months_since_start,
                    'months_since_last': months_since_last
                })
        
        return account_flags, {
            'success': True,
            'total_accounts_analyzed': len(monthly_summary['account'].unique()),
            'flagged_accounts': len(account_flags),
            'new_accounts': len([f for f in account_flags if f['flag_type'] == 'New']),
            'discontinued_accounts': len([f for f in account_flags if f['flag_type'] == 'Discontinued']),
            'insufficient_history_accounts': len([f for f in account_flags if f['flag_type'] == 'Insufficient History'])
        }
        
    except Exception as e:
        return [], {'success': False, 'error': f'Account flagging error: {str(e)}'}


def rank_movements_by_significance(movements_df):
    """
    Rank movements by significance using materiality score and create top N list.
    """
    try:
        if movements_df is None or len(movements_df) == 0:
            return None, {'success': False, 'error': 'No movements to rank'}
        
        # Sort by materiality score descending
        ranked_movements = movements_df.sort_values('materiality_score', ascending=False).copy()
        
        # Add ranking
        ranked_movements['rank'] = range(1, len(ranked_movements) + 1)
        
        # Create summary statistics
        ranking_stats = {
            'success': True,
            'total_movements': len(ranked_movements),
            'top_movement_score': ranked_movements['materiality_score'].iloc[0] if len(ranked_movements) > 0 else 0,
            'avg_materiality_score': ranked_movements['materiality_score'].mean(),
            'critical_movements': len(ranked_movements[ranked_movements['significance'] == 'Critical']),
            'high_movements': len(ranked_movements[ranked_movements['significance'] == 'High']),
            'medium_movements': len(ranked_movements[ranked_movements['significance'] == 'Medium'])
        }
        
        return ranked_movements, ranking_stats
        
    except Exception as e:
        return None, {'success': False, 'error': f'Ranking error: {str(e)}'}


def run_movement_detection_engine(df):
    """
    Main movement detection engine that orchestrates all movement analysis steps.
    """
    try:
        detection_results = {
            'success': False,
            'monthly_summary': None,
            'mom_movements': None,
            'yoy_movements': None,
            'significant_movements': None,
            'account_flags': None,
            'ranked_movements': None,
            'summary_stats': {},
            'errors': []
        }
        
        # Step 1: Calculate monthly summaries
        monthly_summary, monthly_result = calculate_monthly_summaries(df)
        detection_results['summary_stats']['monthly_summary'] = monthly_result
        
        if not monthly_result['success']:
            detection_results['errors'].append(f"Monthly summary: {monthly_result['error']}")
            return detection_results
        
        detection_results['monthly_summary'] = monthly_summary
        
        # Step 2: Calculate MoM movements
        mom_movements, mom_result = calculate_mom_movements(monthly_summary)
        detection_results['summary_stats']['mom_movements'] = mom_result
        
        if not mom_result['success']:
            detection_results['errors'].append(f"MoM movements: {mom_result['error']}")
        else:
            detection_results['mom_movements'] = mom_movements
        
        # Step 3: Calculate YoY movements
        yoy_movements, yoy_result = calculate_yoy_movements(monthly_summary)
        detection_results['summary_stats']['yoy_movements'] = yoy_result
        
        if not yoy_result['success']:
            detection_results['errors'].append(f"YoY movements: {yoy_result['error']}")
        else:
            detection_results['yoy_movements'] = yoy_movements
        
        # Step 4: Combine movements and apply thresholds
        all_movements = []
        if mom_movements is not None and len(mom_movements) > 0:
            all_movements.append(mom_movements)
        if yoy_movements is not None and len(yoy_movements) > 0:
            all_movements.append(yoy_movements)
        
        if all_movements:
            combined_movements = pd.concat(all_movements, ignore_index=True)
            significant_movements, threshold_result = apply_movement_thresholds(combined_movements)
            detection_results['summary_stats']['significant_movements'] = threshold_result
            
            if threshold_result['success']:
                detection_results['significant_movements'] = significant_movements
        
        # Step 5: Detect new and discontinued accounts
        account_flags, account_result = detect_new_and_discontinued_accounts(monthly_summary)
        detection_results['summary_stats']['account_flags'] = account_result
        detection_results['account_flags'] = account_flags
        
        # Step 6: Rank movements by significance
        if detection_results['significant_movements'] is not None and len(detection_results['significant_movements']) > 0:
            ranked_movements, ranking_result = rank_movements_by_significance(detection_results['significant_movements'])
            detection_results['summary_stats']['ranking'] = ranking_result
            
            if ranking_result['success']:
                detection_results['ranked_movements'] = ranked_movements
        
        # Overall success if we have any meaningful output
        detection_results['success'] = (
            detection_results['monthly_summary'] is not None and
            len(detection_results['errors']) == 0
        )
        
        return detection_results
        
    except Exception as e:
        return {
            'success': False,
            'error': f'Movement detection engine error: {str(e)}',
            'monthly_summary': None,
            'mom_movements': None,
            'yoy_movements': None,
            'significant_movements': None,
            'account_flags': None,
            'ranked_movements': None,
            'summary_stats': {},
            'errors': [str(e)]
        }


def detect_financial_statement_format(df):
    """
    Detect if the DataFrame is in financial statement format (wide format).
    Returns detection result and conversion info.
    """
    # Check if first column contains account names and other columns are dates/periods
    if len(df.columns) < 3:
        return {'is_financial_statement': False}
    
    first_col = df.columns[0]
    other_cols = df.columns[1:]
    
    # Check if first column might contain account names
    first_col_sample = df[first_col].dropna().astype(str).head(10).tolist()
    account_indicators = ['account', 'asset', 'liability', 'income', 'expense', 'revenue', 'cost', 'bank', 'cash', 'total']
    
    has_account_indicators = any(
        any(indicator in str(val).lower() for indicator in account_indicators)
        for val in first_col_sample if len(str(val)) > 3
    )
    
    # Check if other columns might be dates or periods
    date_like_cols = 0
    for col in other_cols[:10]:  # Check first 10 columns
        col_str = str(col).lower()
        if any(pattern in col_str for pattern in ['2020', '2021', '2022', '2023', '2024', 'jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec', 'unnamed']):
            date_like_cols += 1
    
    # If we have account-like first column and multiple date-like columns, it's likely financial statements
    is_financial_statement = has_account_indicators and date_like_cols >= 2
    
    return {
        'is_financial_statement': is_financial_statement,
        'account_column': first_col,
        'period_columns': other_cols.tolist(),
        'account_sample': first_col_sample[:5]
    }


def convert_financial_statement_to_long_format(df, detection_result):
    """
    Convert wide-format financial statement to long format (Date, Account, Amount).
    """
    account_col = detection_result['account_column']
    period_cols = detection_result['period_columns']
    
    # Prepare data for conversion
    long_format_data = []
    
    for _, row in df.iterrows():
        account_name = str(row[account_col])
        
        # Skip empty account names or header rows
        if pd.isna(row[account_col]) or len(account_name.strip()) < 2:
            continue
            
        # Skip total rows or summary rows
        if any(skip_word in account_name.lower() for skip_word in ['total', 'subtotal', 'xxx', '---']):
            continue
        
        for period_col in period_cols:
            amount = row[period_col]
            
            # Skip if amount is not numeric or is zero/empty
            if pd.isna(amount) or amount == 0:
                continue
                
            try:
                # Try to convert to numeric
                numeric_amount = pd.to_numeric(amount)
                
                # Create a date from the period column name
                period_str = str(period_col)
                
                # Try to extract date from column name
                if 'unnamed' in period_str.lower():
                    # For unnamed columns, we'll use a sequential date
                    col_index = period_cols.index(period_col)
                    # Generate valid month (1-12), cycling if needed
                    month = ((12 - col_index - 1) % 12) + 1
                    # Generate year, going back if more than 12 columns
                    year = 2022 - (col_index // 12)
                    date_str = f"{year}-{month:02d}-01"
                else:
                    # Try to parse the period name as date
                    date_str = parse_period_to_date(period_str)
                
                long_format_data.append({
                    'Date': date_str,
                    'Account': account_name,
                    'Amount': numeric_amount
                })
            except (ValueError, TypeError):
                continue
    
    # Create new DataFrame in long format
    if long_format_data:
        long_df = pd.DataFrame(long_format_data)
        return long_df
    else:
        return None


def parse_period_to_date(period_str):
    """
    Parse various period string formats to standard date format.
    """
    period_str = str(period_str).strip()
    period_lower = period_str.lower()
    
    # Handle formats like "Dec-22", "Nov-22", "31 Dec 2022", "30 Nov 2022", etc.
    month_abbrevs = {
        'jan': '01', 'feb': '02', 'mar': '03', 'apr': '04', 'may': '05', 'jun': '06',
        'jul': '07', 'aug': '08', 'sep': '09', 'oct': '10', 'nov': '11', 'dec': '12'
    }
    
    # Try to find month name
    found_month = None
    for month_name, month_num in month_abbrevs.items():
        if month_name in period_lower:
            found_month = month_num
            break
    
    if found_month:
        # Extract year - look for 4-digit year first, then 2-digit
        year_match = re.search(r'(\d{4})', period_str)
        if year_match:
            year = year_match.group(1)
        else:
            year_match = re.search(r'(\d{2})', period_str)
            if year_match:
                year_2digit = year_match.group(1)
                # Assume 20xx for years 00-50, 19xx for 51-99
                year = '20' + year_2digit if int(year_2digit) <= 50 else '19' + year_2digit
            else:
                year = '2022'  # Default year
        
        return f"{year}-{found_month}-01"
    
    # Try to extract just numbers for YYYY-MM or MM-YYYY patterns
    numbers = re.findall(r'\d+', period_str)
    if len(numbers) >= 2:
        # Assume first number is month, second is year (or vice versa)
        num1, num2 = int(numbers[0]), int(numbers[1])
        if num1 > 12 and num2 <= 12:  # First is year, second is month
            year, month = num1, num2
        elif num2 > 12 and num1 <= 12:  # First is month, second is year
            month, year = num1, num2
        elif num1 <= 12 and num2 > 12:  # First is month, second is year
            month, year = num1, num2
        else:  # Both could be month or year, assume month-year order
            month, year = num1, num2
        
        # Handle 2-digit years
        if year < 100:
            year = 2000 + year if year <= 50 else 1900 + year
        
        if 1 <= month <= 12:
            return f"{year}-{month:02d}-01"
    
    # Default fallback
    return "2022-01-01"


def detect_column_mappings(df):
    """
    Auto-detect column mappings for Date, Account, and Amount columns.
    Returns a dictionary with detected mappings and debugging info.
    """
    columns = df.columns.tolist()
    mappings = {'date': None, 'account': None, 'amount': None}
    
    # More comprehensive date column patterns
    date_patterns = [
        r'\bdate\b', r'\btime\b', r'\bperiod\b', r'\bmonth\b', r'\bday\b', 
        r'\btransaction.*date\b', r'\bposting.*date\b', r'\beff.*date\b',
        r'\bwhen\b', r'\btimestamp\b', r'\bdated\b'
    ]
    for col in columns:
        if any(re.search(pattern, col.lower()) for pattern in date_patterns):
            mappings['date'] = col
            break
    
    # More comprehensive account column patterns  
    account_patterns = [
        r'\baccount\b', r'\bdescription\b', r'\bcategory\b', r'\bitem\b', 
        r'\bname\b', r'\btitle\b', r'\blabel\b', r'\bdetail\b', r'\btext\b',
        r'\bexpense\b', r'\bincome\b', r'\btype\b', r'\bclass\b'
    ]
    for col in columns:
        if mappings['account'] is None and any(re.search(pattern, col.lower()) for pattern in account_patterns):
            mappings['account'] = col
            break
    
    # More comprehensive amount column patterns
    amount_patterns = [
        r'\bamount\b', r'\bvalue\b', r'\bbalance\b', r'\btotal\b', r'\bsum\b', 
        r'\bdebit\b', r'\bcredit\b', r'\bmoney\b', r'\bcash\b', r'\bcost\b',
        r'\bprice\b', r'\bfee\b', r'\bcharge\b', r'\bpay\b', r'\bdollar\b',
        r'^\$', r'\bcurrency\b', r'\bnet\b', r'\bgross\b'
    ]
    for col in columns:
        if mappings['amount'] is None and any(re.search(pattern, col.lower()) for pattern in amount_patterns):
            mappings['amount'] = col
            break
    
    return mappings


def validate_date_column(df, date_col):
    """
    Validate date column formatting and return validation results.
    """
    if date_col is None or date_col not in df.columns:
        return {'valid': False, 'error': 'Date column not found', 'sample': None}
    
    try:
        # Try to parse dates
        sample_values = df[date_col].dropna().head(5).tolist()
        pd.to_datetime(df[date_col], errors='raise')
        return {'valid': True, 'error': None, 'sample': sample_values}
    except Exception as e:
        sample_values = df[date_col].dropna().head(3).tolist()
        return {'valid': False, 'error': f'Invalid date format: {str(e)}', 'sample': sample_values}


def validate_amount_column(df, amount_col):
    """
    Validate amount column contains numeric values.
    """
    if amount_col is None or amount_col not in df.columns:
        return {'valid': False, 'error': 'Amount column not found', 'sample': None}
    
    try:
        # Get sample values before conversion
        original_values = df[amount_col].head(5).tolist()
        
        # Try to convert to numeric with errors='coerce' to identify problematic values
        numeric_series = pd.to_numeric(df[amount_col], errors='coerce')
        
        # Check if any values became NaN after conversion (indicating non-numeric input)
        non_numeric_mask = pd.isna(numeric_series) & pd.notna(df[amount_col])
        
        if non_numeric_mask.any():
            # Get the actual non-numeric values for error reporting
            problematic_values = df[amount_col][non_numeric_mask].head(3).tolist()
            return {
                'valid': False, 
                'error': f'Non-numeric values found in amount column', 
                'sample': problematic_values
            }
        
        # Check if we have any valid numeric values at all
        valid_numeric_count = numeric_series.count()
        if valid_numeric_count == 0:
            return {
                'valid': False,
                'error': 'No valid numeric values found in amount column',
                'sample': original_values[:3]
            }
        
        # Now try the strict conversion to ensure data types are correct
        pd.to_numeric(df[amount_col], errors='raise')
        return {'valid': True, 'error': None, 'sample': original_values}
        
    except Exception as e:
        sample_values = df[amount_col].head(3).tolist()
        return {'valid': False, 'error': f'Amount validation error: {str(e)}', 'sample': sample_values}


def validate_data_structure(df):
    """
    Comprehensive data structure validation.
    Returns validation results and suggested mappings.
    """
    # First, check if this is a financial statement format
    fs_detection = detect_financial_statement_format(df)
    
    if fs_detection['is_financial_statement']:
        # Convert financial statement to long format
        converted_df = convert_financial_statement_to_long_format(df, fs_detection)
        
        if converted_df is not None and len(converted_df) > 0:
            # Use the converted DataFrame for validation
            validation_df = converted_df
            conversion_info = {
                'was_converted': True,
                'original_format': 'financial_statement',
                'conversion_stats': {
                    'original_shape': df.shape,
                    'converted_shape': converted_df.shape,
                    'accounts_found': len(converted_df['Account'].unique()),
                    'periods_found': len(converted_df['Date'].unique())
                }
            }
        else:
            # Conversion failed
            return {
                'overall_valid': False,
                'error': 'Financial statement format detected but conversion failed',
                'mappings': {'date': None, 'account': None, 'amount': None},
                'validations': {
                    'date': {'valid': False, 'error': 'Conversion from financial statement format failed', 'sample': None},
                    'account': {'valid': False, 'error': 'Conversion from financial statement format failed', 'sample': None},
                    'amount': {'valid': False, 'error': 'Conversion from financial statement format failed', 'sample': None}
                },
                'data_shape': df.shape,
                'columns': df.columns.tolist(),
                'fs_detection': fs_detection
            }
    else:
        # Use original DataFrame for standard validation
        validation_df = df
        conversion_info = {'was_converted': False}
    
    # Detect column mappings on the validation DataFrame
    mappings = detect_column_mappings(validation_df)
    
    # Validate each required column
    date_validation = validate_date_column(validation_df, mappings['date'])
    amount_validation = validate_amount_column(validation_df, mappings['amount'])
    
    # Check for account column (less strict validation)
    account_validation = {
        'valid': mappings['account'] is not None,
        'error': None if mappings['account'] else 'Account/Description column not found',
        'sample': validation_df[mappings['account']].dropna().head(3).tolist() if mappings['account'] else None
    }
    
    # Overall validation status
    all_valid = date_validation['valid'] and amount_validation['valid'] and account_validation['valid']
    
    result = {
        'overall_valid': all_valid,
        'mappings': mappings,
        'validations': {
            'date': date_validation,
            'account': account_validation, 
            'amount': amount_validation
        },
        'data_shape': validation_df.shape,
        'columns': validation_df.columns.tolist(),
        'conversion_info': conversion_info
    }
    
    # Add financial statement detection info if applicable
    if fs_detection['is_financial_statement']:
        result['fs_detection'] = fs_detection
    
    return result


# Page configuration
st.set_page_config(
    page_title="FinGenie - AI-Powered Financial Assistant",
    page_icon="💰",
    layout="wide",
    initial_sidebar_state="collapsed"
)


def initialize_session_state():
    """Initialize all session state variables for the application."""
    if 'uploaded_file' not in st.session_state:
        st.session_state.uploaded_file = None
    if 'processed_data' not in st.session_state:
        st.session_state.processed_data = None
    if 'analysis_results' not in st.session_state:
        st.session_state.analysis_results = None
    if 'generated_charts' not in st.session_state:
        st.session_state.generated_charts = []
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []


def main():
    """Main application function that creates the UI layout and tabs."""
    # Initialize session state
    initialize_session_state()
    
    # Main app header
    st.title("🏦 FinGenie - AI-Powered Financial Assistant")
    st.markdown("Transform your financial data into executive-ready insights")
    
    # Create tabs
    tab1, tab2, tab3, tab4 = st.tabs([
        "📊 Data Preview", 
        "🔍 Insights", 
        "📈 Visuals", 
        "🔮 Forecast"
    ])
    
    with tab1:
        st.header("Data Upload & Preview")
        st.info("Upload your CSV or Excel files here to get started")
        st.markdown("**Supported formats:** CSV, XLSX, XLS")
        st.markdown("**Maximum file size:** 10MB")
        st.markdown("---")
        st.markdown("📋 **What you can do here:**")
        st.markdown("- Upload financial data files")
        st.markdown("- Preview data structure and columns")
        st.markdown("- Validate data format and completeness")
        
        # File upload widget
        uploaded_file = st.file_uploader(
            "Choose a file",
            type=['csv', 'xlsx', 'xls'],
            accept_multiple_files=False,
            help="Upload CSV or Excel files up to 10MB"
        )
        
        # Handle file upload
        if uploaded_file is not None:
            try:
                # Show processing indicator
                with st.spinner('Processing file...'):
                    # File size validation (10MB = 10 * 1024 * 1024 bytes)
                    file_size = len(uploaded_file.getvalue())
                    max_size = 10 * 1024 * 1024  # 10MB
                    
                    if file_size > max_size:
                        st.error(f"❌ File size ({file_size / (1024*1024):.1f}MB) exceeds the 10MB limit. Please choose a smaller file.")
                    else:
                        # Additional file validation
                        file_extension = uploaded_file.name.split('.')[-1].lower()
                        if file_extension not in ['csv', 'xlsx', 'xls']:
                            st.error(f"❌ Unsupported file type: .{file_extension}. Please upload a CSV or Excel file.")
                        else:
                            # Basic file content validation
                            try:
                                # Try to read the file to check if it's corrupted
                                file_content = uploaded_file.getvalue()
                                if len(file_content) == 0:
                                    st.error("❌ The uploaded file is empty. Please choose a file with data.")
                                else:
                                    # File validation passed
                                    st.success(f"✅ File uploaded successfully: {uploaded_file.name} ({file_size / (1024*1024):.1f}MB)")
                                    
                                    # Store in session state
                                    st.session_state.uploaded_file = uploaded_file
                                    
                                    # Display file info
                                    st.markdown("**File Details:**")
                                    st.markdown(f"- **Name:** {uploaded_file.name}")
                                    st.markdown(f"- **Size:** {file_size / (1024*1024):.1f}MB")
                                    st.markdown(f"- **Type:** {uploaded_file.type}")
                                    
                                    # Data structure validation
                                    st.markdown("---")
                                    st.markdown("**📋 Data Structure Validation**")
                                    
                                    try:
                                        # Read file into DataFrame
                                        uploaded_file.seek(0)  # Reset file pointer
                                        if file_extension == 'csv':
                                            df = pd.read_csv(uploaded_file)
                                        else:  # xlsx or xls
                                            df = pd.read_excel(uploaded_file)
                                        
                                        # Run validation
                                        validation_results = validate_data_structure(df)
                                        
                                        # Store results in session state
                                        # If financial statement was converted, store the converted data
                                        if validation_results.get('conversion_info', {}).get('was_converted'):
                                            # Re-run conversion to get the converted DataFrame
                                            fs_detection = detect_financial_statement_format(df)
                                            converted_df = convert_financial_statement_to_long_format(df, fs_detection)
                                            st.session_state.processed_data = converted_df
                                            st.session_state.original_data = df  # Keep original for reference
                                        else:
                                            st.session_state.processed_data = df
                                        
                                        st.session_state.validation_results = validation_results
                                        
                                        # Display validation results
                                        if validation_results['overall_valid']:
                                            st.success("✅ Data structure validation passed!")
                                            
                                            # Show conversion info if financial statement was converted
                                            if validation_results.get('conversion_info', {}).get('was_converted'):
                                                st.info("🔄 **Financial Statement Detected & Converted**")
                                                conv_stats = validation_results['conversion_info']['conversion_stats']
                                                st.markdown("**Conversion Summary:**")
                                                st.markdown(f"- **Original Format:** Wide-format financial statement ({conv_stats['original_shape'][0]} rows × {conv_stats['original_shape'][1]} columns)")
                                                st.markdown(f"- **Converted Format:** Long-format transaction data ({conv_stats['converted_shape'][0]} rows × {conv_stats['converted_shape'][1]} columns)")
                                                st.markdown(f"- **Accounts Found:** {conv_stats['accounts_found']} unique accounts")
                                                st.markdown(f"- **Time Periods:** {conv_stats['periods_found']} periods")
                                                st.markdown("---")
                                            
                                            st.markdown("**Detected Column Mappings:**")
                                            mappings = validation_results['mappings']
                                            st.markdown(f"- **Date Column:** {mappings['date']}")
                                            st.markdown(f"- **Account Column:** {mappings['account']}")
                                            st.markdown(f"- **Amount Column:** {mappings['amount']}")
                                            st.markdown(f"- **Data Shape:** {validation_results['data_shape'][0]} rows, {validation_results['data_shape'][1]} columns")
                                            
                                            # Data Processing Pipeline
                                            st.markdown("---")
                                            st.markdown("**🔧 Data Processing Pipeline**")
                                            
                                            with st.spinner('Cleaning and standardizing data...'):
                                                # Get the validated data for processing
                                                processing_df = st.session_state.processed_data.copy()
                                                
                                                # Run the data processing pipeline
                                                processed_df, processing_results, quality_summary = process_data_pipeline(
                                                    processing_df, 
                                                    mappings
                                                )
                                                
                                                # Store processed data and results
                                                st.session_state.final_processed_data = processed_df
                                                st.session_state.processing_results = processing_results
                                                st.session_state.quality_summary = quality_summary
                                                
                                                # Run movement detection engine
                                                st.session_state.movement_analysis = run_movement_detection_engine(processed_df)
                                            
                                            st.success("✅ Data processing completed!")
                                            
                                            # Display processing results summary
                                            col1, col2 = st.columns(2)
                                            
                                            with col1:
                                                st.markdown("**📊 Processing Summary:**")
                                                
                                                # Missing values handling
                                                if 'missing_values' in processing_results and processing_results['missing_values']['success']:
                                                    missing_summary = processing_results['missing_values']['missing_summary']
                                                    total_missing = sum(info['missing_count'] for info in missing_summary.values())
                                                    st.markdown(f"- **Missing values handled:** {total_missing}")
                                                
                                                # Duplicate removal
                                                if 'duplicates' in processing_results and processing_results['duplicates']['success']:
                                                    dup_result = processing_results['duplicates']
                                                    st.markdown(f"- **Duplicates removed:** {dup_result['duplicates_removed']}")
                                                    st.markdown(f"- **Final row count:** {dup_result['final_count']}")
                                                
                                                # Date standardization
                                                if 'dates' in processing_results and processing_results['dates']['success']:
                                                    date_result = processing_results['dates']
                                                    success_rate = date_result['success_rate'] * 100
                                                    st.markdown(f"- **Date standardization:** {success_rate:.1f}% success rate")
                                                
                                                # Amount conversion
                                                if 'amounts' in processing_results and processing_results['amounts']['success']:
                                                    amount_result = processing_results['amounts']
                                                    success_rate = amount_result['success_rate'] * 100
                                                    st.markdown(f"- **Amount conversion:** {success_rate:.1f}% success rate")
                                            
                                            with col2:
                                                st.markdown("**🎯 Data Quality Score:**")
                                                
                                                if 'error' not in quality_summary:
                                                    quality_score = quality_summary['data_quality_score']
                                                    
                                                    # Color-code the quality score
                                                    if quality_score >= 90:
                                                        st.success(f"**{quality_score:.1f}/100** - Excellent Quality")
                                                    elif quality_score >= 75:
                                                        st.warning(f"**{quality_score:.1f}/100** - Good Quality")
                                                    elif quality_score >= 50:
                                                        st.warning(f"**{quality_score:.1f}/100** - Fair Quality")
                                                    else:
                                                        st.error(f"**{quality_score:.1f}/100** - Poor Quality")
                                                    
                                                    st.markdown(f"- **Total rows:** {quality_summary['total_rows']}")
                                                    st.markdown(f"- **Total columns:** {quality_summary['total_columns']}")
                                                    
                                                    # Show recommendations if any
                                                    if quality_summary['recommendations']:
                                                        st.markdown("**💡 Recommendations:**")
                                                        for rec in quality_summary['recommendations']:
                                                            st.markdown(f"- {rec}")
                                                else:
                                                    st.error("Unable to generate quality summary")
                                            
                                            # Account name standardization results
                                            if 'accounts' in processing_results and processing_results['accounts']['success']:
                                                account_result = processing_results['accounts']
                                                if account_result['reduction_count'] > 0:
                                                    st.info(f"🔧 **Account Name Standardization:** Reduced {account_result['original_unique_accounts']} → {account_result['cleaned_unique_accounts']} unique accounts (simplified {account_result['reduction_count']} variations)")
                                            
                                            st.markdown("---")
                                            st.success("🎉 **Data is ready for analysis!** Navigate to the Insights, Visuals, or Forecast tabs to continue.")
                                            
                                            # Enhanced Data Preview Section
                                            st.markdown("---")
                                            st.markdown("**📋 Data Preview & Summary**")
                                            
                                            # Data preview table component
                                            if st.session_state.final_processed_data is not None:
                                                df_preview = st.session_state.final_processed_data
                                                
                                                # Summary Statistics Section
                                                col1, col2, col3 = st.columns(3)
                                                
                                                with col1:
                                                    st.metric("Total Rows", f"{len(df_preview):,}")
                                                    
                                                with col2:
                                                    # Date range
                                                    if 'date' in df_preview.columns:
                                                        try:
                                                            date_col = pd.to_datetime(df_preview['date'])
                                                            min_date = date_col.min().strftime('%Y-%m-%d')
                                                            max_date = date_col.max().strftime('%Y-%m-%d')
                                                            st.metric("Date Range", f"{min_date} to {max_date}")
                                                        except:
                                                            st.metric("Date Range", "Unable to parse")
                                                    else:
                                                        st.metric("Date Range", "No date column")
                                                
                                                with col3:
                                                    # Account types
                                                    if 'account' in df_preview.columns:
                                                        unique_accounts = df_preview['account'].nunique()
                                                        st.metric("Unique Accounts", f"{unique_accounts:,}")
                                                    else:
                                                        st.metric("Unique Accounts", "No account column")
                                                
                                                # Amount statistics
                                                if 'amount' in df_preview.columns:
                                                    try:
                                                        amount_col = pd.to_numeric(df_preview['amount'], errors='coerce')
                                                        col1, col2, col3, col4 = st.columns(4)
                                                        
                                                        with col1:
                                                            st.metric("Min Amount", f"${amount_col.min():,.2f}")
                                                        with col2:
                                                            st.metric("Max Amount", f"${amount_col.max():,.2f}")
                                                        with col3:
                                                            st.metric("Average", f"${amount_col.mean():,.2f}")
                                                        with col4:
                                                            st.metric("Total", f"${amount_col.sum():,.2f}")
                                                    except:
                                                        st.warning("Unable to calculate amount statistics")
                                                
                                                st.markdown("---")
                                                
                                                # Interactive data table with pagination
                                                st.markdown("**📊 Interactive Data Table**")
                                                
                                                # Show data types
                                                with st.expander("📋 Column Information"):
                                                    col_info = []
                                                    for col in df_preview.columns:
                                                        dtype_str = str(df_preview[col].dtype)
                                                        non_null = df_preview[col].count()
                                                        total = len(df_preview)
                                                        completeness = (non_null / total) * 100
                                                        col_info.append({
                                                            'Column': col,
                                                            'Data Type': dtype_str,
                                                            'Non-Null Count': f"{non_null:,}",
                                                            'Completeness': f"{completeness:.1f}%"
                                                        })
                                                    
                                                    st.dataframe(pd.DataFrame(col_info), use_container_width=True)
                                                
                                                # Row display controls
                                                col1, col2 = st.columns([3, 1])
                                                with col1:
                                                    rows_to_show = st.selectbox(
                                                        "Rows to display:",
                                                        [10, 25, 50, 100, "All"],
                                                        index=3,  # Default to 100
                                                        key="preview_rows"
                                                    )
                                                
                                                with col2:
                                                    show_row_numbers = st.checkbox("Show row numbers", value=True)
                                                
                                                # Display the data table
                                                if rows_to_show == "All":
                                                    display_df = df_preview
                                                else:
                                                    display_df = df_preview.head(rows_to_show)
                                                
                                                if show_row_numbers:
                                                    display_df = display_df.reset_index()
                                                    display_df.rename(columns={'index': 'Row #'}, inplace=True)
                                                
                                                # Data quality highlighting
                                                def highlight_quality_issues(df):
                                                    """Highlight rows with data quality issues"""
                                                    # Create a DataFrame of same shape filled with empty strings
                                                    styled_df = pd.DataFrame('', index=df.index, columns=df.columns)
                                                    
                                                    # Highlight missing values
                                                    for col in df.columns:
                                                        mask = df[col].isna()
                                                        styled_df.loc[mask, col] = 'background-color: #ffcccc'
                                                    
                                                    # Highlight potential outliers in amount column
                                                    if 'amount' in df.columns:
                                                        try:
                                                            amount_col = pd.to_numeric(df['amount'], errors='coerce')
                                                            Q1 = amount_col.quantile(0.25)
                                                            Q3 = amount_col.quantile(0.75)
                                                            IQR = Q3 - Q1
                                                            outlier_mask = (amount_col < (Q1 - 1.5 * IQR)) | (amount_col > (Q3 + 1.5 * IQR))
                                                            styled_df.loc[outlier_mask, 'amount'] = 'background-color: #ffffcc'
                                                        except:
                                                            pass
                                                    
                                                    return styled_df
                                                
                                                # Apply styling and display
                                                styled_df = display_df.style.apply(highlight_quality_issues, axis=None)
                                                st.dataframe(styled_df, use_container_width=True)
                                                
                                                # Legend for highlighting
                                                st.markdown("**Legend:** 🔴 Missing values (light red) | 🟡 Potential outliers (light yellow)")
                                                
                                                # Download options
                                                st.markdown("---")
                                                st.markdown("**💾 Download Processed Data**")
                                                
                                                col1, col2 = st.columns(2)
                                                
                                                with col1:
                                                    # CSV download
                                                    csv_data = df_preview.to_csv(index=False)
                                                    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
                                                    csv_filename = f"processed_data_{timestamp}.csv"
                                                    
                                                    st.download_button(
                                                        label="📄 Download as CSV",
                                                        data=csv_data,
                                                        file_name=csv_filename,
                                                        mime="text/csv",
                                                        help="Download processed data in CSV format"
                                                    )
                                                
                                                with col2:
                                                    # Excel download
                                                    import io
                                                    excel_buffer = io.BytesIO()
                                                    with pd.ExcelWriter(excel_buffer, engine='openpyxl') as writer:
                                                        df_preview.to_excel(writer, index=False, sheet_name='Processed Data')
                                                    excel_data = excel_buffer.getvalue()
                                                    excel_filename = f"processed_data_{timestamp}.xlsx"
                                                    
                                                    st.download_button(
                                                        label="📊 Download as Excel",
                                                        data=excel_data,
                                                        file_name=excel_filename,
                                                        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                                        help="Download processed data in Excel format"
                                                    )
                                                
                                                # Data quality summary from processing
                                                if st.session_state.quality_summary and 'error' not in st.session_state.quality_summary:
                                                    st.markdown("---")
                                                    with st.expander("📈 Data Quality Details"):
                                                        quality_data = st.session_state.quality_summary
                                                        
                                                        st.markdown(f"**Overall Quality Score:** {quality_data['data_quality_score']:.1f}/100")
                                                        
                                                        if quality_data.get('recommendations'):
                                                            st.markdown("**Recommendations:**")
                                                            for rec in quality_data['recommendations']:
                                                                st.markdown(f"- {rec}")
                                                        
                                                        # Show processing warnings if available
                                                        if st.session_state.processing_results:
                                                            warnings = []
                                                            for step, result in st.session_state.processing_results.items():
                                                                if not result.get('success', True):
                                                                    warnings.append(f"{step}: {result.get('error', 'Unknown error')}")
                                                            
                                                            if warnings:
                                                                st.markdown("**Processing Warnings:**")
                                                                for warning in warnings:
                                                                    st.warning(warning)
                                            else:
                                                st.info("No processed data available. Please upload and process a file first.")
                                        
                                        else:
                                            st.warning("⚠️ Data structure validation found issues:")
                                            
                                            # Show available columns for debugging
                                            st.markdown("**Available columns in your file:**")
                                            st.markdown(f"`{', '.join(validation_results['columns'])}`")
                                            st.markdown("---")
                                            
                                            # Show validation errors
                                            validations = validation_results['validations']
                                            for col_type, validation in validations.items():
                                                if not validation['valid']:
                                                    st.error(f"❌ {col_type.title()}: {validation['error']}")
                                                    if validation['sample']:
                                                        st.markdown(f"   Sample values: {validation['sample']}")
                                            
                                            # Show column mapping interface
                                            st.markdown("**🔧 Manual Column Mapping**")
                                            st.markdown("Please map your columns to the required fields:")
                                            
                                            available_columns = [''] + validation_results['columns']
                                            
                                            # Create column mapping selectors
                                            col1, col2, col3 = st.columns(3)
                                            
                                            with col1:
                                                date_mapping = st.selectbox(
                                                    "Date Column:",
                                                    available_columns,
                                                    index=available_columns.index(validation_results['mappings']['date']) if validation_results['mappings']['date'] in available_columns else 0,
                                                    key="date_column_mapping"
                                                )
                                            
                                            with col2:
                                                account_mapping = st.selectbox(
                                                    "Account Column:",
                                                    available_columns,
                                                    index=available_columns.index(validation_results['mappings']['account']) if validation_results['mappings']['account'] in available_columns else 0,
                                                    key="account_column_mapping"
                                                )
                                            
                                            with col3:
                                                amount_mapping = st.selectbox(
                                                    "Amount Column:",
                                                    available_columns,
                                                    index=available_columns.index(validation_results['mappings']['amount']) if validation_results['mappings']['amount'] in available_columns else 0,
                                                    key="amount_column_mapping"
                                                )
                                            
                                            # Re-validate with manual mappings
                                            if st.button("🔄 Re-validate with Selected Mappings"):
                                                manual_mappings = {
                                                    'date': date_mapping if date_mapping else None,
                                                    'account': account_mapping if account_mapping else None,
                                                    'amount': amount_mapping if amount_mapping else None
                                                }
                                                
                                                # Validate manual mappings
                                                date_val = validate_date_column(df, manual_mappings['date'])
                                                amount_val = validate_amount_column(df, manual_mappings['amount'])
                                                account_val = {'valid': manual_mappings['account'] is not None, 'error': None}
                                                
                                                if date_val['valid'] and amount_val['valid'] and account_val['valid']:
                                                    st.success("✅ Manual column mapping validation passed!")
                                                    # Update session state with manual mappings
                                                    validation_results['mappings'] = manual_mappings
                                                    validation_results['overall_valid'] = True
                                                    st.session_state.validation_results = validation_results
                                                    st.rerun()
                                                else:
                                                    st.error("❌ Manual mapping validation failed. Please check your column selections.")
                                    
                                    except Exception as e:
                                        st.error(f"❌ Error reading file data: {str(e)}")
                                        st.markdown("Please ensure your file is a valid CSV or Excel file with proper formatting.")
                                    
                            except Exception as e:
                                st.error(f"❌ File appears to be corrupted or unreadable: {str(e)}")
                                
            except MemoryError:
                st.error("❌ File is too large to process. Please choose a smaller file or contact support.")
            except Exception as e:
                st.error(f"❌ An error occurred while processing the file: {str(e)}")
                
        else:
            # Clear session state if no file uploaded
            if 'uploaded_file' in st.session_state:
                st.session_state.uploaded_file = None
        
    with tab2:
        st.header("🔍 Movement Detection & Insights")
        
        # Check if movement analysis is available
        if 'movement_analysis' in st.session_state and st.session_state.movement_analysis:
            movement_data = st.session_state.movement_analysis
            
            if movement_data['success']:
                st.success("✅ Movement detection analysis completed!")
                
                # Executive Summary Section
                st.markdown("---")
                st.markdown("## 📋 Executive Summary")
                
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    total_movements = len(movement_data.get('ranked_movements', [])) if movement_data.get('ranked_movements') is not None else 0
                    st.metric("Significant Movements", total_movements)
                
                with col2:
                    critical_count = 0
                    if movement_data.get('ranked_movements') is not None:
                        critical_count = len(movement_data['ranked_movements'][movement_data['ranked_movements']['significance'] == 'Critical'])
                    st.metric("Critical Issues", critical_count, delta=f"🚨" if critical_count > 0 else "✅")
                
                with col3:
                    account_flags = len(movement_data.get('account_flags', []))
                    st.metric("Account Flags", account_flags)
                
                with col4:
                    # Monthly analysis coverage
                    monthly_stats = movement_data.get('summary_stats', {}).get('monthly_summary', {})
                    accounts_analyzed = monthly_stats.get('accounts_processed', 0)
                    st.metric("Accounts Analyzed", accounts_analyzed)
                
                # Top Significant Movements Section
                if movement_data.get('ranked_movements') is not None and len(movement_data['ranked_movements']) > 0:
                    st.markdown("---")
                    st.markdown("## 🎯 Top Significant Movements")
                    
                    ranked_movements = movement_data['ranked_movements']
                    top_movements = ranked_movements.head(10)
                    
                    for idx, row in top_movements.iterrows():
                        # Determine significance color
                        if row['significance'] == 'Critical':
                            alert_type = "🚨"
                        elif row['significance'] == 'High':
                            alert_type = "⚠️"
                        else:
                            alert_type = "📊"
                        
                        with st.container():
                            col1, col2, col3 = st.columns([2, 1, 1])
                            
                            with col1:
                                st.markdown(f"**{alert_type} {row['account']}**")
                                st.caption(f"{row['movement_type']} | {row['current_period']} vs {row['previous_period']}")
                            
                            with col2:
                                change_direction = "📈" if row['percentage_change'] > 0 else "📉"
                                st.metric(
                                    "Change",
                                    f"{row['percentage_change']:+.1f}%",
                                    delta=f"{change_direction}"
                                )
                            
                            with col3:
                                st.metric(
                                    "Amount Impact",
                                    f"${row['absolute_change']:+,.0f}",
                                    delta=f"Score: {row['materiality_score']:.0f}"
                                )
                            
                            # Progress bar for materiality score
                            score_normalized = min(row['materiality_score'] / 100, 1.0)
                            st.progress(score_normalized)
                            
                            # AI Commentary Section
                            initialize_commentary_session_state()
                            
                            # Create movement data dictionary for commentary generation
                            movement_dict = {
                                'account': row['account'],
                                'percentage_change': row['percentage_change'],
                                'absolute_change': row['absolute_change'],
                                'current_amount': row['current_amount'],
                                'previous_amount': row['previous_amount'],
                                'movement_type': row['movement_type'],
                                'significance': row['significance']
                            }
                            
                            # Generate or retrieve commentary (using index to ensure unique keys)
                            movement_key = f"{row['account']}_{row['movement_type']}_{idx}"
                            
                            if movement_key not in st.session_state.generated_commentary:
                                with st.spinner("🤖 Generating AI commentary..."):
                                    success, commentary = generate_movement_commentary(movement_dict)
                                    st.session_state.generated_commentary[movement_key] = {
                                        'commentary': commentary,
                                        'success': success,
                                        'timestamp': pd.Timestamp.now()
                                    }
                            
                            # Display commentary
                            commentary_data = st.session_state.generated_commentary[movement_key]
                            
                            with st.expander("🤖 AI Commentary", expanded=True):
                                if commentary_data['success']:
                                    st.markdown(format_commentary_for_streamlit(commentary_data['commentary'], movement_dict))
                                else:
                                    st.markdown(commentary_data['commentary'])
                                    st.caption("⚠️ Generated using fallback analysis")
                                
                                # Regenerate button
                                col_a, col_b = st.columns([1, 1])
                                with col_a:
                                    if st.button(f"🔄 Regenerate", key=f"regen_{movement_key}"):
                                        with st.spinner("🤖 Regenerating commentary..."):
                                            success, new_commentary = generate_movement_commentary(movement_dict, use_cache=False)
                                            st.session_state.generated_commentary[movement_key] = {
                                                'commentary': new_commentary,
                                                'success': success,
                                                'timestamp': pd.Timestamp.now()
                                            }
                                            st.rerun()
                                
                                with col_b:
                                    generation_time = commentary_data['timestamp']
                                    st.caption(f"Generated: {generation_time.strftime('%H:%M:%S')}")
                            
                            st.markdown("---")
                
                # Account Flags Section
                if movement_data.get('account_flags') and len(movement_data['account_flags']) > 0:
                    st.markdown("## 🏷️ Account Status Flags")
                    
                    account_flags = movement_data['account_flags']
                    flags_df = pd.DataFrame(account_flags)
                    flag_summary = flags_df['flag_type'].value_counts()
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        new_count = flag_summary.get('New', 0)
                        st.metric("🆕 New Accounts", new_count)
                        if new_count > 0:
                            new_accounts = flags_df[flags_df['flag_type'] == 'New']['account'].tolist()
                            with st.expander(f"View {new_count} New Accounts"):
                                for account in new_accounts:
                                    st.markdown(f"• {account}")
                    
                    with col2:
                        discontinued_count = flag_summary.get('Discontinued', 0)
                        st.metric("🔴 Discontinued", discontinued_count)
                        if discontinued_count > 0:
                            discontinued_accounts = flags_df[flags_df['flag_type'] == 'Discontinued']['account'].tolist()
                            with st.expander(f"View {discontinued_count} Discontinued Accounts"):
                                for account in discontinued_accounts:
                                    st.markdown(f"• {account}")
                    
                    with col3:
                        insufficient_count = flag_summary.get('Insufficient History', 0)
                        st.metric("⚠️ Limited History", insufficient_count)
                        if insufficient_count > 0:
                            insufficient_accounts = flags_df[flags_df['flag_type'] == 'Insufficient History']['account'].tolist()
                            with st.expander(f"View {insufficient_count} Limited History Accounts"):
                                for account in insufficient_accounts:
                                    st.markdown(f"• {account}")
            
            else:
                st.error("❌ Movement detection analysis failed")
                if movement_data.get('errors'):
                    st.markdown("**Errors encountered:**")
                    for error in movement_data['errors']:
                        st.error(f"• {error}")
                elif movement_data.get('error'):
                    st.error(f"• {movement_data['error']}")
        
        else:
            st.info("📊 **Movement Detection Ready**")
            st.markdown("Upload and process your financial data in the **Data Preview** tab to see movement analysis here.")
            st.markdown("---")
            st.markdown("**🎯 What you'll see:**")
            st.markdown("- **Significant Movements:** MoM changes >10%, YoY changes >15%")
            st.markdown("- **Account Flags:** New, discontinued, or limited history accounts")
            st.markdown("- **Materiality Ranking:** Top movements by impact and percentage")
            st.markdown("- **Executive Summary:** Key insights and alerts for immediate attention")
        
    with tab3:
        st.header("Financial Visualizations")
        st.info("Interactive charts and visual reports will be displayed here")
        st.markdown("**Chart types:**")
        st.markdown("- Trend analysis (Seaborn)")
        st.markdown("- Year-over-year comparisons")
        st.markdown("- Waterfall charts (Plotly)")
        st.markdown("- Month-over-month bridges")
        st.markdown("---")
        st.markdown("📈 **Coming Soon:** Dynamic chart generation")
        
    with tab4:
        st.header("Forecasting")
        st.info("Simple forecasting tools will be available here")
        st.markdown("**Capabilities:**")
        st.markdown("- Manual assumption input")
        st.markdown("- Line-level projections")
        st.markdown("- Trend variance analysis")
        st.markdown("---")
        st.markdown("🔮 **Coming Soon:** AI-assisted forecasting")


if __name__ == "__main__":
    main()