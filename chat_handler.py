import json
import logging
from typing import Tuple, Dict, Any
from datetime import datetime
from openai import OpenAI
from config import OPENAI_API_KEY, SYSTEM_PROMPT, CHAT_STATES
from models import ChatSession
from app import db

logger = logging.getLogger(__name__)
client = OpenAI(api_key=OPENAI_API_KEY)

class ChatHandler:
    @staticmethod
    def get_or_create_session(user_id: str) -> ChatSession:
        """Get or create a new chat session for the user."""
        session = ChatSession.query.filter_by(user_id=user_id).first()
        if not session:
            logger.info(f"Creating new chat session for user: {user_id}")
            session = ChatSession(user_id=user_id)
            db.session.add(session)
            db.session.commit()
        else:
            logger.debug(f"Found existing chat session for user: {user_id}, state: {session.state}")
        return session

    @staticmethod
    def generate_response(message: str, context: Dict[str, Any], current_state: int) -> str:
        """Generate response using GPT-3.5."""
        try:
            logger.debug(f"Generating response for message: {message}")
            logger.debug(f"Current context: {context}")
            logger.debug(f"Current state: {current_state}")

            # If we're in FINAL_QUESTION state, don't generate any response
            if current_state == CHAT_STATES['FINAL_QUESTION']:
                return ""

            # Build conversation history from context
            conversation_history = []
            if 'messages' in context:
                conversation_history = context['messages']

            # Add state-specific context to help guide the response
            state_context = {
                CHAT_STATES['INITIAL']: "Say hey and ask how they are",
                CHAT_STATES['GREETING_SENT']: "Say doing okay and introduce yourself as Ahlam from Mombasa and ask for their name",
                CHAT_STATES['NAME_ASKED']: "Say nice to meet you and ask where they're from",
                CHAT_STATES['LOCATION_ASKED']: "Ask their age",
                CHAT_STATES['AGE_ASKED']: "Say cool im 24 do you want to see something sexy",
                CHAT_STATES['FINAL_QUESTION']: "Stop responding completely",
            }.get(current_state, "Follow the conversation naturally")

            messages = [
                {"role": "system", "content": SYSTEM_PROMPT + f"\nCurrent context: {state_context}"},
                *[{"role": "assistant" if i % 2 == 0 else "user", "content": msg} 
                  for i, msg in enumerate(conversation_history)],
                {"role": "user", "content": message}
            ]

            response = client.chat.completions.create(
                model="gpt-3.5-turbo",
                messages=messages,
                max_tokens=150,
                temperature=0.7
            )

            generated_response = response.choices[0].message.content.strip()
            logger.debug(f"Generated response: {generated_response}")
            return generated_response

        except Exception as e:
            logger.error(f"Error generating response: {e}", exc_info=True)
            return "sorry having trouble responding right now try again later"

    def process_message(self, data: Dict[str, Any]) -> Tuple[str, int]:
        """Process incoming message and return appropriate response."""
        try:
            user_id = data.get('senderName', 'unknown_user')
            message = data.get('senderMessage', '').strip()

            logger.info(f"Processing message from user {user_id}: {message}")

            if not message:
                logger.warning(f"Empty message received from user: {user_id}")
                return "I couldn't understand your message. Could you please try again?", 400

            session = self.get_or_create_session(user_id)

            if session.completed:
                logger.info(f"Conversation already completed for user: {user_id}")
                return "", 200

            # Log current state before processing
            logger.debug(f"Current session state: {session.state}")
            context = json.loads(session.context) if session.context else {}

            # Initialize or update message history
            if 'messages' not in context:
                context['messages'] = []
            context['messages'].append(message)

            response = self.generate_response(message, context, session.state)
            context['messages'].append(response)

            # Update session state based on conversation flow
            previous_state = session.state
            if session.state == CHAT_STATES['FINAL_QUESTION']:
                session.completed = True
                logger.info(f"Marking conversation as completed for user: {user_id}")
            else:
                session.state += 1
            logger.info(f"State transition: {previous_state} -> {session.state}")

            # Update context with new information
            session.context = json.dumps(context)
            session.updated_at = datetime.utcnow()

            logger.debug(f"Updated context: {context}")
            db.session.commit()

            return response, 200

        except Exception as e:
            logger.error(f"Error processing message: {e}", exc_info=True)
            return "An error occurred while processing your message.", 500