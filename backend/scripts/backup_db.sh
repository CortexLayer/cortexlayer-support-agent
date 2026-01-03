#!/bin/bash
set -e

echo "Starting database backup..."

DATE=$(date +%Y%m%d_%H%M%S)
BACKUP_DIR="/backups"
BACKUP_FILE="$BACKUP_DIR/db_$DATE.sql"

mkdir -p $BACKUP_DIR

# Dump database
pg_dump "$DATABASE_URL" > "$BACKUP_FILE"

# Upload to S3
aws s3 cp "$BACKUP_FILE" s3://cortexlayer-backups/db/

# Cleanup local backups older than 7 days
find $BACKUP_DIR -name "db_*.sql" -mtime +7 -delete

echo "Backup completed successfully: $BACKUP_FILE"
