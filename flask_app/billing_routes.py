"""
Billing and subscription management routes
"""
from flask import Blueprint, request, jsonify
from .models import db, User, BillingHistory, SubscriptionTier
from .auth import require_auth
import os

bp = Blueprint('billing', __name__)

# Subscription tier pricing (in USD per month)
TIER_PRICING = {
    SubscriptionTier.FREE: 0,
    SubscriptionTier.BASIC: 19.99,
    SubscriptionTier.PREMIUM: 49.99,
    SubscriptionTier.ENTERPRISE: 199.99
}

# Stripe integration
STRIPE_ENABLED = False
stripe = None
try:
    import stripe as stripe_module
    stripe = stripe_module
    stripe.api_key = os.environ.get('STRIPE_SECRET_KEY')
    STRIPE_ENABLED = bool(stripe.api_key)
except ImportError:
    # Stripe not installed - payment features will be disabled
    STRIPE_ENABLED = False
except Exception:
    STRIPE_ENABLED = False


@bp.route('/subscription', methods=['GET'])
@require_auth
def get_subscription():
    """Get current subscription information"""
    user = request.current_user
    
    return jsonify({
        'subscription': {
            'tier': user.subscription_tier.value,
            'limits': user.get_rate_limit(),
            'pricing': {
                'current_tier': TIER_PRICING[user.subscription_tier],
                'all_tiers': {tier.value: price for tier, price in TIER_PRICING.items()}
            },
            'stripe_customer_id': user.stripe_customer_id,
            'stripe_subscription_id': user.stripe_subscription_id
        }
    })


@bp.route('/subscription/upgrade', methods=['POST'])
@require_auth
def upgrade_subscription():
    """Upgrade subscription tier"""
    user = request.current_user
    data = request.get_json()
    
    target_tier = data.get('tier')
    if not target_tier:
        return jsonify({'error': 'Tier is required'}), 400
    
    try:
        target_tier_enum = SubscriptionTier(target_tier)
    except ValueError:
        return jsonify({'error': 'Invalid tier'}), 400
    
    # Check if upgrade is valid
    tier_order = [SubscriptionTier.FREE, SubscriptionTier.BASIC, SubscriptionTier.PREMIUM, SubscriptionTier.ENTERPRISE]
    current_index = tier_order.index(user.subscription_tier)
    target_index = tier_order.index(target_tier_enum)
    
    if target_index <= current_index:
        return jsonify({'error': 'This is not an upgrade'}), 400
    
    if STRIPE_ENABLED and stripe and target_tier_enum != SubscriptionTier.FREE:
        # Handle Stripe payment
        try:
            if not user.stripe_customer_id:
                # Create customer
                customer = stripe.Customer.create(
                    email=user.email,
                    metadata={'user_id': user.id}
                )
                user.stripe_customer_id = customer.id
            
            # Create or update subscription
            price_id = os.environ.get(f'STRIPE_PRICE_ID_{target_tier_enum.value.upper()}')
            if not price_id:
                return jsonify({'error': 'Payment processing not configured for this tier'}), 500
            
            if user.stripe_subscription_id:
                # Update existing subscription
                subscription = stripe.Subscription.retrieve(user.stripe_subscription_id)
                stripe.Subscription.modify(
                    user.stripe_subscription_id,
                    items=[{
                        'id': subscription['items']['data'][0].id,
                        'price': price_id,
                    }]
                )
            else:
                # Create new subscription
                subscription = stripe.Subscription.create(
                    customer=user.stripe_customer_id,
                    items=[{'price': price_id}],
                    metadata={'user_id': user.id, 'tier': target_tier}
                )
                user.stripe_subscription_id = subscription.id
            
            db.session.commit()
            
            return jsonify({
                'message': 'Subscription upgraded successfully',
                'subscription': {
                    'tier': target_tier,
                    'stripe_subscription_id': user.stripe_subscription_id
                }
            })
        except Exception as e:
            return jsonify({'error': f'Payment processing failed: {str(e)}'}), 500
    else:
        # For free tier or when Stripe is not enabled, just update tier
        user.subscription_tier = target_tier_enum
        db.session.commit()
        
        return jsonify({
            'message': 'Subscription tier updated',
            'subscription': {
                'tier': target_tier
            }
        })


@bp.route('/billing/history', methods=['GET'])
@require_auth
def get_billing_history():
    """Get billing history for current user"""
    user = request.current_user
    history = BillingHistory.query.filter_by(user_id=user.id).order_by(BillingHistory.created_at.desc()).limit(50).all()
    
    return jsonify({
        'billing_history': [{
            'id': record.id,
            'amount': float(record.amount),
            'currency': record.currency,
            'status': record.status,
            'created_at': record.created_at.isoformat(),
            'invoice_id': record.stripe_invoice_id
        } for record in history]
    })


@bp.route('/webhook/stripe', methods=['POST'])
def stripe_webhook():
    """Handle Stripe webhooks for subscription events"""
    if not STRIPE_ENABLED:
        return jsonify({'error': 'Stripe not configured'}), 500
    
    payload = request.data
    sig_header = request.headers.get('Stripe-Signature')
    webhook_secret = os.environ.get('STRIPE_WEBHOOK_SECRET')
    
    try:
        event = stripe.Webhook.construct_event(
            payload, sig_header, webhook_secret
        )
    except ValueError:
        return jsonify({'error': 'Invalid payload'}), 400
    except stripe.error.SignatureVerificationError:
        return jsonify({'error': 'Invalid signature'}), 400
    
    # Handle different event types
    if event['type'] == 'invoice.payment_succeeded':
        invoice = event['data']['object']
        customer_id = invoice['customer']
        
        user = User.query.filter_by(stripe_customer_id=customer_id).first()
        if user:
            billing_record = BillingHistory(
                user_id=user.id,
                stripe_invoice_id=invoice['id'],
                amount=invoice['amount_paid'] / 100,  # Convert from cents
                currency=invoice['currency'],
                status='paid'
            )
            db.session.add(billing_record)
            db.session.commit()
    
    elif event['type'] == 'customer.subscription.deleted':
        subscription = event['data']['object']
        user = User.query.filter_by(stripe_subscription_id=subscription['id']).first()
        if user:
            user.subscription_tier = SubscriptionTier.FREE
            db.session.commit()
    
    return jsonify({'status': 'success'})
