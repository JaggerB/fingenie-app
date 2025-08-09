"""
Test Suite for Story 5.1: Chat Interface Foundation

This module contains comprehensive tests for the chat interface implementation,
including unit tests, integration tests, and end-to-end test scenarios.
"""

import pytest
import streamlit as st
import pandas as pd
from datetime import datetime
import sys
import os

# Add the parent directory to the path to import main module
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

# Import the chat interface functions
from main import (
    create_chat_interface,
    create_chat_message_display,
    display_chat_message,
    create_chat_input_field,
    add_chat_message,
    create_loading_indicator,
    process_chat_message,
    initialize_session_state
)


class TestChatInterfaceFoundation:
    """Test suite for chat interface foundation functionality."""
    
    @pytest.fixture(autouse=True)
    def setup_session_state(self):
        """Initialize session state for each test."""
        if not hasattr(st, 'session_state'):
            st.session_state = {}
        initialize_session_state()
        yield
        # Clean up after each test
        if 'chat_messages' in st.session_state:
            st.session_state.chat_messages = []
        if 'chat_loading' in st.session_state:
            st.session_state.chat_loading = False
        if 'chat_error' in st.session_state:
            st.session_state.chat_error = None

    def test_session_state_initialization(self):
        """Test that chat session state is properly initialized."""
        assert 'chat_messages' in st.session_state
        assert 'chat_conversation_id' in st.session_state
        assert 'chat_loading' in st.session_state
        assert 'chat_error' in st.session_state
        assert isinstance(st.session_state.chat_messages, list)
        assert st.session_state.chat_loading is False
        assert st.session_state.chat_error is None

    def test_add_chat_message_user(self):
        """Test adding a user message to chat history."""
        initial_count = len(st.session_state.chat_messages)
        test_message = "Test user message"
        
        add_chat_message(test_message, 'user')
        
        assert len(st.session_state.chat_messages) == initial_count + 1
        message = st.session_state.chat_messages[-1]
        assert message['type'] == 'user'
        assert message['content'] == test_message
        assert 'timestamp' in message
        assert 'id' in message
        assert message['id'] == initial_count + 1

    def test_add_chat_message_ai(self):
        """Test adding an AI message to chat history."""
        initial_count = len(st.session_state.chat_messages)
        test_message = "Test AI response"
        
        add_chat_message(test_message, 'ai')
        
        assert len(st.session_state.chat_messages) == initial_count + 1
        message = st.session_state.chat_messages[-1]
        assert message['type'] == 'ai'
        assert message['content'] == test_message
        assert 'timestamp' in message
        assert 'id' in message

    def test_message_timestamp_format(self):
        """Test that message timestamps are in correct format."""
        test_message = "Test message"
        add_chat_message(test_message, 'user')
        
        message = st.session_state.chat_messages[-1]
        timestamp = message['timestamp']
        
        # Check if timestamp is in HH:MM format
        assert len(timestamp) == 5  # HH:MM format
        assert timestamp.count(':') == 1
        hours, minutes = timestamp.split(':')
        assert hours.isdigit() and minutes.isdigit()
        assert 0 <= int(hours) <= 23
        assert 0 <= int(minutes) <= 59

    def test_message_id_increment(self):
        """Test that message IDs increment properly."""
        # Add multiple messages
        for i in range(3):
            add_chat_message(f"Message {i+1}", 'user')
        
        # Check that IDs increment properly
        for i, message in enumerate(st.session_state.chat_messages):
            assert message['id'] == i + 1

    def test_process_chat_message_placeholder(self):
        """Test that process_chat_message creates placeholder response."""
        test_message = "Test question"
        initial_count = len(st.session_state.chat_messages)
        
        process_chat_message(test_message)
        
        # Should add both user and AI messages
        assert len(st.session_state.chat_messages) == initial_count + 2
        
        # Check user message
        user_message = st.session_state.chat_messages[-2]
        assert user_message['type'] == 'user'
        assert user_message['content'] == test_message
        
        # Check AI response
        ai_message = st.session_state.chat_messages[-1]
        assert ai_message['type'] == 'ai'
        assert 'placeholder response' in ai_message['content'].lower()

    def test_process_chat_message_error_handling(self):
        """Test error handling in process_chat_message."""
        # Mock an error by making the function fail
        original_add_chat_message = add_chat_message
        
        def mock_add_chat_message(content, message_type='user'):
            if message_type == 'ai':
                raise Exception("Test error")
            return original_add_chat_message(content, message_type)
        
        # Temporarily replace the function
        import main
        main.add_chat_message = mock_add_chat_message
        
        try:
            process_chat_message("Test message")
            assert st.session_state.chat_error is not None
            assert "Failed to process message" in st.session_state.chat_error
        finally:
            # Restore original function
            main.add_chat_message = original_add_chat_message

    def test_chat_message_display_empty(self):
        """Test chat message display when no messages exist."""
        # Ensure no messages exist
        st.session_state.chat_messages = []
        
        # This should not raise an exception
        try:
            create_chat_message_display()
            # If we get here, the function executed successfully
            assert True
        except Exception as e:
            pytest.fail(f"create_chat_message_display failed with empty messages: {e}")

    def test_chat_message_display_with_messages(self):
        """Test chat message display with existing messages."""
        # Add some test messages
        add_chat_message("User message 1", 'user')
        add_chat_message("AI response 1", 'ai')
        add_chat_message("User message 2", 'user')
        
        # This should not raise an exception
        try:
            create_chat_message_display()
            # If we get here, the function executed successfully
            assert True
        except Exception as e:
            pytest.fail(f"create_chat_message_display failed with messages: {e}")

    def test_chat_input_field_creation(self):
        """Test that chat input field is created properly."""
        try:
            user_input, send_button = create_chat_input_field()
            # If we get here, the function executed successfully
            assert True
        except Exception as e:
            pytest.fail(f"create_chat_input_field failed: {e}")

    def test_loading_indicator_creation(self):
        """Test that loading indicator is created properly."""
        # Set loading state
        st.session_state.chat_loading = True
        
        try:
            create_loading_indicator()
            # If we get here, the function executed successfully
            assert True
        except Exception as e:
            pytest.fail(f"create_loading_indicator failed: {e}")

    def test_loading_indicator_not_shown_when_not_loading(self):
        """Test that loading indicator is not shown when not loading."""
        # Ensure loading state is False
        st.session_state.chat_loading = False
        
        try:
            create_loading_indicator()
            # If we get here, the function executed successfully
            assert True
        except Exception as e:
            pytest.fail(f"create_loading_indicator failed when not loading: {e}")

    def test_chat_interface_creation(self):
        """Test that the complete chat interface is created properly."""
        try:
            create_chat_interface()
            # If we get here, the function executed successfully
            assert True
        except Exception as e:
            pytest.fail(f"create_chat_interface failed: {e}")

    def test_chat_interface_with_error_state(self):
        """Test chat interface with error state."""
        st.session_state.chat_error = "Test error message"
        
        try:
            create_chat_interface()
            # Error should be cleared after display
            assert st.session_state.chat_error is None
        except Exception as e:
            pytest.fail(f"create_chat_interface failed with error state: {e}")

    def test_chat_interface_with_loading_state(self):
        """Test chat interface with loading state."""
        st.session_state.chat_loading = True
        
        try:
            create_chat_interface()
            # If we get here, the function executed successfully
            assert True
        except Exception as e:
            pytest.fail(f"create_chat_interface failed with loading state: {e}")

    def test_message_content_validation(self):
        """Test that message content is properly validated and stored."""
        test_messages = [
            "Simple message",
            "Message with special characters: !@#$%^&*()",
            "Message with numbers: 12345",
            "Message with spaces and   tabs",
            "",  # Empty message
            "Very long message " * 100,  # Long message
        ]
        
        for test_message in test_messages:
            add_chat_message(test_message, 'user')
            message = st.session_state.chat_messages[-1]
            assert message['content'] == test_message
            assert message['type'] == 'user'

    def test_message_type_validation(self):
        """Test that message types are properly validated."""
        # Test valid message types
        valid_types = ['user', 'ai']
        for msg_type in valid_types:
            add_chat_message("Test message", msg_type)
            message = st.session_state.chat_messages[-1]
            assert message['type'] == msg_type
        
        # Test invalid message type (should default to 'user')
        add_chat_message("Test message", 'invalid_type')
        message = st.session_state.chat_messages[-1]
        assert message['type'] == 'user'  # Should default to 'user'

    def test_chat_history_persistence(self):
        """Test that chat history persists across function calls."""
        # Add initial messages
        add_chat_message("Message 1", 'user')
        add_chat_message("Response 1", 'ai')
        
        initial_count = len(st.session_state.chat_messages)
        
        # Call functions that might affect chat history
        create_chat_message_display()
        create_chat_interface()
        
        # Chat history should remain intact
        assert len(st.session_state.chat_messages) == initial_count
        assert st.session_state.chat_messages[0]['content'] == "Message 1"
        assert st.session_state.chat_messages[1]['content'] == "Response 1"


