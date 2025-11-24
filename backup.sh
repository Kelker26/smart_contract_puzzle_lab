#!/bin/bash
BACKUP_DIR="backups"
mkdir -p $BACKUP_DIR
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
if [ -f "user_data.json" ]; then
    cp user_data.json "$BACKUP_DIR/user_data_$TIMESTAMP.json"
    echo "✓ Backup created: $BACKUP_DIR/user_data_$TIMESTAMP.json"
else
    echo "⚠ No user_data.json found to backup"
fi
