# Manual Testing Guide - Story 5.2: Financial Data Query Engine

## Overview
This guide provides step-by-step instructions for manually testing the Financial Data Query Engine implementation in Story 5.2. These tests should be performed in the Streamlit interface to verify end-to-end functionality.

## Prerequisites
1. **Application Setup**: Ensure the main application is running (`streamlit run main.py`)
2. **Test Data**: Have sample financial data files ready (CSV, XLSX, XLS)
3. **Browser**: Modern web browser (Chrome, Firefox, Safari, Edge)
4. **Network**: Stable internet connection for Streamlit and AI integration

## Test Environment Setup

### 1. Application Launch
```bash
cd /path/to/Bmad-Install
streamlit run main.py
```

### 2. Browser Setup
- Open browser in incognito/private mode for clean testing
- Ensure browser console is open for error monitoring
- Set browser window to different sizes for responsive testing

### 3. Test Data Preparation
- Upload sample financial data to the application
- Ensure data includes various account types (Revenue, Expenses, Cash)
- Verify data spans multiple time periods for comprehensive testing

## Test Scenarios

### Scenario 1: Natural Language Query Processing

#### Test Case 1.1: Simple Account Queries
**Objective**: Verify basic natural language query understanding

**Steps**:
1. Navigate to the "💬 Chat Interface" tab
2. Enter the query: "What drove the increase in marketing expenses?"
3. Press Enter or click Send
4. Wait for AI response

**Expected Results**:
- ✅ Query is processed within 3 seconds
- ✅ Response includes specific numbers and percentages
- ✅ Response references actual data from the dataset
- ✅ Response includes relevant context and explanations
- ✅ Response format is readable and well-structured

**Test Data**: Sample financial data with marketing expenses

---

#### Test Case 1.2: Time-Based Queries
**Objective**: Verify time period extraction and filtering

**Steps**:
1. Enter the query: "How much revenue did we generate this month?"
2. Press Enter or click Send
3. Wait for AI response

**Expected Results**:
- ✅ Time period "this month" is correctly identified
- ✅ Data is filtered for the specified time period
- ✅ Response includes total revenue amount
- ✅ Response includes breakdown by revenue type
- ✅ Response references actual data from the dataset

**Test Data**: Sample financial data with revenue information

---

#### Test Case 1.3: Ranking Queries
**Objective**: Verify ranking and top/bottom queries

**Steps**:
1. Enter the query: "Show me the top expenses"
2. Press Enter or click Send
3. Wait for AI response

**Expected Results**:
- ✅ Expenses are ranked by amount
- ✅ Top expenses are identified and listed
- ✅ Response includes percentages and amounts
- ✅ Response provides context for the ranking
- ✅ Response format is clear and organized

**Test Data**: Sample financial data with various expense categories

### Scenario 2: Complex Query Processing

#### Test Case 2.1: Multi-Entity Queries
**Objective**: Verify handling of queries with multiple entities

**Steps**:
1. Enter the query: "What caused the spike in sales revenue on January 8th?"
2. Press Enter or click Send
3. Wait for AI response

**Expected Results**:
- ✅ Multiple entities (sales, revenue, January 8th) are extracted
- ✅ Anomaly detection is triggered
- ✅ Response explains the spike with context
- ✅ Response references actual data and amounts
- ✅ Response includes possible causes or explanations

**Test Data**: Sample financial data with sales revenue and anomalies

---

#### Test Case 2.2: Comparison Queries
**Objective**: Verify comparison functionality

**Steps**:
1. Enter the query: "Compare marketing expenses between January and February"
2. Press Enter or click Send
3. Wait for AI response

**Expected Results**:
- ✅ Comparison periods are identified
- ✅ Data is compared between periods
- ✅ Response shows differences and trends
- ✅ Response includes percentages and amounts
- ✅ Response provides insights on the comparison

**Test Data**: Sample financial data spanning multiple months

---

#### Test Case 2.3: Trend Analysis Queries
**Objective**: Verify trend analysis functionality

**Steps**:
1. Enter the query: "What are the trends in our cash flow over the last quarter?"
2. Press Enter or click Send
3. Wait for AI response

**Expected Results**:
- ✅ Trend analysis is performed
- ✅ Response identifies key patterns
- ✅ Response includes trend direction and magnitude
- ✅ Response provides insights on cash flow drivers
- ✅ Response references actual data and amounts

**Test Data**: Sample financial data with cash flow information

### Scenario 3: Follow-up Question Handling

#### Test Case 3.1: Contextual Follow-ups
**Objective**: Verify context maintenance across questions

**Steps**:
1. Enter the query: "What drove the increase in marketing expenses?"
2. Wait for response
3. Enter the follow-up: "Tell me more about that"
4. Wait for AI response

**Expected Results**:
- ✅ Context from previous query is maintained
- ✅ Follow-up response provides additional details
- ✅ Response builds on previous information
- ✅ Response includes more specific breakdowns
- ✅ Conversation flow is natural and coherent

**Test Data**: Sample financial data with marketing expenses

