# Facebook Checker REST API

FastAPI-based REST API for phone number verification on Facebook.

## Quick Start

```bash
pip install fastapi uvicorn pydantic
python server.py
```

**URLs:**
- API: `http://localhost:8000`
- Docs: `http://localhost:8000/docs`
- Proxy: `http://localhost:9080` (internal)
- Stats: `http://localhost:9081/stats`

**Note:** API uses ports 9080/9081 to avoid conflicts with GUI (8080/8081).

---

## Endpoints

### System

**GET** `/api/health` - Health check
```json
{"status": "healthy", "service": "Facebook Account Checker API", "timestamp": "2025-10-24T10:30:00"}
```

**GET** `/api/status` - System status
```json
{"expired": false, "expiration_message": "Valid until November 23, 2025", "expiration_date": "2025-11-23T17:59:59", "active_jobs": 2}
```

### Proxy

**GET** `/api/proxy/config` - Get proxy settings

**POST** `/api/proxy/config` - Set proxy settings
```json
{"enabled": true, "server": "31.59.20.176", "port": 6754, "username": "user", "password": "pass"}
```

**GET** `/api/proxy/test` - Test proxy connection

### Jobs

**GET** `/api/jobs` - List all jobs

**POST** `/api/jobs` - Create job
```json
{"phone_numbers": ["1234567890", "0987654321"], "workers": 5, "headless": false}
```

**GET** `/api/jobs/{job_id}` - Get job details

**GET** `/api/jobs/{job_id}/status` - Get job status (lightweight)

**GET** `/api/jobs/{job_id}/results` - Get job results

**GET** `/api/jobs/{job_id}/logs` - Get job logs

**POST** `/api/jobs/{job_id}/stop` - Stop job

**DELETE** `/api/jobs/{job_id}` - Delete job

**GET** `/api/jobs/{job_id}/stream` - Stream progress (SSE)

---

## Usage

### Python
```python
import requests

BASE_URL = "http://localhost:8000/api"

# Create job
job = requests.post(f"{BASE_URL}/jobs", json={
    "phone_numbers": ["1234567890"],
    "workers": 5,
    "headless": True
}).json()

# Poll status
while True:
    status = requests.get(f"{BASE_URL}/jobs/{job['job_id']}/status").json()
    if status['status'] in ['completed', 'stopped', 'error']:
        break
    time.sleep(2)

# Get results
results = requests.get(f"{BASE_URL}/jobs/{job['job_id']}/results").json()
```

### cURL
```bash
# Create job
curl -X POST http://localhost:8000/api/jobs \
  -H "Content-Type: application/json" \
  -d '{"phone_numbers": ["1234567890"], "workers": 5, "headless": true}'

# Get status
curl http://localhost:8000/api/jobs/{job-id}/status
```

### JavaScript
```javascript
const response = await fetch('http://localhost:8000/api/jobs', {
  method: 'POST',
  headers: {'Content-Type': 'application/json'},
  body: JSON.stringify({phone_numbers: ['1234567890'], workers: 5, headless: true})
});
const job = await response.json();

// Stream progress
const eventSource = new EventSource(`http://localhost:8000/api/jobs/${job.job_id}/stream`);
eventSource.onmessage = (e) => console.log(JSON.parse(e.data));
```

---

## Job Statuses

- `pending` - Created, not started
- `running` - Processing
- `completed` - Finished successfully
- `stopped` - User stopped
- `error` - Error occurred

---

## Error Responses

```json
{"detail": "Error message"}
```

**HTTP Status Codes:** 200 (OK), 201 (Created), 400 (Bad Request), 404 (Not Found), 422 (Validation Error), 500 (Server Error)

---

## Production

```bash
# Uvicorn with workers
uvicorn server:app --host 0.0.0.0 --port 8000 --workers 4

# Gunicorn
gunicorn server:app -w 4 -k uvicorn.workers.UvicornWorker -b 0.0.0.0:8000
```

**Docker:**
```dockerfile
FROM python:3.11-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "server:app", "--host", "0.0.0.0", "--port", "8000"]
```

---

## Security (Production)

- Add authentication (JWT/API keys)
- Enable rate limiting
- Configure CORS properly
- Use HTTPS with reverse proxy
- Validate all inputs (Pydantic handles this)

---

## Notes

- Jobs stored in memory (lost on restart)
- Multiple jobs run concurrently
- Use `/stream` for real-time updates
- Proxy config changes without restart

**Version:** 2.0.0 | **Port:** 8000
