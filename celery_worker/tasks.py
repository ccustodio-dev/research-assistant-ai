from celery import Celery
from crewai_flows.crew_runner import run_research_crew
import os

celery_app = Celery('tasks')

@celery_app.task
def run_research_pipeline(job_data):
    """
    Run the complete research pipeline using CrewAI
    
    Args:
        job_data (dict): Contains the research query and any additional parameters
        
    Returns:
        dict: The research results from the CrewAI pipeline
    """
    try:
        # Extract the query from job data
        query = job_data.get('query', '')
        if not query:
            return {
                'status': 'error',
                'error': 'No query provided in job data'
            }
        
        # Run the CrewAI research pipeline
        result = run_research_crew(query)
        
        return result
        
    except Exception as e:
        return {
            'status': 'error',
            'error': f'Pipeline execution failed: {str(e)}',
            'query': job_data.get('query', '')
        } 