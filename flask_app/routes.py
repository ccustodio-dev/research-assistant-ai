from flask import Blueprint, request, jsonify
from celery_worker.tasks import run_research_pipeline
from .auth import require_auth
from .rate_limiter import require_rate_limit
from .models import db, UsageRecord
from datetime import datetime

bp = Blueprint('api', __name__)

def init_app(app):
    app.register_blueprint(bp, url_prefix='/api')

@bp.route('/submit', methods=['POST'])
@require_auth
@require_rate_limit
def submit():
    """Submit a research job - requires authentication and respects rate limits"""
    # Get the research request data from the request
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing required field: query'}), 400
    
    user = request.current_user
    query = data.get('query', '')
    
    # Create usage record
    usage_record = UsageRecord(
        user_id=user.id,
        query=query[:1000],  # Truncate long queries
        status='pending'
    )
    db.session.add(usage_record)
    db.session.commit()
    
    # Submit the research job to Celery
    job_data = {**data, 'user_id': user.id, 'usage_record_id': usage_record.id}
    job = run_research_pipeline.delay(job_data)
    
    # Update usage record with job_id
    usage_record.job_id = job.id
    db.session.commit()
    
    return jsonify({
        'job_id': job.id,
        'status': 'submitted',
        'message': 'Research job submitted successfully',
        'usage_record_id': usage_record.id
    })

@bp.route('/status/<job_id>', methods=['GET'])
@require_auth
def status(job_id):
    """Get status of a research job"""
    user = request.current_user
    
    # Verify the job belongs to the user
    usage_record = UsageRecord.query.filter_by(job_id=job_id, user_id=user.id).first()
    if not usage_record:
        return jsonify({'error': 'Job not found or access denied'}), 404
    
    # Get the Celery task result
    task_result = run_research_pipeline.AsyncResult(job_id)
    
    response = {
        'job_id': job_id,
        'status': task_result.status
    }
    
    # Add additional info based on status
    if task_result.status == 'SUCCESS':
        response['result'] = task_result.result
        # Update usage record
        usage_record.status = 'completed'
        usage_record.completed_at = datetime.utcnow()
        db.session.commit()
    elif task_result.status == 'FAILURE':
        response['error'] = str(task_result.info)
        usage_record.status = 'failed'
        usage_record.completed_at = datetime.utcnow()
        db.session.commit()
    
    return jsonify(response)

@bp.route('/result/<job_id>', methods=['GET'])
@require_auth
def result(job_id):
    """Get result of a completed research job"""
    user = request.current_user
    
    # Verify the job belongs to the user
    usage_record = UsageRecord.query.filter_by(job_id=job_id, user_id=user.id).first()
    if not usage_record:
        return jsonify({'error': 'Job not found or access denied'}), 404
    
    # Get the Celery task result
    task_result = run_research_pipeline.AsyncResult(job_id)
    
    if task_result.ready():
        if task_result.successful():
            return jsonify({
                'job_id': job_id,
                'status': 'completed',
                'result': task_result.result,
                'usage': {
                    'tokens_used': usage_record.tokens_used or 0,
                    'cost_usd': float(usage_record.cost_usd) if usage_record.cost_usd else 0.0
                }
            })
        else:
            return jsonify({
                'job_id': job_id,
                'status': 'failed',
                'error': str(task_result.info)
            }), 500
    else:
        return jsonify({
            'job_id': job_id,
            'status': 'pending',
            'message': 'Job is still processing'
        }), 202

@bp.route('/usage', methods=['GET'])
@require_auth
def usage_stats():
    """Get usage statistics for current user"""
    user = request.current_user
    
    # Get usage records
    records = UsageRecord.query.filter_by(user_id=user.id).order_by(UsageRecord.created_at.desc()).limit(100).all()
    
    # Calculate totals
    total_jobs = UsageRecord.query.filter_by(user_id=user.id).count()
    completed_jobs = UsageRecord.query.filter_by(user_id=user.id, status='completed').count()
    total_tokens = db.session.query(db.func.sum(UsageRecord.tokens_used)).filter_by(user_id=user.id).scalar() or 0
    total_cost = db.session.query(db.func.sum(UsageRecord.cost_usd)).filter_by(user_id=user.id).scalar() or 0.0
    
    return jsonify({
        'usage_summary': {
            'total_jobs': total_jobs,
            'completed_jobs': completed_jobs,
            'pending_jobs': total_jobs - completed_jobs,
            'total_tokens': int(total_tokens),
            'total_cost_usd': float(total_cost) if total_cost else 0.0
        },
        'recent_jobs': [{
            'job_id': record.job_id,
            'query': record.query[:100] if record.query else None,
            'status': record.status,
            'tokens_used': record.tokens_used or 0,
            'created_at': record.created_at.isoformat(),
            'completed_at': record.completed_at.isoformat() if record.completed_at else None
        } for record in records[:20]]
    }) 