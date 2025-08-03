from flask import Flask, request, jsonify, render_template
import requests
from utils import promt_llm
import asyncio
import logging
from datetime import datetime
from config import FLASK_CONFIG, AI_CONFIG, ERROR_MESSAGES, SUCCESS_MESSAGES, LOGGING_CONFIG

# Configure logging
logging.basicConfig(
    level=getattr(logging, LOGGING_CONFIG['LEVEL']),
    format=LOGGING_CONFIG['FORMAT'],
    filename=LOGGING_CONFIG['FILE']
)
logger = logging.getLogger(__name__)

app = Flask(__name__)
app.secret_key = FLASK_CONFIG['SECRET_KEY']

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
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                "error": "No data provided",
                "message": "Please provide a valid request with a 'promt' field",
                "timestamp": datetime.now().isoformat()
            }), 400

        prompt = data.get("promt")
        history = data.get("history", [])
        
        # Validate input
        if not prompt or not prompt.strip():
            return jsonify({
                "error": "Missing or empty prompt",
                "message": "Please provide a question about your loan data",
                "timestamp": datetime.now().isoformat()
            }), 400
        
        # Check prompt length
        if len(prompt) > AI_CONFIG['MAX_QUERY_LENGTH']:
            return jsonify({
                "error": "Prompt too long",
                "message": f"Please keep your question under {AI_CONFIG['MAX_QUERY_LENGTH']} characters",
                "timestamp": datetime.now().isoformat()
            }), 400

        # Log the request
        logger.info(f"Processing chat request: {prompt[:100]}...")
        
        # Process the request
        response = await promt_llm(query=prompt)
        
        logger.info(f"Chat response generated successfully")
        
        return jsonify({
            "response": response,
            "timestamp": datetime.now().isoformat(),
            "status": "success"
        })

    except Exception as e:
        logger.error(f"Error processing chat request: {e}")
        return jsonify({
            "error": "Internal server error",
            "message": ERROR_MESSAGES['GENERAL_ERROR'],
            "timestamp": datetime.now().isoformat()
        }), 500

@app.route("/health", methods=['GET'])
def health_check():
    """Health check endpoint for monitoring"""
    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "service": "GreenCom Loan Assistant API"
    })

@app.route("/api/info", methods=['GET'])
def api_info():
    """API information endpoint"""
    return jsonify({
        "name": "GreenCom Loan Assistant API",
        "version": "1.0.0",
        "description": "AI-powered loan data analysis and insights",
        "capabilities": [
            "Loan portfolio analysis",
            "Payment trend analysis", 
            "Client behavior insights",
            "Arrears monitoring",
            "Loan manager performance",
            "Product type analysis"
        ],
        "timestamp": datetime.now().isoformat()
    })

@app.errorhandler(404)
def not_found(error):
    return jsonify({
        "error": "Not found",
        "message": "The requested endpoint does not exist",
        "timestamp": datetime.now().isoformat()
    }), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({
        "error": "Internal server error", 
        "message": "Something went wrong on our end. Please try again later.",
        "timestamp": datetime.now().isoformat()
    }), 500

if __name__ == "__main__":
    app.run(
        debug=FLASK_CONFIG['DEBUG'], 
        host=FLASK_CONFIG['HOST'], 
        port=FLASK_CONFIG['PORT']
    )