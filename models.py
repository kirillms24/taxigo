from app import db
from datetime import datetime

class Message(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    sender = db.Column(db.String(20), nullable=False)  # 'user', 'bot', 'operator'
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    handled_by_operator = db.Column(db.Boolean, default=False)
