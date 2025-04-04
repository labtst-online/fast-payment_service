#!/bin/sh

# Exit immediately if a command exits with a non-zero status.
set -e

echo "Waiting for database to be ready..."
# Add a check here if needed, e.g., using pg_isready or netcat
# Example using pg_isready (requires postgresql-client installed in container):
# until pg_isready -h $POSTGRES_SERVER -p $POSTGRES_PORT -U $POSTGRES_USER -d $POSTGRES_DB; do
#   echo >&2 "Postgres is unavailable - sleeping"
#   sleep 1
# done
# echo >&2 "Postgres is up - continuing..."

echo "Running database migrations..."
# Ensure Alembic uses the correct config (usually auto-detected via alembic.ini)
alembic upgrade head

echo "Migrations finished."

# Now execute the main container command (passed as arguments to this script)
# This allows CMD in Dockerfile or command in docker-compose to still work
exec "$@"
