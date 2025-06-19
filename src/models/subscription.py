from src.database import db
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON
from sqlalchemy import Decimal

class SubscriptionPlan(db.Model):
    __tablename__ = 'subscription_plans'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    display_name = db.Column(db.String(100), nullable=False)
    price_monthly = db.Column(Decimal(10, 2), nullable=False)
    price_yearly = db.Column(Decimal(10, 2), nullable=False)
    features = db.Column(JSON)
    max_projects = db.Column(db.Integer, default=-1)  # -1 for unlimited
    max_storage_gb = db.Column(db.Float, default=1.0)
    max_video_length = db.Column(db.Integer, default=5)  # minutes, -1 for unlimited
    max_resolution = db.Column(db.String(10), default='720p')
    allows_white_labeling = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    def __repr__(self):
        return f'<SubscriptionPlan {self.display_name}>'

class Transaction(db.Model):
    __tablename__ = 'transactions'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    subscription_plan_id = db.Column(db.Integer, db.ForeignKey('subscription_plans.id'), nullable=False)
    amount = db.Column(Decimal(10, 2), nullable=False)
    transaction_id = db.Column(db.String(255), unique=True, nullable=False)
    status = db.Column(db.Enum('pending', 'completed', 'failed', 'refunded'), default='pending')
    transaction_date = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('transactions', lazy=True))
    subscription_plan = db.relationship('SubscriptionPlan', backref=db.backref('transactions', lazy=True))

    def __repr__(self):
        return f'<Transaction {self.transaction_id}>'
