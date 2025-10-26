# Iperf Orchestrator Agent

Standalone Python agent for executing iperf3 tests in the Iperf Orchestrator platform.

## Features

- **Automatic Registration**: Registers with Manager on startup
- **Heartbeat Monitoring**: Sends periodic heartbeats to Manager
- **Task Execution**: Claims and executes iperf3 tasks
- **Process Management**: Tracks running iperf3 processes
- **Error Handling**: Robust error handling and logging
- **Graceful Shutdown**: Handles shutdown signals properly

## Setup

### Prerequisites

- Python 3.11+
- iperf3 installed on the system
- Network connectivity to Manager

### Installation

1. **Using pip**
   ```bash
   pip install -r requirements.txt
   ```

2. **Using Poetry**
   ```bash
   poetry install
   poetry shell
   ```

### Configuration

1. **Copy environment file**
   ```bash
   cp env.example .env
   ```

2. **Edit configuration**
   ```bash
   # Manager API URL
   MANAGER_URL=http://localhost:8000
   
   # Agent identification
   AGENT_NAME=agent1
   AGENT_KEY=your-registration-key-here
   
   # API version
   API_VERSION=1
   ```

## Usage

### Running the Agent

```bash
# Direct execution
python agent.py

# With environment file
python agent.py --env-file .env

# With specific environment variables
MANAGER_URL=http://manager:8000 AGENT_NAME=agent1 python agent.py
```

### Systemd Service

1. **Install as systemd service**
   ```bash
   sudo cp deployment/iperf-agent.service /etc/systemd/system/
   sudo systemctl daemon-reload
   sudo systemctl enable iperf-agent
   sudo systemctl start iperf-agent
   ```

2. **Check status**
   ```bash
   sudo systemctl status iperf-agent
   sudo journalctl -u iperf-agent -f
   ```

### Cloud Deployment

Use the provided cloud-init configuration for automated deployment:

```yaml
# See deployment/cloud-init.yaml for full configuration
```

## Agent Lifecycle

### 1. Startup

1. **Read Configuration**: Load environment variables
2. **Register with Manager**: POST /v1/agent/register
3. **Exit on Failure**: If registration fails, agent exits

### 2. Main Loop

1. **Heartbeat**: Send heartbeat every 5 seconds
2. **Task Claiming**: Claim pending tasks if available
3. **Task Execution**: Execute claimed tasks
4. **Process Tracking**: Monitor running processes

### 3. Task Execution

#### Server Tasks (`iperf_server_start`)

```bash
# TCP server
iperf3 -s -p 5200

# UDP server
iperf3 -s -p 5200 -u
```

#### Client Tasks (`iperf_client_run`)

```bash
# TCP client
iperf3 -c 10.0.0.1 -p 5200 -P 16 -t 30 -J

# UDP client
iperf3 -c 10.0.0.1 -p 5200 -u -b 0 -P 16 -t 30 -J
```

#### Kill All Tasks (`kill_all`)

Terminates all tracked iperf3 processes and reports success.

### 4. Shutdown

1. **Signal Handling**: Responds to SIGTERM/SIGINT
2. **Process Cleanup**: Terminates all tracked processes
3. **Graceful Exit**: Clean shutdown with proper logging

## Task Types

### iperf_server_start

Starts an iperf3 server process:
- **Payload**: `{"port": 5200, "udp": false}`
- **Execution**: Non-blocking server process
- **Result**: Success when server starts
- **Cleanup**: Process remains running until killed

### iperf_client_run

Runs an iperf3 client test:
- **Payload**: `{"server_ip": "10.0.0.1", "port": 5200, "udp": false, "parallel": 16, "time": 30}`
- **Execution**: Blocking client process
- **Result**: iperf3 JSON output
- **Cleanup**: Process completes automatically

### kill_all

Terminates all tracked processes:
- **Payload**: `{}`
- **Execution**: Signal all tracked processes
- **Result**: Success with kill count
- **Cleanup**: Clears process tracking

## Process Management

### Process Tracking

The agent maintains a registry of running processes:

```python
{
    task_id: {
        "type": "server|client",
        "port": 5200,
        "pid": 12345,
        "process": subprocess.Popen
    }
}
```

### Process Lifecycle

1. **Start**: Process started and tracked
2. **Monitor**: Process status checked during heartbeats
3. **Complete**: Process finishes or is terminated
4. **Cleanup**: Process removed from tracking

