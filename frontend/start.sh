#!/bin/sh
# Start script for Next.js standalone server

# Use PORT environment variable, default to 3000 if not set
export PORT=${PORT:-3000}

# Start the Next.js server
exec node server.js