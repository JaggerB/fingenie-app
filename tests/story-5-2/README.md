# Story 5.2: Financial Data Query Engine - Test Suite

## 🧪 **Test Architecture Overview**

This test suite provides comprehensive coverage for the Financial Data Query Engine feature implemented in Story 5.2. The tests are organized into unit tests, integration tests, and include proper mocking for external API calls and data processing.

### **Directory Structure**
```
tests/story-5-2/
├── unit/                          # Unit tests (isolated function testing)
│   ├── test_query_parsing.py      # Natural language query parsing tests
│   ├── test_data_extraction.py    # Data extraction and filtering tests
│   ├── test_response_generation.py # Response generation and formatting tests
│   ├── test_context_management.py # Conversation context management tests
│   └── test_error_handling.py     # Error handling and recovery tests
├── integration/                   # Integration tests (workflow testing)
│   ├── test_query_engine_flow.py  # End-to-end query processing
│   ├── test_chat_integration.py   # Chat interface integration
│   └── test_data_integration.py   # Data source integration
├── fixtures/                      # Test data and mock responses
│   ├── sample_financial_data.json # Sample financial data for testing
│   ├── sample_queries.json        # Sample natural language queries
│   ├── mock_ai_responses.json     # Mock AI responses for testing
│   └── test_contexts.json         # Test conversation contexts
├── pytest.ini                     # Test configuration
├── run_tests.py                   # Test runner script
├── MANUAL_TESTING_GUIDE.md        # Manual testing guide
└── README.md                      # This file
```

---

## 🚀 **Quick Start**

### **1. Install Dependencies**
```bash
cd /path/to/Bmad-Install
python3 -m pip install -r requirements.txt
```

### **2. Run All Tests**
```bash
python tests/story-5-2/run_tests.py all
```

### **3. Run with Coverage**
```bash
python tests/story-5-2/run_tests.py coverage
```

---

## 📋 **Test Categories**

### **🔧 Unit Tests**
- **test_query_parsing.py**: Tests for natural language query processing
  - Query intent classification
  - Entity extraction (accounts, dates, metrics)
  - Question format handling
  - Context parsing

- **test_data_extraction.py**: Tests for data extraction and filtering
  - Data querying functions
  - Filtering and aggregation
  - Data validation
  - Missing data handling

- **test_response_generation.py**: Tests for response generation
  - Response template creation
  - Number formatting
  - Context and explanation logic
  - Response validation

- **test_context_management.py**: Tests for conversation context
  - Context storage and retrieval
  - Context maintenance
  - Context cleanup
  - Context validation

- **test_error_handling.py**: Tests for error scenarios
  - Query parsing errors
  - Data extraction errors
  - Response generation errors
  - Context management errors

### **🔄 Integration Tests**
- **test_query_engine_flow.py**: End-to-end workflow testing
  - Complete query processing pipeline
  - Natural language to structured query conversion
  - Data extraction and analysis
  - Response generation and formatting

- **test_chat_integration.py**: Chat interface integration
  - Chat message processing
  - Query integration with chat
  - Response display in chat
  - Context maintenance in chat

- **test_data_integration.py**: Data source integration
  - Session state data access
  - Movement analysis integration
  - Anomaly analysis integration
  - Chart reference integration

---

## 🎯 **Coverage Targets**

| **Component** | **Target** | **Current** | **Status** |
|---------------|------------|-------------|------------|
| **Overall Coverage** | 85% | TBD | 🟡 Pending |
| **Query Parsing** | 90% | TBD | 🟡 Pending |
| **Data Extraction** | 85% | TBD | 🟡 Pending |
| **Response Generation** | 85% | TBD | 🟡 Pending |
| **Context Management** | 90% | TBD | 🟡 Pending |
| **Error Handling** | 95% | TBD | 🟡 Pending |

---

## 🛠️ **Running Tests**

### **Available Commands**
```bash
# Install test dependencies
python tests/story-5-2/run_tests.py install

# Run specific test types
python tests/story-5-2/run_tests.py unit           # Unit tests only
python tests/story-5-2/run_tests.py integration   # Integration tests only
python tests/story-5-2/run_tests.py all           # All tests

# Coverage and reporting
python tests/story-5-2/run_tests.py coverage      # With coverage report
python tests/story-5-2/run_tests.py quick         # Quick smoke tests
```

