# research-assistant-ai

A multi-agent research assistant using Flask (web API), Celery (async tasks), CrewAI (agent coordination), and LangChain (LLM-based research/summarization). Dockerized for easy deployment.

## Features
- Flask web API for submitting research jobs
- Celery for background task management
- CrewAI for multi-agent orchestration
- LangChain for LLM-based research and summarization
- Redis as broker and result backend

## Folder Structure
```
flask_app/
celery_worker/
crewai_flows/
shared/
Dockerfile.web
Dockerfile.worker
docker-compose.yml
.env
.env.example
README.md
```

## Quickstart
1. Copy `.env.example` to `.env` and fill in your API keys and config.
2. Build and start all services:
   ```sh
   docker-compose up --build
   ```
3. Access the Flask API at `http://localhost:5000/api/submit`, etc.

---

## License
MIT
