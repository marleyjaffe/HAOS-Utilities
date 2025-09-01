#!/bin/bash
# run_backup.sh
set -e

NODE_ID=$1

if [ -z "$NODE_ID" ]; then
    echo "Usage: ./run_backup.sh <node_id>"
    echo "Example: ./run_backup.sh 15"
    exit 1
fi

echo "🏠 Home Assistant Z-Wave JS Entity Backup Tool"
echo "============================================="

# Container environment check removed. This script can now be safely run from the HAOS host (SSH/Terminal add-on shell).
# Python commands will be executed inside the Home Assistant Core container using 'ha core exec'.

# Create backup directory INSIDE the Home Assistant Core container
# Fix: Ensure the backup folder is created where Home Assistant Core expects it.
ha core exec -- mkdir -p /config/backups/entity_backups

# Run backup
echo "📦 Starting backup for Node $NODE_ID..."
# Fix: Carefully quote the python command so it is passed as a single argument string to 'ha core exec'.
# This ensures '$NODE_ID' is expanded on the host, but the *entire* command (including the argument) is invoked within the HA container.
# Add error detection: If the backup command fails or returns nonzero, exit immediately and print an error.
set +e
CMD="ha core exec -- /bin/sh -c \"python3 /config/entities_backup.py '$NODE_ID'\""
echo "🔎 Running backup command: $CMD"
ha core exec -- /bin/sh -c "python3 /config/entities_backup.py '$NODE_ID'"
HA_EXIT_CODE=$?
set -e

if [ $HA_EXIT_CODE -ne 0 ]; then
    echo "❌ Backup command failed: ha core exec exited with status $HA_EXIT_CODE"
    echo "Aborting. Backup was NOT created."
    exit 2
fi

# Validation: Confirm the backup file exists from the host after running ha core exec.
BACKUP_PATH="/config/backups/entity_backups/node_${NODE_ID}_backup.json"
if ! [ -f "$BACKUP_PATH" ]; then
    echo "❌ Backup failed: Expected backup file not found at $BACKUP_PATH"
    echo "Aborting. No backup summary shown."
    exit 3
fi

# Only show backup summary if previous steps succeeded and backup file exists.
echo ""
echo "📋 Backup Summary:"
echo "├── Node ID: $NODE_ID"
echo "├── Backup Location: /config/backups/entity_backups/"
echo "└── Files: node_${NODE_ID}_backup.json"
echo ""
echo "Next steps:"
echo "1. Perform Z-Wave JS Replace Node operation"
echo "2. Wait for device interview completion"
# If restoration is needed, run the restore script inside the Home Assistant Core container from the host shell like this:
echo "3. Run: ha core exec -- python3 /config/restore_entities.py \$NODE_ID (if needed)"