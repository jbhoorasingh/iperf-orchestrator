# Iperf Orchestrator - Deployment Guide

This guide covers deploying the Iperf Orchestrator Manager using Docker.

## Overview

The Iperf Orchestrator Manager is packaged as a single Docker container that includes:
- **Backend**: FastAPI application (Python 3.11)
- **Frontend**: Vue 3 web interface
- **Nginx**: Serves frontend static files and proxies API requests
- **SQLite**: Database for storing exercises, tests, and results

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 1.29+ (optional but recommended)

### Using Docker Compose (Recommended)

1. **Clone the repository** (or copy these files to your server)

2. **Create environment file** (optional - for custom configuration):
   ```bash
   cat > .env <<EOF
   SECRET_KEY=your-strong-secret-key-here
   ADMIN_USERNAME=admin
   ADMIN_PASSWORD=your-secure-password
   EOF
   ```

3. **Build and start the container**:
   ```bash
   docker-compose up -d
   ```

4. **Access the application**:
   - Web UI: http://localhost
   - API: http://localhost/v1/
   - Default login: `admin` / `admin123` (or your custom password)

5. **View logs**:
   ```bash
   docker-compose logs -f
   ```

6. **Stop the container**:
   ```bash
   docker-compose down
   ```

### Using Docker CLI

1. **Build the image**:
   ```bash
   docker build -t iperf-orchestrator .
   ```

2. **Run the container**:
   ```bash
   docker run -d \
     --name iperf-orchestrator \
     -p 80:80 \
     -e SECRET_KEY=your-strong-secret-key-here \
     -e ADMIN_USERNAME=admin \
     -e ADMIN_PASSWORD=your-secure-password \
     -v iperf-data:/app/data \
     --restart unless-stopped \
     iperf-orchestrator
   ```

3. **Access the application**:
   - Web UI: http://localhost

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | SQLite database path | `sqlite:///./data/iperf_orchestrator.db` |
| `SECRET_KEY` | JWT signing key (change in production!) | `change-this-secret-key-in-production` |
| `ADMIN_USERNAME` | Admin username for login | `admin` |
| `ADMIN_PASSWORD` | Admin password for login | `admin123` |
| `API_VERSION` | API version number | `1` |

### Volume Management

The container uses a persistent volume for the database:
- **Volume**: `iperf-data` mounted at `/app/data`
- **Contents**: SQLite database file and WAL files

**Backup the database**:
```bash
docker cp iperf-orchestrator:/app/data/iperf_orchestrator.db ./backup.db
```

**Restore the database**:
```bash
docker cp ./backup.db iperf-orchestrator:/app/data/iperf_orchestrator.db
docker-compose restart
```

## Production Deployment

### Security Considerations

1. **Change default credentials**:
   - Set strong `SECRET_KEY` (use `openssl rand -hex 32`)
   - Change `ADMIN_PASSWORD` from default

2. **Use HTTPS**:
   - Put the container behind a reverse proxy (nginx, Caddy, Traefik)
   - Configure SSL/TLS certificates

3. **Restrict access**:
   - Use firewall rules to limit access
   - Consider using a VPN or SSH tunnel for remote access

### Example Nginx Reverse Proxy with SSL

```nginx
server {
    listen 443 ssl http2;
    server_name iperf.example.com;

    ssl_certificate /path/to/cert.pem;
    ssl_certificate_key /path/to/key.pem;

    location / {
        proxy_pass http://localhost:80;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}

server {
    listen 80;
    server_name iperf.example.com;
    return 301 https://$server_name$request_uri;
}
```

### Using Different Port

To run on a different port (e.g., 8080):

**Docker Compose**:
```yaml
ports:
  - "8080:80"
```

**Docker CLI**:
```bash
docker run -p 8080:80 ...
```

### Resource Limits

Add resource limits for production:

**Docker Compose**:
```yaml
services:
  iperf-orchestrator:
    # ... other config ...
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G
        reservations:
          cpus: '1'
          memory: 512M
```

