from flask import Flask, request, jsonify
from flask_cors import CORS
import logging
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
import os

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
CORS(app)  # Enable CORS for all routes

# Database configuration
class Base(DeclarativeBase):
    pass

db = SQLAlchemy(model_class=Base)
app.config.from_object('config')

# Verify OpenAI API key is present
if not os.environ.get("OPENAI_API_KEY"):
    logger.error("OpenAI API key not found in environment variables")
    raise ValueError("OpenAI API key is required")

db.init_app(app)

# Import dependencies after app initialization
from chat_handler import ChatHandler
from utils import format_response, log_request, extract_message

chat_handler = ChatHandler()

logger.info("Initializing Flask routes...")

@app.route('/')
def index():
    """Root endpoint for testing."""
    logger.debug("Root endpoint accessed")
    routes = [str(rule) for rule in app.url_map.iter_rules()]
    logger.info("Registered routes: %s", routes)
    return jsonify({
        "status": "running",
        "routes": routes
    })

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint."""
    logger.debug("Health check endpoint accessed")
    return jsonify({"status": "healthy"}), 200

@app.route('/chat', methods=['POST'])
def chat():
    """Chat endpoint that handles incoming messages."""
    logger.debug("Chat endpoint accessed with request method: %s", request.method)
    logger.debug("Request headers: %s", dict(request.headers))

    try:
        data = request.get_json()
        logger.debug("Received JSON data: %s", data)

        if not data:
            logger.error("No JSON data provided in request")
            return jsonify({"error": "No data provided"}), 400

        # Log incoming request
        log_request(data)

        # Extract and normalize message
        message = extract_message(data)
        if not message:
            logger.error("No message found in request data")
            return jsonify({"error": "No message found in request"}), 400

        # Process message and get response
        response, status_code = chat_handler.process_message(data)
        logger.debug("Generated response: %s, status: %d", response, status_code)

        if status_code != 200:
            return jsonify({"error": response}), status_code

        if not response:  # Empty response for completed conversations
            return jsonify(format_response("")), 200

        return jsonify(format_response(response)), 200

    except Exception as e:
        logger.error(f"Error in chat endpoint: {e}", exc_info=True)
        return jsonify({"error": "Internal server error"}), 500

logger.info("Flask routes initialized successfully")

# Create database tables
with app.app_context():
    import models  # noqa: F401
    db.create_all()