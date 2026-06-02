# Teaching Planning Assistant (TPA)

## 🎯 Overview

Teaching Planning Assistant is an **autonomous educational content generation engine** powered by DeepSeek V4 Flash through DeepSeek's OpenAI-compatible API. It generates structured educational content aligned with the Chilean national curriculum (Currículum Nacional de Chile).

### Key Features

- 🎓 **Lesson Plan Generation** - Structured lesson plans with objectives, activities, and assessments
- 📝 **Quiz Generation** - Multiple question types with Bloom's taxonomy alignment
- 🎮 **Activity Generation** - Interactive learning activities with differentiation
- 📊 **Exam Generation** - Summative assessments with answer keys and rubrics
- 📚 **Summary Generation** - Unit summaries with flashcards and concept maps
- ♿ **NEE Adaptations** - Content adaptation for Special Educational Needs
- ✅ **Quality Validation** - Automated content quality gates
- 📦 **Batch Processing** - Async generation with webhook notifications
- 🤖 **AI Tutor** - Conversational tutoring support

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                    TPA API (FastAPI)                        │
├─────────────────────────────────────────────────────────────┤
│  ┌─────────┐ ┌─────────┐ ┌─────────┐ ┌─────────┐           │
│  │ Planning│ │ Content │ │  Batch  │ │  Tutor  │           │
│  │ Router  │ │ Router  │ │ Router  │ │ Router  │           │
│  └────┬────┘ └────┬────┘ └────┬────┘ └────┬────┘           │
│       │           │           │           │                 │
│  ┌────┴───────────┴───────────┴───────────┴────┐           │
│  │       Content Generation Service            │           │
│  │   (DeepSeek V4 Flash, OpenAI-compatible)  │           │
│  └────────────────────────────────────────────┘           │
│                         │                                  │
│  ┌──────────────────────┴──────────────────────┐          │
│  │         Curriculum Service                   │          │
│  │    (Chilean National Curriculum Data)        │          │
│  └─────────────────────────────────────────────┘          │
└─────────────────────────────────────────────────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Python 3.11+
- PostgreSQL (or SQLite for development)
- DeepSeek API key (`DEEPSEEK_API_KEY`)

### Installation

```bash
# Clone repository
git clone https://github.com/your-org/teaching-planning-assistant.git
cd teaching-planning-assistant

# Create virtual environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
.\venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt

# Configure environment
cp .env.example .env
# Edit .env with your settings
```

### Configuration

Create a `.env` file with:

```env
# Required
DEEPSEEK_API_KEY=your_deepseek_api_key
DATABASE_URL=postgresql+asyncpg://user:pass@localhost/tpa
SECRET_KEY=your_secret_key_here

# Optional AI settings
DEEPSEEK_BASE_URL=https://api.deepseek.com/v1
DEEPSEEK_MODEL=deepseek-v4-flash
AI_REQUEST_TIMEOUT_SECONDS=120
AI_MAX_OUTPUT_TOKENS=16000

# Optional
ENVIRONMENT=development
LOG_LEVEL=INFO
```

### Running the Server

```bash
# Development
uvicorn api.main:app --reload --host 0.0.0.0 --port 8000

# Production
gunicorn api.main:app -w 4 -k uvicorn.workers.UvicornWorker --bind 0.0.0.0:8000
```

## 📚 API Documentation

### Base URL

```
http://localhost:8000/api/v1
```

### Authentication

TPA supports two authentication methods:

1. **JWT Token** (for user-facing applications)
   ```
   Authorization: Bearer <token>
   ```

2. **API Key** (for service-to-service communication)
   ```
   X-API-Key: tpa_xxxxxxxxxxxxxxxxxxxxx
   ```

### Endpoints Overview

