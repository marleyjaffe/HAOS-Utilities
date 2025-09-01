### 🏠 Home Assistant Z-Wave JS Entity Backup Tool
=============================================
📦 Starting backup for Node 15...
Starting backup for Z-Wave JS Node 15...
✅ Backup completed successfully!
📁 Backup saved to: /config/backups/entity_backups/node_15_backup.json
📊 Entities backed up: 8

📋 Backup Summary:
├── Node ID: 15
├── Backup Location: /config/backups/entity_backups/
└── Files: node_15_backup.json

Next steps:
1. Perform Z-Wave JS Replace Node operation
2. Wait for device interview completion  
3. Run: python3 /config/restore_entities.py 15 (if needed)

## SSH Execution Guide 
# 1. SSH into Home Assistant
ssh root@homeassistant.local

# 2. Navigate to config directory
cd /config

# 3. Upload the Python files
# (Use scp, SFTP, or File Editor add-on)

# 4. Make run script executable
chmod +x run_backup.sh

# 5. Execute backup (replace 15 with your node ID)
./run_backup.sh 15

## Backup File Structure  
{
  "timestamp": 1699123456.789,
  "node_id": 15,
  "entity_count": 8,
  "entities": [
    {
      "entity_id": "switch.power_strip_outlet_1",
      "domain": "switch",
      "object_id": "power_strip_outlet_1",
      "state": "off",
      "attributes": {
        "friendly_name": "Living Room Lamp",
        "icon": "mdi:lamp"
      },
      "friendly_name": "Living Room Lamp",
      "node_id": 15,
      "registry_name": "Living Room Lamp",
      "platform": "zwave_js"
    }
  ]
}