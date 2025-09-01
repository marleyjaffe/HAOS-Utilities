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

---

## AppDaemon Installation

AppDaemon must be installed and configured *before* using this mapper utility. Choose one of the supported methods below to install AppDaemon on your system. For usage and configuration of this utility, see the sections that follow.

### **1. Docker**

A stable and popular AppDaemon container image is [`acockburn/appdaemon`](https://hub.docker.com/r/acockburn/appdaemon).
- **Start with Docker Compose:**
  ```yaml
  version: "3.7"
  services:
    appdaemon:
      image: acockburn/appdaemon:latest
      restart: unless-stopped
      container_name: appdaemon
      environment:
        - DASH_URL=http://localhost:5050
        - HA_URL=http://homeassistant:8123
        - TOKEN=your_long_lived_access_token
      volumes:
        - ./appdaemon_config:/conf      # <- persist ALL AppDaemon config, including apps/
      ports:
        - 5050:5050    # web UI (optional)
  ```
- Adjust `TOKEN` and targets as needed for your HA install.
- The `/conf` directory is *persisted and shared* for apps, configuration, and utility files.

### **2. Pip Install (Linux & Raspberry Pi OS)**

- **Recommended:** Use a Python virtual environment.
  ```sh
  sudo apt update
  sudo apt install python3 python3-venv python3-pip -y
  python3 -m venv ~/appdaemon-venv
  source ~/appdaemon-venv/bin/activate
  pip install wheel
  pip install appdaemon
  # Create a config dir (e.g. ~/appdaemon-config)
  mkdir -p ~/appdaemon-config
  ```
- Copy this utility app to `~/appdaemon-config/apps/`.
- Start AppDaemon:
  ```sh
  appdaemon -c ~/appdaemon-config
  ```

### **3. Pip Install (Windows)**

- **Recommended:** Use a virtual environment (`venv`) in PowerShell or Command Prompt.
  ```powershell
  py -3 -m venv %USERPROFILE%\appdaemon-venv
  %USERPROFILE%\appdaemon-venv\Scripts\activate
  pip install wheel
  pip install appdaemon
  mkdir %USERPROFILE%\appdaemon-config
  ```
- Copy this utility app to `%USERPROFILE%\appdaemon-config\apps\`
- Start AppDaemon:
  ```powershell
  appdaemon -c %USERPROFILE%\appdaemon-config
  ```

### **4. Home Assistant Add-On (Reference)**

If running Home Assistant OS/Supervised, install the official AppDaemon add-on ("AppDaemon 4" in Supervisor > Add-on Store).
**Follow the official [Home Assistant Add-on AppDaemon docs](https://github.com/hassio-addons/addon-appdaemon#readme)** for all details. See [AppDaemon docs](https://appdaemon.readthedocs.io/) for custom app placement/config specifics.

### **5. Running AppDaemon at Startup (Systemd/init.d)**

For advanced users wishing to run AppDaemon at system startup as a background service:

- **Systemd template** (`/etc/systemd/system/appdaemon.service`):
  ```
  [Unit]
  Description=AppDaemon service
  After=network.target

  [Service]
  Type=simple
  User=YOUR_USERNAME
  WorkingDirectory=/home/YOUR_USERNAME/appdaemon-config
  ExecStart=/home/YOUR_USERNAME/appdaemon-venv/bin/appdaemon -c /home/YOUR_USERNAME/appdaemon-config
  Restart=always

  [Install]
  WantedBy=multi-user.target
  ```
  - Replace `YOUR_USERNAME` and paths as needed.
  - Enable and start:
    ```sh
    sudo systemctl enable appdaemon
    sudo systemctl start appdaemon
    ```

- **init.d snippet** (legacy, use only if needed):
  Place an executable script in `/etc/init.d/appdaemon` that starts appdaemon as your user with correct env/venv and config. Reference [AppDaemon docs > Running as a Service](https://appdaemon.readthedocs.io/en/latest/INSTALL.html#running-as-a-service).

Full install/config instructions: [AppDaemon Documentation](https://appdaemon.readthedocs.io/en/latest/INSTALL.html)

## Containerized Usage with Built-In Docker Image

You can build and run this Z-Wave Entity Mapper utility in a self-contained Docker container using the supplied Dockerfile. This provides a reproducible, isolated AppDaemon environment containing the mapping scripts and all dependencies.

### 1. Build the Docker Image

```sh
docker build -t appdaemon-zwave-mapper .
```
- Run this in the project root directory (where the Dockerfile is present).
- The image includes AppDaemon installed in a dedicated Python venv.

### 2. Prepare a Configuration Directory

Create a local directory to persist your AppDaemon config, YAML mapping, and script state:
```sh
mkdir -p ./appdaemon_config
# (copy your existing config and 'apps/' here if needed)
```
On first run, the image provides defaults in `/app`, but you should use a mounted `/conf` volume for persistence and customization.

### 3. Run the Container

Example:

```sh
docker run -d \
  --name appdaemon-zwave-mapper \
  -p 5050:5050 -p 5051:5051 \
  -v "$(pwd)/appdaemon_config:/conf" \
  -e HA_URL=http://homeassistant:8123 \
  -e TOKEN=your_long_lived_access_token \
  appdaemon-zwave-mapper
```
- Adjust environment variables (`HA_URL`, `TOKEN`, etc.) as needed for your Home Assistant instance.
- The `/conf` directory inside the container is **where AppDaemon expects all config and apps**, and will persist all state, reports, and mapping files.
- Ports `5050` (main web UI) and `5051` (dashboard) are exposed by default.
- Use `-v` to map a **persistent config directory**.

### 4. Container Entry

The image starts AppDaemon using `/conf` as the config root. See AppDaemon documentation for extra runtime options (override the CMD as needed).

> **Note:** This image is distinct from the official [`acockburn/appdaemon`](https://hub.docker.com/r/acockburn/appdaemon) image and is designed for standalone Home Assistant utility mapping. You are responsible for secrets, network access, and config backups.

### 5. Update/Restart

To update code/config, rebuild the image and restart the container:
```sh
docker build -t appdaemon-zwave-mapper .
docker stop appdaemon-zwave-mapper && docker rm appdaemon-zwave-mapper
docker run ... # As above
```

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