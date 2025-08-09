# FinGenie - AI-Powered Financial Assistant

🏦 Transform your financial data into executive-ready insights using AI-powered automation.

## Overview

FinGenie helps finance teams automate monthly management reporting using static uploads of financial data. It transforms raw P&L, balance sheet, and KPI files into executive-ready visuals and insights through an intuitive web interface with AI-powered chat capabilities.

## Features

- **📊 Data Upload & Preview** - Upload CSV/Excel files with validation
- **🔍 AI-Generated Insights** - Automated commentary and anomaly detection  
- **📈 Financial Visualizations** - Interactive charts and reports
- **💬 AI Chat Interface** - Natural language Q&A about your financial data
- **🔮 Forecasting** - Simple forecasting tools with manual assumptions
- **📋 Unified Dashboard** - Combined movement analysis and anomaly detection
- **📤 Export Capabilities** - Executive summaries and CSV downloads

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager
- OpenAI API key (for AI commentary generation)

### Installation

1. **Clone or download the project files**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure OpenAI API key:**
   ```bash
   export OPENAI_API_KEY="your-api-key-here"
   ```

4. **Run the application:**
   ```bash
   streamlit run main.py
   ```

5. **Open your browser** to the URL shown in terminal (typically `http://localhost:8501`)

### First Use

1. Navigate to the **Data Preview** tab
2. Upload your CSV or Excel financial data files
3. Explore insights, visualizations, and forecasting tools
4. Use the **Chat Interface** for natural language Q&A about your data
5. View the unified **Insights Dashboard** for comprehensive analysis

## Supported File Formats

- **CSV** (.csv) - Comma-separated values
- **Excel** (.xlsx, .xls) - Microsoft Excel files
- **Maximum file size:** 10MB

## System Requirements

- **Performance:** Charts and commentary load within 60 seconds
- **Response time:** Q&A responds in less than 3 seconds average
- **Storage:** Data stored in-session only (no persistent database)
- **Authentication:** Basic login protection

## Development Status

This is **EPIC 5 COMPLETE** - the interactive Q&A chat system with comprehensive AI-powered analysis:

### ✅ **Completed Features**
- ✅ Multi-tab navigation
- ✅ Session state management  
- ✅ File upload functionality
- ✅ AI commentary generation
- ✅ Movement detection engine
- ✅ Anomaly detection system
- ✅ Unified insights dashboard
- ✅ Export capabilities
- ✅ **NEW**: AI-powered chat interface with natural language processing
- ✅ **NEW**: Financial data query engine with contextual responses
- ✅ **NEW**: Modern ChatGPT-style UI with excellent UX
- ✅ **NEW**: Trend analysis and intelligent response generation

### 🎯 **Key Achievements**
- **Epic 4**: Complete visualization system (trend, YoY, waterfall charts)
- **Epic 5**: Complete chat interface with AI-powered query processing
- **Modern UI**: ChatGPT-style interface with clean, professional design
- **Intelligent Responses**: Contextual, meaningful financial analysis
- **Production Ready**: All core features implemented and tested

## Testing

### Automated Tests
Run the comprehensive test suite:

```bash
# Run Story 5.2 tests (chat interface)
cd tests/story-5-2
python3 -m pytest unit/ -v

# Run Story 3.4 tests (dashboard)
cd tests/story-3-4
python3 run_tests.py all
```

### Manual Testing
Follow the comprehensive manual testing guides:
- [Chat Interface Testing](tests/story-5-2/MANUAL_TESTING_GUIDE.md)
- [Dashboard Testing](tests/story-3-4/MANUAL_E2E_TEST_GUIDE.md)

## Chat Interface Features

### **Natural Language Queries**
- Ask questions like "What's our revenue trend?"
- Query specific time periods: "What was revenue in April 2021?"
- Request analysis: "What drove the increase in marketing expenses?"
- Get contextual responses with specific numbers and insights

### **Intelligent Response Types**
- **Trend Analysis**: Direction, percentage changes, monthly breakdowns
- **Revenue Analysis**: Revenue-specific insights and breakdowns
- **Expense Analysis**: Expense-focused analysis with rankings
- **Movement Analysis**: Movement explanations with causes and context

### **Modern User Experience**
- ChatGPT-style interface with clean design
- Real-time message processing
- Form-based input (no double-click issues)
- Persistent chat history
- Responsive design across devices