### **Direct pytest Commands**
```bash
# Run all tests with verbose output
pytest tests/story-5-2/ -v

# Run specific test file
pytest tests/story-5-2/unit/test_query_parsing.py -v

# Run with coverage
pytest tests/story-5-2/ --cov=main --cov-report=html

# Run only failing tests
pytest tests/story-5-2/ --lf
```

---

## 🧩 **Test Data & Fixtures**

### **Sample Financial Data**
The `fixtures/sample_financial_data.json` contains realistic financial scenarios:
- Revenue and expense data
- Movement analysis results
- Anomaly detection data
- Chart configurations
- Session state data

### **Sample Queries**
The `fixtures/sample_queries.json` contains test queries:
- Natural language questions
- Follow-up questions
- Complex queries
- Edge cases
- Error scenarios

### **Mock AI Responses**
The `fixtures/mock_ai_responses.json` contains mock responses:
- Successful query responses
- Error responses
- Contextual responses
- Chart references
- Follow-up responses

---

## 📊 **Test Scenarios**

### **Unit Test Scenarios**
1. **Query Parsing**
   - Parse simple questions ("What drove the increase in marketing expenses?")
   - Parse complex questions with multiple entities
   - Parse follow-up questions
   - Handle malformed queries

2. **Data Extraction**
   - Extract relevant data based on query
   - Filter data by date ranges
   - Aggregate data for analysis
   - Handle missing data gracefully

3. **Response Generation**
   - Generate contextual responses
   - Format numbers and percentages
   - Include relevant context
   - Reference charts and insights

4. **Context Management**
   - Store conversation context
   - Retrieve context for follow-ups
   - Maintain context across sessions
   - Clean up old context

### **Integration Test Scenarios**
1. **End-to-End Query Processing**
   - Complete natural language to response workflow
   - Multiple query types
   - Error handling and recovery
   - Performance validation

2. **Chat Integration**
   - Query processing in chat interface
   - Response display in chat
   - Context maintenance in chat
   - Error handling in chat

3. **Data Integration**
   - Session state data access
   - Movement analysis integration
   - Anomaly analysis integration
   - Chart reference integration

---

## 🎯 **Success Criteria**

### **Functional Requirements**
- ✅ Natural language queries processed accurately
- ✅ Relevant data extracted and analyzed
- ✅ Contextual responses generated with specific numbers
- ✅ Chart and insight references working correctly
- ✅ Follow-up questions handled with context
- ✅ Error handling and recovery implemented

### **Non-Functional Requirements**
- ✅ Query processing within 3 seconds
- ✅ High accuracy in query understanding
- ✅ Seamless integration with existing systems
- ✅ Scalable architecture for complex queries
- ✅ Comprehensive error handling

### **Quality Requirements**
- ✅ 85% code coverage
- ✅ All unit tests passing
- ✅ All integration tests passing
- ✅ Manual testing completed
- ✅ Performance requirements met

---

## 📝 **Test Documentation**

### **Test Reports**
- Test reports are automatically generated
- Coverage reports available in HTML format
- Performance metrics tracked
- Error logs maintained

### **Manual Testing**
- Comprehensive manual testing guide
- Step-by-step test scenarios
- User experience validation
- Cross-browser testing

### **Continuous Integration**
- Tests integrated into CI/CD pipeline
- Automated test execution
- Coverage reporting
- Quality gates

---

## 🚨 **Known Issues**

### **Current Limitations**
- Story 5.2 implementation not yet complete
- Test infrastructure ready for implementation
- Mock data and responses prepared
- Integration points identified

### **Future Enhancements**
- Performance testing for large datasets
- Load testing for concurrent queries
- Security testing for query processing
- Accessibility testing for chat interface

---

## 📞 **Support**

For questions or issues with the test suite:
1. Check the test documentation
2. Review the manual testing guide
3. Run the test suite with verbose output
4. Check the test reports for detailed information

---

**Last Updated**: 2024-12-19  
**Test Suite Version**: 1.0  
**Status**: Ready for Implementation 