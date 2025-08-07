from crewai import Task, Crew
from .agent_configs import create_agents
import os

def run_research_crew(query):
    """
    Run the complete research pipeline using CrewAI
    
    Args:
        query (str): The research query to investigate
        
    Returns:
        dict: The formatted research results
    """
    
    # Create the agents
    researcher, summarizer, formatter = create_agents()
    
    # Define the research task
    research_task = Task(
        description=f"""
        Conduct comprehensive research on the following topic: {query}
        
        Your research should include:
        1. Current state of the topic
        2. Recent developments and trends
        3. Key players and technologies involved
        4. Future outlook and predictions
        5. Relevant statistics and data
        
        Provide detailed, well-sourced information that covers multiple aspects of the topic.
        """,
        agent=researcher,
        expected_output="A comprehensive research report with detailed findings on the topic"
    )
    
    # Define the summarization task
    summarize_task = Task(
        description="""
        Take the research findings and create a clear, concise summary that:
        1. Highlights the most important points
        2. Organizes information logically
        3. Maintains accuracy while being accessible
        4. Includes key insights and takeaways
        
        Focus on making the information easy to understand while preserving the depth of the research.
        """,
        agent=summarizer,
        expected_output="A well-structured summary of the research findings",
        context=[research_task]
    )
    
    # Define the formatting task
    format_task = Task(
        description="""
        Format the summarized research into a professional report that includes:
        1. Executive summary
        2. Key findings and insights
        3. Detailed analysis
        4. Recommendations or conclusions
        5. Sources and references
        
        Structure the report for maximum clarity and professional presentation.
        """,
        agent=formatter,
        expected_output="A professionally formatted research report",
        context=[summarize_task]
    )
    
    # Create the crew
    crew = Crew(
        agents=[researcher, summarizer, formatter],
        tasks=[research_task, summarize_task, format_task],
        verbose=True
    )
    
    # Execute the crew
    try:
        result = crew.kickoff()
        return {
            "status": "success",
            "query": query,
            "result": result,
            "pipeline": "search -> summarize -> format"
        }
    except Exception as e:
        return {
            "status": "error",
            "query": query,
            "error": str(e),
            "pipeline": "search -> summarize -> format"
        } 