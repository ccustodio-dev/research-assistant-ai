from flask import Blueprint, request, jsonify
from celery_worker.tasks import run_research_pipeline

bp = Blueprint('api', __name__)

def init_app(app):
    app.register_blueprint(bp, url_prefix='/api')

@bp.route('/submit', methods=['POST'])
def submit():
    # Get the research request data from the request
    data = request.get_json()
    
    if not data or 'query' not in data:
        return jsonify({'error': 'Missing required field: query'}), 400
    
    # Submit the research job to Celery
    job = run_research_pipeline.delay(data)
    
    return jsonify({
        'job_id': job.id,
        'status': 'submitted',
        'message': 'Research job submitted successfully'
    })

@bp.route('/status/<job_id>', methods=['GET'])
def status(job_id):
    # Get the Celery task result
    task_result = run_research_pipeline.AsyncResult(job_id)
    
    response = {
        'job_id': job_id,
        'status': task_result.status
    }
    
    # Add additional info based on status
    if task_result.status == 'SUCCESS':
        response['result'] = task_result.result
    elif task_result.status == 'FAILURE':
        response['error'] = str(task_result.info)
    
    return jsonify(response)

@bp.route('/result/<job_id>', methods=['GET'])
def result(job_id):
    # Get the Celery task result
    task_result = run_research_pipeline.AsyncResult(job_id)
    
    if task_result.ready():
        if task_result.successful():
            return jsonify({
                'job_id': job_id,
                'status': 'completed',
                'result': task_result.result
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