# Docker Deployment Guide

Run NodeWalker in a containerized environment with Chrome pre-installed.

## Quick Start

### Using Docker Compose (Recommended)

```bash
# Start NodeWalker
docker-compose up -d

# Check logs
docker-compose logs -f

# Stop
docker-compose down
```

NodeWalker API will be available at `http://localhost:8585`

### Using Docker CLI

```bash
# Build image
docker build -t nodewalker .

# Run container
docker run -d \
  --name nodewalker \
  -p 8585:8585 \
  -p 9222:9222 \
  nodewalker

# Check logs
docker logs -f nodewalker

# Stop and remove
docker stop nodewalker && docker rm nodewalker
```

## Verify Installation

```bash
# Health check
curl http://localhost:8585/health

# Get available tools
curl http://localhost:8585/tools

# Test navigation
curl -X POST http://localhost:8585/execute \
  -H "Content-Type: application/json" \
  -d '{"tool": "navigate", "arguments": {"url": "https://example.com"}}'
```

## Configuration

### Custom Browser Config

Mount your own `browser_config.json`:

```bash
docker run -d \
  -p 8585:8585 \
  -v $(pwd)/my-config.json:/app/browser_config.json:ro \
  nodewalker
```

### Environment Variables

| Variable | Default | Description |
|----------|---------|-------------|
| `NODEWALKER_CHROME_PORT` | `9222` | Chrome DevTools Protocol port |

Example:

```bash
docker run -d \
  -p 8585:8585 \
  -e NODEWALKER_CHROME_PORT=9333 \
  nodewalker
```

## Troubleshooting

### Chrome fails to start

**Symptom**: Container starts but `/health` returns disconnected

**Solution**: Chrome needs more shared memory in Docker

```yaml
# docker-compose.yml
services:
  nodewalker:
    shm_size: '2gb'  # Add this line
```

Or with Docker CLI:

```bash
docker run -d --shm-size=2g -p 8585:8585 nodewalker
```

### Connection timeout

**Symptom**: `Could not connect to Chrome after 3 attempts`

**Solution**: Increase startup wait time

```dockerfile
# In Dockerfile, change:
CMD ... sleep 3 && ...
# To:
CMD ... sleep 10 && ...
```

### Permission denied errors

**Symptom**: Chrome crashes with permission errors

**Solution**: Already handled by running as non-root user. If issues persist:

```bash
docker run -d \
  --cap-add=SYS_ADMIN \
  -p 8585:8585 \
  nodewalker
```

## Production Deployment

### With Reverse Proxy (nginx)

```nginx
server {
    listen 80;
    server_name nodewalker.example.com;

    location / {
        proxy_pass http://localhost:8585;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host $host;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Resource Limits

Adjust in `docker-compose.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '4'      # Max 4 CPU cores
      memory: 4G     # Max 4GB RAM
    reservations:
      cpus: '1'      # Min 1 CPU core
      memory: 1G     # Min 1GB RAM
```

### Persistent Logs

Mount log directory:

```yaml
volumes:
  - ./logs:/app/logs
```

## Multi-Instance Deployment

Run multiple NodeWalker instances:

```yaml
version: '3.8'
services:
  nodewalker-1:
    build: .
    ports:
      - "8585:8585"
      - "9222:9222"
  
  nodewalker-2:
    build: .
    ports:
      - "8586:8585"
      - "9223:9222"
  
  nodewalker-3:
    build: .
    ports:
      - "8587:8585"
      - "9224:9222"
```

Load balance with nginx:

```nginx
upstream nodewalker_backend {
    server localhost:8585;
    server localhost:8586;
    server localhost:8587;
}

server {
    listen 80;
    location / {
        proxy_pass http://nodewalker_backend;
    }
}
```

## Security Considerations

1. **Don't expose port 9222 publicly** - it gives full browser control
2. **Use authentication** - Add API key middleware in production
3. **Network isolation** - Run in private Docker network
4. **Resource limits** - Prevent DoS via resource exhaustion

Example secure setup:

```yaml
services:
  nodewalker:
    build: .
    ports:
      - "127.0.0.1:8585:8585"  # Only localhost
    networks:
      - internal
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 2G

networks:
  internal:
    driver: bridge
```