class TestChatInterfaceIntegration:
    """Integration tests for chat interface with other components."""
    
    @pytest.fixture(autouse=True)
    def setup_session_state(self):
        """Initialize session state for each test."""
        if not hasattr(st, 'session_state'):
            st.session_state = {}
        initialize_session_state()
        yield
        # Clean up after each test
        if 'chat_messages' in st.session_state:
            st.session_state.chat_messages = []

    def test_chat_interface_with_processed_data(self):
        """Test chat interface when processed data is available."""
        # Mock processed data
        test_data = pd.DataFrame({
            'Date': ['2024-01-01', '2024-01-02'],
            'Account': ['Revenue', 'Expenses'],
            'Amount': [1000, 500]
        })
        st.session_state.final_processed_data = test_data
        
        try:
            create_chat_interface()
            # If we get here, the function executed successfully
            assert True
        except Exception as e:
            pytest.fail(f"create_chat_interface failed with processed data: {e}")

    def test_chat_interface_without_processed_data(self):
        """Test chat interface when no processed data is available."""
        # Ensure no processed data
        if 'final_processed_data' in st.session_state:
            del st.session_state.final_processed_data
        
        try:
            create_chat_interface()
            # If we get here, the function executed successfully
            assert True
        except Exception as e:
            pytest.fail(f"create_chat_interface failed without processed data: {e}")

    def test_chat_interface_with_movement_analysis(self):
        """Test chat interface when movement analysis data is available."""
        # Mock movement analysis data
        st.session_state.movement_analysis = {
            'ranked_movements': pd.DataFrame({
                'account': ['Revenue', 'Expenses'],
                'movement': [100, -50],
                'percentage': [10.0, -5.0]
            })
        }
        
        try:
            create_chat_interface()
            # If we get here, the function executed successfully
            assert True
        except Exception as e:
            pytest.fail(f"create_chat_interface failed with movement analysis: {e}")

    def test_chat_interface_with_anomaly_analysis(self):
        """Test chat interface when anomaly analysis data is available."""
        # Mock anomaly analysis data
        st.session_state.anomaly_analysis = {
            'combined_anomalies': pd.DataFrame({
                'Date': ['2024-01-01'],
                'Account': ['Revenue'],
                'Amount': [1000],
                'anomaly_score': [0.8]
            })
        }
        
        try:
            create_chat_interface()
            # If we get here, the function executed successfully
            assert True
        except Exception as e:
            pytest.fail(f"create_chat_interface failed with anomaly analysis: {e}")