### Error Handling

- **Process Failures**: Logged and reported to Manager
- **Network Errors**: Exponential backoff retry
- **Manager Unavailable**: Agent exits (404 response)
- **Signal Handling**: Graceful shutdown on SIGTERM/SIGINT

## Logging

### Log Format

All logs are in JSONL format:

```json
{
  "timestamp": "2024-01-01T12:00:00Z",
  "level": "info",
  "message": "Task started",
  "agent_name": "agent1",
  "task_id": 123,
  "pid": 12345
}
```

### Log Levels

- **info**: Normal operations
- **error**: Errors and failures
- **debug**: Detailed debugging information

### Log Output

- **Development**: stdout
- **Production**: systemd journal
- **File**: Optional file logging

## Configuration Options

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `MANAGER_URL` | Manager API URL | `http://localhost:8000` |
| `AGENT_NAME` | Agent identifier | `agent1` |
| `AGENT_KEY` | Registration key | Required |
| `API_VERSION` | API version | `1` |

### Command Line Options

```bash
python agent.py --help
python agent.py --env-file .env
python agent.py --debug
```

## Security

### Authentication

Agent authentication uses:
- `X-AGENT-NAME`: Agent identifier
- `X-AGENT-KEY`: Registration key
- `X-API-Version`: API version
- `Idempotency-Key`: Request deduplication

### Process Security

- **Non-root execution**: Agent runs as non-root user
- **Process isolation**: Limited process access
- **Resource limits**: Memory and CPU limits
- **Network security**: HTTPS communication

## Monitoring

### Health Checks

- **Heartbeat**: Regular Manager communication
- **Process Status**: Running process monitoring
- **Network Connectivity**: Manager reachability
- **Resource Usage**: CPU and memory monitoring

### Metrics

- **Task Count**: Tasks executed per agent
- **Success Rate**: Task success percentage
- **Response Time**: Manager communication latency
- **Resource Usage**: CPU and memory utilization

## Troubleshooting

### Common Issues

1. **Registration Failures**
   - Check MANAGER_URL is correct
   - Verify AGENT_NAME and AGENT_KEY match Manager
   - Check network connectivity

2. **Task Execution Failures**
   - Verify iperf3 is installed
   - Check port availability
   - Review agent logs

3. **Process Management Issues**
   - Check process permissions
   - Verify signal handling
   - Review systemd configuration

### Debug Mode

Enable debug logging:

```bash
export LOG_LEVEL=DEBUG
python agent.py
```

### Log Analysis

```bash
# View agent logs
journalctl -u iperf-agent -f

# Filter by level
journalctl -u iperf-agent | grep ERROR

# View recent logs
journalctl -u iperf-agent --since "1 hour ago"
```

### Process Inspection

```bash
# Check running processes
ps aux | grep iperf3

# Check agent process
ps aux | grep agent.py

# Check systemd status
systemctl status iperf-agent
```

## Performance

### Optimization

- **Connection Pooling**: HTTP client reuse
- **Process Management**: Efficient process tracking
- **Memory Usage**: Minimal memory footprint
- **CPU Usage**: Low CPU overhead

### Scaling

- **Multiple Agents**: Deploy multiple agent instances
- **Load Distribution**: Manager distributes tasks
- **Resource Management**: Per-agent resource limits
- **Network Optimization**: Efficient communication

## Development

### Code Structure

```
agent.py              # Main agent script
requirements.txt      # Python dependencies
env.example          # Environment template
deployment/          # Deployment configurations
```

### Testing

```bash
# Run tests
python -m pytest tests/

# Run with coverage
python -m pytest --cov=agent tests/
```

### Code Style

- **Black**: Code formatting
- **isort**: Import sorting
- **flake8**: Linting
- **mypy**: Type checking

## Deployment

### Manual Deployment

1. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

2. **Configure Environment**
   ```bash
   cp env.example .env
   # Edit .env with your settings
   ```

3. **Run Agent**
   ```bash
   python agent.py
   ```

### Automated Deployment

1. **Cloud-init**: Use provided cloud-init configuration
2. **Docker**: Build and run with Docker
3. **Systemd**: Install as systemd service
4. **Kubernetes**: Deploy with Kubernetes manifests

### Production Considerations

- **Resource Limits**: Set appropriate limits
- **Monitoring**: Implement health checks
- **Logging**: Configure log rotation
- **Security**: Use secure communication
- **Backup**: Backup configuration files
