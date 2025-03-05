from app import db
from datetime import datetime

class ChatSession(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.String(128), unique=True, nullable=False)
    state = db.Column(db.Integer, default=0)
    context = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    completed = db.Column(db.Boolean, default=False)

    def __repr__(self):
        return f'<ChatSession {self.user_id}>'
