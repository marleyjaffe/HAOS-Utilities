# restore_entities.py
import json
import asyncio
import sys
from pathlib import Path

class HAEntityRestore:
    def __init__(self, config_path="/config"):
        self.config_path = Path(config_path)
        self.backup_dir = self.config_path / "backups" / "entity_backups"
    
    async def restore_entities(self, backup_file: Path, node_id: int):
        sys.path.insert(0, '/usr/src/homeassistant')
        from homeassistant.core import HomeAssistant
        from homeassistant.helpers.entity_registry import async_get as async_get_registry
        from homeassistant.bootstrap import async_setup_hass
        from homeassistant.config import load_yaml_config_file
        
        # Load backup
        with open(backup_file) as f:
            backup_data = json.load(f)
        
        # Initialize HA
        config_dir = str(self.config_path)
        hass = HomeAssistant(config_dir)
        
        try:
            config = await load_yaml_config_file(self.config_path / "configuration.yaml")
        except:
            config = {}
        
        await async_setup_hass(hass, config)
        await hass.async_start()
        
        entity_registry = async_get_registry(hass)
        restored_count = 0
        
        for entity_data in backup_data['entities']:
            entity_id = entity_data['entity_id']
            
            # Check if entity exists
            if hass.states.get(entity_id):
                # Restore customizations
                if entity_data.get('customizations'):
                    hass.data.setdefault('customize', {})[entity_id] = entity_data['customizations']
                
                # Update entity registry
                entry = entity_registry.async_get(entity_id)
                if entry and entity_data.get('registry_name'):
                    entity_registry.async_update_entity(
                        entity_id,
                        name=entity_data['registry_name'],
                        icon=entity_data.get('registry_icon')
                    )
                
                restored_count += 1
        
        await hass.async_stop()
        return restored_count

async def restore_main():
    if len(sys.argv) != 2:
        print("Usage: python restore_entities.py <node_id>")
        sys.exit(1)
    
    node_id = int(sys.argv[1])
    restore_tool = HAEntityRestore()
    backup_file = restore_tool.backup_dir / f'node_{node_id}_backup.json'
    
    if not backup_file.exists():
        print(f"❌ Backup file not found: {backup_file}")
        sys.exit(1)
    
    print(f"Restoring entities for Node {node_id}...")
    restored = await restore_tool.restore_entities(backup_file, node_id)
    print(f"✅ Restored {restored} entities")

if __name__ == "__main__":
    asyncio.run(restore_main())