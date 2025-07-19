#!/bin/sh
set -e

# Debug: Show all environment variables
echo "Environment variables:"
env | grep -E "PORT|RAILWAY" || true

# Railway provides PORT as an environment variable
if [ -z "$PORT" ]; then
  echo "WARNING: PORT is not set. Using default port 3000"
  export PORT=3000
else
  echo "PORT is set to: $PORT"
fi

echo "Starting Next.js server on port $PORT"

# Execute the main command
exec "$@"