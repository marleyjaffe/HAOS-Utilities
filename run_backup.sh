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

# Check if running in HA container
if [ ! -d "/usr/src/homeassistant" ]; then
    echo "❌ Error: Must run from Home Assistant container"
    echo "SSH into Home Assistant and try again"
    exit 1
fi

# Create backup directory
mkdir -p /config/backups/entity_backups

# Run backup
echo "📦 Starting backup for Node $NODE_ID..."
python3 /config/entities_backup.py $NODE_ID

echo ""
echo "📋 Backup Summary:"
echo "├── Node ID: $NODE_ID"
echo "├── Backup Location: /config/backups/entity_backups/"
echo "└── Files: node_${NODE_ID}_backup.json"
echo ""
echo "Next steps:"
echo "1. Perform Z-Wave JS Replace Node operation"
echo "2. Wait for device interview completion"
echo "3. Run: python3 /config/restore_entities.py $NODE_ID (if needed)"