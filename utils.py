import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)

def normalize_input(message: str) -> str:
    """Normalize input message by converting to lowercase and trimming spaces."""
    return message.lower().strip()

def extract_message(data: Dict[str, Any]) -> str:
    """Extract message from input data."""
    try:
        # Try to get senderMessage first, then fall back to message
        message = data.get('senderMessage', data.get('message', ''))
        return normalize_input(message)
    except Exception as e:
        logger.error(f"Error extracting message: {e}")
        return ''

def format_response(message: str) -> Dict[str, Any]:
    """Format the response according to the specified format."""
    return {
        "data": [
            {
                "message": message
            }
        ]
    }

def log_request(data: Dict[str, Any]) -> None:
    """Log incoming request data."""
    try:
        logger.info(f"Incoming request data: {json.dumps(data)}")
    except Exception as e:
        logger.error(f"Error logging request: {e}")
