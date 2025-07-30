#!/bin/bash

# Finance Hub Local Development Startup Script (No Docker)
# This script starts all services locally

set -e

echo "🚀 Starting Finance Hub Local Development..."

# Colors for output
GREEN='\033[0;32m'
BLUE='\033[0;34m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if Redis is running
if ! redis-cli ping > /dev/null 2>&1; then
    echo -e "${YELLOW}⚠️  Redis is not running. Starting Redis...${NC}"
    redis-server --daemonize yes
    sleep 2
fi

# Check if PostgreSQL is running
if ! pg_isready > /dev/null 2>&1; then
    echo -e "${RED}❌ PostgreSQL is not running. Please start PostgreSQL first.${NC}"
    echo -e "${YELLOW}   On macOS: brew services start postgresql${NC}"
    echo -e "${YELLOW}   On Ubuntu: sudo systemctl start postgresql${NC}"
    exit 1
fi

# Navigate to project directory
cd "$(dirname "$0")"

# Kill any existing processes
echo -e "${BLUE}🛑 Stopping any existing processes...${NC}"
pkill -f "celery -A core" || true
pkill -f "python manage.py runserver" || true
pkill -f "npm run dev" || true
sleep 2

# Backend setup
echo -e "${BLUE}🔧 Setting up backend...${NC}"
cd backend

# Create virtual environment if it doesn't exist
if [ ! -d "venv" ]; then
    echo -e "${BLUE}Creating virtual environment...${NC}"
    python3 -m venv venv
fi

# Activate virtual environment
source venv/bin/activate

# Install dependencies
echo -e "${BLUE}📦 Installing backend dependencies...${NC}"
pip install -r requirements.txt

# Run migrations
echo -e "${BLUE}🔄 Running database migrations...${NC}"
python manage.py migrate

# Create logs directory if it doesn't exist
mkdir -p logs

# Start Celery worker in background
echo -e "${BLUE}🔄 Starting Celery worker...${NC}"
celery -A core worker -l info -Q celery,banking,billing,reports,notifications --concurrency=2 > logs/celery_worker.log 2>&1 &
CELERY_PID=$!
echo -e "${GREEN}✅ Celery worker started (PID: $CELERY_PID)${NC}"

# Start Celery beat in background (optional)
echo -e "${BLUE}⏰ Starting Celery beat...${NC}"
celery -A core beat -l info > logs/celery_beat.log 2>&1 &
BEAT_PID=$!
echo -e "${GREEN}✅ Celery beat started (PID: $BEAT_PID)${NC}"

# Start Django development server in background
echo -e "${BLUE}🌐 Starting Django server...${NC}"
python manage.py runserver > logs/django.log 2>&1 &
DJANGO_PID=$!
echo -e "${GREEN}✅ Django server started (PID: $DJANGO_PID)${NC}"

# Frontend setup
cd ../frontend

# Install dependencies if needed
if [ ! -d "node_modules" ]; then
    echo -e "${BLUE}📦 Installing frontend dependencies...${NC}"
    npm install
fi

# Start frontend development server in background
echo -e "${BLUE}🎨 Starting frontend server...${NC}"
npm run dev > ../backend/logs/frontend.log 2>&1 &
FRONTEND_PID=$!
echo -e "${GREEN}✅ Frontend server started (PID: $FRONTEND_PID)${NC}"

# Wait for services to start
echo -e "${BLUE}⏳ Waiting for services to start...${NC}"
sleep 5

# Check Celery health
echo -e "${BLUE}🔍 Checking Celery health...${NC}"
response=$(curl -s -o /dev/null -w "%{http_code}" http://localhost:8000/api/banking/health/celery/ 2>/dev/null || echo "000")

if [ "$response" = "200" ]; then
    echo -e "${GREEN}✅ Celery is healthy!${NC}"
else
    echo -e "${YELLOW}⚠️  Celery health check returned: $response${NC}"
    echo -e "${YELLOW}   Check logs/celery_worker.log for details${NC}"
fi

# Create a stop script
cat > stop-local.sh << 'EOF'
#!/bin/bash
echo "🛑 Stopping Finance Hub services..."
pkill -f "celery -A core" || true
pkill -f "python manage.py runserver" || true
pkill -f "npm run dev" || true
echo "✅ All services stopped"
EOF
chmod +x stop-local.sh

# Display service info
echo -e "\n${GREEN}✨ Finance Hub is running!${NC}"
echo -e "\n${BLUE}📍 Service URLs:${NC}"
echo -e "   Frontend:       ${GREEN}http://localhost:3000${NC}"
echo -e "   Backend API:    ${GREEN}http://localhost:8000${NC}"
echo -e "   Admin Panel:    ${GREEN}http://localhost:8000/admin${NC}"
echo -e "   Health Check:   ${GREEN}http://localhost:8000/api/banking/health/celery/${NC}"

echo -e "\n${BLUE}📋 Log Files:${NC}"
echo -e "   Django:         ${YELLOW}backend/logs/django.log${NC}"
echo -e "   Celery Worker:  ${YELLOW}backend/logs/celery_worker.log${NC}"
echo -e "   Celery Beat:    ${YELLOW}backend/logs/celery_beat.log${NC}"
echo -e "   Frontend:       ${YELLOW}backend/logs/frontend.log${NC}"

echo -e "\n${BLUE}🔧 Commands:${NC}"
echo -e "   Stop all:       ${YELLOW}./stop-local.sh${NC}"
echo -e "   Django logs:    ${YELLOW}tail -f backend/logs/django.log${NC}"
echo -e "   Celery logs:    ${YELLOW}tail -f backend/logs/celery_worker.log${NC}"

echo -e "\n${YELLOW}⚠️  Services are running in background.${NC}"
echo -e "${YELLOW}   Use ./stop-local.sh to stop all services.${NC}"

# Follow Django logs
echo -e "\n${BLUE}📋 Following Django logs...${NC}"
echo -e "${YELLOW}Press Ctrl+C to stop viewing logs (services will continue running)${NC}\n"
cd backend
tail -f logs/django.log logs/celery_worker.log