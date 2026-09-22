#!/usr/bin/env bash
# Exit immediately if a command exits with a non-zero status
set -o errexit

# Install Python dependencies
pip install -r requirements.txt

# Run migrations for Django internal auth and session database
python manage.py migrate --no-input


python manage.py create_admin \
  --username "$ADMIN_USERNAME" \
  --email "$ADMIN_EMAIL" \
  --password "$ADMIN_PASSWORD"

# Collect static assets
python manage.py collectstatic --no-input

# Synchronize/migrate portfolio data into MongoDB Atlas idempotently
python manage.py import_existing_data
