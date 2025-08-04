# FinGenie - AI-Powered Financial Assistant

🏦 Transform your financial data into executive-ready insights using AI-powered automation.

## Overview

FinGenie helps finance teams automate monthly management reporting using static uploads of financial data. It transforms raw P&L, balance sheet, and KPI files into executive-ready visuals and insights through an intuitive web interface.

## Features

- **📊 Data Upload & Preview** - Upload CSV/Excel files with validation
- **🔍 AI-Generated Insights** - Automated commentary and anomaly detection  
- **📈 Financial Visualizations** - Interactive charts and reports
- **🔮 Forecasting** - Simple forecasting tools with manual assumptions

## Quick Start

### Prerequisites

- Python 3.8 or higher
- pip package manager

### Installation

1. **Clone or download the project files**

2. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Run the application:**
   ```bash
   streamlit run main.py
   ```

4. **Open your browser** to the URL shown in terminal (typically `http://localhost:8501`)

### First Use

1. Navigate to the **Data Preview** tab
2. Upload your CSV or Excel financial data files
3. Explore insights, visualizations, and forecasting tools
4. Use the chat interface for Q&A about your data

## Supported File Formats

- **CSV** (.csv) - Comma-separated values
- **Excel** (.xlsx, .xls) - Microsoft Excel files
- **Maximum file size:** 10MB

## System Requirements

- **Performance:** Charts and commentary load within 60 seconds
- **Response time:** Q&A responds in less than 10 seconds average
- **Storage:** Data stored in-session only (no persistent database)
- **Authentication:** Basic login protection

## Development Status

This is **STORY-001** - the foundational application structure. Additional features are coming in future releases:

- ✅ Multi-tab navigation
- ✅ Session state management  
- ✅ Professional UI layout
- 🔄 File upload functionality (STORY-002)
- 🔄 AI commentary generation (STORY-005)
- 🔄 Chart generation (STORY-006)
- 🔄 Q&A chat interface (STORY-009)

## Troubleshooting

### Application won't start
- Ensure Python 3.8+ is installed: `python --version`
- Install requirements: `pip install -r requirements.txt`
- Check for port conflicts on 8501

### Performance issues
- Refresh the browser page
- Check internet connection for external dependencies
- Ensure adequate system memory (4GB+ recommended)

## Support

For technical issues or questions, refer to the project documentation or contact the development team.

---

**Version:** STORY-001 Foundation  
**Last Updated:** Initial Release