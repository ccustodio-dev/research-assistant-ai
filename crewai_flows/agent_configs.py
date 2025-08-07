from crewai import Agent, Task, Crew
from langchain_openai import ChatOpenAI
import os

def create_agents():
    """Create the research agents with specific roles"""
    
    # Initialize the LLM - Using GPT-3.5-turbo for free tier compatibility
    llm = ChatOpenAI(
        model="gpt-3.5-turbo",
        temperature=0.1,
        api_key=os.getenv("OPENAI_API_KEY")
    )
    
    # Research Agent - Searches for information
    researcher = Agent(
        role='Research Analyst',
        goal='Find comprehensive and accurate information on the given topic',
        backstory="""You are an expert research analyst with years of experience in gathering 
        and analyzing information from various sources. You have a keen eye for detail and 
        always ensure the information you find is relevant and up-to-date.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # Summarizer Agent - Creates concise summaries
    summarizer = Agent(
        role='Content Summarizer',
        goal='Create clear, concise, and well-structured summaries of research findings',
        backstory="""You are a skilled content summarizer who excels at distilling complex 
        information into clear, actionable insights. You have a talent for organizing 
        information logically and highlighting the most important points.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    # Formatter Agent - Formats the final output
    formatter = Agent(
        role='Content Formatter',
        goal='Format research findings into a professional, well-structured report',
        backstory="""You are a professional content formatter who specializes in creating 
        polished, well-organized reports. You have expertise in structuring information 
        for maximum clarity and impact.""",
        verbose=True,
        allow_delegation=False,
        llm=llm
    )
    
    return researcher, summarizer, formatter 