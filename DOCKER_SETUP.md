# Docker Setup Guide for DYNERGY Project

This guide explains the containerization setup for the DYNERGY Energy Tariff Comparison platform.

## 📦 Architecture Overview

The project uses a **multi-container architecture** with Docker Compose orchestrating two services:

### 1. Backend Container (`Dockerfile.backend`)
- **Base Image**: Python 3.11 slim
- **Purpose**: Runs the FastAPI application
- **Port**: 8000
- **Key Features**:
  - REST API for tariff calculations
  - Energy usage forecasting
  - Price data scraping
  - Data persistence via volumes

### 2. Frontend Container (`Dockerfile.frontend`)
- **Base Image**: Node 18 (build) → Nginx Alpine (serve)
- **Purpose**: Serves the Vue.js SPA
- **Port**: 80 (mapped to 3000 on host)
- **Key Features**:
  - Multi-stage build (optimized size)
  - Nginx serves static files
  - Automatic API proxying to backend
  - Production-ready configuration

## 🎯 Why Multi-Container?

### Advantages
1. **Separation of Concerns**: Each service has its own environment and dependencies
2. **Independent Scaling**: Can scale frontend and backend separately
3. **Development Efficiency**: Changes to one service don't require rebuilding both
4. **Production-Ready**: Mirrors production deployment architecture
5. **Clear Boundaries**: Better for academic presentation and grading

### Network Communication
- Containers communicate via Docker's internal network (`dynergy-network`)
- Frontend proxies API calls to backend using service name `http://backend:8000`
- External access: Frontend on port 3000, Backend on port 8000

## 🚀 Quick Start

### Build and Run
```bash
# Build and start all services
docker-compose up --build

# Or run in background (detached mode)
docker-compose up -d --build
```

### Stop Services
```bash
# Stop containers but keep data
docker-compose down

# Stop and remove volumes (clean slate)
docker-compose down -v
```

### View Logs
```bash
# All services
docker-compose logs -f

# Specific service
docker-compose logs -f backend
docker-compose logs -f frontend
```

## 📝 Container Details

### Backend (`dynergy-backend`)

**Build Context**: Project root  
**Dependencies**: 
- Python packages from `requirements.txt`
- System libraries (gcc, g++)

**Volume Mounts**:
- `./app_data:/app/app_data` - Market data and forecasts
- `./data:/app/data` - Analysis data

**Health Check**: 
- Endpoint: `http://localhost:8000/health`
- Interval: 30 seconds
- Useful for monitoring container status

**Entry Point**: 
```bash
uvicorn app:app --host 0.0.0.0 --port 8000
```

### Frontend (`dynergy-frontend`)

**Build Process** (Multi-stage):
1. **Stage 1 - Builder**:
   - Install Node.js dependencies
   - Build Vue.js application with Vite
   - Output: Static files in `dist/`

2. **Stage 2 - Server**:
   - Copy built files to Nginx
   - Apply custom Nginx configuration
   - Serve on port 80

**Nginx Configuration**:
- Serves Vue.js SPA from `/usr/share/nginx/html`
- Proxies `/api/*` requests to `http://backend:8000`
- Enables gzip compression
- Caches static assets (1 year)
- Security headers enabled

## 🔧 Configuration Files

### `docker-compose.yml`
Main orchestration file defining:
- Services (backend, frontend)
- Port mappings
- Volume mounts
- Networks
- Health checks
- Restart policies

### `Dockerfile.backend`
Backend container definition:
- Python 3.11 base
- System dependencies
- Python packages
- Application code
- Health check
- Start command

### `Dockerfile.frontend`
Frontend container definition:
- Multi-stage build
- Node.js build stage
- Nginx serving stage
- Optimized for production

### `nginx.conf`
Nginx web server configuration:
- SPA routing support
- API proxy configuration
- Caching strategy
- Compression settings
- Security headers

### `.dockerignore`
Excludes unnecessary files from Docker build:
- Node modules (rebuilt in container)
- Python cache
- Git files
- Development artifacts
- Analysis notebooks

## 🧪 Testing the Setup

After running `docker-compose up`, verify:

1. **Backend Health**:
   ```bash
   curl http://localhost:8000/health
   # Should return: {"status":"healthy",...}
   ```

2. **Backend API**:
   ```bash
   curl http://localhost:8000/api/tariffs
   # Should return tariff data
   ```

3. **Frontend**:
   - Open browser: http://localhost:3000
   - Should see DYNERGY interface

4. **Container Status**:
   ```bash
   docker-compose ps
   # Both services should show "Up" status
   ```

5. **Logs**:
   ```bash
   docker-compose logs backend | tail -20
   docker-compose logs frontend | tail -20
   ```

