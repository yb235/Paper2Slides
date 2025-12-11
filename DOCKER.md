# Docker Setup for Paper2Slides

## Quick Start

### 1. Build and Run with Docker Compose (Recommended)

```bash
# Build and start the container
docker-compose up --build

# Or run in detached mode
docker-compose up -d --build

# View logs
docker-compose logs -f

# Stop the container
docker-compose down
```

### 2. Build and Run with Docker

```bash
# Build the image
docker build -t paper2slides .

# Run the container
docker run -p 8000:8000 \
  -v ${PWD}/outputs:/app/outputs \
  -v ${PWD}/uploads:/app/uploads \
  -v ${PWD}/paper2slides/.env:/app/paper2slides/.env \
  paper2slides

# Run in detached mode
docker run -d -p 8000:8000 \
  -v ${PWD}/outputs:/app/outputs \
  -v ${PWD}/uploads:/app/uploads \
  -v ${PWD}/paper2slides/.env:/app/paper2slides/.env \
  --name paper2slides-app \
  paper2slides
```

## Access the Application

Once the container is running:

- **Web Interface**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Health Check**: http://localhost:8000/health

## Managing the Container

```bash
# View running containers
docker ps

# Stop the container
docker stop paper2slides-app

# Start the container
docker start paper2slides-app

# Remove the container
docker rm paper2slides-app

# View logs
docker logs -f paper2slides-app

# Execute commands in the container
docker exec -it paper2slides-app /bin/bash
```

## Volume Mounts

The Docker setup uses volumes to persist data:

- `./outputs` - Generated slides and outputs
- `./uploads` - Uploaded PDF files
- `./paper2slides/.env` - Environment configuration

## Troubleshooting

### Container won't start
- Check that port 8000 is not already in use
- Verify the `.env` file exists and contains valid API keys

### API keys not working
- Ensure the `.env` file is properly mounted
- Check logs: `docker-compose logs -f`

### Build fails
- Ensure you have enough disk space
- Try cleaning Docker cache: `docker system prune -a`

## Development Mode

For development with live reload:

```bash
# Run with code mounted as volume
docker run -p 8000:8000 \
  -v ${PWD}/paper2slides:/app/paper2slides \
  -v ${PWD}/api:/app/api \
  -v ${PWD}/outputs:/app/outputs \
  paper2slides
```

## Production Deployment

For production, consider:

1. Using environment variables instead of mounting `.env`
2. Setting up proper logging and monitoring
3. Using a reverse proxy (nginx) for SSL/TLS
4. Implementing backup strategies for volumes
5. Setting resource limits in docker-compose.yml

```yaml
services:
  paper2slides:
    # ... other config
    deploy:
      resources:
        limits:
          cpus: '2'
          memory: 4G
        reservations:
          cpus: '1'
          memory: 2G
```
