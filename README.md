# Iperf Orchestrator

A distributed network performance testing platform that coordinates `iperf3` tests across multiple agents via a central Manager with a modern web interface.

## Architecture

```
+------------------+           HTTPS            +-----------------+
|     AGENT(S)     |  <---------------------->  |     MANAGER     |
|  - register      |     /v1/agent/...          |  FastAPI + DB   |
|  - heartbeat     |  pull tasks / push results |  (SQLite dev)   |
|  - claim & exec  |                            |                 |
+------------------+                            +-----------------+
             ^                                                ^
             |                                +---------------+-------------+
             |                                |     WEB UI (Vue+Tailwind)   |
             |                                |   - Agents / Exercises /    |
             |                                |     Tests / Tasks / Results |
             |                                +-----------------------------+
```

## Features

- **Distributed Testing**: Coordinate iperf3 tests across multiple agents
- **Port Management**: Automatic port reservation to prevent conflicts
- **Real-time Monitoring**: Live status updates and task tracking
- **Modern UI**: Vue 3 + Tailwind CSS web interface
- **Agent Management**: Register, monitor, and manage test agents
- **Exercise Orchestration**: Create and manage multi-test scenarios
- **Results Analysis**: Parse and visualize iperf3 JSON results

## Quick Start

### Prerequisites

- Python 3.11+
- Node.js 18+
- iperf3 installed on agent machines

### Development Setup

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd iperf-orchestrator
   ```

2. **Backend Setup**
   ```bash
   cd backend
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   pip install -r requirements.txt
   
   # Copy environment file
   cp env.example .env
   # Edit .env with your settings
   
   # Run database migrations
   alembic upgrade head
   
   # Start the backend
   uvicorn app.main:app --reload
   ```

3. **Frontend Setup**
   ```bash
   cd frontend
   npm install
   npm run dev
   ```

4. **Agent Setup**
   ```bash
   cd agent
   pip install -r requirements.txt
   
   # Copy environment file
   cp env.example .env
   # Edit .env with manager URL and agent credentials
   
   # Run the agent
   python agent.py
   ```

### Docker Setup

1. **Start the full stack**
   ```bash
   cd backend
   docker-compose up -d
   ```

2. **Access the application**
   - Manager API: http://localhost:8000
   - Web UI: http://localhost:3000
   - Default login: admin / admin123

## Usage

### 1. Create Agents

First, create agent records in the Manager:

```bash
curl -X POST http://localhost:8000/v1/agents \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "agent1",
    "registration_key": "secret-key-123",
    "operating_system": "linux"
  }'
```

### 2. Start Agents

On each agent machine, run the agent script:

```bash
export MANAGER_URL=http://manager-ip:8000
export AGENT_NAME=agent1
export AGENT_KEY=secret-key-123
python agent.py
```

### 3. Create Exercise

Use the web UI or API to create an exercise:

```bash
curl -X POST http://localhost:8000/v1/exercises \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Network Test 1",
    "duration_seconds": 30,
    "notes": "Testing network performance"
  }'
```

### 4. Add Tests

Add tests to the exercise:

```bash
curl -X POST http://localhost:8000/v1/exercises/1/tests \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "server_agent_id": 1,
    "client_agent_id": 2,
    "server_port": 5200,
    "udp": false,
    "parallel": 16,
    "time_seconds": 30
  }'
```

### 5. Start Exercise

```bash
curl -X POST http://localhost:8000/v1/exercises/1/start \
  -H "Authorization: Bearer <token>"
```

## API Documentation

### Authentication

All admin endpoints require a Bearer token:

```bash
# Login to get token
curl -X POST http://localhost:8000/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username": "admin", "password": "admin123"}'
```

### Agent Endpoints

Agent endpoints require special headers:

```bash
curl -X POST http://localhost:8000/v1/agent/heartbeat \
  -H "X-AGENT-NAME: agent1" \
  -H "X-AGENT-KEY: secret-key-123" \
  -H "X-API-Version: 1" \
  -H "Content-Type: application/json" \
  -d '{"ip_address": "10.0.0.1", "running": []}'
```

## Configuration

### Manager Configuration

Environment variables for the Manager:

```bash
DATABASE_URL=sqlite:///./iperf_orchestrator.db
SECRET_KEY=your-secret-key-here
ADMIN_USERNAME=admin
ADMIN_PASSWORD=admin123
API_VERSION=1
```

### Agent Configuration

Environment variables for agents:

```bash
MANAGER_URL=http://localhost:8000
AGENT_NAME=agent1
AGENT_KEY=your-registration-key-here
API_VERSION=1
```

## Deployment

### Cloud Deployment

Use the provided cloud-init configuration for automated agent deployment:

```yaml
#cloud-config
# See deployment/cloud-init.yaml for full configuration
```

### Systemd Services

Install as systemd services for production:

```bash
# Copy service files
sudo cp deployment/iperf-agent.service /etc/systemd/system/
sudo cp deployment/manager-systemd.service /etc/systemd/system/

# Enable and start services
sudo systemctl enable iperf-agent
sudo systemctl start iperf-agent
```

### Docker Production

```bash
# Build and run with Docker Compose
docker-compose -f docker-compose.prod.yml up -d
```

## API Reference

### Admin Endpoints

- `POST /v1/agents` - Create agent
- `GET /v1/agents` - List agents
- `GET /v1/agents/{id}` - Get agent details
- `DELETE /v1/agents/{id}` - Delete agent
- `POST /v1/exercises` - Create exercise
- `GET /v1/exercises` - List exercises
- `POST /v1/exercises/{id}/tests` - Add test to exercise
- `POST /v1/exercises/{id}/start` - Start exercise
- `POST /v1/exercises/{id}/stop` - Stop exercise
- `GET /v1/exercises/{id}/results` - Get exercise results
- `GET /v1/tasks` - List tasks
- `POST /v1/tasks/{id}/cancel` - Cancel task

### Agent Endpoints

- `POST /v1/agent/register` - Register agent
- `POST /v1/agent/heartbeat` - Send heartbeat
- `POST /v1/agent/tasks/claim` - Claim task
- `POST /v1/agent/tasks/{id}/started` - Mark task started
- `POST /v1/agent/tasks/{id}/result` - Submit task result

## Development

### Running Tests

```bash
cd backend
pytest tests/
```

### Code Formatting

```bash
# Backend
cd backend
black app/
isort app/

# Frontend
cd frontend
npm run format
```

### Database Migrations

```bash
cd backend
# Create migration
alembic revision --autogenerate -m "Description"

# Apply migrations
alembic upgrade head

# Rollback
alembic downgrade -1
```

## Troubleshooting

### Common Issues

1. **Agent can't connect to Manager**
   - Check MANAGER_URL is correct
   - Verify network connectivity
   - Check firewall settings

2. **Port conflicts**
   - Manager automatically prevents port conflicts
   - Check port reservations in UI

3. **Tasks not executing**
   - Verify agent is online (heartbeat < 15s)
   - Check agent logs for errors
   - Verify iperf3 is installed on agent

### Logs

- Manager logs: Check application logs
- Agent logs: JSONL format to stdout
- System logs: `journalctl -u iperf-agent`

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## License

MIT License - see LICENSE file for details.
