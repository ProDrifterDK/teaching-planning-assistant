# TPA API Summary

## Version 2.0.0

### New Endpoints in This Version

| Endpoint | Description | Auth |
|----------|-------------|------|
| POST `/planning/generate-plan-structured` | Structured lesson generation | JWT/API Key |
| POST `/content/generate-quiz` | Quiz generation | JWT/API Key |
| POST `/content/generate-activity` | Activity generation | JWT/API Key |
| POST `/content/generate-exam` | Exam generation | JWT/API Key |
| POST `/content/generate-reinforcement` | Reinforcement materials | JWT/API Key |
| POST `/content/generate-summary` | Unit summaries | JWT/API Key |
| POST `/content/adapt-content` | NEE adaptations | JWT/API Key |
| POST `/validation/validate-content` | Quality validation | JWT/API Key |
| POST `/batch/generate` | Batch processing | API Key |
| POST `/tutor/chat` | AI tutor | JWT/API Key |

### Authentication

- JWT: `Authorization: Bearer <token>`
- API Key: `X-API-Key: tpa_xxx`

### Rate Limits

- API Key: 100/minute
- JWT/IP: 30/minute

### Response Format

All endpoints return:
```json
{
  "success": true,
  "data": {...},
  "generation_metadata": {
    "requested_at": "2024-01-01T00:00:00Z",
    "completed_at": "2024-01-01T00:00:01Z",
    "duration_ms": 1000,
    "model": "gemini-2.0-flash-exp"
  },
  "error": null
}
```

### Error Codes

| Code | Description |
|------|-------------|
| 400 | Bad Request - Invalid parameters |
| 401 | Unauthorized - Missing/invalid auth |
| 403 | Forbidden - Insufficient permissions |
| 404 | Not Found - Resource doesn't exist |
| 429 | Rate Limit Exceeded |
| 500 | Internal Server Error |