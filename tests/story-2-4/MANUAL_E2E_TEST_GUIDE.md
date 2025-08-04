# Manual E2E Test Guide - Story 2.4: Data Preview Display

## Overview
This document provides step-by-step manual testing instructions for the data preview functionality implemented in Story 2.4. These tests should be performed in the Streamlit interface to verify end-to-end functionality.

## Prerequisites
- Streamlit application is running (`streamlit run main.py`)
- Sample CSV or Excel files available for testing
- Web browser with access to the Streamlit app

## Test Data Files
Create these test files for comprehensive testing:

### 1. Valid Financial Data (test_financial_data.csv)
```csv
Date,Account,Amount,Description
2024-01-01,Cash,5000.00,Opening Balance
2024-01-02,Revenue - Sales,-12500.50,Monthly Sales
2024-01-03,Expense - Office,850.75,Office Supplies
2024-01-04,Cash,2500.00,Deposit
2024-01-05,Revenue - Service,-8750.25,Consulting Revenue
2024-01-06,Expense - Rent,1200.00,Office Rent
2024-01-07,Cash,1500.00,Transfer
2024-01-08,Revenue - Sales,-15000.00,Product Sales
2024-01-09,Expense - Utilities,450.50,Electricity Bill
2024-01-10,Cash,3000.00,Client Payment
```

### 2. Data with Quality Issues (test_data_quality_issues.csv)
```csv
Date,Account,Amount,Description
2024-01-01,Cash,1000.50,Opening balance
2024-01-02,Revenue,-2500.75,Sales revenue
,Expenses,750.25,Office supplies
2024-01-04,,999999.99,Large deposit
2024-01-05,Revenue,-1800.00,
```

## Manual Test Cases

### Test Case 1: Basic Data Upload and Preview
**Objective:** Verify basic data upload and preview functionality

**Steps:**
1. Open the Streamlit application in browser
2. Navigate to the "📊 Data Preview" tab
3. Upload the `test_financial_data.csv` file
4. Wait for processing to complete

**Expected Results:**
- ✅ File uploads successfully with green success message
- ✅ Data structure validation passes
- ✅ Processing pipeline completes successfully
- ✅ Enhanced Data Preview section appears below processing results
- ✅ Summary statistics display correctly:
  - Total Rows: 10
  - Date Range: 2024-01-01 to 2024-01-10
  - Unique Accounts: 3 (Cash, Revenue, Expenses)
  - Amount statistics show min, max, average, and total

### Test Case 2: Interactive Data Table
**Objective:** Test the interactive data table functionality

**Steps:**
1. Continue from Test Case 1
2. Expand the "📋 Column Information" section
3. Test different "Rows to display" options (10, 25, 50, 100, All)
4. Toggle the "Show row numbers" checkbox
5. Observe the data table display

**Expected Results:**
- ✅ Column Information shows all 4 columns with data types and completeness
- ✅ Data table adjusts row count based on selection
- ✅ Row numbers appear/disappear when checkbox is toggled
- ✅ Data table is scrollable and responsive
- ✅ Data displays with proper formatting

### Test Case 3: Data Quality Highlighting
**Objective:** Test data quality issue highlighting

**Steps:**
1. Upload the `test_data_quality_issues.csv` file
2. Wait for processing to complete
3. Observe the data table in the preview section
4. Check the legend for highlighting explanation

**Expected Results:**
- ✅ Missing values are highlighted with light red background
- ✅ Potential outliers (999999.99) are highlighted with light yellow background
- ✅ Legend shows: "🔴 Missing values (light red) | 🟡 Potential outliers (light yellow)"
- ✅ Data quality score reflects the issues in the data

### Test Case 4: Download Functionality
**Objective:** Test CSV and Excel download features

**Steps:**
1. Continue from any successful upload test
2. Scroll to the "💾 Download Processed Data" section
3. Click "📄 Download as CSV" button
4. Click "📊 Download as Excel" button
5. Check downloaded files

**Expected Results:**
- ✅ CSV file downloads with filename format: `processed_data_YYYYMMDD_HHMMSS.csv`
- ✅ Excel file downloads with filename format: `processed_data_YYYYMMDD_HHMMSS.xlsx`
- ✅ Downloaded CSV file contains all processed data
- ✅ Downloaded Excel file opens correctly with "Processed Data" sheet
- ✅ Data formatting is preserved in downloads

### Test Case 5: Data Quality Details
**Objective:** Test data quality summary display

**Steps:**
1. Continue from any successful upload test
2. Expand the "📈 Data Quality Details" section
3. Review the quality information displayed

