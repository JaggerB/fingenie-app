"""
FinGenie - Progressive Loading Version
This version loads features incrementally to identify what's causing the main app to hang.
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import numpy as np # Added for np.number
import os

# Import Story 5.2 query engine functions
try:
    from query_engine import (
        parse_natural_language_query,
        extract_entities,
        classify_query_intent,
        process_query_context,
        extract_relevant_data,
        filter_data_by_parameters,
        aggregate_data_for_analysis,
        validate_data_availability,
        handle_missing_data,
        extract_movement_analysis_data,
        extract_anomaly_analysis_data,
        filter_data_by_significance,
        aggregate_data_by_category,
        validate_data_completeness,
        generate_contextual_response,
        manage_conversation_context
    )
    QUERY_ENGINE_AVAILABLE = True
except ImportError:
    QUERY_ENGINE_AVAILABLE = False
    st.warning("Query engine not available. Using placeholder functions.")

def initialize_session_state():
    """Initialize session state variables."""
    if 'messages' not in st.session_state:
        st.session_state.messages = []
    if 'final_processed_data' not in st.session_state:
        st.session_state.final_processed_data = pd.DataFrame()
    if 'use_llm' not in st.session_state:
        st.session_state.use_llm = True

# Optional OpenAI client (used for higher-quality answers)
def _get_openai_client():
    try:
        from openai import OpenAI  # openai>=1.0.0
    except Exception:
        return None, False, None

    # Prefer Streamlit secrets if present, fallback to env
    api_key = os.environ.get("OPENAI_API_KEY")
    # Session override (set from UI)
    try:
        if hasattr(st, "session_state") and st.session_state.get("OPENAI_API_KEY_OVERRIDE"):
            api_key = st.session_state.get("OPENAI_API_KEY_OVERRIDE") or api_key
    except Exception:
        pass
    try:
        # st.secrets is available at runtime inside Streamlit
        if not api_key and hasattr(st, "secrets"):
            api_key = st.secrets.get("OPENAI_API_KEY", None)
    except Exception:
        pass

    if not api_key:
        return None, False, None

    model_name = os.environ.get("OPENAI_MODEL")
    try:
        if not model_name and hasattr(st, "secrets"):
            model_name = st.secrets.get("OPENAI_MODEL", None)
    except Exception:
        pass

    try:
        client = OpenAI(api_key=api_key)
        return client, True, (model_name or "gpt-4o-mini")
    except Exception:
        return None, False, None

def _summarize_dataframe_for_prompt(dataframe: pd.DataFrame, max_rows: int = 5) -> dict:
    """Create a compact, safe summary of a DataFrame for LLM prompting."""
    if dataframe is None or dataframe.empty:
        return {
            "columns": [],
            "row_count": 0,
            "samples": [],
            "numeric_overview": {},
            "account_overview": {},
            "time_overview": {}
        }

    summary: dict = {}
    # Column types
    column_types = {col: str(dtype) for col, dtype in dataframe.dtypes.items()}
    summary["columns"] = column_types
    summary["row_count"] = int(len(dataframe))

    # Sample rows (head)
    samples = dataframe.head(max_rows).copy()
    # Ensure serializable types
    summary["samples"] = samples.fillna("").astype(str).to_dict(orient="records")

    # Numeric overview for Amount if present
    numeric_overview = {}
    if "Amount" in dataframe.columns:
        amounts = pd.to_numeric(dataframe["Amount"], errors="coerce").dropna()
        if not amounts.empty:
            numeric_overview = {
                "sum": float(amounts.sum()),
                "mean": float(amounts.mean()),
                "min": float(amounts.min()),
                "max": float(amounts.max()),
                "count": int(amounts.shape[0])
            }
    summary["numeric_overview"] = numeric_overview

    # Account overview (top totals)
    account_overview = {}
    if "Account" in dataframe.columns and "Amount" in dataframe.columns:
        try:
            totals = (
                dataframe.groupby("Account")["Amount"].sum().sort_values(ascending=False).head(10)
            )
            account_overview = {str(k): float(v) for k, v in totals.items()}
        except Exception:
            account_overview = {}
    summary["account_overview"] = account_overview

    # Time overview (months)
    time_overview = {}
    if "Month" in dataframe.columns and "Amount" in dataframe.columns:
        try:
            month_totals = (
                dataframe.groupby("Month")["Amount"].sum().sort_values(ascending=False).head(12)
            )
            time_overview = {str(k): float(v) for k, v in month_totals.items()}
        except Exception:
            time_overview = {}
    summary["time_overview"] = time_overview

    return summary

def _build_llm_system_prompt() -> str:
    """System prompt to enforce high-quality, data-grounded answers."""
    return (
        "You are FinGenie, a financial analysis assistant. "
        "Answer ONLY using the provided dataset context. If the data does not contain the answer, say so clearly. "
        "Prefer concise, high-signal responses. Include small calculations inline where helpful (e.g., percentage = part / total). "
        "Format with short sections and bullet points using clear labels. Avoid speculation."
    )

def _build_llm_user_prompt(query: str, dataset_summary: dict, relevant_summary: dict) -> str:
    """Compose a compact user prompt containing dataset summaries and the user question."""
    import json
    safe_dataset = json.dumps(dataset_summary, ensure_ascii=False)[:5000]
    safe_relevant = json.dumps(relevant_summary, ensure_ascii=False)[:5000]
    return (
        f"User question: {query}\n\n"
        "Global dataset summary (schema, samples, totals):\n"
        f"{safe_dataset}\n\n"
        "Filtered subset relevant to the question (if any):\n"
        f"{safe_relevant}\n\n"
        "Instructions: Use numbers from the relevant subset when available; otherwise use the global summary. "
        "Be precise and helpful to a finance stakeholder. Provide 4-8 bullets maximum with key figures and short explanations."
    )

def _generate_llm_answer(query: str, full_df: pd.DataFrame, relevant_df: pd.DataFrame) -> str:
    """Call the LLM to produce a data-grounded answer. Falls back gracefully on errors."""
    client, available, model_name = _get_openai_client()
    if not available or client is None:
        return "LLM is not configured. Please set OPENAI_API_KEY (or Streamlit secrets) to enable AI-enhanced answers."

    try:
        dataset_summary = _summarize_dataframe_for_prompt(full_df)
        relevant_summary = _summarize_dataframe_for_prompt(relevant_df if relevant_df is not None else pd.DataFrame())

        system_prompt = _build_llm_system_prompt()
        user_prompt = _build_llm_user_prompt(query, dataset_summary, relevant_summary)

        completion = client.chat.completions.create(
            model=model_name,
            temperature=0.2,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ],
        )
        answer = completion.choices[0].message.content.strip() if completion and completion.choices else ""
        if not answer:
            return "I couldn't generate an answer from the model. Please try rephrasing your question."
        return answer
    except Exception as exc:
        return f"I couldn't contact the AI model ({exc}). Falling back to a simpler analysis."

def create_upload_tab():
    """Create the upload and preview tab."""
    st.header("📊 Data Upload & Preview")
    st.info("Upload your financial data to begin analysis")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload CSV or Excel files"
    )
    
    if uploaded_file is not None:
        try:
            with st.spinner('Processing file...'):
                if uploaded_file.name.endswith('.csv'):
                    df = pd.read_csv(uploaded_file)
                else:
                    df = pd.read_excel(uploaded_file)
                
                # Clean and process the data
                processed_df = clean_and_process_data(df)
                
                st.session_state.final_processed_data = processed_df
                st.success(f"✅ File uploaded successfully: {uploaded_file.name}")
                st.write(f"**Original Data Shape:** {df.shape}")
                st.write(f"**Processed Data Shape:** {processed_df.shape}")
                st.write(f"**Original Columns:** {list(df.columns)}")
                st.write(f"**Processed Columns:** {list(processed_df.columns)}")
                
                # Show preview
                st.subheader("Original Data Preview")
                st.dataframe(df.head())
                
                st.subheader("Processed Data Preview")
                st.dataframe(processed_df.head())
                
                # Show some debugging info
                if 'Month' in processed_df.columns:
                    st.subheader("🔍 Month Information")
                    unique_months = processed_df['Month'].unique()
                    st.write(f"**Unique Months Found:** {list(unique_months)}")
                    st.write(f"**Number of Unique Months:** {len(unique_months)}")
                
        except Exception as e:
            st.error(f"Error processing file: {str(e)}")

def clean_and_process_data(df):
    """Clean and process the uploaded data to extract financial information."""
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Create a copy to work with
    processed_df = df.copy()
    
    try:
        # Check if this is a financial statement format
        if 'Profit and Loss' in processed_df.columns:
            processed_df = process_financial_statement_format(processed_df)
        else:
            # Try to detect columns automatically
            processed_df = auto_detect_columns(processed_df)
        
        # Ensure we have the required columns
        if 'Amount' not in processed_df.columns:
            processed_df = create_amount_column(processed_df)
        
        if 'Account' not in processed_df.columns:
            processed_df = create_account_column(processed_df)
        
        # Clean up any remaining issues
        processed_df = clean_final_data(processed_df)
        
    except Exception as e:
        st.warning(f"Data processing encountered issues: {str(e)}. Using original data.")
        return df
    
    return processed_df

def process_financial_statement_format(df):
    """Process financial statement format with monthly columns."""
    result_data = []
    
    # Find the row with month headers (like "Dec-22", "Nov-22", etc.)
    month_row = None
    for idx, row in df.iterrows():
        if pd.notna(row['Profit and Loss']) and row['Profit and Loss'] == 'None':
            # Check if the next columns contain month-year data
            month_columns = []
            for col in df.columns[1:]:  # Skip the first column
                if pd.notna(row[col]) and isinstance(row[col], str):
                    if any(month in row[col].lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                        month_columns.append(col)
            
            if len(month_columns) > 0:
                month_row = idx
                break
    
    if month_row is not None:
        # Extract month names from the month row
        months = []
        for col in df.columns[1:]:
            if pd.notna(df.iloc[month_row][col]) and isinstance(df.iloc[month_row][col], str):
                month_value = df.iloc[month_row][col]
                # Clean up the month name
                if any(month in month_value.lower() for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                    months.append(month_value)
                else:
                    months.append(None)
            else:
                months.append(None)
        
        # Process each row after the month row
        for idx in range(month_row + 1, len(df)):
            row = df.iloc[idx]
            account_name = row['Profit and Loss']
            
            # Skip empty rows or header rows
            if pd.isna(account_name) or account_name == 'None' or not isinstance(account_name, str):
                continue
            
            # Skip total rows or section headers
            if any(keyword in account_name.lower() for keyword in ['total', 'less', 'gross', 'net', 'for the month']):
                continue
            
            # Extract amounts for each month
            for col_idx, col in enumerate(df.columns[1:], 0):  # Start from 0 for proper indexing
                if col_idx < len(months) and months[col_idx] is not None:
                    amount = row[col]
                    
                    # Convert amount to numeric
                    if pd.notna(amount):
                        try:
                            # Handle currency formatting (e.g., "GBP 76,103.33")
                            if isinstance(amount, str):
                                # Remove currency symbols and commas
                                amount_str = amount.replace('GBP', '').replace('$', '').replace(',', '').strip()
                                amount = float(amount_str)
                            else:
                                amount = float(amount)
                            
                            if amount != 0:  # Only add non-zero amounts
                                result_data.append({
                                    'Account': account_name,
                                    'Amount': amount,
                                    'Month': months[col_idx]
                                })
                        except (ValueError, TypeError):
                            continue
    
    # If we found data, create DataFrame
    if result_data:
        result_df = pd.DataFrame(result_data)
        return result_df
    else:
        # Fallback: try to extract any numeric data with better month handling
        return extract_any_numeric_data(df)

def extract_any_numeric_data(df):
    """Extract any numeric data from the DataFrame as a fallback."""
    result_data = []
    
    # Try to find month information in column names or first few rows
    month_names = []
    
    # Check if column names contain month information
    for col in df.columns[1:]:  # Skip the first column
        col_str = str(col).lower()
        if any(month in col_str for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
            month_names.append(str(col))
        else:
            # Check if this column has month data in the first few rows
            for idx in range(min(5, len(df))):
                cell_value = str(df.iloc[idx][col]).lower()
                if any(month in cell_value for month in ['jan', 'feb', 'mar', 'apr', 'may', 'jun', 'jul', 'aug', 'sep', 'oct', 'nov', 'dec']):
                    month_names.append(str(df.iloc[idx][col]))
                    break
            else:
                # If no month found, use a generic name
                month_names.append(f"Period {len(month_names) + 1}")
    
    for idx, row in df.iterrows():
        account_name = row.get('Profit and Loss', f'Row_{idx}')
        
        if pd.isna(account_name) or account_name == 'None':
            continue
        
        for col_idx, col in enumerate(df.columns[1:]):  # Skip the first column
            amount = row[col]
            
            if pd.notna(amount):
                try:
                    if isinstance(amount, str):
                        # Try to extract numeric value from string
                        import re
                        numeric_match = re.search(r'[\d,]+\.?\d*', amount.replace(',', ''))
                        if numeric_match:
                            amount = float(numeric_match.group().replace(',', ''))
                        else:
                            continue
                    else:
                        amount = float(amount)
                    
                    if amount != 0:
                        # Use month name if available, otherwise use column name
                        month_name = month_names[col_idx] if col_idx < len(month_names) else str(col)
                        result_data.append({
                            'Account': account_name,
                            'Amount': amount,
                            'Month': month_name
                        })
                except (ValueError, TypeError):
                    continue
    
    if result_data:
        return pd.DataFrame(result_data)
    else:
        # Return a minimal DataFrame
        return pd.DataFrame({
            'Account': ['Sample Account'],
            'Amount': [0],
            'Month': ['Unknown']
        })

def auto_detect_columns(df):
    """Automatically detect and rename columns."""
    # Look for numeric columns that could be amounts
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    # Look for text columns that could be accounts
    text_columns = df.select_dtypes(include=['object']).columns.tolist()
    
    if numeric_columns and text_columns:
        # Use the first numeric column as Amount
        amount_col = numeric_columns[0]
        # Use the first text column as Account
        account_col = text_columns[0]
        
        result_df = df[[account_col, amount_col]].copy()
        result_df.columns = ['Account', 'Amount']
        return result_df
    
    return df

def create_amount_column(df):
    """Create an Amount column from numeric data."""
    # Look for any numeric columns
    numeric_columns = df.select_dtypes(include=[np.number]).columns.tolist()
    
    if numeric_columns:
        # Use the first numeric column
        df['Amount'] = df[numeric_columns[0]]
    else:
        # Create a dummy amount column
        df['Amount'] = 0
    
    return df

def create_account_column(df):
    """Create an Account column from text data."""
    # Look for any text columns
    text_columns = df.select_dtypes(include=['object']).columns.tolist()
    
    if text_columns:
        # Use the first text column
        df['Account'] = df[text_columns[0]]
    else:
        # Create a dummy account column
        df['Account'] = 'Unknown Account'
    
    return df

def create_simplified_dataframe(df):
    """Create a simplified DataFrame when processing fails."""
    # Try to extract any meaningful data
    result_data = []
    
    for idx, row in df.iterrows():
        for col in df.columns:
            if pd.notna(row[col]):
                if isinstance(row[col], (int, float)) and row[col] != 0:
                    result_data.append({
                        'Account': f'Row {idx} - {col}',
                        'Amount': row[col]
                    })
    
    if result_data:
        return pd.DataFrame(result_data)
    else:
        # Return a minimal DataFrame
        return pd.DataFrame({
            'Account': ['Sample Account'],
            'Amount': [0]
        })

def clean_final_data(df):
    """Clean the final processed data."""
    if df is None or df.empty:
        return pd.DataFrame()
    
    # Remove rows with missing or invalid data
    df = df.dropna(subset=['Amount'])
    
    # Convert Amount to numeric
    df['Amount'] = pd.to_numeric(df['Amount'], errors='coerce')
    df = df.dropna(subset=['Amount'])
    
    # Remove zero amounts
    df = df[df['Amount'] != 0]
    
    return df

# Add modern CSS styling
def add_custom_css():
    """Add custom CSS for modern, clean design."""
    st.markdown("""
    <style>
    /* Modern, clean design */
    .main {
        background-color: #f8f9fa;
    }
    
    /* Chat interface styling */
    .chat-container {
        background: white;
        border-radius: 12px;
        padding: 20px;
        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        margin: 10px 0;
    }
    
    /* Message bubbles */
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 12px 16px;
        border-radius: 18px 18px 4px 18px;
        margin: 8px 0;
        max-width: 80%;
        margin-left: auto;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    .assistant-message {
        background: white;
        color: #333;
        padding: 12px 16px;
        border-radius: 18px 18px 18px 4px;
        margin: 8px 0;
        max-width: 80%;
        border: 1px solid #e1e5e9;
        box-shadow: 0 2px 8px rgba(0,0,0,0.05);
    }
    
    /* Metrics styling */
    .metric-card {
        background: white;
        border-radius: 8px;
        padding: 16px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        border-left: 4px solid #667eea;
    }
    
    /* Header styling */
    .main-header {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 20px;
        border-radius: 12px;
        margin-bottom: 20px;
    }
    
    /* Tab styling */
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    
    .stTabs [data-baseweb="tab"] {
        background-color: white;
        border-radius: 8px 8px 0 0;
        padding: 8px 16px;
        border: 1px solid #e1e5e9;
    }
    
    .stTabs [aria-selected="true"] {
        background-color: #667eea;
        color: white;
    }
    
    /* Input styling */
    .stTextInput > div > div > input {
        border-radius: 20px;
        border: 2px solid #e1e5e9;
    }
    
    .stTextInput > div > div > input:focus {
        border-color: #667eea;
        box-shadow: 0 0 0 2px rgba(102, 126, 234, 0.2);
    }
    
    /* Button styling */
    .stButton > button {
        border-radius: 20px;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        border: none;
        color: white;
        padding: 8px 24px;
        font-weight: 600;
    }
    
    .stButton > button:hover {
        background: linear-gradient(135deg, #5a6fd8 0%, #6a4190 100%);
        transform: translateY(-1px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    </style>
    """, unsafe_allow_html=True)

def create_modern_chat_interface():
    """Create a ChatGPT-style chat interface with proper formatting and smooth UX."""
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2rem; font-weight: 700;">💬 Chat Interface</h1>
        <p style="margin: 5px 0 0 0; opacity: 0.9;">Ask questions about your financial data</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Check if query engine is available
    try:
        from query_engine import parse_natural_language_query, extract_relevant_data, generate_contextual_response
        st.success("✅ Query Engine Loaded Successfully!")
        query_engine_available = True
    except ImportError:
        st.warning("⚠️ Query Engine not available. Using basic responses.")
        query_engine_available = False
    
    # Initialize chat history
    if "messages" not in st.session_state:
        st.session_state.messages = []
    
    # Create a container for the chat area
    chat_container = st.container()
    
    with chat_container:
        # Display chat messages in ChatGPT style
        if st.session_state.messages:
            for message in st.session_state.messages:
                if message["role"] == "user":
                    # User message - right aligned with blue background
                    st.markdown(f"""
                    <div style="display: flex; justify-content: flex-end; margin: 10px 0;">
                        <div style="background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 12px 16px; border-radius: 18px 18px 4px 18px; max-width: 70%; box-shadow: 0 2px 8px rgba(0,0,0,0.1);">
                            {message["content"]}
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
                else:
                    # AI message - left aligned with white background
                    st.markdown(f"""
                    <div style="display: flex; justify-content: flex-start; margin: 10px 0;">
                        <div style="background: white; color: #333; padding: 12px 16px; border-radius: 18px 18px 18px 4px; max-width: 70%; border: 1px solid #e1e5e9; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                            <div style="font-weight: 600; margin-bottom: 8px; color: #667eea;">🤖 FinGenie</div>
                            <div style="line-height: 1.5;">
                                {_format_response_content(message["content"])}
                            </div>
                        </div>
                    </div>
                    """, unsafe_allow_html=True)
        else:
            # Welcome message
            st.markdown("""
            <div style="text-align: center; padding: 40px 20px; color: #666;">
                <div style="font-size: 3rem; margin-bottom: 20px;">💬</div>
                <h3 style="color: #333; margin-bottom: 10px;">Welcome to FinGenie Chat</h3>
                <p style="font-size: 1.1rem; line-height: 1.5;">
                    Ask me anything about your financial data!<br>
                    Try questions like:<br>
                    • "What drove the increase in marketing expenses?"<br>
                    • "Show me the top expenses"<br>
                    • "What's our revenue trend?"
                </p>
            </div>
            """, unsafe_allow_html=True)
    
    # Chat input area - fixed at bottom
    st.markdown("---")
    
    # Create input area with modern styling using form
    with st.form(key="chat_form", clear_on_submit=True):
        col1, col2 = st.columns([6, 1])
        with col1:
            user_input = st.text_input(
                "Ask me about your financial data...",
                key="chat_input",
                placeholder="e.g., What drove the increase in marketing expenses?",
                label_visibility="collapsed"
            )
        with col2:
            submit_button = st.form_submit_button("Send", use_container_width=True)
    
    # Process user input when form is submitted
    if submit_button and user_input and user_input.strip():
        # Add user message to chat history
        st.session_state.messages.append({
            "role": "user", 
            "content": user_input.strip(),
            "timestamp": datetime.now().isoformat()
        })
        
        # Generate response
        with st.spinner("🤔 Processing your question..."):
            try:
                response = None
                if query_engine_available and 'final_processed_data' in st.session_state:
                    # Parse to get entities and relevant subset
                    parsed_query = parse_natural_language_query(user_input.strip())
                    relevant_data = pd.DataFrame()
                    if parsed_query:
                        relevant_data = extract_relevant_data(
                            st.session_state.final_processed_data,
                            parsed_query['entities']
                        )

                    # Prefer LLM answer if configured
                    if st.session_state.get('use_llm') and _get_openai_client()[1]:
                        response = _generate_llm_answer(
                            user_input.strip(),
                            st.session_state.final_processed_data,
                            relevant_data
                        )
                        # If model declined, fall back to deterministic
                        if response.startswith("LLM is not configured") or response.startswith("I couldn't contact the AI model"):
                            response = None

                    if not response:
                        # Deterministic fallback
                        if parsed_query and not relevant_data.empty:
                            if parsed_query['query_type'] == 'movement_explanation':
                                response = _generate_clean_movement_explanation(user_input.strip(), relevant_data, parsed_query['entities'])
                            elif parsed_query['query_type'] == 'data_summary':
                                response = _generate_clean_data_summary(user_input.strip(), relevant_data, parsed_query['entities'])
                            elif parsed_query['query_type'] == 'trend_analysis':
                                response = _generate_clean_trend_analysis(user_input.strip(), relevant_data, parsed_query['entities'])
                            else:
                                response = generate_contextual_response(user_input.strip(), relevant_data, parsed_query['entities'])
                        else:
                            response = "I couldn't find data related to your question. Try specifying an account or timeframe (e.g., 'marketing trend this quarter')."
                else:
                    response = "I don't have access to your financial data yet. Please upload your data in the 'Upload & Preview' tab first."
                    
            except Exception as e:
                response = f"I encountered an error while processing your query: {str(e)}. Please try rephrasing your question."
        
        # Add assistant response to chat history
        st.session_state.messages.append({
            "role": "assistant", 
            "content": response,
            "timestamp": datetime.now().isoformat()
        })
        
        # Rerun to update the chat display
        st.rerun()

def _format_response_content(content):
    """Format response content for clean display."""
    # First, let's handle the markdown formatting properly
    import re
    
    # Replace markdown bold with HTML strong tags
    formatted_content = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', content)
    
    # Replace newlines with <br> tags
    formatted_content = formatted_content.replace("\n", "<br>")
    
    # Replace bullet points
    formatted_content = formatted_content.replace("•", "•")
    
    # Add proper spacing for sections
    formatted_content = formatted_content.replace("📊", "<br><br>📊")
    formatted_content = formatted_content.replace("🏢", "<br><br>🏢")
    formatted_content = formatted_content.replace("📅", "<br><br>📅")
    formatted_content = formatted_content.replace("📈", "<br><br>📈")
    
    return formatted_content

def _generate_clean_movement_explanation(query, data, entities):
    """Generate clean movement explanation response without markdown."""
    if data.empty:
        return "I couldn't find any data related to your query about movements."
    
    # Check if Amount column exists
    if 'Amount' not in data.columns:
        return "I found data but it doesn't have an 'Amount' column. Please check your data structure."
    
    total_amount = data['Amount'].sum()
    count = len(data)
    average = data['Amount'].mean()
    
    # Determine the type of analysis based on the query
    query_lower = query.lower()
    
    if 'trend' in query_lower or 'pattern' in query_lower:
        # Trend analysis
        response = f"Based on the data, here's the trend analysis for your query: '{query}'\n\n"
        response += "📈 Trend Analysis:\n"
        response += f"• Total Amount: ${total_amount:,.2f}\n"
        response += f"• Number of Transactions: {count:,}\n"
        response += f"• Average Amount: ${average:,.2f}\n\n"
        
        # Add trend insights
        if 'Month' in data.columns and len(data['Month'].unique()) > 1:
            monthly_trend = data.groupby('Month')['Amount'].sum().sort_index()
            if len(monthly_trend) > 1:
                first_month = monthly_trend.iloc[0]
                last_month = monthly_trend.iloc[-1]
                trend_direction = "increasing" if last_month > first_month else "decreasing"
                trend_percentage = abs((last_month - first_month) / first_month * 100) if first_month != 0 else 0
                response += f"📊 Trend Direction: {trend_direction.title()} ({trend_percentage:.1f}% change)\n"
        
    elif 'drove' in query_lower or 'caused' in query_lower or 'increase' in query_lower or 'decrease' in query_lower:
        # Movement analysis
        response = f"Based on the data, here's what I found for your query: '{query}'\n\n"
        response += "📊 Movement Analysis:\n"
        response += f"• Total Amount: ${total_amount:,.2f}\n"
        response += f"• Number of Transactions: {count:,}\n"
        response += f"• Average Amount: ${average:,.2f}\n\n"
    else:
        # General analysis
        response = f"Based on the data, here's what I found for your query: '{query}'\n\n"
        response += "📊 Analysis:\n"
        response += f"• Total Amount: ${total_amount:,.2f}\n"
        response += f"• Number of Transactions: {count:,}\n"
        response += f"• Average Amount: ${average:,.2f}\n\n"
    
    # Check if Account column exists before using it
    if 'Account' in data.columns:
        try:
            account_breakdown = data.groupby('Account')['Amount'].sum().sort_values(ascending=False)
            response += "🏢 Breakdown by Account:\n"
            for account, amount in account_breakdown.head(5).items():
                percentage = (amount / total_amount * 100) if total_amount > 0 else 0
                response += f"• {account}: ${amount:,.2f} ({percentage:.1f}%)\n"
        except Exception:
            response += "Note: Unable to break down by account due to data structure issues.\n"
    else:
        response += "Note: No account information available in the data.\n"
    
    # Check if Month column exists and format it properly
    if 'Month' in data.columns:
        try:
            month_breakdown = data.groupby('Month')['Amount'].sum().sort_values(ascending=False)
            response += "\n📅 Breakdown by Month:\n"
            for month, amount in month_breakdown.head(5).items():
                # Clean up month name if it's showing as "Unnamed: X"
                if str(month).startswith('Unnamed:'):
                    month_display = f"Period {str(month).split(':')[1].strip()}"
                else:
                    month_display = str(month)
                percentage = (amount / total_amount * 100) if total_amount > 0 else 0
                response += f"• {month_display}: ${amount:,.2f} ({percentage:.1f}%)\n"
        except Exception:
            response += "\nNote: Unable to break down by month due to data structure issues.\n"
    
    return response

def _generate_clean_data_summary(query, data, entities):
    """Generate clean data summary response without markdown."""
    if data.empty:
        return "I couldn't find any data related to your query."
    
    # Check if Amount column exists
    if 'Amount' not in data.columns:
        return "I found data but it doesn't have an 'Amount' column. Please check your data structure."
    
    total_amount = data['Amount'].sum()
    count = len(data)
    average = data['Amount'].mean()
    
    # Determine the type of summary based on the query
    query_lower = query.lower()
    
    if 'trend' in query_lower or 'pattern' in query_lower:
        response = f"Here's the trend analysis for your query: '{query}'\n\n"
        response += "📈 Trend Summary:\n"
    elif 'revenue' in query_lower or 'income' in query_lower:
        response = f"Here's the revenue analysis for your query: '{query}'\n\n"
        response += "💰 Revenue Summary:\n"
    elif 'expense' in query_lower or 'cost' in query_lower:
        response = f"Here's the expense analysis for your query: '{query}'\n\n"
        response += "💸 Expense Summary:\n"
    else:
        response = f"Here's a summary of the data for your query: '{query}'\n\n"
        response += "📊 Summary Statistics:\n"
    
    response += f"• Total Amount: ${total_amount:,.2f}\n"
    response += f"• Number of Records: {count:,}\n"
    response += f"• Average Amount: ${average:,.2f}\n"
    
    # Add insights based on data
    if count > 1:
        min_amount = data['Amount'].min()
        max_amount = data['Amount'].max()
        response += f"• Range: ${min_amount:,.2f} to ${max_amount:,.2f}\n"
    
    # Add month information if available
    if 'Month' in data.columns:
        unique_months = data['Month'].nunique()
        response += f"• Number of Months: {unique_months}\n"
        
        # Show top months
        month_totals = data.groupby('Month')['Amount'].sum().sort_values(ascending=False)
        response += f"\n📅 Top Months by Amount:\n"
        for month, amount in month_totals.head(3).items():
            # Clean up month name if it's showing as "Unnamed: X"
            if str(month).startswith('Unnamed:'):
                month_display = f"Period {str(month).split(':')[1].strip()}"
            else:
                month_display = str(month)
            percentage = (amount / total_amount * 100) if total_amount > 0 else 0
            response += f"• {month_display}: ${amount:,.2f} ({percentage:.1f}%)\n"
    
    # Add account breakdown if available
    if 'Account' in data.columns:
        try:
            account_breakdown = data.groupby('Account')['Amount'].sum().sort_values(ascending=False)
            response += f"\n🏢 Top Accounts:\n"
            for account, amount in account_breakdown.head(3).items():
                percentage = (amount / total_amount * 100) if total_amount > 0 else 0
                response += f"• {account}: ${amount:,.2f} ({percentage:.1f}%)\n"
        except Exception:
            pass
    
    return response

def _generate_clean_trend_analysis(query, data, entities):
    """Generate clean trend analysis response."""
    if data.empty:
        return "I couldn't find any data related to your trend analysis query."
    
    # Check if Amount column exists
    if 'Amount' not in data.columns:
        return "I found data but it doesn't have an 'Amount' column. Please check your data structure."
    
    total_amount = data['Amount'].sum()
    count = len(data)
    average = data['Amount'].mean()
    
    response = f"Here's the trend analysis for your query: '{query}'\n\n"
    response += "📈 Trend Analysis:\n"
    response += f"• Total Amount: ${total_amount:,.2f}\n"
    response += f"• Number of Transactions: {count:,}\n"
    response += f"• Average Amount: ${average:,.2f}\n\n"
    
    # Add trend insights if we have time-based data
    if 'Month' in data.columns and len(data['Month'].unique()) > 1:
        try:
            monthly_trend = data.groupby('Month')['Amount'].sum().sort_index()
            if len(monthly_trend) > 1:
                first_month = monthly_trend.iloc[0]
                last_month = monthly_trend.iloc[-1]
                
                if first_month != 0:
                    trend_direction = "increasing" if last_month > first_month else "decreasing"
                    trend_percentage = abs((last_month - first_month) / first_month * 100)
                    response += f"📊 Trend Direction: {trend_direction.title()} ({trend_percentage:.1f}% change)\n"
                    
                    # Add trend description
                    if trend_percentage > 20:
                        response += f"📈 This represents a {'significant' if trend_percentage > 50 else 'moderate'} {trend_direction} trend.\n"
                    else:
                        response += f"📈 This represents a {'slight' if trend_percentage < 10 else 'moderate'} {trend_direction} trend.\n"
                
                # Show monthly breakdown
                response += f"\n📅 Monthly Breakdown:\n"
                for month, amount in monthly_trend.items():
                    if str(month).startswith('Unnamed:'):
                        month_display = f"Period {str(month).split(':')[1].strip()}"
                    else:
                        month_display = str(month)
                    percentage = (amount / total_amount * 100) if total_amount > 0 else 0
                    response += f"• {month_display}: ${amount:,.2f} ({percentage:.1f}%)\n"
        except Exception as e:
            response += f"Note: Unable to analyze monthly trends due to data structure issues.\n"
    else:
        response += "Note: No time-based data available for trend analysis.\n"
    
    # Add account breakdown if available
    if 'Account' in data.columns:
        try:
            account_breakdown = data.groupby('Account')['Amount'].sum().sort_values(ascending=False)
            response += f"\n🏢 Account Breakdown:\n"
            for account, amount in account_breakdown.head(5).items():
                percentage = (amount / total_amount * 100) if total_amount > 0 else 0
                response += f"• {account}: ${amount:,.2f} ({percentage:.1f}%)\n"
        except Exception:
            response += "Note: Unable to break down by account due to data structure issues.\n"
    
    return response

def create_executive_overview_tab():
    """Create the executive overview tab."""
    st.header("🔍 Executive Overview")
    st.info("This tab shows executive summary and key insights")
    
    processed_data = st.session_state.get('final_processed_data')
    if processed_data is not None and not processed_data.empty:
        st.success(f"✅ Data loaded: {len(processed_data)} records")
        
        # Show basic statistics
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Records", len(processed_data))
        with col2:
            if 'Amount' in processed_data.columns:
                total_amount = processed_data['Amount'].sum()
                st.metric("Total Amount", f"${total_amount:,.2f}")
            else:
                st.metric("Total Amount", "N/A")
        with col3:
            if 'Account' in processed_data.columns:
                unique_accounts = processed_data['Account'].nunique()
                st.metric("Unique Accounts", unique_accounts)
            else:
                st.metric("Unique Accounts", "N/A")
        
        # Show top accounts by amount
        if 'Amount' in processed_data.columns and 'Account' in processed_data.columns:
            st.subheader("📊 Top Accounts by Amount")
            top_accounts = processed_data.groupby('Account')['Amount'].sum().sort_values(ascending=False).head(10)
            
            # Create a bar chart
            st.bar_chart(top_accounts)
            
            # Show table
            st.dataframe(top_accounts.reset_index().rename(columns={'Amount': 'Total Amount'}))
        
        # Show data quality metrics
        st.subheader("🔍 Data Quality Metrics")
        col1, col2, col3 = st.columns(3)
        with col1:
            if 'Amount' in processed_data.columns:
                avg_amount = processed_data['Amount'].mean()
                st.metric("Average Amount", f"${avg_amount:,.2f}")
        with col2:
            if 'Amount' in processed_data.columns:
                max_amount = processed_data['Amount'].max()
                st.metric("Maximum Amount", f"${max_amount:,.2f}")
        with col3:
            if 'Amount' in processed_data.columns:
                min_amount = processed_data['Amount'].min()
                st.metric("Minimum Amount", f"${min_amount:,.2f}")
                
    else:
        st.warning("No data uploaded yet. Please upload data in the 'Upload & Preview' tab.")

def create_movement_analysis_tab():
    """Create the movement analysis tab."""
    st.header("📈 Movement Analysis")
    st.info("This tab shows movement analysis and trends")
    
    processed_data = st.session_state.get('final_processed_data')
    if processed_data is not None and not processed_data.empty:
        st.success(f"✅ Data available for movement analysis")
        
        if 'Amount' in processed_data.columns and 'Account' in processed_data.columns:
            # Show movement analysis
            st.subheader("📊 Account Movements")
            
            # Calculate movements (simplified - comparing to average)
            avg_by_account = processed_data.groupby('Account')['Amount'].mean()
            current_by_account = processed_data.groupby('Account')['Amount'].sum()
            
            movements = pd.DataFrame({
                'Account': current_by_account.index,
                'Current_Amount': current_by_account.values,
                'Average_Amount': avg_by_account.values
            })
            
            movements['Movement'] = movements['Current_Amount'] - movements['Average_Amount']
            movements['Movement_Percent'] = (movements['Movement'] / movements['Average_Amount'] * 100).fillna(0)
            
            # Show top movements
            st.subheader("🚀 Top Positive Movements")
            top_positive = movements[movements['Movement'] > 0].sort_values('Movement', ascending=False).head(5)
            st.dataframe(top_positive)
            
            st.subheader("📉 Top Negative Movements")
            top_negative = movements[movements['Movement'] < 0].sort_values('Movement').head(5)
            st.dataframe(top_negative)
            
            # Show movement chart
            st.subheader("📈 Movement Chart")
            movement_chart_data = movements.set_index('Account')['Movement'].sort_values(ascending=False)
            st.bar_chart(movement_chart_data)
            
        else:
            st.warning("Amount and Account columns required for movement analysis.")
    else:
        st.warning("No data uploaded yet. Please upload data in the 'Upload & Preview' tab.")

def create_anomaly_detection_tab():
    """Create the anomaly detection tab."""
    st.header("🚨 Anomaly Detection")
    st.info("This tab shows anomaly detection results")
    
    processed_data = st.session_state.get('final_processed_data')
    if processed_data is not None and not processed_data.empty:
        st.success(f"✅ Data available for anomaly detection")
        
        if 'Amount' in processed_data.columns:
            # Simple anomaly detection using z-score
            amounts = processed_data['Amount'].abs()
            mean_amount = amounts.mean()
            std_amount = amounts.std()
            
            # Find anomalies (values more than 2 standard deviations from mean)
            anomalies = processed_data[amounts > (mean_amount + 2 * std_amount)]
            
            st.subheader("🔍 Anomaly Detection Results")
            
            col1, col2 = st.columns(2)
            with col1:
                st.metric("Total Records", len(processed_data))
                st.metric("Mean Amount", f"${mean_amount:,.2f}")
            with col2:
                st.metric("Anomalies Found", len(anomalies))
                st.metric("Anomaly Rate", f"{(len(anomalies)/len(processed_data)*100):.1f}%")
            
            if len(anomalies) > 0:
                st.subheader("🚨 Detected Anomalies")
                st.dataframe(anomalies)
                
                # Show anomaly chart
                st.subheader("📊 Anomaly Distribution")
                anomaly_chart = anomalies.groupby('Account')['Amount'].sum().sort_values(ascending=False)
                st.bar_chart(anomaly_chart)
            else:
                st.success("✅ No significant anomalies detected in the data.")
        else:
            st.warning("Amount column required for anomaly detection.")
    else:
        st.warning("No data uploaded yet. Please upload data in the 'Upload & Preview' tab.")

def create_visualizations_tab():
    """Create the visualizations tab."""
    st.header("📊 Visualizations")
    st.info("This tab shows charts and graphs")
    
    processed_data = st.session_state.get('final_processed_data')
    if processed_data is not None and not processed_data.empty:
        st.success(f"✅ Data available for visualizations")
        
        if 'Amount' in processed_data.columns and 'Account' in processed_data.columns:
            # Create various visualizations
            
            # 1. Bar chart of amounts by account
            st.subheader("🥧 Amount Distribution by Account")
            account_totals = processed_data.groupby('Account')['Amount'].sum()
            st.bar_chart(account_totals)
            
            # 2. Line chart of amounts (if we have month data)
            if 'Month' in processed_data.columns:
                st.subheader("📈 Amount Trends by Month")
                month_totals = processed_data.groupby('Month')['Amount'].sum().sort_index()
                st.line_chart(month_totals)
            
            # 3. Top accounts table
            st.subheader("🏆 Top 10 Accounts by Amount")
            top_accounts = account_totals.sort_values(ascending=False).head(10)
            st.dataframe(top_accounts.reset_index().rename(columns={'Amount': 'Total Amount'}))
            
            # 4. Summary statistics
            st.subheader("📈 Summary Statistics")
            col1, col2 = st.columns(2)
            with col1:
                st.write("**Amount Statistics:**")
                st.write(f"• Mean: ${processed_data['Amount'].mean():,.2f}")
                st.write(f"• Median: ${processed_data['Amount'].median():,.2f}")
                st.write(f"• Standard Deviation: ${processed_data['Amount'].std():,.2f}")
            with col2:
                st.write("**Account Statistics:**")
                st.write(f"• Total Accounts: {processed_data['Account'].nunique()}")
                st.write(f"• Total Records: {len(processed_data)}")
                st.write(f"• Average per Account: ${processed_data.groupby('Account')['Amount'].sum().mean():,.2f}")
                
        else:
            st.warning("Amount and Account columns required for visualizations.")
    else:
        st.warning("No data uploaded yet. Please upload data in the 'Upload & Preview' tab.")

def main():
    """Main application function."""
    # Set page config
    st.set_page_config(
        page_title="FinGenie - Modern Financial Analysis",
        page_icon="📊",
        layout="wide",
        initial_sidebar_state="collapsed"
    )
    
    # Initialize session state
    initialize_session_state()
    
    # Add custom CSS for modern design
    add_custom_css()
    
    # Modern header
    st.markdown("""
    <div class="main-header">
        <h1 style="margin: 0; font-size: 2.5rem; font-weight: 700;">📊 FinGenie</h1>
        <p style="margin: 5px 0 0 0; opacity: 0.9; font-size: 1.1rem;">Modern Financial Data Analysis & AI-Powered Insights</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Create tabs with modern styling
    tab1, tab2, tab3, tab4, tab5, tab6, tab7 = st.tabs([
        "📊 Upload & Preview",
        "🔍 Executive Overview", 
        "📈 Movement Analysis",
        "⚠️ Anomaly Detection",
        "📊 Visualizations",
        "💬 Chat Interface",
        "📄 Docs Q&A (Excel)"
    ])
    
    with tab1:
        create_upload_tab()
    
    with tab2:
        create_executive_overview_tab()
    
    with tab3:
        create_movement_analysis_tab()
    
    with tab4:
        create_anomaly_detection_tab()
    
    with tab5:
        create_visualizations_tab()
    
    with tab6:
        create_modern_chat_interface()

    with tab7:
        create_docs_qa_tab()


def create_docs_qa_tab():
    import os
    import json
    from ingestion.ingest_excel import normalize_excel
    from retrieval.vector_store import LocalVectorStore
    from rag.pipeline import build_evidence_pack

    st.header("📄 Docs Q&A (Excel)")
    st.info("Upload Excel workbooks, index locally, and ask questions. Runs fully offline by default.")

    if "docs_store" not in st.session_state:
        st.session_state.docs_store = LocalVectorStore(path=".vectordb", collection="excel_docs")
    if "facts_df" not in st.session_state:
        st.session_state.facts_df = pd.DataFrame(columns=["Doc","Sheet","Account","Period","Amount"]) 

    up_files = st.file_uploader("Upload Excel files", type=["xlsx","xls"], accept_multiple_files=True)
    if up_files:
        with st.spinner("Indexing workbooks..."):
            store = st.session_state.docs_store
            for f in up_files:
                content = f.read()
                facts, chunks = normalize_excel(content, f.name)
                if not facts.empty:
                    st.session_state.facts_df = pd.concat([st.session_state.facts_df, facts], ignore_index=True)
                if chunks:
                    store.add(ids=[c['id'] for c in chunks],
                              texts=[c['text'] for c in chunks],
                              metadatas=[c['metadata'] for c in chunks])
            st.success("Indexing complete.")

    # Simple stats
    if not st.session_state.facts_df.empty:
        c1, c2, c3 = st.columns(3)
        with c1:
            st.metric("Facts", len(st.session_state.facts_df))
        with c2:
            st.metric("Docs", st.session_state.facts_df['Doc'].nunique())
        with c3:
            st.metric("Sheets", st.session_state.facts_df['Sheet'].nunique())

    st.markdown("---")
    # Determine availability dynamically (via secrets/env)
    client_dbg, _available, model_dbg = _get_openai_client()
    use_ai = st.checkbox("Use AI analysis (if OPENAI_API_KEY is set)", value=_available)
    if _available:
        st.caption(f"AI status: available ({model_dbg})")
    else:
        st.caption("AI status: not configured. Set OPENAI_API_KEY (env or .streamlit/secrets) and restart the app.")
    with st.form("docs_qa_form", clear_on_submit=False):
        q = st.text_input("Ask a question about your workbooks", placeholder="e.g., Top 5 cost drivers this quarter vs last")
        submitted = st.form_submit_button("Ask")

    if submitted and q.strip():
        store = st.session_state.docs_store
        facts_df = st.session_state.facts_df
        filters = {}
        # Apply simple intent filters (month/year + account keywords like "rent")
        filtered_df = _filter_facts_by_query(q, facts_df)
        pack = build_evidence_pack(q, filtered_df if not filtered_df.empty else facts_df, store, filters)

        # Deterministic summary
        answer_lines = []
        target_df = filtered_df if not filtered_df.empty else facts_df
        if not target_df.empty and "Amount" in target_df.columns:
            total = float(target_df["Amount"].sum())
            count = int(target_df.shape[0])
            answer_lines.append(f"Total Amount in retrieved scope: ${total:,.2f}")
            answer_lines.append(f"Records considered: {count}")
            # If the user mentioned a known account (e.g., rent), surface its amount for the detected period
            acc = _extract_account_keyword(q)
            period_label = _extract_month_label(q)
            if acc:
                acc_df = target_df[target_df["Account"].str.contains(acc, case=False, na=False)]
                if not acc_df.empty:
                    if period_label:
                        acc_period_df = acc_df[acc_df["Period"].astype(str).str.contains(period_label, case=False, na=False)]
                        amt = float(acc_period_df["Amount"].sum()) if not acc_period_df.empty else float(acc_df["Amount"].sum())
                    else:
                        amt = float(acc_df["Amount"].sum())
                    answer_lines.append(f"{acc.title()} amount{' for ' + period_label if period_label else ''}: ${amt:,.2f}")
        else:
            # Offer hints if the precise filter returned nothing
            acc = _extract_account_keyword(q)
            if acc and "Account" in facts_df.columns:
                acc_only = facts_df[facts_df["Account"].astype(str).str.contains(acc, case=False, na=False)]
                if not acc_only.empty and "Period" in acc_only.columns:
                    sample_periods = sorted(list({str(p) for p in acc_only["Period"].head(12)}))
                    answer_lines.append("No exact match found. Nearby periods for '" + acc + "' include: " + ", ".join(sample_periods))
                else:
                    answer_lines.append("No matching rows found for your question.")
            else:
                answer_lines.append("No matching rows found for your question.")

        st.subheader("Answer")
        base_answer = "\n".join(answer_lines) or "I retrieved relevant rows and citations below."

        if use_ai and _get_openai_client()[1]:
            ai_answer = _generate_llm_answer(q.strip(), st.session_state.facts_df, filtered_df if not filtered_df.empty else facts_df)
            st.write(ai_answer)
        elif use_ai and not _available:
            st.warning("AI was toggled on, but no API key was detected. Add OPENAI_API_KEY and restart the app.")
        else:
            st.write(base_answer)

        # Query debug
        with st.expander("Debug (query)", expanded=False):
            acc = _extract_account_keyword(q)
            month = _extract_month_label(q)
            st.write({
                "account_keyword": acc,
                "parsed_month_label": month,
                "facts_rows": 0 if facts_df is None else int(facts_df.shape[0]),
                "filtered_rows": 0 if filtered_df is None else int(filtered_df.shape[0]),
            })
            if facts_df is not None and not facts_df.empty:
                if acc:
                    st.write("sample_accounts", list(facts_df["Account"].astype(str).dropna().unique())[:15])
                st.write("sample_periods", list(facts_df["Period"].astype(str).dropna().unique())[:15])

        # Citations
        st.subheader("Citations")
        for c in pack.get("citations", [])[:5]:
            st.write(f"- {c.get('doc')} › {c.get('sheet')} (row {c.get('row')}): {c.get('excerpt')}")


def _extract_month_label(query: str) -> str:
    """Return a label like 'Dec-22', 'Dec 22', 'December 2022', or month-only 'Dec'.
    We try to be flexible because workbooks use different month formats."""
    q = (query or "").lower()
    months = {
        'jan': 'Jan', 'january': 'Jan', 'feb': 'Feb', 'february': 'Feb', 'mar': 'Mar', 'march': 'Mar',
        'apr': 'Apr', 'april': 'Apr', 'may': 'May', 'jun': 'Jun', 'june': 'Jun', 'jul': 'Jul', 'july': 'Jul',
        'aug': 'Aug', 'august': 'Aug', 'sep': 'Sep', 'sept': 'Sep', 'september': 'Sep', 'oct': 'Oct', 'october': 'Oct',
        'nov': 'Nov', 'november': 'Nov', 'dec': 'Dec', 'december': 'Dec'
    }
    year = None
    import re
    m = re.search(r"20\d{2}", q)
    if m:
        year = m.group(0)
    for k, abbr in months.items():
        if k in q:
            if year:
                yy = year[-2:]
                # Return multiple acceptable formats to match diverse sheets
                return f"{abbr}-{yy}"
            return abbr
    return ""


def _extract_account_keyword(query: str) -> str:
    q = (query or "").lower()
    keywords = ["rent", "marketing", "utilities", "revenue", "income", "expenses"]
    for kw in keywords:
        if kw in q:
            return kw
    return ""


def _filter_facts_by_query(query: str, facts_df: pd.DataFrame) -> pd.DataFrame:
    if facts_df is None or facts_df.empty:
        return pd.DataFrame(columns=["Doc","Sheet","Account","Period","Amount"]) 
    df = facts_df.copy()
    # Account filter
    acc = _extract_account_keyword(query)
    if acc and "Account" in df.columns:
        df = df[df["Account"].astype(str).str.contains(acc, case=False, na=False)]
    # Month/year filter
    label = _extract_month_label(query)
    if label and "Period" in df.columns:
        # accept various month formats
        month_abbr = label.split('-')[0]
        period_str = df["Period"].astype(str)
        mask = period_str.str.contains(month_abbr, case=False, na=False)
        if '-' in label:
            yy = label.split('-')[1]
            mask = mask & period_str.str.contains(yy, case=False, na=False)
        # also match full names like December 2022
        full_map = { 'Jan':'January', 'Feb':'February', 'Mar':'March', 'Apr':'April', 'May':'May', 'Jun':'June', 'Jul':'July', 'Aug':'August', 'Sep':'September', 'Oct':'October', 'Nov':'November', 'Dec':'December' }
        full_name = full_map.get(month_abbr, month_abbr)
        mask = mask | period_str.str.contains(full_name, case=False, na=False)
        df = df[mask]
    return df

if __name__ == "__main__":
    main() 