class TestChatInterfaceEndToEnd:
    """End-to-end tests for chat interface workflow."""
    
    @pytest.fixture(autouse=True)
    def setup_session_state(self):
        """Initialize session state for each test."""
        if not hasattr(st, 'session_state):
            st.session_state = {}
        initialize_session_state()
        yield
        # Clean up after each test
        if 'chat_messages' in st.session_state:
            st.session_state.chat_messages = []

    def test_complete_chat_workflow(self):
        """Test the complete chat workflow from start to finish."""
        # Step 1: Initialize chat interface
        try:
            create_chat_interface()
        except Exception as e:
            pytest.fail(f"Step 1 failed: {e}")
        
        # Step 2: Add a user message
        try:
            add_chat_message("What are the key insights from my data?", 'user')
        except Exception as e:
            pytest.fail(f"Step 2 failed: {e}")
        
        # Step 3: Process the message
        try:
            process_chat_message("What are the key insights from my data?")
        except Exception as e:
            pytest.fail(f"Step 3 failed: {e}")
        
        # Step 4: Verify the conversation
        assert len(st.session_state.chat_messages) == 2
        assert st.session_state.chat_messages[0]['type'] == 'user'
        assert st.session_state.chat_messages[1]['type'] == 'ai'
        assert "key insights" in st.session_state.chat_messages[0]['content'].lower()

    def test_multiple_message_conversation(self):
        """Test a conversation with multiple messages."""
        # Add multiple messages in a conversation
        conversation = [
            ("What are the trends in revenue?", 'user'),
            ("Revenue trends placeholder response", 'ai'),
            ("Show me the biggest movements", 'user'),
            ("Biggest movements placeholder response", 'ai'),
            ("Create a chart for expenses", 'user'),
            ("Chart creation placeholder response", 'ai'),
        ]
        
        for content, msg_type in conversation:
            try:
                add_chat_message(content, msg_type)
            except Exception as e:
                pytest.fail(f"Failed to add message '{content}': {e}")
        
        # Verify conversation
        assert len(st.session_state.chat_messages) == len(conversation)
        
        # Verify message order and types
        for i, (content, msg_type) in enumerate(conversation):
            message = st.session_state.chat_messages[i]
            assert message['content'] == content
            assert message['type'] == msg_type

    def test_chat_interface_error_recovery(self):
        """Test that chat interface recovers from errors."""
        # Simulate an error
        st.session_state.chat_error = "Test error occurred"
        
        try:
            create_chat_interface()
            # Error should be cleared after display
            assert st.session_state.chat_error is None
        except Exception as e:
            pytest.fail(f"Chat interface failed to recover from error: {e}")

    def test_chat_interface_performance(self):
        """Test chat interface performance with many messages."""
        # Add many messages to test performance
        message_count = 50
        
        for i in range(message_count):
            add_chat_message(f"Message {i+1}", 'user' if i % 2 == 0 else 'ai')
        
        # Verify all messages were added
        assert len(st.session_state.chat_messages) == message_count
        
        # Test that display still works
        try:
            create_chat_message_display()
            assert True
        except Exception as e:
            pytest.fail(f"Chat interface failed with {message_count} messages: {e}")


if __name__ == "__main__":
    # Run the tests
    pytest.main([__file__, "-v"]) 