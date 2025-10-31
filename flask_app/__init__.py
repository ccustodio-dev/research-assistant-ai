from flask import Flask
from flask_jwt_extended import JWTManager
from flask_cors import CORS
from . import routes
from . import auth_routes
from . import billing_routes
from .models import db
import os
from celery_worker.tasks import celery_app
from datetime import timedelta

app = Flask(__name__)
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY', 'dev-secret-key-change-in-production')

# Database configuration
database_url = os.environ.get('DATABASE_URL', 'sqlite:///research_tool.db')
if database_url.startswith('postgres'):
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# JWT configuration
app.config['JWT_SECRET_KEY'] = os.environ.get('JWT_SECRET_KEY', os.environ.get('SECRET_KEY', 'jwt-secret-change-in-production'))
app.config['JWT_ACCESS_TOKEN_EXPIRES'] = timedelta(hours=24)

# Configure Celery
app.config['CELERY_BROKER_URL'] = os.environ.get('CELERY_BROKER_URL', 'redis://localhost:6379/0')
app.config['CELERY_RESULT_BACKEND'] = os.environ.get('CELERY_RESULT_BACKEND', 'redis://localhost:6379/0')

# Initialize extensions
db.init_app(app)
jwt = JWTManager(app)
CORS(app)  # Enable CORS for API access

# Create database tables
with app.app_context():
    db.create_all()

# Register routes
routes.init_app(app)
app.register_blueprint(auth_routes.bp, url_prefix='/api/auth')
app.register_blueprint(billing_routes.bp, url_prefix='/api/billing')

# Health check endpoint
@app.route('/health', methods=['GET'])
def health():
    return {'status': 'healthy', 'service': 'research-assistant-api'}

__all__ = ["app"] 