---

#### Test Case 3.2: Related Follow-ups
**Objective**: Verify handling of related follow-up questions

**Steps**:
1. Enter the query: "Show me the top expenses"
2. Wait for response
3. Enter the follow-up: "What about the revenue side?"
4. Wait for AI response

**Expected Results**:
- ✅ Context switching is handled appropriately
- ✅ Response focuses on revenue information
- ✅ Response maintains conversation coherence
- ✅ Response provides relevant revenue insights
- ✅ Response format is consistent

**Test Data**: Sample financial data with expenses and revenue

---

#### Test Case 3.3: Chart Generation Requests
**Objective**: Verify chart generation via chat

**Steps**:
1. Enter the query: "What are the sales trends?"
2. Wait for response
3. Enter the follow-up: "Can you show me a chart for that?"
4. Wait for AI response

**Expected Results**:
- ✅ Chart generation is triggered
- ✅ Chart is displayed inline in chat
- ✅ Chart shows relevant sales trend data
- ✅ Response includes chart insights
- ✅ Chart quality is consistent with existing charts

**Test Data**: Sample financial data with sales information

### Scenario 4: Error Handling and Edge Cases

#### Test Case 4.1: Unrelated Queries
**Objective**: Verify handling of unrelated or non-financial queries

**Steps**:
1. Enter the query: "What is the meaning of life?"
2. Press Enter or click Send
3. Wait for AI response

**Expected Results**:
- ✅ Query is identified as unrelated
- ✅ Response politely redirects to financial topics
- ✅ Response suggests relevant financial queries
- ✅ Error handling is graceful
- ✅ User experience remains positive

**Test Data**: None required

---

#### Test Case 4.2: Empty Queries
**Objective**: Verify handling of empty or invalid queries

**Steps**:
1. Enter an empty query (just press Enter)
2. Wait for AI response

**Expected Results**:
- ✅ Empty query is detected
- ✅ Response prompts for a valid query
- ✅ Response provides examples of valid queries
- ✅ Error handling is user-friendly
- ✅ Application remains stable

**Test Data**: None required

---

#### Test Case 4.3: Non-existent Data Queries
**Objective**: Verify handling of queries for non-existent data

**Steps**:
1. Enter the query: "What is the revenue for account XYZ?"
2. Press Enter or click Send
3. Wait for AI response

**Expected Results**:
- ✅ Non-existent account is identified
- ✅ Response explains data availability
- ✅ Response suggests available accounts
- ✅ Response is helpful and informative
- ✅ Error handling is constructive

**Test Data**: Sample financial data (account XYZ should not exist)

---

#### Test Case 4.4: Future Date Queries
**Objective**: Verify handling of queries for future dates

**Steps**:
1. Enter the query: "Show me the data for 2099"
2. Press Enter or click Send
3. Wait for AI response

**Expected Results**:
- ✅ Future date is identified
- ✅ Response explains data availability
- ✅ Response provides available time periods
- ✅ Response is helpful and informative
- ✅ Error handling is constructive

**Test Data**: Sample financial data (should not include 2099)

### Scenario 5: Integration Testing

#### Test Case 5.1: Chat Interface Integration
**Objective**: Verify seamless integration with chat interface

**Steps**:
1. Navigate to Chat Interface tab
2. Verify chat interface loads correctly
3. Enter a test query
4. Verify response appears in chat
5. Test multiple queries in sequence

**Expected Results**:
- ✅ Chat interface loads without errors
- ✅ Queries are processed and responses displayed
- ✅ Chat history is maintained
- ✅ UI is responsive and user-friendly
- ✅ Integration is seamless

**Test Data**: Sample financial data

---

#### Test Case 5.2: Data Source Integration
**Objective**: Verify integration with existing data sources

**Steps**:
1. Upload sample financial data
2. Navigate to Chat Interface tab
3. Enter queries about the uploaded data
4. Verify responses reference actual data

**Expected Results**:
- ✅ Queries access uploaded data correctly
- ✅ Responses reference actual data values
- ✅ Data filtering works correctly
- ✅ Data aggregation works correctly
- ✅ Integration is accurate

**Test Data**: Sample financial data files

---

#### Test Case 5.3: Chart Reference Integration
**Objective**: Verify integration with existing chart system

**Steps**:
1. Enter a query that should reference charts
2. Verify chart references in response
3. Test chart generation requests
4. Verify chart quality and relevance

**Expected Results**:
- ✅ Chart references are included in responses
- ✅ Chart generation works correctly
- ✅ Chart quality is consistent
- ✅ Chart relevance is high
- ✅ Integration is seamless

**Test Data**: Sample financial data with chart-worthy information

### Scenario 6: Performance Testing

#### Test Case 6.1: Response Time Testing
**Objective**: Verify query processing performance

**Steps**:
1. Enter a simple query
2. Time the response
3. Enter a complex query
4. Time the response
5. Repeat with different query types