**Expected Results:**
- ✅ Overall Quality Score displays as X.X/100
- ✅ Recommendations are listed (if any)
- ✅ Processing warnings are shown (if any)
- ✅ Quality score color-coding works:
  - Green for ≥90 (Excellent)
  - Yellow for 75-89 (Good) or 50-74 (Fair)
  - Red for <50 (Poor)

### Test Case 6: Large Dataset Handling
**Objective:** Test performance with larger datasets

**Steps:**
1. Create or use a CSV file with 500+ rows
2. Upload the large file
3. Test different "Rows to display" options
4. Test scrolling and navigation

**Expected Results:**
- ✅ Large file uploads without errors
- ✅ Processing completes within reasonable time
- ✅ Preview shows first 100 rows by default
- ✅ "All" option works but may be slower
- ✅ Pagination controls work smoothly
- ✅ Download functionality works for large datasets

### Test Case 7: Error Handling
**Objective:** Test graceful error handling

**Steps:**
1. Try uploading an invalid file format (e.g., .txt)
2. Try uploading a corrupted CSV file
3. Try uploading a file larger than 10MB
4. Try uploading an empty file

**Expected Results:**
- ✅ Invalid file formats show appropriate error messages
- ✅ Corrupted files are handled gracefully
- ✅ Large files show size limit error
- ✅ Empty files show appropriate error message
- ✅ App remains stable after errors

### Test Case 8: Mobile/Responsive Testing
**Objective:** Test responsive design on different screen sizes

**Steps:**
1. Test the data preview on desktop browser
2. Resize browser window to tablet size
3. Resize browser window to mobile size
4. Test all functionality at different sizes

**Expected Results:**
- ✅ Layout adapts to different screen sizes
- ✅ Data table remains usable on smaller screens
- ✅ Buttons and controls are accessible
- ✅ Text remains readable
- ✅ Download functionality works on all sizes

### Test Case 9: Session State Persistence
**Objective:** Test data persistence across tab navigation

**Steps:**
1. Upload and process a file successfully
2. Navigate to "🔍 Insights" tab
3. Navigate back to "📊 Data Preview" tab
4. Verify data is still available

**Expected Results:**
- ✅ Processed data remains available after tab navigation
- ✅ All preview functionality still works
- ✅ Quality summary persists
- ✅ Download options remain functional

### Test Case 10: Empty State Handling
**Objective:** Test behavior when no data is available

**Steps:**
1. Open the application without uploading any files
2. Navigate directly to "📊 Data Preview" tab
3. Observe the display

**Expected Results:**
- ✅ Shows informative message: "No processed data available. Please upload and process a file first."
- ✅ No errors or broken functionality
- ✅ Upload section is clearly visible and functional

## Test Results Documentation

For each test case, document the results:

| Test Case | Status | Notes | Issues Found |
|-----------|--------|-------|--------------|
| 1. Basic Upload | ✅ Pass / ❌ Fail | | |
| 2. Interactive Table | ✅ Pass / ❌ Fail | | |
| 3. Quality Highlighting | ✅ Pass / ❌ Fail | | |
| 4. Download Functionality | ✅ Pass / ❌ Fail | | |
| 5. Quality Details | ✅ Pass / ❌ Fail | | |
| 6. Large Dataset | ✅ Pass / ❌ Fail | | |
| 7. Error Handling | ✅ Pass / ❌ Fail | | |
| 8. Mobile/Responsive | ✅ Pass / ❌ Fail | | |
| 9. Session Persistence | ✅ Pass / ❌ Fail | | |
| 10. Empty State | ✅ Pass / ❌ Fail | | |

## Test Environment Information

Document the test environment details:

- **Date of Testing:** [Fill in]
- **Tester Name:** [Fill in]
- **Browser:** [Chrome/Firefox/Safari/Edge and version]
- **Screen Resolution:** [Fill in]
- **Operating System:** [Fill in]
- **Streamlit Version:** [Fill in]
- **Python Version:** [Fill in]

## Issues and Recommendations

Use this section to document any issues found during testing and recommendations for improvement:

### Issues Found
- [List any bugs or issues discovered]

### Recommendations
- [List any suggested improvements or enhancements]

## Sign-off

- **Tester Signature:** _________________ **Date:** _________
- **Reviewer Signature:** _________________ **Date:** _________

---

**Note:** This manual testing should be performed after all unit tests and integration tests pass successfully. Any issues found during manual testing should be addressed before considering the story complete.