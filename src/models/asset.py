from src.main import db # Assuming db is initialized in main.py
from datetime import datetime

class Asset(db.Model):
    __tablename__ = 'assets'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_id = db.Column(db.Integer, db.ForeignKey('projects.id'), nullable=True) # Assets can be shared or project-specific
    asset_name = db.Column(db.String(255), nullable=False)
    asset_type = db.Column(db.String(50)) # e.g., 'video', 'image', 'audio'
    storage_provider = db.Column(db.Enum('firebase', 'cloudinary', 'backblaze'), nullable=False)
    file_path = db.Column(db.String(500), nullable=False)
    # Renamed 'metadata' to 'asset_metadata' to avoid conflict
    asset_metadata = db.Column(db.JSON) # For storing additional asset-specific metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('assets', lazy=True))
    project = db.relationship('Project', backref=db.backref('assets', lazy=True))

    def __repr__(self):
        return f'<Asset {self.asset_name}>'
