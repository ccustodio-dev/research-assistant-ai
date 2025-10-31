"""
Authentication and authorization utilities
"""
from functools import wraps
from flask import request, jsonify
from flask_jwt_extended import create_access_token, jwt_required, get_jwt_identity, verify_jwt_in_request
import hashlib
from .models import db, User, APIKey, SubscriptionTier
from datetime import datetime, timedelta


def hash_password(password):
    """Hash a password using SHA-256 (for demo - use bcrypt in production)"""
    return hashlib.sha256(password.encode()).hexdigest()


def verify_password(password_hash, password):
    """Verify a password against its hash"""
    return password_hash == hash_password(password)


def get_user_from_request():
    """Extract user from request - either JWT or API key"""
    # Try JWT token first
    try:
        verify_jwt_in_request(optional=True)
        user_id = get_jwt_identity()
        if user_id:
            return User.query.get(user_id)
    except:
        pass
    
    # Try API key
    api_key = request.headers.get('X-API-Key') or request.headers.get('Authorization', '').replace('Bearer ', '')
    if api_key and api_key.startswith('rsk_'):
        key_hash = APIKey.hash_key(api_key)
        api_key_obj = APIKey.query.filter_by(key_hash=key_hash, is_active=True).first()
        if api_key_obj:
            # Update last used timestamp
            api_key_obj.last_used_at = datetime.utcnow()
            db.session.commit()
            return api_key_obj.user
    
    return None


def require_auth(f):
    """Decorator to require authentication"""
    @wraps(f)
    @jwt_required(optional=True)
    def decorated_function(*args, **kwargs):
        user = get_user_from_request()
        
        if not user:
            return jsonify({'error': 'Authentication required'}), 401
        
        if not user.is_active:
            return jsonify({'error': 'Account is inactive'}), 403
        
        # Attach user to request context
        request.current_user = user
        return f(*args, **kwargs)
    
    return decorated_function


def require_tier(*required_tiers):
    """Decorator to require specific subscription tier"""
    def decorator(f):
        @wraps(f)
        @require_auth
        def decorated_function(*args, **kwargs):
            user = request.current_user
            
            if user.subscription_tier not in required_tiers:
                return jsonify({
                    'error': 'Insufficient subscription tier',
                    'required': [t.value for t in required_tiers],
                    'current': user.subscription_tier.value
                }), 403
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator
