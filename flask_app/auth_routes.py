"""
Authentication and user management routes
"""
from flask import Blueprint, request, jsonify
from flask_jwt_extended import create_access_token
from .models import db, User, APIKey, SubscriptionTier
from .auth import hash_password, verify_password, require_auth, get_user_from_request
from datetime import datetime

bp = Blueprint('auth', __name__)


@bp.route('/register', methods=['POST'])
def register():
    """Register a new user"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    # Check if user already exists
    if User.query.filter_by(email=data['email']).first():
        return jsonify({'error': 'User with this email already exists'}), 409
    
    # Create new user
    user = User(
        email=data['email'],
        password_hash=hash_password(data['password']),
        full_name=data.get('full_name'),
        subscription_tier=SubscriptionTier.FREE
    )
    
    db.session.add(user)
    db.session.commit()
    
    # Create access token
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'User registered successfully',
        'user': {
            'id': user.id,
            'email': user.email,
            'subscription_tier': user.subscription_tier.value
        },
        'access_token': access_token
    }), 201


@bp.route('/login', methods=['POST'])
def login():
    """Login and get access token"""
    data = request.get_json()
    
    if not data or not data.get('email') or not data.get('password'):
        return jsonify({'error': 'Email and password are required'}), 400
    
    user = User.query.filter_by(email=data['email']).first()
    
    if not user or not verify_password(user.password_hash, data['password']):
        return jsonify({'error': 'Invalid email or password'}), 401
    
    if not user.is_active:
        return jsonify({'error': 'Account is inactive'}), 403
    
    access_token = create_access_token(identity=user.id)
    
    return jsonify({
        'message': 'Login successful',
        'user': {
            'id': user.id,
            'email': user.email,
            'subscription_tier': user.subscription_tier.value
        },
        'access_token': access_token
    })


@bp.route('/me', methods=['GET'])
@require_auth
def get_current_user():
    """Get current user information"""
    user = request.current_user
    
    # Get usage stats
    limits = user.get_rate_limit()
    usage_stats = {
        'subscription_tier': user.subscription_tier.value,
        'rate_limits': limits
    }
    
    return jsonify({
        'user': {
            'id': user.id,
            'email': user.email,
            'full_name': user.full_name,
            'subscription_tier': user.subscription_tier.value,
            'created_at': user.created_at.isoformat()
        },
        'usage_stats': usage_stats
    })


@bp.route('/api-keys', methods=['GET'])
@require_auth
def list_api_keys():
    """List all API keys for the current user"""
    user = request.current_user
    keys = APIKey.query.filter_by(user_id=user.id, is_active=True).all()
    
    return jsonify({
        'api_keys': [{
            'id': key.id,
            'name': key.name,
            'key_prefix': key.key_prefix,
            'created_at': key.created_at.isoformat(),
            'last_used_at': key.last_used_at.isoformat() if key.last_used_at else None
        } for key in keys]
    })


@bp.route('/api-keys', methods=['POST'])
@require_auth
def create_api_key():
    """Create a new API key"""
    data = request.get_json()
    user = request.current_user
    
    key = APIKey.generate_key()
    key_hash = APIKey.hash_key(key)
    
    api_key = APIKey(
        user_id=user.id,
        key_hash=key_hash,
        key_prefix=key[:16],
        name=data.get('name', 'Default API Key')
    )
    
    db.session.add(api_key)
    db.session.commit()
    
    # Return the key only once
    return jsonify({
        'message': 'API key created successfully',
        'api_key': key,
        'key_info': {
            'id': api_key.id,
            'name': api_key.name,
            'key_prefix': api_key.key_prefix,
            'created_at': api_key.created_at.isoformat()
        },
        'warning': 'Store this key securely. It will not be shown again.'
    }), 201


@bp.route('/api-keys/<int:key_id>', methods=['DELETE'])
@require_auth
def delete_api_key(key_id):
    """Delete an API key"""
    user = request.current_user
    api_key = APIKey.query.filter_by(id=key_id, user_id=user.id).first_or_404()
    
    api_key.is_active = False
    db.session.commit()
    
    return jsonify({'message': 'API key deleted successfully'})
