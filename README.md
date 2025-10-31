# Research Assistant AI - Monetized Platform

A monetized, multi-agent research assistant platform using Flask (web API), Celery (async tasks), CrewAI (agent coordination), and LangChain (LLM-based research/summarization). Features user authentication, subscription tiers, rate limiting, and payment integration.

## Features

### Core Functionality
- Flask web API for submitting research jobs
- Celery for background task management
- CrewAI for multi-agent orchestration
- LangChain for LLM-based research and summarization
- Redis as broker and result backend

### Monetization Features
- **User Authentication**: JWT-based authentication and API key management
- **Subscription Tiers**: Free, Basic, Premium, and Enterprise plans
- **Rate Limiting**: Tier-based daily and monthly request limits
- **Usage Tracking**: Detailed usage statistics, token tracking, and cost calculation
- **Payment Integration**: Stripe integration for subscription management
- **Billing History**: Complete billing and payment history tracking
- **API Keys**: Secure API key generation for programmatic access

## Subscription Tiers

| Tier | Price/Month | Daily Limit | Monthly Limit |
|------|-------------|-------------|---------------|
| Free | $0 | 10 requests | 50 requests |
| Basic | $19.99 | 100 requests | 1,000 requests |
| Premium | $49.99 | 500 requests | 10,000 requests |
| Enterprise | $199.99 | Unlimited | Unlimited |

## Folder Structure
```
flask_app/
  ├── __init__.py          # Flask app initialization
  ├── routes.py            # Main API routes
  ├── auth_routes.py       # Authentication endpoints
  ├── billing_routes.py    # Billing and subscription endpoints
  ├── models.py            # Database models
  ├── auth.py              # Authentication utilities
  └── rate_limiter.py      # Rate limiting logic
celery_worker/
  ├── tasks.py             # Celery tasks
  └── agents/              # Agent implementations
crewai_flows/
  ├── crew_runner.py       # CrewAI orchestration
  └── agent_configs.py     # Agent configurations
shared/
  └── langchain_setup.py   # LangChain setup
Dockerfile.web
Dockerfile.worker
docker-compose.yml
requirements.txt
README.md
API_DOCUMENTATION.md
```

## Quickstart

### 1. Environment Setup

Create a `.env` file with the following variables:

```bash
# Flask Configuration
SECRET_KEY=your-secret-key-here
JWT_SECRET_KEY=your-jwt-secret-key-here

# Database
DATABASE_URL=sqlite:///research_tool.db
# Or for PostgreSQL: postgresql://user:password@localhost/research_tool

# Redis
REDIS_URL=redis://localhost:6379/1
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# OpenAI
OPENAI_API_KEY=your-openai-api-key

# Stripe (optional, for payment processing)
STRIPE_SECRET_KEY=sk_test_...
STRIPE_WEBHOOK_SECRET=whsec_...
STRIPE_PRICE_ID_FREE=price_...
STRIPE_PRICE_ID_BASIC=price_...
STRIPE_PRICE_ID_PREMIUM=price_...
STRIPE_PRICE_ID_ENTERPRISE=price_...
```

### 2. Build and Start Services

```bash
docker-compose up --build
```

### 3. Initialize Database

The database tables are automatically created on first run. For SQLite, this happens automatically. For PostgreSQL, ensure the database exists.

### 4. Access the API

- API Base URL: `http://localhost:5001`
- Health Check: `http://localhost:5001/health`

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API documentation.

### Example: Register and Use the API

```bash
# Register a new user
curl -X POST http://localhost:5001/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123","full_name":"John Doe"}'

# Login
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password123"}'

# Submit a research job (use token from login)
curl -X POST http://localhost:5001/api/submit \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query":"Latest developments in AI"}'
```

## API Endpoints

### Authentication
- `POST /api/auth/register` - Register new user
- `POST /api/auth/login` - Login and get JWT token
- `GET /api/auth/me` - Get current user info
- `POST /api/auth/api-keys` - Create API key
- `GET /api/auth/api-keys` - List API keys
- `DELETE /api/auth/api-keys/<id>` - Delete API key

### Research Operations
- `POST /api/submit` - Submit research job
- `GET /api/status/<job_id>` - Check job status
- `GET /api/result/<job_id>` - Get job result
- `GET /api/usage` - Get usage statistics

### Billing
- `GET /api/billing/subscription` - Get subscription info
- `POST /api/billing/subscription/upgrade` - Upgrade subscription
- `GET /api/billing/history` - Get billing history
- `POST /api/billing/webhook/stripe` - Stripe webhook handler

## Development

### Local Development (without Docker)

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment variables
export FLASK_APP=flask_app
export FLASK_ENV=development

# Run Flask
flask run

# Run Celery worker (in separate terminal)
celery -A celery_worker.tasks.celery_app worker --loglevel=info
```

## Database Schema

- **Users**: User accounts with subscription tiers
- **APIKeys**: API keys for programmatic access
- **UsageRecords**: Track all research job executions
- **BillingHistory**: Payment and billing records

## Security Considerations

- All passwords are hashed (SHA-256 for demo; use bcrypt in production)
- API keys are hashed before storage
- JWT tokens expire after 24 hours
- Rate limiting prevents abuse
- User-scoped data access (users can only access their own jobs)

## Production Deployment

1. Use PostgreSQL instead of SQLite
2. Use strong, unique SECRET_KEY and JWT_SECRET_KEY
3. Enable HTTPS
4. Configure proper Stripe webhook endpoints
5. Set up database backups
6. Use environment-specific configuration
7. Enable Redis persistence
8. Set up monitoring and logging

## License
MIT
