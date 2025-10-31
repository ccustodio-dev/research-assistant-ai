# Research Tool API Documentation

## Overview

This API provides access to an AI-powered research assistant with multi-agent orchestration. The service is monetized through subscription tiers with different rate limits and features.

## Base URL

```
http://localhost:5000
```

## Authentication

All protected endpoints require authentication via either:

1. **JWT Token** (Bearer token in Authorization header)
2. **API Key** (X-API-Key header or Bearer token starting with `rsk_`)

### Headers

```
Authorization: Bearer <JWT_TOKEN>
# OR
X-API-Key: rsk_<API_KEY>
```

## Subscription Tiers

| Tier | Price/Month | Daily Limit | Monthly Limit |
|------|-------------|-------------|---------------|
| Free | $0 | 10 requests | 50 requests |
| Basic | $19.99 | 100 requests | 1,000 requests |
| Premium | $49.99 | 500 requests | 10,000 requests |
| Enterprise | $199.99 | Unlimited | Unlimited |

## Endpoints

### Authentication

#### Register User
```http
POST /api/auth/register
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword",
  "full_name": "John Doe"
}
```

**Response:**
```json
{
  "message": "User registered successfully",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "subscription_tier": "free"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Login
```http
POST /api/auth/login
Content-Type: application/json

{
  "email": "user@example.com",
  "password": "securepassword"
}
```

**Response:**
```json
{
  "message": "Login successful",
  "user": {
    "id": 1,
    "email": "user@example.com",
    "subscription_tier": "free"
  },
  "access_token": "eyJ0eXAiOiJKV1QiLCJhbGc..."
}
```

#### Get Current User
```http
GET /api/auth/me
Authorization: Bearer <TOKEN>
```

#### Create API Key
```http
POST /api/auth/api-keys
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "name": "My API Key"
}
```

**Response:**
```json
{
  "message": "API key created successfully",
  "api_key": "rsk_xxxxxxxxxxxxx",
  "key_info": {
    "id": 1,
    "name": "My API Key",
    "key_prefix": "rsk_xxxxxxxx",
    "created_at": "2024-01-01T00:00:00"
  },
  "warning": "Store this key securely. It will not be shown again."
}
```

#### List API Keys
```http
GET /api/auth/api-keys
Authorization: Bearer <TOKEN>
```

#### Delete API Key
```http
DELETE /api/auth/api-keys/<key_id>
Authorization: Bearer <TOKEN>
```

### Research Operations

#### Submit Research Job
```http
POST /api/submit
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "query": "Latest developments in quantum computing"
}
```

**Response:**
```json
{
  "job_id": "abc123-def456",
  "status": "submitted",
  "message": "Research job submitted successfully",
  "usage_record_id": 1
}
```

#### Check Job Status
```http
GET /api/status/<job_id>
Authorization: Bearer <TOKEN>
```

**Response:**
```json
{
  "job_id": "abc123-def456",
  "status": "SUCCESS",
  "result": {
    "status": "success",
    "query": "Latest developments in quantum computing",
    "result": "...",
    "pipeline": "search -> summarize -> format"
  }
}
```

#### Get Job Result
```http
GET /api/result/<job_id>
Authorization: Bearer <TOKEN>
```

**Response:**
```json
{
  "job_id": "abc123-def456",
  "status": "completed",
  "result": {
    "status": "success",
    "query": "...",
    "result": "..."
  },
  "usage": {
    "tokens_used": 5000,
    "cost_usd": 0.01
  }
}
```

#### Get Usage Statistics
```http
GET /api/usage
Authorization: Bearer <TOKEN>
```

**Response:**
```json
{
  "usage_summary": {
    "total_jobs": 25,
    "completed_jobs": 23,
    "pending_jobs": 2,
    "total_tokens": 125000,
    "total_cost_usd": 0.25
  },
  "recent_jobs": [...]
}
```

### Billing & Subscriptions

#### Get Subscription Info
```http
GET /api/billing/subscription
Authorization: Bearer <TOKEN>
```

#### Upgrade Subscription
```http
POST /api/billing/subscription/upgrade
Authorization: Bearer <TOKEN>
Content-Type: application/json

{
  "tier": "basic"
}
```

#### Get Billing History
```http
GET /api/billing/history
Authorization: Bearer <TOKEN>
```

## Rate Limiting

Rate limits are enforced based on subscription tier. When exceeded, the API returns:

```json
{
  "error": "Rate limit exceeded",
  "limit_type": "daily",
  "limit": 10,
  "reset_at": "2024-01-02T00:00:00"
}
```

**Status Code:** 429 Too Many Requests

## Error Responses

### 400 Bad Request
```json
{
  "error": "Missing required field: query"
}
```

### 401 Unauthorized
```json
{
  "error": "Authentication required"
}
```

### 403 Forbidden
```json
{
  "error": "Insufficient subscription tier",
  "required": ["premium"],
  "current": "free"
}
```

### 404 Not Found
```json
{
  "error": "Job not found or access denied"
}
```

### 429 Too Many Requests
```json
{
  "error": "Rate limit exceeded",
  "limit_type": "daily",
  "limit": 10,
  "reset_at": "2024-01-02T00:00:00"
}
```

### 500 Internal Server Error
```json
{
  "error": "Pipeline execution failed: ..."
}
```

## Usage Examples

### Python Example
```python
import requests

# Login
response = requests.post('http://localhost:5000/api/auth/login', json={
    'email': 'user@example.com',
    'password': 'password'
})
token = response.json()['access_token']

# Submit research
headers = {'Authorization': f'Bearer {token}'}
response = requests.post(
    'http://localhost:5000/api/submit',
    json={'query': 'Latest AI developments'},
    headers=headers
)
job_id = response.json()['job_id']

# Check status
response = requests.get(
    f'http://localhost:5000/api/status/{job_id}',
    headers=headers
)
print(response.json())
```

### cURL Example
```bash
# Register
curl -X POST http://localhost:5000/api/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"user@example.com","password":"password"}'

# Submit research
curl -X POST http://localhost:5000/api/submit \
  -H "Authorization: Bearer <TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{"query":"Quantum computing latest news"}'
```

## Webhooks

### Stripe Webhooks

Configure Stripe webhooks at `/api/billing/webhook/stripe` to handle:
- `invoice.payment_succeeded` - Record successful payments
- `customer.subscription.deleted` - Downgrade to free tier

## Environment Variables

Required environment variables:
- `SECRET_KEY` - Flask secret key
- `JWT_SECRET_KEY` - JWT signing key
- `DATABASE_URL` - Database connection string
- `CELERY_BROKER_URL` - Redis broker URL
- `CELERY_RESULT_BACKEND` - Redis result backend URL
- `STRIPE_SECRET_KEY` - Stripe API key (optional)
- `STRIPE_WEBHOOK_SECRET` - Stripe webhook secret (optional)
