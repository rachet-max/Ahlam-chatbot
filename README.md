# Ahlam Chatbot

A Flask-based conversational AI chatbot using GPT-3.5 for natural language processing.

## Features
- Natural conversation flow with context awareness
- Multilingual support (English and Swahili)
- Web interface for easy interaction
- Conversation state management

## Setup
1. Clone the repository
2. Set up environment variables:
   - `OPENAI_API_KEY`: Your OpenAI API key
   - `SESSION_SECRET`: Secret key for Flask sessions
   - `DATABASE_URL`: PostgreSQL database URL (for Railway deployment)

## Development
```bash
# Install dependencies
pip install -r requirements.txt

# Run the application
python main.py
```

## Deployment
The application is configured for deployment on Railway:
1. Connect your GitHub repository to Railway
2. Set the required environment variables
3. Deploy the main branch

The application will automatically use the Procfile for deployment configuration.
