# 🧠 Research Squad

Your personal multi-agent research assistant — powered by LangChain, CrewAI, Flask, Celery, and Docker.

This project automatically spins up a team of AI agents to research topics, summarize findings, and return a formatted report — all asynchronously and containerized for easy deployment.

---

## 🚀 Features

- 🌐 **Flask API** for submitting research requests
- ⏱️ **Celery** queue for async processing
- 🧑‍💼 **CrewAI**-managed team of agents:
  - `Searcher`: Gathers relevant online sources
  - `Summarizer`: Extracts and condenses key points
  - `Formatter`: Compiles a clean, readable report
- 🪄 **LangChain** for LLM integration and task chains
- 🐳 Fully **Dockerized** and ready to deploy

---

## 📦 Tech Stack

| Component | Role |
|----------|------|
| **Flask** | Web API and result endpoints |
| **Celery** | Background task queue |
| **Redis** | Message broker + result backend |
| **CrewAI** | Agent orchestration |
| **LangChain** | LLM chains for research and summarization |
| **Docker** | Deployment and isolation |

---

## 🛠️ Setup

### 1. Clone the repo
```bash
git clone https://github.com/yourusername/research-squad.git
cd research-squad
