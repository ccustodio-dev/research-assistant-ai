from flask_sqlalchemy import SQLAlchemy
from datetime import datetime, timedelta
import secrets
import hashlib
from enum import Enum

db = SQLAlchemy()


class SubscriptionTier(Enum):
    FREE = "free"
    BASIC = "basic"
    PREMIUM = "premium"
    ENTERPRISE = "enterprise"


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True, nullable=False, index=True)
    password_hash = db.Column(db.String(255), nullable=False)
    full_name = db.Column(db.String(255))
    subscription_tier = db.Column(db.Enum(SubscriptionTier), default=SubscriptionTier.FREE, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True)
    stripe_customer_id = db.Column(db.String(255), unique=True, nullable=True)
    stripe_subscription_id = db.Column(db.String(255), unique=True, nullable=True)
    
    # Relationships
    api_keys = db.relationship('APIKey', backref='user', lazy=True, cascade='all, delete-orphan')
    usage_records = db.relationship('UsageRecord', backref='user', lazy=True)
    
    def __repr__(self):
        return f'<User {self.email}>'
    
    def get_rate_limit(self):
        """Get rate limits based on subscription tier"""
        limits = {
            SubscriptionTier.FREE: {'daily': 10, 'monthly': 50},
            SubscriptionTier.BASIC: {'daily': 100, 'monthly': 1000},
            SubscriptionTier.PREMIUM: {'daily': 500, 'monthly': 10000},
            SubscriptionTier.ENTERPRISE: {'daily': -1, 'monthly': -1}  # -1 means unlimited
        }
        return limits.get(self.subscription_tier, limits[SubscriptionTier.FREE])


class APIKey(db.Model):
    __tablename__ = 'api_keys'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    key_hash = db.Column(db.String(255), unique=True, nullable=False, index=True)
    key_prefix = db.Column(db.String(16), nullable=False)  # First 8 chars for display
    name = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    last_used_at = db.Column(db.DateTime, nullable=True)
    is_active = db.Column(db.Boolean, default=True)
    
    @staticmethod
    def generate_key():
        """Generate a new API key"""
        key = f"rsk_{secrets.token_urlsafe(32)}"
        return key
    
    @staticmethod
    def hash_key(key):
        """Hash the API key for storage"""
        return hashlib.sha256(key.encode()).hexdigest()
    
    def verify_key(self, key):
        """Verify if the provided key matches"""
        return self.key_hash == self.hash_key(key)
    
    def __repr__(self):
        return f'<APIKey {self.key_prefix}...>'


class UsageRecord(db.Model):
    __tablename__ = 'usage_records'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    job_id = db.Column(db.String(255), nullable=False)
    query = db.Column(db.Text)
    tokens_used = db.Column(db.Integer, default=0)
    cost_usd = db.Column(db.Numeric(10, 6), default=0.0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow, index=True)
    completed_at = db.Column(db.DateTime, nullable=True)
    status = db.Column(db.String(50), default='pending')
    
    def __repr__(self):
        return f'<UsageRecord {self.job_id}>'


class BillingHistory(db.Model):
    __tablename__ = 'billing_history'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    stripe_invoice_id = db.Column(db.String(255), unique=True, nullable=True)
    amount = db.Column(db.Numeric(10, 2), nullable=False)
    currency = db.Column(db.String(3), default='usd')
    status = db.Column(db.String(50))  # paid, pending, failed
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<BillingHistory {self.id}>'
