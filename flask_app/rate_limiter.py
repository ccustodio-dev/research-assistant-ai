"""
Rate limiting based on subscription tiers
"""
from functools import wraps
from flask import request, jsonify, g
from datetime import datetime, timedelta
from .models import db, UsageRecord
import redis


def get_redis_client():
    """Get Redis client for rate limiting"""
    try:
        import os
        redis_url = os.environ.get('REDIS_URL', 'redis://localhost:6379/1')
        return redis.from_url(redis_url, decode_responses=True)
    except:
        return None


def check_rate_limit(user):
    """Check if user has exceeded rate limits"""
    redis_client = get_redis_client()
    if not redis_client:
        # If Redis is not available, allow the request (fallback mode)
        # In production, you might want to log this and handle differently
        return True, None
    
    limits = user.get_rate_limit()
    user_id = str(user.id)
    
    # Check daily limit
    if limits['daily'] > 0:
        daily_key = f"rate_limit:daily:{user_id}:{datetime.utcnow().strftime('%Y-%m-%d')}"
        daily_count = redis_client.get(daily_key)
        if daily_count and int(daily_count) >= limits['daily']:
            reset_time = (datetime.utcnow() + timedelta(days=1)).replace(hour=0, minute=0, second=0)
            return False, {
                'limit_type': 'daily',
                'limit': limits['daily'],
                'reset_at': reset_time.isoformat()
            }
    
    # Check monthly limit
    if limits['monthly'] > 0:
        monthly_key = f"rate_limit:monthly:{user_id}:{datetime.utcnow().strftime('%Y-%m')}"
        monthly_count = redis_client.get(monthly_key)
        if monthly_count and int(monthly_count) >= limits['monthly']:
            next_month = (datetime.utcnow().replace(day=1) + timedelta(days=32)).replace(day=1)
            return False, {
                'limit_type': 'monthly',
                'limit': limits['monthly'],
                'reset_at': next_month.isoformat()
            }
    
    return True, None


def increment_rate_limit(user):
    """Increment rate limit counters"""
    redis_client = get_redis_client()
    if not redis_client:
        return
    
    user_id = str(user.id)
    now = datetime.utcnow()
    
    # Increment daily counter
    daily_key = f"rate_limit:daily:{user_id}:{now.strftime('%Y-%m-%d')}"
    redis_client.incr(daily_key)
    redis_client.expire(daily_key, 86400)  # 24 hours
    
    # Increment monthly counter
    monthly_key = f"rate_limit:monthly:{user_id}:{now.strftime('%Y-%m')}"
    redis_client.incr(monthly_key)
    redis_client.expire(monthly_key, 2592000)  # 30 days


def require_rate_limit(f):
    """Decorator to enforce rate limiting"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import request
        from .auth import get_user_from_request
        
        user = getattr(request, 'current_user', None)
        if not user:
            user = get_user_from_request()
            if not user:
                return jsonify({'error': 'Authentication required'}), 401
        
        allowed, error_info = check_rate_limit(user)
        if not allowed:
            return jsonify({
                'error': 'Rate limit exceeded',
                **error_info
            }), 429
        
        # Increment counter (will be called even if request fails later, but that's acceptable)
        increment_rate_limit(user)
        
        return f(*args, **kwargs)
    
    return decorated_function