| Category | Endpoint | Method | Description |
|----------|----------|--------|-------------|
| **Health** | `/health` | GET | Basic health check |
| | `/health/ready` | GET | Readiness probe with dependencies |
| | `/health/detailed` | GET | Full system metrics |
| **Planning** | `/planning/generate-plan-structured` | POST | Generate structured lesson plan |
| **Content** | `/content/generate-quiz` | POST | Generate quiz |
| | `/content/generate-activity` | POST | Generate activity |
| | `/content/generate-exam` | POST | Generate exam |
| | `/content/generate-reinforcement` | POST | Generate reinforcement materials |
| | `/content/generate-summary` | POST | Generate unit summary |
| | `/content/adapt-content` | POST | Adapt content for NEE |
| **Validation** | `/validation/validate-content` | POST | Validate content quality |
| | `/validation/quick-check` | POST | Quick validation |
| **Batch** | `/batch/generate` | POST | Submit batch job |
| | `/batch/{job_id}` | GET | Get job status |
| | `/batch/{job_id}/cancel` | POST | Cancel job |
| **Tutor** | `/tutor/chat` | POST | Chat with AI tutor |
| **Admin** | `/admin/apikeys` | POST | Create API key |
| | `/admin/apikeys` | GET | List API keys |

### Interactive Documentation

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 📖 Usage Examples

### Generate a Structured Lesson Plan

```bash
curl -X POST "http://localhost:8000/api/v1/planning/generate-plan-structured" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "oa_ids": ["MA05OA01", "MA05OA02"],
    "grade_level": "5° Básico",
    "subject": "Matemáticas",
    "duration_minutes": 90,
    "include_differentiation": true
  }'
```

### Generate a Quiz

```bash
curl -X POST "http://localhost:8000/api/v1/content/generate-quiz" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "oa_ids": ["LE05OA03"],
    "grade_level": "5° Básico",
    "subject": "Lenguaje",
    "num_questions": 10,
    "question_types": ["multiple_choice", "true_false"],
    "include_explanations": true
  }'
```

### Adapt Content for NEE

```bash
curl -X POST "http://localhost:8000/api/v1/content/adapt-content" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "lesson",
    "original_content": "...",
    "nee_types": ["dyslexia", "adhd"],
    "adaptation_level": "moderate",
    "student_grade_level": "5° Básico",
    "include_teacher_guide": true
  }'
```

### Submit Batch Job

```bash
curl -X POST "http://localhost:8000/api/v1/batch/generate" \
  -H "X-API-Key: your_api_key" \
  -H "Content-Type: application/json" \
  -d '{
    "content_type": "quiz",
    "items": [
      {"item_id": "q1", "oa_ids": ["MA05OA01"], "grade_level": "5°", "subject": "Matemáticas", "num_questions": 5},
      {"item_id": "q2", "oa_ids": ["MA05OA02"], "grade_level": "5°", "subject": "Matemáticas", "num_questions": 5}
    ],
    "webhook_url": "https://your-service.com/webhooks/tpa"
  }'
```

## 🔒 Rate Limiting

| Client Type | Limit |
|------------|-------|
| API Key | 100 requests/minute |
| JWT/IP | 30 requests/minute |

Rate limit headers included in responses:
- `X-RateLimit-Limit`
- `X-RateLimit-Remaining`
- `X-RateLimit-Reset`

## 🔗 Webhook Events

| Event | Description |
|-------|-------------|
| `batch.progress` | Sent every 5 items processed |
| `batch.completed` | Sent when batch completes |

Webhooks include HMAC-SHA256 signature in `X-TPA-Signature` header.

## 🛠️ Development

### Project Structure

```
teaching-planning-assistant/
├── api/
│   ├── core/           # Configuration, security
│   ├── db/             # Database models and CRUD
│   ├── middleware/     # Rate limiting
│   ├── routers/        # API endpoints
│   ├── services/       # Business logic
│   └── main.py         # Application entry
├── data/
│   ├── processed/      # Enriched curriculum data
│   └── raw/            # Raw curriculum data
├── docs/
│   ├── api/            # OpenAPI specs
│   └── architectural/  # Design docs
└── scripts/
    └── processing/     # Data processing scripts
```

### Running Tests

```bash
pytest tests/ -v --cov=api --cov-report=html
```

## 📊 Monitoring

- Health checks: `/health`, `/health/ready`, `/health/live`
- Detailed metrics: `/health/detailed`
- Logs: Structured JSON logging to stdout

## 🤝 Integration with Colegio Alas Inclusivas

TPA serves as the core content generation microservice for Colegio Alas Inclusivas platform:

1. **Content Generation Queue** → Batch endpoint
2. **Quality Gates** → Validation endpoint
3. **NEE Support** → Adapt content endpoint
4. **Student Support** → Tutor chat endpoint

## 📄 License

MIT License - See LICENSE file

## 🆘 Support

- Documentation: [docs/](./docs)
- Issues: GitHub Issues
- Contact: team@example.com