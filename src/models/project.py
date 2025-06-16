from src.main import db # Assuming db is initialized in main.py
from datetime import datetime
from sqlalchemy.dialects.mysql import JSON

class Project(db.Model):
    __tablename__ = 'projects'

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    project_name = db.Column(db.String(255), nullable=False)
    project_type = db.Column(db.Enum('magic_clipper', 'ai_remix', 'vibe_editor', 'ppt_converter', 'motion_graphics'), nullable=False)
    project_data = db.Column(JSON)
    storage_provider = db.Column(db.Enum('firebase', 'cloudinary', 'backblaze'))
    file_path = db.Column(db.String(500))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    user = db.relationship('User', backref=db.backref('projects', lazy=True))

    def __repr__(self):
        return f'<Project {self.project_name}>'
