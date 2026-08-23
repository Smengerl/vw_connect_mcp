"""State extraction mixin for TibberAdapter.

Converts a Tibber Data API device-detail response (a flat list of
capability dicts) into ChargingModel plus a plain range-in-km float.
Tibber's confirmed capability set is 5 fields (ARCHITECTURE.md §3.1), all
charging/range related — no doors/windows/tyres/lights/climatization/
position/maintenance equivalent exists, so those categories are simply not
implemented here at all (the adapter returns None for them directly, see
tibber_adapter.py).
"""

from __future__ import annotations

from typing import Any, Optional

from weconnect_mcp.adapter.abstract_adapter import ChargingModel

# Tibber Data API capability ids (confirmed live, ARCHITECTURE.md §3.1).
_ID_SOC = "storage.stateOfCharge"          # %
_ID_TARGET_SOC = "storage.targetStateOfCharge"  # %
_ID_RANGE = "range.remaining"              # m
_ID_CONNECTOR = "connector.status"         # connected/disconnected/unknown
_ID_CHARGING = "charging.status"           # charging/idle/unknown

_STATUS_CONNECTED = "connected"
_STATUS_CHARGING = "charging"


class TibberStateExtractionMixin:
    """Mixin providing vehicle state extraction from Tibber device details."""

    @staticmethod
    def _capability(detail: dict[str, Any], capability_id: str) -> Optional[dict[str, Any]]:
        for cap in detail.get("capabilities", []):
            if cap.get("id") == capability_id:
                return cap
        return None

    def _get_tibber_charging_state(self, detail: dict[str, Any]) -> Optional[ChargingModel]:
        """Extract charging info from a Tibber device-detail response."""
        soc_cap = self._capability(detail, _ID_SOC)
        target_cap = self._capability(detail, _ID_TARGET_SOC)
        connector_cap = self._capability(detail, _ID_CONNECTOR)
        charging_cap = self._capability(detail, _ID_CHARGING)

        if not any([soc_cap, target_cap, connector_cap, charging_cap]):
            return None

        current_soc = float(soc_cap["value"]) if soc_cap and soc_cap.get("value") is not None else None
        target_soc = int(target_cap["value"]) if target_cap and target_cap.get("value") is not None else None

        is_plugged_in = None
        if connector_cap is not None:
            is_plugged_in = connector_cap.get("value") == _STATUS_CONNECTED

        is_charging = None
        charging_state_str = None
        if charging_cap is not None:
            charging_state_str = charging_cap.get("value")
            is_charging = charging_state_str == _STATUS_CHARGING

        return ChargingModel(
            is_charging=is_charging,
            is_plugged_in=is_plugged_in,
            charging_power_kw=None,  # not exposed by Tibber
            charging_state=charging_state_str,
            remaining_time_minutes=None,  # not exposed by Tibber
            target_soc_percent=target_soc,
            current_soc_percent=current_soc,
            charge_mode=None,  # not exposed by Tibber
        )

    def _get_tibber_range_km(self, detail: dict[str, Any]) -> Optional[float]:
        """Extract remaining range (in km) from a Tibber device-detail response."""
        range_cap = self._capability(detail, _ID_RANGE)
        if range_cap is None or range_cap.get("value") is None:
            return None

        value = float(range_cap["value"])
        unit = range_cap.get("unit")
        return value / 1000 if unit == "m" else value
