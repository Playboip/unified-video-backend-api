from flask import Flask, jsonify, request, Blueprint
from flask_sqlalchemy import SQLAlchemy
from flask_jwt_extended import JWTManager, create_access_token, jwt_required, get_jwt_identity
from datetime import datetime, timedelta
import os
import sys
import json

# Ensure proper path for imports
sys.path.insert(0, os.path.dirname(__file__))
# Initialize Flask app
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev_secret_key_change_in_production')
app.config['JWT_SECRET_KEY'] = os.getenv('JWT_SECRET_KEY', 'jwt_dev_secret_key_change_in_production')
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=1)

# Database configuration
app.config['SQLALCHEMY_DATABASE_URI'] = f"mysql+pymysql://{os.getenv('DB_USERNAME', 'root')}:{os.getenv('DB_PASSWORD', 'password')}@{os.getenv('DB_HOST', 'localhost')}:{os.getenv('DB_PORT', '3306')}/{os.getenv('DB_NAME', 'mydb')}"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Initialize extensions
db = SQLAlchemy(app)
jwt = JWTManager(app)

# Import models after db initialization to avoid circular imports
from src.models.user import User
from src.models.project import Project
from src.models.asset import Asset
from src.models.subscription import SubscriptionPlan, Transaction
from src.models.white_label import WhiteLabelConfig

# Import routes
from src.routes.auth import auth_bp
from src.routes.projects import projects_bp
from src.routes.assets import assets_bp
from src.routes.subscriptions import subscriptions_bp
from src.routes.white_label import white_label_bp
from src.routes.video_editor import editor_bp

# Register blueprints
app.register_blueprint(auth_bp, url_prefix='/api/auth')
app.register_blueprint(projects_bp, url_prefix='/api/projects')
app.register_blueprint(assets_bp, url_prefix='/api/assets')
app.register_blueprint(subscriptions_bp, url_prefix='/api/subscriptions')
app.register_blueprint(white_label_bp, url_prefix='/api/white-label')
app.register_blueprint(editor_bp, url_prefix='/api/editor')

# Error handlers
@app.errorhandler(404)
def not_found(error):
    return jsonify({'error': 'Not found'}), 404

@app.errorhandler(500)
def server_error(error):
    return jsonify({'error': 'Server error'}), 500

# Root route
@app.route('/')
def index():
    return jsonify({
        'name': 'Vibe Video Editor API',
        'version': '1.0.0',
        'status': 'running'
    })

# White label domain handling middleware
@app.before_request
def handle_white_label_domain():
    host = request.headers.get('Host', '')
    if host and host != 'localhost' and not host.startswith('127.0.0.1'):
        # Check if this is a white-labeled domain
        white_label = WhiteLabelConfig.query.filter_by(custom_domain=host, domain_verified=True).first()
        if white_label:
            # Store white label info in request context for later use
            request.white_label_user_id = white_label.user_id
            request.white_label_config = white_label
        else:
            request.white_label_user_id = None
            request.white_label_config = None

# Initialize database
@app.before_first_request
def initialize_database():
    db.create_all()
    
    # Create default subscription plans if they don't exist
    if SubscriptionPlan.query.count() == 0:
        plans = [
            {
                'name': 'free',
                'display_name': 'Free',
                'price_monthly': 0,
                'price_yearly': 0,
                'features': json.dumps([
                    '5 projects',
                    '720p max resolution',
                    '5 minutes max video length',
                    'Basic effects only',
                    'Watermarked exports'
                ]),
                'max_projects': 5,
                'max_storage_gb': 1.0,
                'max_video_length': 5,
                'max_resolution': '720p',
                'allows_white_labeling': False
            },
            {
                'name': 'basic',
                'display_name': 'Basic',
                'price_monthly': 9.99,
                'price_yearly': 99.99,
                'features': json.dumps([
                    'Unlimited projects',
                    '1080p resolution',
                    '15 minutes max video length',
                    'All standard effects',
                    'No watermark'
                ]),
                'max_projects': -1,  # Unlimited
                'max_storage_gb': 10.0,
                'max_video_length': 15,
                'max_resolution': '1080p',
                'allows_white_labeling': False
            },
            {
                'name': 'pro',
                'display_name': 'Pro',
                'price_monthly': 19.99,
                'price_yearly': 199.99,
                'features': json.dumps([
                    'Unlimited projects',
                    '4K resolution',
                    'Unlimited video length',
                    'All premium effects',
                    'AI-powered editing',
                    'Priority support'
                ]),
                'max_projects': -1,  # Unlimited
                'max_storage_gb': 50.0,
                'max_video_length': -1,  # Unlimited
                'max_resolution': '4k',
                'allows_white_labeling': False
            },
            {
                'name': 'enterprise',
                'display_name': 'Enterprise',
                'price_monthly': 49.99,
                'price_yearly': 499.99,
                'features': json.dumps([
                    'Unlimited projects',
                    '8K resolution',
                    'Unlimited video length',
                    'All premium effects',
                    'AI-powered editing',
                    'Team collaboration',
                    'White labeling',
                    'Dedicated support'
                ]),
                'max_projects': -1,  # Unlimited
                'max_storage_gb': 200.0,
                'max_video_length': -1,  # Unlimited
                'max_resolution': '8k',
                'allows_white_labeling': True
            }
        ]
        
        for plan_data in plans:
            plan = SubscriptionPlan(**plan_data)
            db.session.add(plan)
        
        db.session.commit()

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)
