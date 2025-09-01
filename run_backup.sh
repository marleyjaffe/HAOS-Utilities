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

# Create backup directory
mkdir -p /config/backups/entity_backups

# Run backup
echo "📦 Starting backup for Node $NODE_ID..."
# Run the backup script INSIDE the Home Assistant Core container
ha core exec -- python3 /config/entities_backup.py $NODE_ID

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