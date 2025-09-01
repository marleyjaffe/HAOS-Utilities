# Z-Wave Entity Mapper & Migrator for Home Assistant (AppDaemon + Z-Wave JS)

Automate extraction, renaming, backup, and restoration of Z-Wave device entities and configuration in Home Assistant with robust logging, reporting, and YAML-driven mapping.

---

## Features

- Extracts all entity IDs and full attributes for a given Z-Wave device.
- Exports editable YAML mapping file - supports 1:1 and partial/sparse mapping (for different switch types/port counts).
- Renames new Z-Wave entities to user-specified names with validation, full logging, backup of states, and reporting of unmapped/surplus entities.
- Exports full device configuration (parameters) where supported by Z-Wave JS.
- Restores config/parameters to new device if models allow (with full reporting if some can't be mapped).
- Backs up all data, outputs human-friendly YAML operation reports.
- Fully logged/error reported at every step.

---

## Usage

### 1. Prerequisites

- [AppDaemon](https://appdaemon.readthedocs.io/) installed and configured with Home Assistant/HASS integration.
- Z-Wave JS integration enabled.

### 2. File Placement

- Place `apps/zwave_entity_mapper.py` and `apps/zwave_entity_mapping.yaml` in your AppDaemon `apps/` directory.
- Ensure backup subdir exists (default: `apps/zwave_backup/`).

### 3. AppDaemon Configuration Example

Add to your `apps/apps.yaml` (edit device IDs and mapping file path as needed):

```yaml
zwave_entity_mapper:
  module: zwave_entity_mapper
  class: ZWaveEntityMapper
  target_device_id: !your_original_zwave_device_id_here!
  mapping_file: zwave_entity_mapping.yaml
  backup_dir: zwave_backup
  report_file: last_run_report.yaml
  # Optional: For restoring config to a new device
  # restore_to_device_id: !new_zwave_device_id!
```

### 4. Initial Entity Extraction & YAML Export

- On first run, the script extracts all entities for the target device and outputs:
    - `zwave_entity_mapping.yaml` (edit this for mapping, see below)
    - Backup of all entity states
    - Z-Wave device config backup

### 5. Edit Mapping YAML

Example for 1-to-1 and partial (sparse) mapping:
```yaml
mappings:
  - current_entity: switch.old_switch_switch_1
    target_entity: switch.new_switch_switch_1
  - current_entity: switch.old_switch_switch_2
    target_entity: switch.new_switch_switch_2
  - current_entity: switch.old_switch_switch_3
    target_entity:
  - current_entity: switch.old_switch_switch_4
    target_entity:  # Not mapped (skipped)
```
- Leave `target_entity` blank/null for any source entity to skip mapping.

### 6. Entity Rename & Reporting

- Script will back up each entity state, validate no naming collisions, and perform renames via Home Assistant entity registry.
- Full YAML report written to e.g. `last_run_report.yaml`, including:
    - Which entities were renamed, errors, skipped, unmapped, and surplus entities

### 7. Z-Wave Device Config Backup/Restore

- Backs up all available config parameters via Z-Wave JS (as permitted by the integration).
- If `restore_to_device_id` is specified, attempts to restore all mapped parameters to the new device (skips parameters not present; errors are logged and reported).

--- 

## Flow Overview

1. Extract all entities and configuration for the selected Z-Wave JS device (`target_device_id`).
2. Write template YAML mapping (`zwave_entity_mapping.yaml`) for user edit.
3. Back up all entity states and Z-Wave device config.
4. If mapping file edited, process mapping to perform renames and report unmapped/surplus.
5. On request, restore device parameters to a new device (best effort).

---

## Limitations

- **Requires Home Assistant with Z-Wave JS and AppDaemon.**
- Entity renaming and config restore depend on capabilities of HA and Z-Wave JS APIs.
- Parameters/config may not be transferable between different device models/hardware.
- Some advanced or custom device parameters may not be exported/restored (limited by the integration).
- Home Assistant entity IDs must be unique—duplicate renames will be skipped and reported.
- Only entities assigned to a single Z-Wave device are considered.

---

## Output Files

- `zwave_entity_mapping.yaml` — editable mapping file for entity renames
- `zwave_backup/entity_backup_*.yaml` — state/attribute backup pre-rename
- `zwave_backup/zwave_device_config_*.yaml` — device configuration backup
- `last_run_report.yaml` — YAML summary of all script operations/results

---

## See Also

- [AppDaemon Documentation](https://appdaemon.readthedocs.io/)
- [Z-Wave JS Integration Docs](https://www.home-assistant.io/integrations/zwave_js/)

---

## Example Advanced Sparse Mapping

```yaml
# Only remap a subset; other old entities will be ignored:
mappings:
  - current_entity: sensor.old_battery
    target_entity: sensor.new_battery
  - current_entity: switch.old_1
    target_entity: switch.new_1
  - current_entity: switch.old_2
    target_entity:
  - current_entity: binary_sensor.old_contact
    target_entity:  # skipped entirely
```

---

For troubleshooting, check `last_run_report.yaml` and AppDaemon logs.