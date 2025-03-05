import json
import logging
from typing import Tuple, Dict, Any
from datetime import datetime
import openai
from config import OPENAI_API_KEY, SYSTEM_PROMPT, CHAT_STATES
from models import ChatSession
from app import db

logger = logging.getLogger(__name__)
openai.api_key = OPENAI_API_KEY

class ChatHandler:
    @staticmethod
    def get_or_create_session(user_id: str) -> ChatSession:
        """Get or create a new chat session for the user."""
        session = ChatSession.query.filter_by(user_id=user_id).first()
        if not session:
            session = ChatSession(user_id=user_id)
            db.session.add(session)
            db.session.commit()
        return session

    @staticmethod
    def generate_response(message: str, context: Dict[str, Any]) -> str:
        """Generate response using GPT-3.5."""
        try:
            messages = [
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "assistant", "content": json.dumps(context)},
                {"role": "user", "content": message}
            ]
            
            response = openai.ChatCompletion.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )
            
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"Error generating response: {e}")
            return "I apologize, but I'm having trouble responding right now. Please try again later."

    def process_message(self, data: Dict[str, Any]) -> Tuple[str, int]:
        """Process incoming message and return appropriate response."""
        try:
            user_id = data.get('senderName', 'unknown_user')
            message = data.get('senderMessage', '').strip()
            
            if not message:
                return "I couldn't understand your message. Could you please try again?", 400

            session = self.get_or_create_session(user_id)
            
            if session.completed:
                return "", 200

            context = json.loads(session.context) if session.context else {}
            response = self.generate_response(message, context)
            
            # Update session state based on conversation flow
            if session.state == CHAT_STATES['FINAL_QUESTION']:
                session.completed = True
            else:
                session.state += 1
            
            # Update context with new information
            context['last_message'] = message
            context['last_response'] = response
            session.context = json.dumps(context)
            session.updated_at = datetime.utcnow()
            
            db.session.commit()
            
            return response, 200
            
        except Exception as e:
            logger.error(f"Error processing message: {e}")
            return "An error occurred while processing your message.", 500
