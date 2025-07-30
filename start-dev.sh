#!/bin/bash

# Finance Hub Development Environment Startup Script
# This script starts all necessary services for development

set -e

echo "🚀 Starting Finance Hub Development Environment..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo -e "${RED}❌ Docker is not running. Please start Docker first.${NC}"
    exit 1
fi

# Check if docker-compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo -e "${RED}❌ docker-compose is not installed. Please install it first.${NC}"
    exit 1
fi

# Function to wait for a service to be healthy
wait_for_service() {
    local service=$1
    local max_attempts=30
    local attempt=1
    
    echo -e "${BLUE}⏳ Waiting for $service to be healthy...${NC}"
    
    while [ $attempt -le $max_attempts ]; do
        if docker-compose ps | grep -q "$service.*healthy"; then
            echo -e "${GREEN}✅ $service is healthy!${NC}"
            return 0
        elif docker-compose ps | grep -q "$service.*running"; then
            # Service is running but not healthy yet
            sleep 2
        else
            echo -e "${YELLOW}⚠️  $service is not running. Starting...${NC}"
            docker-compose up -d $service
            sleep 5
        fi
        
        attempt=$((attempt + 1))
    done
    
    echo -e "${RED}❌ $service failed to become healthy after $max_attempts attempts${NC}"
    return 1
}

# Function to check Celery worker status
check_celery_status() {
    echo -e "${BLUE}🔍 Checking Celery worker status...${NC}"
    
    # Wait a bit for the worker to start
    sleep 5
    
    # Check health endpoint
    response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/banking/health/celery/ 2>/dev/null || echo "000")
    
    if [ "$response" = "200" ]; then
        echo -e "${GREEN}✅ Celery worker is healthy!${NC}"
        curl -s http://localhost:8000/api/banking/health/celery/ | python -m json.tool 2>/dev/null || true
    else
        echo -e "${YELLOW}⚠️  Celery worker health check returned status: $response${NC}"
        echo -e "${YELLOW}   Worker might still be starting up...${NC}"
    fi
}

# Navigate to project directory
cd "$(dirname "$0")"

# Stop any existing containers
echo -e "${BLUE}🛑 Stopping existing containers...${NC}"
docker-compose down

# Start infrastructure services first
echo -e "${BLUE}🏗️  Starting infrastructure services...${NC}"
docker-compose up -d db redis

# Wait for database and Redis to be healthy
wait_for_service "db"
wait_for_service "redis"

# Run database migrations
echo -e "${BLUE}🔄 Running database migrations...${NC}"
docker-compose run --rm backend python manage.py migrate

# Start backend and Celery services
echo -e "${BLUE}🚀 Starting backend services...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d backend celery_worker celery_beat

# Wait for backend to be ready
sleep 5

# Check Celery status
check_celery_status

# Start frontend
echo -e "${BLUE}🎨 Starting frontend...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d frontend

# Start optional development services
echo -e "${BLUE}🛠️  Starting development tools...${NC}"
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up -d flower

# Start dev profile services
docker-compose --profile dev up -d

# Display service URLs
echo -e "\n${GREEN}✨ Finance Hub is ready!${NC}"
echo -e "\n${BLUE}📍 Service URLs:${NC}"
echo -e "   Frontend:       ${GREEN}http://localhost:3000${NC}"
echo -e "   Backend API:    ${GREEN}http://localhost:8000${NC}"
echo -e "   Admin Panel:    ${GREEN}http://localhost:8000/admin${NC}"
echo -e "   Flower (Celery): ${GREEN}http://localhost:5555${NC}"
echo -e "   pgAdmin:        ${GREEN}http://localhost:5050${NC}"
echo -e "   Mailhog:        ${GREEN}http://localhost:8025${NC}"

echo -e "\n${BLUE}📊 Health Check:${NC}"
echo -e "   Celery Health:  ${GREEN}http://localhost:8000/api/banking/health/celery/${NC}"

echo -e "\n${BLUE}🔧 Useful Commands:${NC}"
echo -e "   View logs:      ${YELLOW}docker-compose logs -f [service]${NC}"
echo -e "   Stop all:       ${YELLOW}docker-compose down${NC}"
echo -e "   Restart service: ${YELLOW}docker-compose restart [service]${NC}"
echo -e "   Run tests:      ${YELLOW}docker-compose run --rm backend python manage.py test${NC}"
echo -e "   Shell access:   ${YELLOW}docker-compose exec backend bash${NC}"

echo -e "\n${GREEN}Happy coding! 🎉${NC}"

# Keep checking logs for important services
echo -e "\n${BLUE}📋 Following logs for key services...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop viewing logs (services will continue running)${NC}\n"

docker-compose logs -f backend celery_worker