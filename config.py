"""
Configuration settings for the Brightcom Loan Assistant API
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
    'MAX_QUERY_LENGTH': 500,  # Reduced for better performance
    'MAX_SQL_LENGTH': 300,    # Reduced for security and performance
    'TIMEOUT_SECONDS': 90,    # Increased timeout for complex queries (90 seconds)
    'MAX_ITERATIONS': 6,      # Reduced to prevent excessive processing time
    'TEMPERATURE': 0.1,       # Lower temperature for more consistent responses
    'REQUEST_TIMEOUT': 100    # Total request timeout including processing
}

# Data Configuration
DATA_CONFIG = {
    'CSV_FILE_PATH': 'processed_data.csv',
    'ENCODING': 'utf-8',
    'MAX_ROWS_DISPLAY': 10    # Limit displayed rows for performance
}

# UI Configuration
UI_CONFIG = {
    'APP_TITLE': 'Brightcom Loan Assistant',
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

# Error Messages - Improved for better user experience
ERROR_MESSAGES = {
    'NO_DATA': "I'm sorry, but I can't access the loan data right now. Please check if the data file exists and try again.",
    'INVALID_QUERY': "I couldn't understand that question. Please try asking about loans, payments, or clients in a simpler way.",
    'COMPLEX_QUERY': "That question is too complex. Please ask a simpler question about your loan data.",
    'EMPTY_RESULTS': "I couldn't find any data matching your question. Try asking about something else in your loan portfolio.",
    'TIMEOUT': "The request is taking longer than expected. Please try a simpler question or try again in a moment.",
    'RESOURCE_ERROR': "I'm having trouble processing that question. Please try asking about something more specific in your loan data.",
    'GENERAL_ERROR': "I'm having trouble understanding that question. Please rephrase it or ask about something else in your loan portfolio.",
    'NETWORK_ERROR': "I'm having trouble connecting right now. Please check your connection and try again.",
    'CONNECTION_TIMEOUT': "The request is taking longer than expected. Please try again in a moment.",
    'NETWORK_ISSUE': "Network connection issue. Please check your internet connection.",
    'SQL_ERROR': "There was an issue with the database query. Please try rephrasing your question.",
    'DATA_LOAD_ERROR': "Unable to load loan data. Please check if the data file is available and try again.",
    'TOOL_ERROR': "I'm having trouble using the data analysis tools. Please try asking your question in a different way."
}

# Success Messages
SUCCESS_MESSAGES = {
    'WELCOME': "Hello! I'm here to help you with loan and financial data questions. What would you like to know about your loan portfolio?",
    'DEFAULT_RESPONSE': "I'd be happy to help with loan-related questions! What would you like to know about your loan portfolio?",
    'MEMORY_CLEARED': "Conversation memory has been cleared. You can start a new conversation.",
    'QUERY_SUCCESS': "I've analyzed your loan data. Here's what I found:"
}

# Logging Configuration - Enhanced for better debugging
LOGGING_CONFIG = {
    'LEVEL': 'INFO',
    'FORMAT': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    'FILE': 'loan_assistant.log',
    'MAX_BYTES': 10485760,  # 10MB
    'BACKUP_COUNT': 5
}

# Performance Configuration
PERFORMANCE_CONFIG = {
    'CACHE_ENABLED': True,
    'CACHE_TIMEOUT': 300,  # 5 minutes
    'MAX_CONCURRENT_REQUESTS': 5,
    'REQUEST_TIMEOUT': 30,
    'RETRY_ATTEMPTS': 3,
    'RETRY_DELAY': 1
}

# Security Configuration
SECURITY_CONFIG = {
    'ALLOWED_SQL_KEYWORDS': ['SELECT', 'FROM', 'WHERE', 'ORDER BY', 'GROUP BY', 'LIMIT', 'COUNT', 'SUM', 'AVG', 'MAX', 'MIN'],
    'BLOCKED_SQL_KEYWORDS': ['INSERT', 'UPDATE', 'DELETE', 'DROP', 'CREATE', 'ALTER', 'EXEC', 'EXECUTE'],
    'MAX_QUERY_COMPLEXITY': 5,  # Number of clauses allowed
    'RATE_LIMIT_PER_MINUTE': 30
} 