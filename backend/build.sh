#!/usr/bin/env bash

# Exit immediately if a command exits with a non-zero status
set -o errexit

echo "========================================"
echo "Starting Render build"
echo "========================================"

# Install Python dependencies
echo "Installing dependencies..."
pip install -r requirements.txt

# Run Django migrations
echo "Running Django migrations..."
python manage.py migrate --no-input

# Create or update production admin
echo "Configuring production admin..."

if [ -n "${ADMIN_USERNAME:-}" ] && [ -n "${ADMIN_PASSWORD:-}" ]; then
    python manage.py create_admin \
        --username "$ADMIN_USERNAME" \
        --email "${ADMIN_EMAIL:-}" \
        --password "$ADMIN_PASSWORD"
else
    echo "WARNING: ADMIN_USERNAME or ADMIN_PASSWORD is not configured."
    echo "Skipping admin account setup."
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --no-input

# Synchronize existing portfolio data with MongoDB Atlas
echo "Synchronizing portfolio data..."
python manage.py import_existing_data

echo "========================================"
echo "Build completed successfully"
echo "========================================"