**Docker CLI**:
```bash
docker run --cpus="2" --memory="2g" ...
```

## Agent Setup

Once the Manager is running, you need to deploy agents on test machines:

1. **On the Manager UI**:
   - Navigate to Agents page
   - Create a new agent with a name and registration key
   - Note the agent name and key

2. **On each agent machine**:
   ```bash
   cd agent
   pip install -r requirements.txt

   # Create .env file
   cat > .env <<EOF
   MANAGER_URL=http://your-manager-host
   AGENT_NAME=agent-name-from-ui
   AGENT_KEY=registration-key-from-ui
   EOF

   # Run agent
   python agent.py
   ```

3. **Verify connection**:
   - Agent should appear as "online" in the Manager UI
   - Check agent logs for successful registration

## Monitoring

### Health Check

The container includes a health check endpoint:
```bash
curl http://localhost/healthz
```

Expected response:
```json
{"status": "healthy"}
```

### Container Logs

View logs from both nginx and backend:
```bash
# All logs
docker-compose logs -f

# Backend only
docker exec iperf-orchestrator tail -f /var/log/supervisor/backend.log

# Nginx only
docker exec iperf-orchestrator tail -f /var/log/supervisor/nginx.log
```

### Database Inspection

Access the database directly:
```bash
docker exec -it iperf-orchestrator sqlite3 /app/data/iperf_orchestrator.db

# Example queries
sqlite> SELECT id, name, started_at, ended_at FROM exercises;
sqlite> SELECT id, name, status, last_heartbeat FROM agents;
sqlite> .quit
```

## Troubleshooting

### Container won't start

1. Check logs:
   ```bash
   docker-compose logs
   ```

2. Verify port 80 is not in use:
   ```bash
   sudo lsof -i :80
   ```

3. Check disk space:
   ```bash
   df -h
   ```

### Frontend shows "Network Error"

1. Check backend is running:
   ```bash
   docker exec iperf-orchestrator curl http://127.0.0.1:8000/healthz
   ```

2. Check nginx configuration:
   ```bash
   docker exec iperf-orchestrator nginx -t
   ```

### Database locked errors

SQLite can have concurrency issues. If you see "database is locked":
1. Ensure only one Manager instance is running
2. Check for orphaned processes accessing the database

### Agent can't connect to Manager

1. Verify Manager is accessible from agent machine:
   ```bash
   curl http://manager-host/healthz
   ```

2. Check agent configuration (MANAGER_URL, credentials)

3. Review agent logs for connection errors

## Upgrading

To upgrade to a new version:

1. **Pull latest code**:
   ```bash
   git pull
   ```

2. **Rebuild and restart**:
   ```bash
   docker-compose down
   docker-compose build --no-cache
   docker-compose up -d
   ```

3. **Verify health**:
   ```bash
   curl http://localhost/healthz
   ```

**Note**: Database migrations run automatically on container start.

## Backup and Restore

### Backup

```bash
# Backup database
docker cp iperf-orchestrator:/app/data ./backup-$(date +%Y%m%d)

# Or use docker-compose
docker-compose exec iperf-orchestrator sqlite3 /app/data/iperf_orchestrator.db ".backup /tmp/backup.db"
docker cp iperf-orchestrator:/tmp/backup.db ./backup-$(date +%Y%m%d).db
```

### Restore

```bash
# Stop the container
docker-compose down

# Restore database files
docker volume rm iperf-orchestrator_iperf-data
docker volume create iperf-orchestrator_iperf-data
docker run --rm -v iperf-orchestrator_iperf-data:/data -v $(pwd)/backup:/backup alpine cp -r /backup/* /data/

# Start the container
docker-compose up -d
```

## Support

For issues and questions:
- Check logs first: `docker-compose logs -f`
- Review this documentation
- Check GitHub issues: [your-repo-url]
