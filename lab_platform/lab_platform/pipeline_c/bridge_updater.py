from __future__ import annotations

import yaml

from lab_platform.config import LabConfig
from lab_platform.workspace import promote_bridge


def update_bridge_level(
    config: LabConfig, device_id: str, level: str, run_id: str
) -> None:
    promote_bridge(config, device_id, level, run_id)


def load_vendor_sdk_version(config: LabConfig, device_id: str) -> str | None:
    caps_path = config.registry_dir / "device_capabilities.yaml"
    if not caps_path.exists():
        return None
    caps = yaml.safe_load(caps_path.read_text(encoding="utf-8"))
    dev = caps.get("devices", {}).get(device_id, {})
    plugin = dev.get("driver_bridge_plugin", "")
    if not plugin:
        return None
    parts = plugin.split("/")
    if len(parts) >= 2:
        plugin_path = config.data_root / parts[0] / parts[1] / "plugin.yaml"
        if plugin_path.exists():
            data = yaml.safe_load(plugin_path.read_text(encoding="utf-8"))
            return data.get("sdk_version")
    return None
