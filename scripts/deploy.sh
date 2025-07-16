#!/bin/bash

# Finance Management App - Deployment Script
# This script automates the deployment process

set -e  # Exit on error

echo "🚀 Starting Finance Management App Deployment..."

# Color codes for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[✓]${NC} $1"
}

print_error() {
    echo -e "${RED}[✗]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[!]${NC} $1"
}

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    print_error "Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    print_error "Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Environment selection
echo "Select deployment environment:"
echo "1) Development (includes pgAdmin, Mailhog)"
echo "2) Production"
read -p "Enter choice [1-2]: " ENV_CHOICE

case $ENV_CHOICE in
    1)
        COMPOSE_PROFILES="dev"
        ENV_FILE=".env.development"
        print_status "Development environment selected"
        ;;
    2)
        COMPOSE_PROFILES=""
        ENV_FILE=".env.production"
        print_status "Production environment selected"
        ;;
    *)
        print_error "Invalid choice"
        exit 1
        ;;
esac

# Check for backend .env file
if [ ! -f "backend/.env" ]; then
    if [ -f "backend/.env.example" ]; then
        print_warning "No .env file found. Creating from .env.example..."
        cp backend/.env.example backend/.env
        print_warning "Please update backend/.env with your configuration"
        read -p "Press enter to continue after updating .env file..."
    else
        print_error "No .env or .env.example file found in backend/"
        exit 1
    fi
fi

# Create required directories
print_status "Creating required directories..."
mkdir -p backend/staticfiles
mkdir -p backend/media
mkdir -p logs

# Build Docker images
print_status "Building Docker images..."
docker-compose build

# Start services
print_status "Starting services..."
if [ "$COMPOSE_PROFILES" = "dev" ]; then
    docker-compose --profile dev up -d
else
    docker-compose up -d
fi

# Wait for database to be ready
print_status "Waiting for database to be ready..."
sleep 10

# Run database migrations
print_status "Running database migrations..."
docker-compose exec backend python manage.py migrate

# Create default categories
print_status "Creating default categories..."
docker-compose exec backend python manage.py create_default_categories || true

# Seed plans (if command exists)
print_status "Seeding subscription plans..."
docker-compose exec backend python manage.py seed_plans || true

# Collect static files
print_status "Collecting static files..."
docker-compose exec backend python manage.py collectstatic --noinput

# Create superuser (optional)
read -p "Do you want to create a superuser? (y/n): " CREATE_SUPERUSER
if [ "$CREATE_SUPERUSER" = "y" ]; then
    docker-compose exec backend python manage.py createsuperuser
fi

# Show running services
print_status "Deployment complete! Services running:"
docker-compose ps

echo ""
echo "🎉 Deployment successful!"
echo ""
echo "Access the application at:"
echo "  - Frontend: http://localhost:3000"
echo "  - Backend API: http://localhost:8000"
echo "  - Django Admin: http://localhost:8000/admin"

if [ "$COMPOSE_PROFILES" = "dev" ]; then
    echo "  - pgAdmin: http://localhost:5050 (admin@financeapp.com / admin)"
    echo "  - Mailhog: http://localhost:8025"
fi

echo ""
echo "To stop the services, run: docker-compose down"
echo "To view logs, run: docker-compose logs -f [service_name]"