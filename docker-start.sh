#!/bin/bash

# DYNERGY - Docker Quick Start Script
# This script helps test and validate your Docker setup

set -e  # Exit on error

echo "🐳 DYNERGY Docker Setup Validator"
echo "=================================="
echo ""

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if Docker is installed
echo "1️⃣  Checking Docker installation..."
if command -v docker &> /dev/null; then
    DOCKER_VERSION=$(docker --version)
    echo -e "${GREEN}✓${NC} Docker is installed: $DOCKER_VERSION"
else
    echo -e "${RED}✗${NC} Docker is not installed"
    echo "   Please install Docker Desktop from: https://www.docker.com/products/docker-desktop"
    exit 1
fi

# Check if Docker daemon is running
echo ""
echo "2️⃣  Checking Docker daemon..."
if docker info &> /dev/null; then
    echo -e "${GREEN}✓${NC} Docker daemon is running"
else
    echo -e "${RED}✗${NC} Docker daemon is not running"
    echo "   Please start Docker Desktop"
    exit 1
fi

# Check if docker-compose is available
echo ""
echo "3️⃣  Checking Docker Compose..."
if docker compose version &> /dev/null; then
    COMPOSE_VERSION=$(docker compose version)
    echo -e "${GREEN}✓${NC} Docker Compose is available: $COMPOSE_VERSION"
elif command -v docker-compose &> /dev/null; then
    COMPOSE_VERSION=$(docker-compose --version)
    echo -e "${GREEN}✓${NC} Docker Compose is available: $COMPOSE_VERSION"
    COMPOSE_CMD="docker-compose"
else
    echo -e "${RED}✗${NC} Docker Compose is not available"
    exit 1
fi

# Set compose command (newer docker compose vs older docker-compose)
if [ -z "$COMPOSE_CMD" ]; then
    COMPOSE_CMD="docker compose"
fi

# Check if required files exist
echo ""
echo "4️⃣  Checking required files..."
REQUIRED_FILES=("docker-compose.yml" "Dockerfile.backend" "Dockerfile.frontend" "nginx.conf" "requirements.txt" "app.py")
ALL_FILES_EXIST=true

for file in "${REQUIRED_FILES[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file exists"
    else
        echo -e "${RED}✗${NC} $file is missing"
        ALL_FILES_EXIST=false
    fi
done

if [ "$ALL_FILES_EXIST" = false ]; then
    echo ""
    echo -e "${RED}Some required files are missing. Please ensure all Docker configuration files are present.${NC}"
    exit 1
fi

# Check for port conflicts
echo ""
echo "5️⃣  Checking for port conflicts..."
PORTS_OK=true

if lsof -Pi :8000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠${NC}  Port 8000 is already in use (Backend port)"
    PORTS_OK=false
fi

if lsof -Pi :3000 -sTCP:LISTEN -t >/dev/null 2>&1 ; then
    echo -e "${YELLOW}⚠${NC}  Port 3000 is already in use (Frontend port)"
    PORTS_OK=false
fi

if [ "$PORTS_OK" = true ]; then
    echo -e "${GREEN}✓${NC} Ports 8000 and 3000 are available"
fi

# Offer to clean up existing containers
echo ""
echo "6️⃣  Checking for existing containers..."
if docker ps -a | grep -q "dynergy-"; then
    echo -e "${YELLOW}⚠${NC}  Found existing DYNERGY containers"
    read -p "   Do you want to remove them? (y/N) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "   Removing existing containers..."
        $COMPOSE_CMD down -v
        echo -e "${GREEN}✓${NC} Containers removed"
    fi
else
    echo -e "${GREEN}✓${NC} No existing containers found"
fi

# Ask if user wants to build and start
echo ""
echo "=================================="
echo "Pre-flight checks complete!"
echo ""
echo "Ready to build and start DYNERGY containers."
echo ""
echo "This will:"
echo "  • Build backend container (~5 minutes first time)"
echo "  • Build frontend container (~2 minutes first time)"
echo "  • Start both containers"
echo "  • Make application available at:"
echo "    - Frontend: http://localhost:3000"
echo "    - Backend:  http://localhost:8000"
echo "    - API Docs: http://localhost:8000/docs"
echo ""

read -p "Do you want to continue? (Y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Nn]$ ]]; then
    echo ""
    echo "🚀 Building and starting containers..."
    echo "   (This may take several minutes on first run)"
    echo ""
    
    # Build and start
    $COMPOSE_CMD up --build -d
    
    # Wait a bit for containers to start
    echo ""
    echo "⏳ Waiting for containers to be healthy..."
    sleep 5
    
    # Check container status
    echo ""
    echo "📊 Container Status:"
    $COMPOSE_CMD ps
    
    # Wait for backend to be ready
    echo ""
    echo "⏳ Waiting for backend to be ready..."
    MAX_ATTEMPTS=30
    ATTEMPT=0
    
    while [ $ATTEMPT -lt $MAX_ATTEMPTS ]; do
        if curl -s http://localhost:8000/health > /dev/null 2>&1; then
            echo -e "${GREEN}✓${NC} Backend is ready!"
            break
        fi
        ATTEMPT=$((ATTEMPT + 1))
        sleep 2
        echo -n "."
    done
    
    if [ $ATTEMPT -eq $MAX_ATTEMPTS ]; then
        echo ""
        echo -e "${YELLOW}⚠${NC}  Backend is taking longer than expected to start"
        echo "   Check logs with: $COMPOSE_CMD logs backend"
    fi
    
    # Final check
    echo ""
    echo "=================================="
    echo "🎉 DYNERGY is running!"
    echo ""
    echo "Access the application:"
    echo "  🌐 Frontend:     http://localhost:3000"
    echo "  🔧 Backend API:  http://localhost:8000"
    echo "  📚 API Docs:     http://localhost:8000/docs"
    echo ""
    echo "Useful commands:"
    echo "  View logs:       $COMPOSE_CMD logs -f"
    echo "  Stop:            $COMPOSE_CMD down"
    echo "  Restart:         $COMPOSE_CMD restart"
    echo "  Full cleanup:    $COMPOSE_CMD down -v"
    echo ""
    echo "Press Ctrl+C to stop watching logs, containers will keep running."
    echo ""
    
    # Follow logs
    $COMPOSE_CMD logs -f
else
    echo ""
    echo "Setup cancelled. You can manually start with:"
    echo "  $COMPOSE_CMD up --build"
fi
