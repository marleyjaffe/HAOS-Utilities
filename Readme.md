# Z-Wave Entity Mapper & Migrator for Home Assistant (AppDaemon + Z-Wave JS)

Automate extraction, renaming, backup, and restoration of Z-Wave device entities and configuration in Home Assistant with robust logging, reporting, and YAML-driven mapping.

---

## Installation: Home Assistant AppDaemon Add-on

This utility is designed to run as an AppDaemon app using the official AppDaemon Home Assistant add-on. Other installation types (Docker, pip, Python venv, etc.) are not covered here—refer to [AppDaemon documentation](https://appdaemon.readthedocs.io/en/latest/INSTALL.html) for advanced/manual setups.

### 1. Install the AppDaemon Add-On

1. In Home Assistant, go to **Settings** > **Add-ons**.
2. Click **Add-on Store**.
3. Find and install the official **AppDaemon 4** add-on ([docs](https://github.com/hassio-addons/addon-appdaemon#readme)).
4. Once installed, open the add-on and start it for initial setup (set any basic options as needed for your instance).

### 2. Prepare the Directory Structure

1. In your Home Assistant config folder (where `configuration.yaml` is located), ensure an `apps` directory exists:
   - If not, create it: `apps/`
2. Inside `apps/`, copy the following files:
   - `zwave_entity_mapper.py`
   - `zwave_entity_mapping.yaml`
3. (Recommended) Create a backup subdirectory for state/config backups:
   - `apps/zwave_backup/`
4. For the HADashboard UI, ensure the following directory exists:
   - `apps/dashboards/`
5. Copy the dashboard YAML:
   - Copy `dashboards/zwave_entity_mapper.dash` into `apps/dashboards/`.

### 3. App Setup

1. Edit your `apps.yaml` (located in `apps/`):
   - Add a new entry for the Z-Wave Entity Mapper (see Usage section below for a sample configuration).
2. Configure `target_device_id`, mapping file path, backup location, and any other settings as needed.

### 4. Restart AppDaemon Add-on

- After copying or updating any utility files or configurations, **restart the AppDaemon add-on** from the HA add-ons dashboard.
  - This ensures your app and dashboards are loaded and active.

### 5. Accessing HADashboard

- Open: `http://<your-home-assistant-host>:5050/zwave_entity_mapper`
  - Replace `<your-home-assistant-host>` with the hostname or IP of your HA instance.
- The default dashboard port is `5050`.
- If authentication (username/password) is enabled in AppDaemon, you will be prompted to log in.

#### First-time Tips & Authentication

- On first run, the `zwave_entity_mapper` app will:
  - Extract available Z-Wave device entities to a mapping YAML.
  - Create backup files in the specified backup directory.
- **If you update mapping or app files in `apps/`, always restart the AppDaemon add-on** for changes to take effect.
- To avoid permission issues, copy/update files using the same user as HA (often via Samba, SSH, or the VSCode add-on).
- For advanced or manual installation (Docker, pip, etc.), see the [AppDaemon documentation](https://appdaemon.readthedocs.io/en/latest/INSTALL.html).

---

## Usage

### 1. Prerequisites

- [AppDaemon](https://appdaemon.readthedocs.io/) Home Assistant add-on installed and running.
- Z-Wave JS integration enabled.

### 2. File Placement

- Place `zwave_entity_mapper.py` and `zwave_entity_mapping.yaml` in the `apps/` directory of your HA config.
- Ensure a backup subdir exists: `apps/zwave_backup/`.

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
    - `zwave_entity_mapping.yaml` (edit this file for mapping, see below)
    - A backup of all entity states
    - Z-Wave device config backup

### 5. Edit Mapping YAML

Sample mapping:

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

- Leave `target_entity` blank/null for any entity you don't wish to map.

### 6. Entity Rename & Reporting

- Script will back up each entity state, validate no naming collisions, and perform renames via Home Assistant entity registry.
- Full YAML report written to e.g. `last_run_report.yaml`, including:
    - Entities renamed
    - Errors, skipped, unmapped, and surplus entities

### 7. Z-Wave Device Config Backup/Restore

- Backs up all available config parameters via Z-Wave JS.
- If `restore_to_device_id` is specified, attempts to restore all mapped parameters to the new device and logs any skipped parameters.

---

## HADashboard Interface

A simple web dashboard is included for direct operation and result viewing via AppDaemon's HADashboard. This provides a point-and-click UI for export, import, backup, and restore actions as well as live feedback/status.

### Enabling the Dashboard

1. **Copy the dashboard YAML:**
   - Place `apps/dashboards/zwave_entity_mapper.dash` into `apps/dashboards/`.
2. **Ensure the utility app (`zwave_entity_mapper.py`) is enabled and running in AppDaemon.**
   - All sensor and trigger states are handled automatically.
3. **Access the dashboard UI:**
   - Open `http://<your-home-assistant-host>:5050/zwave_entity_mapper` in your browser.
   - Dashboard port defaults to `5050`.
   - If authentication is configured, log in with your AppDaemon dashboard credentials.

### Dashboard Features

- **Operation Buttons:**
  - **Export Entities:** Generates/refreshes the mapping YAML with all current Z-Wave entities for the configured device.
  - **Import Mapping:** Applies the mapping file and initiates migration/renaming per mapping.
  - **Backup Config:** Backs up all entity states and device configuration.
  - **Restore Config:** Attempts to restore parameters/config to a "restore to" device (see AppDaemon app args).

- **Live Output Widgets:**
  - **Status:** Shows the current operation or idle state.
  - **Message:** Shows success/error details after each operation.
  - **Migration Summary:** Shows number of unmapped entities, error count, and last run time.

#### Dashboard Entity Mapping

- Dashboard actions are triggered via these sensors:
  - `sensor.zem_dashboard_export_trigger`
  - `sensor.zem_dashboard_import_trigger`
  - `sensor.zem_dashboard_backup_trigger`
  - `sensor.zem_dashboard_restore_trigger`
- Output sensors:
  - `sensor.zem_dashboard_status`
  - `sensor.zem_dashboard_message`
  - `sensor.zem_dashboard_summary`
- These are managed automatically by the AppDaemon utility.

#### Notes

- If you've enabled authentication in AppDaemon (`api_password`, etc.), you must log in via the dashboard URL.
- All dashboard operations and output files remain available in your AppDaemon config directory for advanced/manual use.
- For customizations, edit the dashboard YAML as desired.

---

## Flow Overview

1. Extract all entities and configuration for the selected Z-Wave JS device (`target_device_id`).
2. Write template YAML mapping (`zwave_entity_mapping.yaml`) for user edit.
3. Back up all entity states and Z-Wave device config.
4. If mapping file edited, process mapping to perform renames and report unmapped/surplus.
5. On request, restore device parameters to a new device (best effort).

---

## Limitations

- **Requires Home Assistant with Z-Wave JS and AppDaemon Add-On.**
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