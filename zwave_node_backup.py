import appdaemon.plugins.hass.hassapi as hass
import os
import subprocess
import logging

# AppDaemon app for backing up a Z-Wave node's entity to a JSON file using an external Python script.
# Comments, logging, and notifications are robust to fit backup/validation/reporting requirements.
# Does NOT attempt any container exec or platform abstraction logic.

class ZwaveNodeBackup(hass.Hass):
    def initialize(self):
        """
        Called once when the app is initialized or reloaded.
        Sets the service handler and configuration options.
        """
        # Configurable: Service name and default node_id (optional)
        self.app_service = self.args.get('service', 'zwave_node_backup/backup')
        self.default_node_id = self.args.get('node_id', None)
        # Listen for service calls
        self.register_service(self.app_service, self.handle_backup_service)
        self.log(
            f"ZwaveNodeBackup initialized; registered service '{self.app_service}'", level="INFO"
        )

    def handle_backup_service(self, namespace, domain, service, data):
        """
        Service handler entrypoint. Responsible for carrying out the backup workflow.
        """
        try:
            # Obtain node_id from call or config
            node_id = data.get("node_id") or self.default_node_id
            if node_id is None:
                raise ValueError("No 'node_id' provided in service call or App config.")
            # Ensure node_id is integer, convert for naming.
            try:
                node_id_str = str(int(node_id))
            except Exception:
                raise ValueError(f"Invalid node_id '{node_id}': must be an integer.")

            backup_dir = "/config/backups/entity_backups"
            backup_file = f"{backup_dir}/node_{node_id_str}_backup.json"
            entities_backup_script = "/config/entities_backup.py"

            # Step 1: Ensure backup dir exists
            if not os.path.exists(backup_dir):
                try:
                    os.makedirs(backup_dir, exist_ok=True)
                except Exception as e:
                    raise RuntimeError(
                        f"Failed to create backup directory '{backup_dir}': {e}"
                    )

            # Step 2: Run backup script and capture output
            if not os.path.isfile(entities_backup_script):
                raise FileNotFoundError(
                    f"Python backup script not found at: {entities_backup_script}"
                )
            try:
                self.log(
                    f"Running backup for node {node_id_str} via {entities_backup_script}",
                    level="INFO",
                )
                result = subprocess.run(
                    ["python3", entities_backup_script, node_id_str],
                    capture_output=True,
                    text=True,
                    timeout=180,
                )
            except Exception as e:
                raise RuntimeError(f"Error executing backup script: {e}")

            # Step 3: Check backup result
            if result.returncode != 0:
                self.log(
                    f"entities_backup.py returned nonzero exit code: {result.returncode}\nStdout: {result.stdout}\nStderr: {result.stderr}",
                    level="ERROR",
                )
                self._notify(
                    "Z-Wave Entity Backup",
                    f"Failed to back up node {node_id_str}: backup script returned error.\n\nStdout:\n{result.stdout}\n\nStderr:\n{result.stderr}",
                    error=True,
                )
                return

            # Step 4: Validate backup file existence
            if not os.path.isfile(backup_file):
                self.log(
                    f"Expected backup file was NOT created: {backup_file}",
                    level="ERROR",
                )
                self._notify(
                    "Z-Wave Entity Backup",
                    f"Backup for node {node_id_str} failed: file {backup_file} was not created.",
                    error=True,
                )
                return

            # Step 5: Success reporting
            msg = (
                f"Backup successful for Z-Wave node {node_id_str}.\n"
                f"Backup file: {backup_file}\n"
                "You may now proceed to validate or restore entities as needed."
            )
            self.log(msg, level="INFO")
            self._notify("Z-Wave Entity Backup", msg)
        except Exception as exc:
            # Final catch-all error path
            err_msg = f"Z-Wave node backup failed: {exc}"
            self.log(err_msg, level="ERROR")
            self._notify("Z-Wave Entity Backup", err_msg, error=True)

    def _notify(self, title, message, error=False):
        """
        Send a persistent_notification to Home Assistant and log,
        also emits at appropriate log level.
        """
        try:
            notification = {
                "title": title,
                "message": message,
            }
            self.call_service(
                "persistent_notification/create",
                **notification,
            )
        except Exception as notify_err:
            self.log(
                f"Failed to send HA notification: {notify_err}", level="ERROR"
            )
        level = "ERROR" if error else "INFO"
        self.log(message, level=level)