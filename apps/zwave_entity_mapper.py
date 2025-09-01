"""
Z-Wave Entity Mapper & Migrator for Home Assistant (AppDaemon + Z-Wave JS)

Features:
- Extract all Z-Wave entity IDs and attributes for selected device.
- Export and edit YAML entity mapping file (sparse mapping supported).
- Script-driven renaming of new entities per mapping, with validation, backup, reporting.
- Backup/export of Z-Wave JS device configuration (where feasible).
- Config/parameters restore to new device (best effort).
- Robust logging and error reporting.

See README.md for usage.
"""

import appdaemon.plugins.hass.hassapi as hass
import yaml
import os
import datetime

class ZWaveEntityMapper(hass.Hass):
    def initialize(self):
        self.log("ZWave Entity Mapper App initializing...")

        # Configuration
        self.target_device_id = self.args.get("target_device_id")
        self.mapping_file = self.args.get("mapping_file", "zwave_entity_mapping.yaml")
        self.backup_dir = self.args.get("backup_dir", "zwave_backup")
        self.report_file = self.args.get("report_file", "last_run_report.yaml")
        self.summary_file = self.args.get("summary_file", "dashboard_summary.yaml")

        # Initial setup
        os.makedirs(self.backup_dir, exist_ok=True)

        # --- HADashboard Integration Setup ----
        # Register dashboard triggers and states
        self.dashboard_triggers = [
            "sensor.zem_dashboard_export_trigger",
            "sensor.zem_dashboard_import_trigger",
            "sensor.zem_dashboard_backup_trigger",
            "sensor.zem_dashboard_restore_trigger"
        ]
        self.dashboard_status = "sensor.zem_dashboard_status"
        self.dashboard_message = "sensor.zem_dashboard_message"
        self.dashboard_summary = "sensor.zem_dashboard_summary"

        # Ensure all dashboard sensors exist and are initialized OFF/idle
        for trig in self.dashboard_triggers:
            self.set_state(trig, state="off", namespace="hadashboard")
        self.set_state(self.dashboard_status, state="Idle", namespace="hadashboard")
        self.set_state(self.dashboard_message, state="", namespace="hadashboard")
        self.set_state(self.dashboard_summary, state="No run yet", namespace="hadashboard")

        # Listen for dashboard triggers
        for trig in self.dashboard_triggers:
            self.listen_state(self.dashboard_trigger_handler, trig, namespace="hadashboard")

        # Run the normal workflow on startup (optional)
        # self.run_in(self.main_flow, 1)

    def main_flow(self, kwargs):
        try:
            self.log("Starting Z-Wave entity extraction and mapping process...")

            # 1. Extract all entity IDs and attributes for the selected device
            zwave_entities, attributes = self.extract_zwave_entities(self.target_device_id)
            self.log(f"Found {len(zwave_entities)} Z-Wave entities for device '{self.target_device_id}'.")

            # 2. Export entity YAML mapping template if not present
            if not os.path.exists(self.mapping_file):
                self.export_mapping_template(zwave_entities)
                self.log(f"Entity mapping YAML template exported to {self.mapping_file}.")

            # 3. Backup current entity state/config
            self.backup_entity_configs(zwave_entities)

            # 4. Load user-supplied mapping file
            with open(self.mapping_file, 'r') as f:
                mapping = yaml.safe_load(f) or {}

            # 5. Apply mapping (renaming, validation, reporting)
            report = self.apply_entity_mapping(zwave_entities, mapping)

            # 6. Backup Z-Wave device configuration (if feasible)
            self.backup_zwave_device_config(self.target_device_id)

            # 7. Attempt restore if restoring to a new device (if args supplied)
            restore_device_id = self.args.get("restore_to_device_id")
            if restore_device_id:
                self.restore_zwave_config(restore_device_id, mapping)

            # 8. Write report
            with open(self.report_file, "w") as f:
                yaml.safe_dump(report, f)
            self.log(f"Operation report written to {self.report_file}")

        except Exception as e:
            self.log(f"Error in AppDaemon flow: {e}", level="ERROR")

    def extract_zwave_entities(self, device_id):
        """
        Extract all entity IDs and their attributes for a given Z-Wave JS device_id.
        Returns: (list of entity_ids, dict of {entity_id: attrs})
        """
        all_entities = self.get_state()
        zwave_entities = []
        entity_attrs = {}

        # Direct device-entity association by device_id
        for entity_id, state in all_entities.items():
            if isinstance(state, dict) and state.get('device_id') == device_id:
                zwave_entities.append(entity_id)
                entity_attrs[entity_id] = state

        return zwave_entities, entity_attrs

    def export_mapping_template(self, entities):
        """
        Generates a YAML mapping template with empty target names for user edit.
        """
        mapping = {
            'mappings': [
                {'current_entity': ent, 'target_entity': None}
                for ent in entities
            ]
        }
        with open(self.mapping_file, "w") as f:
            yaml.safe_dump(mapping, f)

    def backup_entity_configs(self, entities):
        """
        Export attributes/states for all entities as a backup.
        """
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = os.path.join(self.backup_dir, f"entity_backup_{now}.yaml")
        states = {e: self.get_state(e, attribute='all') for e in entities}
        with open(fname, 'w') as f:
            yaml.safe_dump(states, f)
        self.log(f"Entity configs backed up to {fname}")

    def apply_entity_mapping(self, entities, mapping):
        """
        Rename entities as per user mapping YAML. Validate, backup each entity before change,
        handle collisions, and log/report unmapped/skipped/conflicts.
        """
        mapped = []
        unmapped = []
        surplus = entities.copy()
        errors = []

        # All current entity_ids for collision detection
        all_existing_eids = set(self.get_state().keys())

        map_dict = {m['current_entity']: m['target_entity']
                    for m in mapping.get('mappings', []) if m.get('current_entity')}

        for ent in entities:
            tgt = map_dict.get(ent)
            if tgt and tgt != ent:
                # Validate: Check if target_id exists and isn't being replaced as part of mapping
                if tgt in all_existing_eids:
                    err = f"Target entity_id '{tgt}' already exists. Skipping rename '{ent}' => '{tgt}'"
                    mapped.append({'from': ent, 'to': tgt, 'status': 'error', 'error': err})
                    self.log(err, level="ERROR")
                    errors.append(err)
                else:
                    try:
                        # Backup state of this entity before renaming
                        state = self.get_state(ent, attribute='all')
                        backup_path = os.path.join(
                            self.backup_dir,
                            f"{ent.replace('.', '_')}_pre_rename.yaml"
                        )
                        with open(backup_path, "w") as f:
                            yaml.safe_dump(state, f)
                        self.log(f"Backed up state of '{ent}' to '{backup_path}'")

                        self.call_service("config/entity_registry/update_entity",
                                          entity_id=ent, new_entity_id=tgt)
                        mapped.append({'from': ent, 'to': tgt, 'status': 'renamed'})
                        self.log(f"Renamed '{ent}' to '{tgt}'")
                    except Exception as e:
                        mapped.append({'from': ent, 'to': tgt, 'status': 'error', 'error': str(e)})
                        self.log(f"Failed to rename '{ent}': {e}", level="ERROR")
                        errors.append(str(e))
                surplus.remove(ent)
            elif tgt == ent:
                mapped.append({'from': ent, 'to': tgt, 'status': 'unchanged'})
                surplus.remove(ent)
            else:
                unmapped.append(ent)
                self.log(f"No mapping provided for '{ent}'. Skipped.", level="WARNING")

        report = {
            'mappings': mapped,
            'unmapped_entities': unmapped,
            'surplus_entities': surplus,
            'errors': errors
        }
        return report

    def backup_zwave_device_config(self, device_id):
        """
        Backup parameters/config for a Z-Wave JS device (limited by integration API).
        """
        now = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
        fname = os.path.join(self.backup_dir, f"zwave_device_config_{now}.yaml")

        # Attempt to get node config parameters (works if integration supports it)
        node_params = self.get_state("zwave_js", attribute="all")
        backup = {}
        for aid, node in node_params.items():
            if isinstance(node, dict) and node.get('device_id') == device_id:
                backup[aid] = node.get('attributes', {})
        with open(fname, "w") as f:
            yaml.safe_dump(backup, f)
        self.log(f"Z-Wave device config exported to {fname}")

    def restore_zwave_config(self, device_id, mapping):
        """
        Attempt to restore config/params to a new device (best effort).
        Logs/report which parameters could not be restored and why.
        """
        unmapped_params = []
        errors = []
        restored = []

        try:
            old_params = self.get_state("zwave_js", attribute="all")
            old_config = {}
            for aid, node in old_params.items():
                if isinstance(node, dict) and node.get('device_id') == self.target_device_id:
                    old_config = node.get('attributes', {}).get('parameters', {})
                    break

            # Try to read target/new device parameters to check existence
            new_params = None
            for aid, node in old_params.items():
                if isinstance(node, dict) and node.get('device_id') == device_id:
                    new_params = node.get('attributes', {}).get('parameters', {})
                    break

            if old_config and new_params:
                for param, value in old_config.items():
                    if param not in new_params:
                        self.log(f"Parameter {param} not present on new device: skipping", level="WARNING")
                        unmapped_params.append(param)
                        continue
                    try:
                        self.call_service(
                            "zwave_js/set_config_parameter",
                            device_id=device_id,
                            parameter=param,
                            value=value
                        )
                        self.log(f"Restored parameter {param} to {value} on {device_id}")
                        restored.append(param)
                    except Exception as e:
                        self.log(f"Failed to restore parameter {param}: {e}", level="ERROR")
                        errors.append({param: str(e)})
            else:
                self.log("No config parameters found on old or new device, or models are incompatible.", level="WARNING")
        except Exception as e:
            self.log(f"Restore process failed: {e}", level="ERROR")
            errors.append({"restore_process": str(e)})

        # Optionally: return a summary/report/dict for caller/report
        return {
            "restored": restored,
            "unmapped_parameters": unmapped_params,
            "errors": errors
        }