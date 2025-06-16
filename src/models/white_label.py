from src.main import db # Assuming db is initialized in main.py
from datetime import datetime

class WhiteLabelConfig(db.Model):
    __tablename__ = 'white_label_configs'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), unique=True, nullable=False)
    custom_domain = db.Column(db.String(255), unique=True, nullable=False)
    domain_verified = db.Column(db.Boolean, default=False)
    logo_url = db.Column(db.String(500))
    favicon_url = db.Column(db.String(500))
    primary_color = db.Column(db.String(7)) # Hex color code, e.g., #RRGGBB
    secondary_color = db.Column(db.String(7))
    contact_email = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('white_label_config', uselist=False))

    def __repr__(self):
        return f'<WhiteLabelConfig {self.custom_domain}>'