## 🛠️ Troubleshooting

### Backend won't start
```bash
# Check logs
docker-compose logs backend

# Common issues:
# - Missing dependencies → Check requirements.txt
# - Port already in use → Kill process on port 8000
# - Permission issues → Check volume mount permissions
```

### Frontend won't build
```bash
# Check build logs
docker-compose logs frontend

# Common issues:
# - npm install fails → Check package.json
# - Vite build fails → Check for syntax errors
# - Nginx won't start → Check nginx.conf syntax
```

### Containers can't communicate
```bash
# Verify network
docker network inspect project_energy_tariffs_dynergy-network

# Both containers should be listed
# Backend should be accessible as "backend" from frontend
```

### Data not persisting
```bash
# Check volume mounts
docker-compose config

# Verify volumes exist
docker volume ls

# Check permissions
ls -la app_data/ data/
```

## 🎓 For Grading/Presentation

### Starting Fresh
```bash
# Clean everything
docker-compose down -v
docker system prune -a

# Rebuild from scratch
docker-compose up --build
```

### Demonstrating the Architecture
1. Show `docker-compose.yml` - orchestration
2. Show `Dockerfile.backend` - backend containerization
3. Show `Dockerfile.frontend` - frontend multi-stage build
4. Show `nginx.conf` - production serving
5. Run `docker-compose up` - live demo
6. Show `docker-compose ps` - running services
7. Access application in browser

### Key Points for Professors
- ✅ Multi-container architecture (industry best practice)
- ✅ Separation of concerns (backend/frontend)
- ✅ Production-ready setup (Nginx serving, health checks)
- ✅ Data persistence (volume mounts)
- ✅ Easy to run (`docker-compose up`)
- ✅ Reproducible environment
- ✅ Well documented

## 📊 Resource Requirements

**Minimum**:
- CPU: 2 cores
- RAM: 4GB
- Disk: 5GB free

**Recommended**:
- CPU: 4 cores
- RAM: 8GB
- Disk: 10GB free

**Build Time** (first run):
- Backend: ~5 minutes
- Frontend: ~2 minutes
- Total: ~7 minutes

**Subsequent Starts**:
- ~10 seconds (using cached images)

## 🔄 Development Workflow

### Local Development (Without Docker)
```bash
# Use start.sh for rapid development
./start.sh
```

### Testing Changes in Docker
```bash
# Rebuild specific service
docker-compose up --build backend

# Or rebuild everything
docker-compose up --build
```

### Production Deployment
The same Docker setup can be used in production:
- Deploy to AWS ECS/Fargate
- Use Kubernetes
- Deploy to any Docker-compatible hosting
- Add reverse proxy (Traefik/Caddy)
- Add SSL certificates
- Configure environment variables

## 📚 Further Reading

- [Docker Documentation](https://docs.docker.com/)
- [Docker Compose Documentation](https://docs.docker.com/compose/)
- [Nginx Documentation](https://nginx.org/en/docs/)
- [FastAPI Deployment](https://fastapi.tiangolo.com/deployment/)
- [Vue.js Production Deployment](https://vuejs.org/guide/best-practices/production-deployment.html)

## 🐛 Common Issues

### Port Already in Use
```bash
# Find process using port 8000
lsof -i :8000

# Kill it
kill -9 <PID>
```

### Docker Daemon Not Running
```bash
# Start Docker Desktop (macOS/Windows)
# Or on Linux:
sudo systemctl start docker
```

### Permission Denied
```bash
# Add user to docker group (Linux)
sudo usermod -aG docker $USER

# Logout and login again
```

### Out of Disk Space
```bash
# Clean up Docker
docker system prune -a --volumes

# Remove unused images
docker image prune -a
```

## ✅ Checklist for Submission

Before submitting your project:

- [ ] `docker-compose up` works on fresh clone
- [ ] Both containers start successfully
- [ ] Frontend accessible at http://localhost:3000
- [ ] Backend accessible at http://localhost:8000
- [ ] API documentation available at http://localhost:8000/docs
- [ ] Health check returns healthy status
- [ ] README.md has clear Docker instructions
- [ ] All configuration files committed to Git
- [ ] No hardcoded credentials or sensitive data
- [ ] Logs show no critical errors
- [ ] Sample data included for testing

## 📞 Support

If you encounter issues:
1. Check this guide first
2. Review Docker logs: `docker-compose logs`
3. Verify Docker is running: `docker --version`
4. Check system resources: `docker system df`
5. Try clean rebuild: `docker-compose down -v && docker-compose up --build`

---

**Last Updated**: November 2025  
**Docker Compose Version**: 3.8  
**Tested On**: Docker Desktop 4.x (macOS/Windows), Docker Engine 24.x (Linux)
