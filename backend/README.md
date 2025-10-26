# Iperf Orchestrator Backend

FastAPI-based Manager API for coordinating distributed iperf3 tests.

## Setup

### Prerequisites

- Python 3.11+
- Poetry (recommended) or pip

### Installation

1. **Using Poetry (recommended)**
   ```bash
   poetry install
   poetry shell
   ```

2. **Using pip**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

### Configuration

1. **Copy environment file**
   ```bash
   cp env.example .env
   ```

2. **Edit configuration**
   ```bash
   # Database
   DATABASE_URL=sqlite:///./iperf_orchestrator.db
   
   # JWT Settings
   SECRET_KEY=your-secret-key-here-change-in-production
   ALGORITHM=HS256
   ACCESS_TOKEN_EXPIRE_MINUTES=30
   
   # Admin User (for dev)
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=admin123
   
   # API Settings
   API_VERSION=1
   ```

### Database Setup

1. **Run migrations**
   ```bash
   alembic upgrade head
   ```

2. **Create initial migration (if needed)**
   ```bash
   alembic revision --autogenerate -m "Initial migration"
   alembic upgrade head
   ```

### Running the Server

1. **Development**
   ```bash
   uvicorn app.main:app --reload
   ```

2. **Production**
   ```bash
   uvicorn app.main:app --host 0.0.0.0 --port 8000
   ```

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/docs
- ReDoc: http://localhost:8000/redoc

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app

# Run specific test file
pytest tests/test_agents.py
```

## Database Schema

### Tables

- **agents**: Agent information and status
- **exercises**: Test exercise definitions
- **tests**: Individual test configurations
- **tasks**: Task execution tracking
- **port_reservations**: Port conflict prevention
- **idempotency_log**: Request deduplication

### Key Constraints

- Unique agent names
- Port reservations per (agent, port)
- Task state machine: pending → accepted → running → succeeded/failed
- Idempotency keys for agent mutations

## Background Jobs

The Manager runs several background tasks:

1. **Offline Marker** (5s interval)
   - Marks agents offline if last_heartbeat > 15s

2. **Timeout Sweeper** (5s interval)
   - Marks client tasks as timed_out if exceeded duration + grace

3. **Reservation Cleanup** (60s interval)
   - Releases port reservations for terminal server tasks
   - Cleans up stale reservations

4. **Exercise Auto-Ender** (5s interval)
   - Automatically ends exercises when all tasks are in terminal states (succeeded, failed, timed_out, canceled)
   - Creates kill_all tasks to clean up iperf server processes
   - Releases port reservations
   - Keeps manual stop option available via API

## API Endpoints

### Admin Endpoints (require Bearer token)

- `POST /v1/agents` - Create agent
- `GET /v1/agents` - List agents with status filter
- `GET /v1/agents/{id}` - Get agent details
- `DELETE /v1/agents/{id}` - Unregister agent
- `POST /v1/exercises` - Create exercise
- `GET /v1/exercises` - List exercises
- `GET /v1/exercises/{id}` - Get exercise with tests and tasks
- `POST /v1/exercises/{id}/tests` - Add test to exercise
- `POST /v1/exercises/{id}/start` - Start exercise
- `POST /v1/exercises/{id}/stop` - Stop exercise
- `GET /v1/exercises/{id}/results` - Get parsed results
- `GET /v1/tasks` - List tasks with filters
- `GET /v1/tasks/{id}` - Get task details
- `POST /v1/tasks/{id}/cancel` - Cancel task
- `GET /v1/ports/reservations` - List active reservations

### Agent Endpoints (require agent headers)

- `POST /v1/agent/register` - Register agent
- `POST /v1/agent/heartbeat` - Send heartbeat
- `POST /v1/agent/tasks/claim` - Claim pending task
- `POST /v1/agent/tasks/{id}/started` - Mark task started
- `POST /v1/agent/tasks/{id}/result` - Submit task result

### Public Endpoints

- `GET /healthz` - Health check

## Error Handling

All errors follow a consistent format:

```json
{
  "error": "error_code",
  "message": "Human readable message",
  "details": {
    "additional": "context"
  }
}
```

### Common Error Codes

- `400` - Bad Request (validation errors)
- `401` - Unauthorized (invalid credentials)
- `404` - Not Found (agent must exit)
- `409` - Conflict (port reservation conflict)
- `426` - Upgrade Required (API version mismatch)

## Security

### Authentication

- Admin endpoints: JWT Bearer tokens
- Agent endpoints: Header-based authentication
- API version enforcement on all requests

### Agent Security

Agents must provide:
- `X-AGENT-NAME`: Agent identifier
- `X-AGENT-KEY`: Registration key
- `X-API-Version`: API version (1)
- `Idempotency-Key`: UUID for mutating requests

### Database Security

- SQLite WAL mode for concurrent access
- Transactional task claiming
- Port reservation atomicity

## Monitoring

### Health Checks

- `GET /healthz` - Basic health check
- Database connectivity
- Background job status

### Logging

- Structured JSON logging
- Request/response logging
- Error tracking
- Performance metrics

## Performance

### Database Optimization

- Indexes on frequently queried columns
- WAL mode for SQLite
- Connection pooling
- Query optimization

### Background Jobs

- Async task execution
- Efficient polling intervals
- Resource cleanup
- Memory management

## Deployment

### Docker

```bash
# Build image
docker build -t iperf-orchestrator-manager .

# Run container
docker run -p 8000:8000 \
  -e DATABASE_URL=sqlite:///./data/iperf_orchestrator.db \
  -v $(pwd)/data:/app/data \
  iperf-orchestrator-manager
```

### Systemd

```bash
# Copy service file
sudo cp deployment/manager-systemd.service /etc/systemd/system/

# Enable and start
sudo systemctl enable iperf-manager
sudo systemctl start iperf-manager
```

### Environment Variables

Production environment variables:

```bash
DATABASE_URL=postgresql://user:pass@localhost/iperf_orchestrator
SECRET_KEY=your-production-secret-key
ADMIN_USERNAME=admin
ADMIN_PASSWORD=secure-password
API_VERSION=1
```

## Troubleshooting

### Common Issues

1. **Database locked errors**
   - Check SQLite WAL mode is enabled
   - Verify no long-running transactions

2. **Agent registration failures**
   - Verify agent name and key match
   - Check network connectivity
   - Review agent logs

3. **Port conflicts**
   - Check reservation cleanup is running
   - Verify no stale reservations
   - Review port reservation logs

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
uvicorn app.main:app --reload
```

### Database Inspection

```bash
# Connect to SQLite database
sqlite3 iperf_orchestrator.db

# Check tables
.tables

# Check agents
SELECT * FROM agents;

# Check reservations
SELECT * FROM port_reservations WHERE released_at IS NULL;
```
