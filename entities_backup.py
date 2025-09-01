# entities_backup.py
import json
import asyncio
import sys
import os
from pathlib import Path

class HAEntityBackup:
    def __init__(self, config_path="/config"):
        self.config_path = Path(config_path)
        self.backup_dir = self.config_path / "backups" / "entity_backups"
        self.backup_dir.mkdir(parents=True, exist_ok=True)
    
    async def backup_entities(self, node_id: int):
        try:
            # Import HA components
            sys.path.insert(0, '/usr/src/homeassistant')
            from homeassistant.core import HomeAssistant
            from homeassistant.config import load_yaml_config_file
            from homeassistant.helpers.entity_registry import async_get as async_get_registry
            from homeassistant.helpers.device_registry import async_get as async_get_device_registry
            from homeassistant.bootstrap import async_setup_hass
            
            # Initialize minimal HA instance
            config_dir = str(self.config_path)
            hass = HomeAssistant(config_dir)
            
            # Load configuration
            try:
                config = await load_yaml_config_file(self.config_path / "configuration.yaml")
            except Exception as e:
                print(f"Warning: Could not load config: {e}")
                config = {}
            
            # Setup core components
            await async_setup_hass(hass, config)
            await hass.async_start()
            
            # Get entity registry
            entity_registry = async_get_registry(hass)
            device_registry = async_get_device_registry(hass)
            
            # Find Z-Wave JS entities for specific node
            node_entities = []
            zwave_pattern = f"node_{node_id}"
            
            # Get all states
            all_states = hass.states.async_all()
            
            for state in all_states:
                entity_id = state.entity_id
                
                # Check if entity belongs to target node
                if (zwave_pattern in entity_id or 
                    any(zwave_pattern in str(attr) for attr in state.attributes.values() if isinstance(attr, str))):
                    
                    # Get entity registry entry
                    entity_entry = entity_registry.async_get(entity_id)
                    
                    entity_data = {
                        'entity_id': entity_id,
                        'domain': entity_id.split('.')[0],
                        'object_id': entity_id.split('.')[1],
                        'state': state.state,
                        'attributes': dict(state.attributes),
                        'friendly_name': state.attributes.get('friendly_name', entity_id),
                        'icon': state.attributes.get('icon'),
                        'device_class': state.attributes.get('device_class'),
                        'unit_of_measurement': state.attributes.get('unit_of_measurement'),
                        'customizations': hass.data.get('customize', {}).get(entity_id, {}),
                        'node_id': node_id
                    }
                    
                    # Add entity registry info if available
                    if entity_entry:
                        entity_data.update({
                            'registry_name': entity_entry.name,
                            'registry_icon': entity_entry.icon,
                            'disabled': entity_entry.disabled,
                            'device_id': entity_entry.device_id,
                            'area_id': entity_entry.area_id,
                            'platform': entity_entry.platform
                        })
                    
                    node_entities.append(entity_data)
            
            # Save backup
            backup_file = self.backup_dir / f'node_{node_id}_backup.json'
            
            backup_data = {
                'timestamp': hass.loop.time(),
                'node_id': node_id,
                'entity_count': len(node_entities),
                'entities': node_entities
            }
            
            with open(backup_file, 'w') as f:
                json.dump(backup_data, f, indent=2, default=str)
            
            await hass.async_stop()
            
            return backup_file, len(node_entities)
            
        except Exception as e:
            print(f"Error during backup: {e}")
            if 'hass' in locals():
                await hass.async_stop()
            raise

async def main():
    if len(sys.argv) != 2:
        print("Usage: python entities_backup.py <node_id>")
        print("Example: python entities_backup.py 15")
        sys.exit(1)
    
    try:
        node_id = int(sys.argv[1])
    except ValueError:
        print("Error: Node ID must be an integer")
        sys.exit(1)
    
    backup_tool = HAEntityBackup()
    
    print(f"Starting backup for Z-Wave JS Node {node_id}...")
    
    try:
        backup_file, entity_count = await backup_tool.backup_entities(node_id)
        print(f"✅ Backup completed successfully!")
        print(f"📁 Backup saved to: {backup_file}")
        print(f"📊 Entities backed up: {entity_count}")
        
    except Exception as e:
        print(f"❌ Backup failed: {e}")
        sys.exit(1)

if __name__ == "__main__":
    asyncio.run(main())