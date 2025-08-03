"""
Configuration settings for the GreenCom Loan Assistant API
"""

import os

# Flask Configuration
FLASK_CONFIG = {
    'DEBUG': True,
    'HOST': '0.0.0.0',
    'PORT': 5500,
    'SECRET_KEY': os.environ.get('SECRET_KEY', 'your-secret-key-here')
}

# AI Model Configuration
AI_CONFIG = {
    'MODEL_NAME': 'mistral',
    'MAX_QUERY_LENGTH': 1000,
    'MAX_SQL_LENGTH': 500,
    'TIMEOUT_SECONDS': 30
}

# Data Configuration
DATA_CONFIG = {
    'CSV_FILE_PATH': 'processed_data.csv',
    'ENCODING': 'utf-8'
}

# UI Configuration
UI_CONFIG = {
    'APP_TITLE': 'GreenCom Loan Assistant',
    'APP_DESCRIPTION': 'Your intelligent financial data companion',
    'WELCOME_MESSAGE': "I'm here to help you understand your loan data better. You can ask me about:",
    'SUGGESTIONS': [
        {
            'text': 'Active Loans',
            'query': 'How many active loans do we have?',
            'icon': 'fas fa-chart-bar'
        },
        {
            'text': 'High Arrears',
            'query': 'Which clients have the highest arrears?',
            'icon': 'fas fa-exclamation-triangle'
        },
        {
            'text': 'Portfolio Value',
            'query': 'What is our total loan portfolio value?',
            'icon': 'fas fa-dollar-sign'
        },
        {
            'text': 'Multiple Loans',
            'query': 'Show me clients with multiple loans',
            'icon': 'fas fa-users'
        },
        {
            'text': 'Payment Trends',
            'query': 'Show me payment trends',
            'icon': 'fas fa-chart-line'
        },
        {
            'text': 'Loan Managers',
            'query': 'Which loan managers have the most clients?',
            'icon': 'fas fa-user-tie'
        },
        {
            'text': 'Loan Products',
            'query': 'What are our most popular loan products?',
            'icon': 'fas fa-tags'
        }
    ]
}

# Error Messages
ERROR_MESSAGES = {
    'NO_DATA': "I'm sorry, but I can't access the loan data right now. Please try again later.",
    'INVALID_QUERY': "I couldn't understand that question. Could you please ask about loans, payments, or clients in a different way?",
    'COMPLEX_QUERY': "That query is too complex. Could you please ask a simpler question about the loan data?",
    'EMPTY_RESULTS': "I couldn't find any data matching your question. Could you try rephrasing it or ask about something else in the loan portfolio?",
    'TIMEOUT': "I'm taking a bit longer than usual to process your question. Could you try asking it again in a moment?",
    'RESOURCE_ERROR': "I'm having trouble processing that complex question. Could you try asking about something more specific in your loan data?",
    'GENERAL_ERROR': "I'm having trouble understanding that question. Could you please rephrase it or ask about something else in your loan portfolio?",
    'NETWORK_ERROR': "I'm having trouble connecting right now. Please check your connection and try again.",
    'CONNECTION_TIMEOUT': "The request is taking longer than expected. Please try again in a moment.",
    'NETWORK_ISSUE': "Network connection issue. Please check your internet connection."
}

# Success Messages
SUCCESS_MESSAGES = {
    'WELCOME': "Hello! I'm here to help you with loan and financial data questions. What would you like to know about your loan portfolio?",
    'DEFAULT_RESPONSE': "I'd be happy to help with loan-related questions! What would you like to know about your loan portfolio?"
}

# Logging Configuration
LOGGING_CONFIG = {
    'LEVEL': 'INFO',
    'FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'FILE': 'loan_assistant.log'
} 