from celery import Celery
from crewai_flows.crew_runner import run_research_crew
import os
from flask import Flask
from flask_app.models import db, UsageRecord

celery_app = Celery('tasks')

def create_flask_app():
    """Create Flask app context for database operations"""
    from flask_app import app
    return app

@celery_app.task
def run_research_pipeline(job_data):
    """
    Run the complete research pipeline using CrewAI
    
    Args:
        job_data (dict): Contains the research query and any additional parameters
        
    Returns:
        dict: The research results from the CrewAI pipeline
    """
    app = create_flask_app()
    
    with app.app_context():
        usage_record_id = job_data.get('usage_record_id')
        usage_record = None
        
        if usage_record_id:
            try:
                usage_record = UsageRecord.query.get(usage_record_id)
            except:
                pass
        
        try:
            # Extract the query from job data
            query = job_data.get('query', '')
            if not query:
                error_result = {
                    'status': 'error',
                    'error': 'No query provided in job data'
                }
                if usage_record:
                    usage_record.status = 'failed'
                    db.session.commit()
                return error_result
            
            # Run the CrewAI research pipeline
            result = run_research_crew(query)
            
            # Track usage (estimate tokens and cost)
            if usage_record:
                # Estimate tokens (rough calculation: ~4 chars per token)
                estimated_tokens = len(str(result).replace('\n', ' ')) // 4
                # Estimate cost using GPT-3.5-turbo pricing: $0.002 per 1K tokens
                estimated_cost = (estimated_tokens / 1000) * 0.002
                
                usage_record.tokens_used = estimated_tokens
                usage_record.cost_usd = estimated_cost
                
                if result.get('status') == 'success':
                    usage_record.status = 'completed'
                else:
                    usage_record.status = 'failed'
                
                db.session.commit()
            
            return result
            
        except Exception as e:
            error_result = {
                'status': 'error',
                'error': f'Pipeline execution failed: {str(e)}',
                'query': job_data.get('query', '')
            }
            
            if usage_record:
                usage_record.status = 'failed'
                db.session.commit()
            
            return error_result 