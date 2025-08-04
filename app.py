from flask import Flask, request, jsonify, render_template
import requests
from utils_simple import promt_llm, clear_conversation_memory, get_conversation_memory
import asyncio
import logging
import time
from datetime import datetime
from config import FLASK_CONFIG, AI_CONFIG, ERROR_MESSAGES, SUCCESS_MESSAGES, LOGGING_CONFIG, PERFORMANCE_CONFIG, SECURITY_CONFIG
import re

# Configure logging with rotation
from logging.handlers import RotatingFileHandler
import os

# Create logs directory if it doesn't exist
os.makedirs('logs', exist_ok=True)

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['LEVEL']),
    format=LOGGING_CONFIG['FORMAT'],
    handlers=[
        RotatingFileHandler(
            f"logs/{LOGGING_CONFIG['FILE']}", 
            maxBytes=LOGGING_CONFIG['MAX_BYTES'], 
            backupCount=LOGGING_CONFIG['BACKUP_COUNT']
        ),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = FLASK_CONFIG['SECRET_KEY']

# Simple rate limiting
request_timestamps = {}

def check_rate_limit(client_ip):
    """Simple rate limiting implementation"""
    current_time = time.time()
    if client_ip in request_timestamps:
        # Clean old timestamps
        request_timestamps[client_ip] = [t for t in request_timestamps[client_ip] 
                                        if current_time - t < 60]
        
        if len(request_timestamps[client_ip]) >= SECURITY_CONFIG['RATE_LIMIT_PER_MINUTE']:
            return False
        
        request_timestamps[client_ip].append(current_time)
    else:
        request_timestamps[client_ip] = [current_time]
    
    return True

def validate_sql_query(query):
    """Validate SQL query for security"""
    if not query:
        return False, "Empty query"
    
    query_upper = query.upper()
    
    # Check for blocked keywords
    for blocked in SECURITY_CONFIG['BLOCKED_SQL_KEYWORDS']:
        if blocked in query_upper:
            return False, f"Blocked SQL keyword: {blocked}"
    
    # Check for basic SELECT structure
    if not re.search(r'^SELECT\s+', query_upper):
        return False, "Query must start with SELECT"
    
    # Check for df table reference
    if 'FROM DF' not in query_upper:
        return False, "Query must reference the 'df' table"
    
    # Check query complexity
    complexity = len(re.findall(r'\b(WHERE|ORDER BY|GROUP BY|HAVING|LIMIT)\b', query_upper))
    if complexity > SECURITY_CONFIG['MAX_QUERY_COMPLEXITY']:
        return False, "Query too complex"
    
    return True, "Valid query"

def sanitize_input(text):
    """Sanitize user input"""
    if not text:
        return ""
    
    # Remove potentially dangerous characters
    text = re.sub(r'[<>"\']', '', text)
    return text.strip()

@app.route("/")
def index():
    return render_template("index.html")

@app.route("/home/", methods=['GET'])
async def home():
    try:
        response = await promt_llm(query="Hello, How are you")
        return jsonify({
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error in home endpoint: {e}")
        return jsonify({
            "response": SUCCESS_MESSAGES['WELCOME'],
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        }), 200

@app.route("/chat", methods=['POST'])
async def chat():
    start_time = time.time()
    client_ip = request.remote_addr
    
    try:
        # Rate limiting
        if not check_rate_limit(client_ip):
            return jsonify({
                "error": "Rate limit exceeded",
                "message": "Too many requests. Please wait a minute before trying again.",
                "timestamp": datetime.now().isoformat()
            }), 429
        
        # Validate request
        if not request.is_json:
            return jsonify({
                "error": "Invalid content type",
                "message": "Request must be JSON",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No data provided",
                "message": "Please provide a valid request with a 'promt' field",
                "timestamp": datetime.now().isoformat()
            }), 400

        prompt = data.get("promt")
        history = data.get("history", [])
        
        # Sanitize and validate input
        if not prompt or not prompt.strip():
            return jsonify({
                "error": "Missing or empty prompt",
                "message": "Please provide a question about your loan data",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        prompt = sanitize_input(prompt)
        
        # Check prompt length
        if len(prompt) > AI_CONFIG['MAX_QUERY_LENGTH']:
            return jsonify({
                "error": "Prompt too long",
                "message": f"Please keep your question under {AI_CONFIG['MAX_QUERY_LENGTH']} characters",
                "timestamp": datetime.now().isoformat()
            }), 400

        # Log the request
        logger.info(f"Processing chat request from {client_ip}: {prompt[:100]}...")
        
        # Process the request with timeout
        try:
            # Use a more generous timeout for AI processing
            response = await asyncio.wait_for(
                promt_llm(query=prompt), 
                timeout=AI_CONFIG['REQUEST_TIMEOUT']
            )
        except asyncio.TimeoutError:
            logger.warning(f"Request timeout for client {client_ip} after {AI_CONFIG['REQUEST_TIMEOUT']}s")
            return jsonify({
                "error": "Request timeout",
                "message": ERROR_MESSAGES['TIMEOUT'],
                "timestamp": datetime.now().isoformat(),
                "timeout_seconds": AI_CONFIG['REQUEST_TIMEOUT']
            }), 408
        
        # Log response time
        response_time = time.time() - start_time
        logger.info(f"Chat response generated successfully in {response_time:.2f}s")
        
        return jsonify({
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "status": "success",
            "response_time": round(response_time, 2)
        })

    except Exception as e:
        logger.error(f"Error processing chat request from {client_ip}: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": ERROR_MESSAGES['GENERAL_ERROR'],
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/health", methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    try:
        # Check if data file exists
        from config import DATA_CONFIG
        import os
        data_file_exists = os.path.exists(DATA_CONFIG['CSV_FILE_PATH'])
        
        return jsonify({
            "status": "healthy" if data_file_exists else "degraded",
            "timestamp": datetime.now().isoformat(),
            "service": "Brightcom Loan Assistant API",
            "data_file_available": data_file_exists,
            "uptime": time.time() - app.start_time if hasattr(app, 'start_time') else 0
        })
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return jsonify({
            "status": "unhealthy",
            "timestamp": datetime.now().isoformat(),
            "service": "Brightcom Loan Assistant API",
            "error": str(e)
        }), 500

@app.route("/api/info", methods=['GET'])
def api_info():
    """API information endpoint"""
    return jsonify({
        "name": "Brightcom Loan Assistant API",
        "version": "2.0.0",
        "description": "AI-powered loan data analysis and insights",
        "capabilities": [
            "Loan portfolio analysis",
            "Payment trend analysis", 
            "Client behavior insights",
            "Arrears monitoring",
            "Loan manager performance",
            "Product type analysis"
        ],
        "config": {
            "max_query_length": AI_CONFIG['MAX_QUERY_LENGTH'],
            "max_sql_length": AI_CONFIG['MAX_SQL_LENGTH'],
            "timeout_seconds": AI_CONFIG['TIMEOUT_SECONDS'],
            "rate_limit_per_minute": SECURITY_CONFIG['RATE_LIMIT_PER_MINUTE']
        },
        "timestamp": datetime.now().isoformat()
    })

@app.route("/api/memory/clear", methods=['POST'])
def clear_memory():
    """Clear conversation memory"""
    try:
        result = clear_conversation_memory()
        logger.info("Memory cleared successfully")
        return jsonify({
            "message": result,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error clearing memory: {e}")
        return jsonify({
            "error": "Failed to clear memory",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/memory", methods=['GET'])
def get_memory():
    """Get current conversation memory"""
    try:
        memory_messages = get_conversation_memory()
        return jsonify({
            "memory": [{"role": msg.type, "content": msg.content} for msg in memory_messages],
            "message_count": len(memory_messages),
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error getting memory: {e}")
        return jsonify({
            "error": "Failed to get memory",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/debug/memory", methods=['GET'])
def debug_memory():
    """Debug endpoint to check memory status"""
    try:
        memory_messages = get_conversation_memory()
        return jsonify({
            "memory_exists": True,
            "memory_type": "simple_agent",
            "message_count": len(memory_messages),
            "messages": [{"role": msg.type, "content": msg.content[:100] + "..." if len(msg.content) > 100 else msg.content} for msg in memory_messages],
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        })
    except Exception as e:
        logger.error(f"Error in debug memory: {e}")
        return jsonify({
            "error": "Debug memory failed",
            "message": str(e),
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/api/validate-query", methods=['POST'])
def validate_query():
    """Validate SQL query endpoint for testing"""
    try:
        data = request.get_json()
        if not data or 'query' not in data:
            return jsonify({
                "error": "Missing query",
                "message": "Please provide a 'query' field"
            }), 400
        
        query = data['query']
        is_valid, message = validate_sql_query(query)
        
        return jsonify({
            "valid": is_valid,
            "message": message,
            "timestamp": datetime.now().isoformat()
        })
    except Exception as e:
        logger.error(f"Error validating query: {e}")
        return jsonify({
            "error": "Validation failed",
            "message": str(e)
        }), 500

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not found",
        "message": "The requested endpoint does not exist",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(405)
def method_not_allowed(error):
    return jsonify({
        "error": "Method not allowed",
        "message": "The HTTP method is not supported for this endpoint",
        "timestamp": datetime.now().isoformat()
    }), 405

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Internal server error: {error}")
    return jsonify({
        "error": "Internal server error", 
        "message": "Something went wrong on our end. Please try again later.",
        "timestamp": datetime.now().isoformat()
    }), 500

@app.errorhandler(Exception)
def handle_exception(error):
    logger.error(f"Unhandled exception: {error}")
    return jsonify({
        "error": "Unexpected error",
        "message": "An unexpected error occurred. Please try again.",
        "timestamp": datetime.now().isoformat()
    }), 500

# Store app start time for uptime calculation
app.start_time = time.time()

if __name__ == "__main__":
    logger.info("Starting Brightcom Loan Assistant API...")
    app.run(
        debug=FLASK_CONFIG['DEBUG'], 
        host=FLASK_CONFIG['HOST'], 
        port=FLASK_CONFIG['PORT']
    )