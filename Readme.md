# Z-Wave Node Backup App for AppDaemon & Home Assistant

## Overview

The `zwave_node_backup.py` AppDaemon app provides an automated workflow to trigger, manage, and store backup files for individual Z-Wave nodes in a Home Assistant environment. It is designed to simplify the routine backup of Z-Wave nodes, integrating with ancillary scripts (notably [`entities_backup.py`](entities_backup.py:1)) for robust device/state preservation. This enables routine save-points before network changes, troubleshooting, or migration—improving reliability and disaster recovery for Home Assistant users utilizing Z-Wave.

## Prerequisites

- **Home Assistant** instance (tested with Supervisor and Core installations).
- **AppDaemon** installed, configured, and connected to your Home Assistant instance ([AppDaemon docs](https://appdaemon.readthedocs.io/)).
- **Python 3**. The app and supporting scripts require a working Python 3 installation.
- **File system access**:
  - The user running AppDaemon must have read/write permissions in the backup script locations and the target backup storage directories.
- **Location of Supporting Script**:
  - Ensure [`entities_backup.py`](entities_backup.py:1) is present in the same directory as this app or update its import path in [`zwave_node_backup.py`](zwave_node_backup.py:1).
  - Both scripts must be accessible by the AppDaemon application environment.

## Installation

1. **Copy App Files**:
   - Place [`zwave_node_backup.py`](zwave_node_backup.py:1) and [`entities_backup.py`](entities_backup.py:1) into the `apps` directory of your AppDaemon configuration (commonly `~/.homeassistant/appdaemon/apps/`).
2. **Update AppDaemon config**:
   - Edit your `apps.yaml` (or equivalent app configuration file) to register the app and set options. See configuration below.
3. **Restart AppDaemon**:
   - After saving changes, restart AppDaemon for the new app to be loaded.

## Configuration

### 1. Via `apps.yaml`

Add a configuration for `zwave_node_backup` in your AppDaemon `apps.yaml`:

```yaml
zwave_node_backup:
  module: zwave_node_backup
  class: ZWaveNodeBackup
  node_id: 5                 # REQUIRED: Node ID of the Z-Wave device to backup
  backup_dir: /config/backups # OPTIONAL: Directory where backups will be stored
  notify_service: notify.mobile_app_yourdevice  # OPTIONAL: Home Assistant notification service to use
```

- `node_id`: Z-Wave node number you wish to back up (see Z-Wave integration panel for list of nodes).
- `backup_dir`: (optional) Override default backup location. Must be accessible by AppDaemon.
- `notify_service`: (optional) Notification target for success/failure messages.

### 2. Via Service Call (If Supported)

If the script provides a Home Assistant service for backup, you can trigger backups for specific nodes dynamically (see Usage below). Otherwise, adjust the config and reload AppDaemon.

## Usage

### Initiate a Backup

- **Automatic**: If scheduled or triggered by configuration, the backup will run for the node configured in `apps.yaml`.
- **Manual Service Call** (if implemented): Use Home Assistant’s Developer Tools to call the relevant AppDaemon service, passing the `node_id` parameter.

#### Example Service Call

```yaml
service: appdaemon.call_service
data:
  app: zwave_node_backup
  service: backup_node
  node_id: 5
```

### Output and Result Notifications

- **Backup Location**: Backup files will be stored in the directory specified by `backup_dir` (default is typically under `/config/backups/`).
- **Logging**: AppDaemon logs will show detailed steps, errors, and results of each backup operation.
- **Notifications**: If `notify_service` is set, the app will push notifications about success or failure to the specified Home Assistant device.
- **Backup artifacts**: Typically `.json` or `.tar` files named with the Z-Wave node ID and timestamp.

## Success & Failure Interpretation

- **On Success**:
  - A notification (`notify_service`) and log entry confirms the backup file creation.
  - The backup file is saved with a matching timestamp and node ID.
  - Next steps: Optionally verify the file exists and matches expected size/format.
- **On Failure**:
  - Notification and/or log entry will indicate the type of failure (e.g. "Node ID not found", "File system write error", "entities_backup.py not found", etc).
  - Review the log details and check all prerequisites (especially node ID validity, permissions, and scripts’ presence).

## Next Steps After Backup

- Download the backup file(s) and store them safely offline for redundancy.
- For restoration, refer to the unbackup or restore script (e.g. [`restore_entities.py`](restore_entities.py:1)) and follow its documentation.
- Test newly restored states on a test node or during maintenance windows whenever possible.

## Troubleshooting

**Common Errors & Resolutions:**

| Error/Notification                     | Likely Cause                                             | Resolution                                         |
|-----------------------------------------|----------------------------------------------------------|----------------------------------------------------|
| "Node ID not found"                     | Incorrect `node_id` provided, or device offline          | Verify node ID and network, update config/service   |
| "entities_backup.py not found/imported" | Support script missing or import path incorrect           | Confirm both files are together or fix import path  |
| "Permission denied"                     | Lacking write permission for target backup directory      | Fix file system permissions, run AppDaemon as correct user |
| "Backup failed: file system error"      | Disk full, directory missing, filename invalid            | Check free space, ensure directories exist & writable|
| No notification sent                    | `notify_service` not set or is incorrect                  | Double-check `notify_service` value and syntax      |
| No backup files found after run         | Misconfigured `backup_dir` or backup process errors       | Confirm directory path, check logs for failures     |

- **Log review**: Inspect AppDaemon and Home Assistant logs for stack traces or warnings.
- **Update/Restart**: After resolving issues, reload or restart AppDaemon to apply the changes.
- If issues persist, update both app and Home Assistant to latest versions, and inspect support forums.

## Support

For additional help, refer to the official [AppDaemon documentation](https://appdaemon.readthedocs.io/) or Community Forums. Issues with [`entities_backup.py`](entities_backup.py:1) are addressed separately in that app’s own documentation.