**Expected Results**:
- ✅ Simple queries respond within 3 seconds
- ✅ Complex queries respond within 5 seconds
- ✅ Performance is consistent
- ✅ No timeouts or errors
- ✅ User experience is smooth

**Test Data**: Sample financial data

---

#### Test Case 6.2: Large Dataset Testing
**Objective**: Verify performance with large datasets

**Steps**:
1. Upload a large financial dataset
2. Enter queries about the data
3. Verify response times
4. Test data extraction accuracy

**Expected Results**:
- ✅ Performance remains acceptable with large datasets
- ✅ Data extraction is accurate
- ✅ Response times are reasonable
- ✅ No performance degradation
- ✅ User experience remains good

**Test Data**: Large financial dataset

## Test Data Requirements

### Sample Financial Data
Create these test files for comprehensive testing:

#### 1. Basic Financial Data (test_basic_data.csv)
```csv
Date,Account,Amount,Description
2024-01-01,Cash,5000.00,Opening Balance
2024-01-02,Revenue - Sales,-12500.50,Monthly Sales
2024-01-03,Expense - Marketing,850.75,Marketing Campaign
2024-01-04,Cash,2500.00,Deposit
2024-01-05,Revenue - Service,-8750.25,Consulting Revenue
2024-01-06,Expense - Rent,1200.00,Office Rent
2024-01-07,Cash,1500.00,Transfer
2024-01-08,Revenue - Sales,-15000.00,Product Sales
2024-01-09,Expense - Utilities,450.50,Electricity Bill
2024-01-10,Cash,3000.00,Client Payment
```

#### 2. Extended Financial Data (test_extended_data.csv)
```csv
Date,Account,Amount,Description
2024-01-01,Cash,5000.00,Opening Balance
2024-01-02,Revenue - Sales,-12500.50,Monthly Sales
2024-01-03,Expense - Marketing,850.75,Marketing Campaign
2024-01-04,Cash,2500.00,Deposit
2024-01-05,Revenue - Service,-8750.25,Consulting Revenue
2024-01-06,Expense - Rent,1200.00,Office Rent
2024-01-07,Cash,1500.00,Transfer
2024-01-08,Revenue - Sales,-15000.00,Product Sales
2024-01-09,Expense - Utilities,450.50,Electricity Bill
2024-01-10,Cash,3000.00,Client Payment
2024-01-11,Expense - Marketing,1200.00,Digital Ads
2024-01-12,Revenue - Sales,-18000.00,Q4 Sales
2024-01-13,Expense - Marketing,950.25,Content Creation
2024-01-14,Cash,4000.00,Investment
2024-01-15,Expense - Marketing,750.00,Social Media
```

## Success Criteria

### Functional Requirements
- ✅ Natural language queries processed accurately
- ✅ Relevant data extracted and analyzed
- ✅ Contextual responses generated with specific numbers
- ✅ Chart and insight references working correctly
- ✅ Follow-up questions handled with context
- ✅ Error handling and recovery implemented

### Non-Functional Requirements
- ✅ Query processing within 3 seconds
- ✅ High accuracy in query understanding
- ✅ Seamless integration with existing systems
- ✅ Scalable architecture for complex queries
- ✅ Comprehensive error handling

### Quality Requirements
- ✅ 85% code coverage
- ✅ All unit tests passing
- ✅ All integration tests passing
- ✅ Manual testing completed
- ✅ Performance requirements met

## Reporting

### Test Results Documentation
1. **Test Execution Log**: Document all test cases executed
2. **Issues Found**: Record any bugs or issues discovered
3. **Performance Metrics**: Document response times and performance
4. **User Experience Notes**: Record UX observations and feedback
5. **Recommendations**: Provide suggestions for improvements

### Test Report Template
```
Test Report - Story 5.2: Financial Data Query Engine
==================================================

Test Date: [Date]
Tester: [Name]
Environment: [Browser/OS]

Test Results:
- Total Test Cases: [Number]
- Passed: [Number]
- Failed: [Number]
- Blocked: [Number]

Key Findings:
- [List key findings]

Issues Found:
- [List issues with severity]

Performance Metrics:
- Average Response Time: [Time]
- Slowest Query: [Query/Time]
- Fastest Query: [Query/Time]

Recommendations:
- [List recommendations]

Overall Assessment:
- [Pass/Fail/Blocked]
```

## Troubleshooting

### Common Issues
1. **Slow Response Times**: Check network connection and AI service availability
2. **Incorrect Responses**: Verify test data and query formatting
3. **Integration Errors**: Check application logs and dependencies
4. **UI Issues**: Clear browser cache and restart application

### Error Recovery
1. **Application Errors**: Restart the Streamlit application
2. **Data Issues**: Re-upload test data files
3. **Network Issues**: Check internet connection and retry
4. **Browser Issues**: Try different browser or clear cache

## Support

For questions or issues with manual testing:
1. Check the test documentation
2. Review the automated test results
3. Consult the troubleshooting guide
4. Contact the development team

---

**Last Updated**: 2024-12-19  
**Version**: 1.0  
**Status**: Ready for Testing 