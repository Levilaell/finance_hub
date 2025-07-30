#!/bin/bash
echo "🛑 Stopping Finance Hub services..."
pkill -f "celery -A core" || true
pkill -f "python manage.py runserver" || true
pkill -f "npm run dev" || true
echo "✅ All services stopped"
