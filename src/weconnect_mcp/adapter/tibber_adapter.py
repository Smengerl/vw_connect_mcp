"""Tibber Data API adapter for VW vehicles (read-only, charging/range only).

Alternative to CarConnectivityAdapter now that VW has blocked third-party
BFF access (see experiment/vw-device-flow-attestation-bypass/FINDING.md).
Reads vehicle data via the Tibber Data API instead — see
experiment/tibber-integration/TIBBER_API.md for the full API research and
the architecture analysis (§7) this adapter implements.

Two hard limitations, by design, not oversight — both confirmed live and
documented in TIBBER_API.md:
- Read coverage: Tibber exposes only 11 of the ~51 data points
  CarConnectivity/VW-direct provides (identity fields + SoC/range/
  charging/plug status). Doors, windows, tyres, lights, climatization,
  position, and maintenance have no Tibber equivalent at all -> the
  corresponding get_* methods always return None.
- Write coverage: the Tibber Data API is entirely read-only (confirmed via
  its OpenAPI schema, no command endpoint exists) -> every command method
  always returns a "not supported" result dict.

Auth: TibberDataAPI is constructed with allow_interactive_login=False, so
this adapter's __init__ never opens a browser or blocks on user input — it
requires a token file already produced by the one-time interactive setup
tool (weconnect_mcp.cli.tibber_login_cli). If that file is missing or its
refresh token is unusable, __init__ raises TibberAuthError with a clear
remediation message.
"""

from __future__ import annotations

import logging
from datetime import timedelta
from typing import Any, Dict, List, Optional

from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, VehicleModel, VehicleListItem, VehicleDetailLevel,
    PhysicalStatusModel, EnergyStatusModel, ClimateStatusModel,
    RangeInfo, ElectricDriveInfo, MaintenanceModel, PositionModel,
)
from weconnect_mcp.adapter.mixins import (
    CacheMixin, VehicleResolutionMixin, TibberStateExtractionMixin,
)
from weconnect_mcp.adapter.tibber_client import (
    TibberDataAPI, TokenStore, vin_from_external_id,
)

# Cache duration — same default as CarConnectivityAdapter; Tibber's own API
# docs also ask clients to be polite about polling frequency.
CACHE_DURATION_SECONDS = 300  # 5 minutes

logger = logging.getLogger(__name__)

_NOT_SUPPORTED: Dict[str, Any] = {
    "success": False,
    "error": "Not supported: the Tibber Data API is read-only (no command endpoints exist).",
}


class TibberAdapter(
    CacheMixin,
    VehicleResolutionMixin,
    TibberStateExtractionMixin,
    AbstractAdapter,
):
    """Adapter for VW vehicles using the Tibber Data API.

    Composed of mixins for the concerns it shares with CarConnectivityAdapter:
    - CacheMixin: data caching to avoid hammering Tibber's API
    - VehicleResolutionMixin: resolve vehicle identifiers to VIN
    - TibberStateExtractionMixin: extract charging/range state from a
      Tibber device-detail response

    Deliberately has no CommandMixin equivalent — every command method
    below returns _NOT_SUPPORTED directly, since the underlying API has no
    write endpoint to call.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: Optional[str],
        redirect_uri: str,
        token_path: str,
    ) -> None:
        """Initialize adapter.

        Args:
            client_id: Tibber Data API OAuth2 client id.
            client_secret: Tibber Data API OAuth2 client secret.
            redirect_uri: Must match the redirect URI registered on the
                client (only used to validate a stored token was issued
                for the same client — no browser interaction happens here).
            token_path: Path to the token file produced by
                weconnect_mcp.cli.tibber_login_cli.
        """
        self._last_fetch_time = None
        self._cache_duration = timedelta(seconds=CACHE_DURATION_SECONDS)

        self.client = TibberDataAPI(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            store=TokenStore(token_path),
            allow_interactive_login=False,
        )
        self._vehicles_cache: List[Dict[str, Any]] = []
        self._fetch_data()  # initial fetch, mirrors CarConnectivityAdapter

    def _fetch_data(self) -> None:
        """Fetch the vehicle list from Tibber and update cache timestamp."""
        self._vehicles_cache = self.client.vehicles()
        self._mark_data_fetched()
        logger.info("Fetched fresh vehicle list from Tibber (%d vehicle(s))", len(self._vehicles_cache))

    def shutdown(self) -> None:
        """No persistent connection to close."""

    def __enter__(self) -> "TibberAdapter":
        return self

    def __exit__(self, exc_type, exc_value, traceback) -> None:
        self.shutdown()

    async def __aenter__(self) -> "TibberAdapter":
        return self

    async def __aexit__(self, exc_type, exc_value, traceback) -> None:
        self.shutdown()

    # ── vehicle lookup helpers ────────────────────────────────────────────────

    def list_vehicles(self) -> list[VehicleListItem]:
        """Get list of vehicles with VIN, name, model.

        Tibber has no license plate data, so that field is always None.
        """
        self._ensure_fresh_data()
        items = []
        for entry in self._vehicles_cache:
            info = entry.get("info", {})
            vin = vin_from_external_id(entry.get("externalId", ""))
            items.append(VehicleListItem(
                vin=vin,
                name=info.get("name"),
                model=info.get("model"),
                license_plate=None,
            ))
        return items

    def _find_vehicle_entry(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Resolve an identifier to the cached Tibber vehicle-list entry."""
        self._ensure_fresh_data()
        vin = self.resolve_vehicle_id(vehicle_id) or vehicle_id
        for entry in self._vehicles_cache:
            if vin_from_external_id(entry.get("externalId", "")).lower() == vin.lower():
                return entry
        return None

    def _get_device_detail(self, vehicle_id: str) -> Optional[Dict[str, Any]]:
        """Fetch the full device detail (capabilities) for one vehicle."""
        entry = self._find_vehicle_entry(vehicle_id)
        if entry is None:
            return None
        return self.client.device(entry["homeId"], entry["id"])

    # ── read methods ─────────────────────────────────────────────────────────

    def get_vehicle(self, vehicle_id: str, details: VehicleDetailLevel = VehicleDetailLevel.FULL) -> Optional[VehicleModel]:
        """Get vehicle info. Fields with no Tibber equivalent stay None."""
        entry = self._find_vehicle_entry(vehicle_id)
        if entry is None:
            return None

        info = entry.get("info", {})
        vin = vin_from_external_id(entry.get("externalId", ""))

        connection_state = None
        if details != VehicleDetailLevel.BASIC:
            detail = self.client.device(entry["homeId"], entry["id"])
            for attr in detail.get("attributes", []):
                if attr.get("id") == "isOnline":
                    connection_state = "online" if attr.get("value") else "offline"

        return VehicleModel(
            vin=vin,
            model=info.get("model"),
            name=info.get("name"),
            manufacturer=info.get("brand"),
            connection_state=connection_state,
            # license_plate, odometer, state, type, software_version,
            # model_year: no Tibber equivalent (TIBBER_API.md README table)
        )

    def get_physical_status(self, vehicle_id: str, components: Optional[List[str]] = None) -> Optional[PhysicalStatusModel]:
        """Doors/windows/tyres/lights have no Tibber equivalent."""
        return None

    def get_energy_status(self, vehicle_id: str) -> Optional[EnergyStatusModel]:
        """Get energy and range info from Tibber's charging capabilities."""
        detail = self._get_device_detail(vehicle_id)
        if detail is None:
            return None

        charging = self._get_tibber_charging_state(detail)
        range_info = self._get_tibber_range_info(detail)
        if charging is None and range_info is None:
            return None

        electric_info = ElectricDriveInfo(
            battery_level_percent=charging.current_soc_percent if charging else None,
            battery_temperature_kelvin=None,  # not exposed by Tibber
            charging=charging,
        )
        range_model = RangeInfo(
            total_km=range_info.total_range_km if range_info else None,
            electric_km=range_info.electric_drive.range_km if range_info and range_info.electric_drive else None,
            combustion_km=None,  # Tibber only ever reports EVs
        )

        return EnergyStatusModel(
            vehicle_type="electric",
            range=range_model,
            electric=electric_info,
            combustion=None,
        )

    def get_climate_status(self, vehicle_id: str) -> Optional[ClimateStatusModel]:
        """Climatization and window heating have no Tibber equivalent."""
        return None

    def get_maintenance_info(self, vehicle_id: str) -> Optional[MaintenanceModel]:
        """Maintenance schedule has no Tibber equivalent."""
        return None

    def get_position(self, vehicle_id: str) -> Optional[PositionModel]:
        """GPS position has no Tibber equivalent."""
        return None

    # ── command methods (all unsupported — Tibber Data API is read-only) ────

    def lock_vehicle(self, vehicle_id: str) -> Dict[str, Any]:
        return _NOT_SUPPORTED

    def unlock_vehicle(self, vehicle_id: str) -> Dict[str, Any]:
        return _NOT_SUPPORTED

    def start_climatization(self, vehicle_id: str, target_temp_celsius: Optional[float] = None) -> Dict[str, Any]:
        return _NOT_SUPPORTED

    def stop_climatization(self, vehicle_id: str) -> Dict[str, Any]:
        return _NOT_SUPPORTED

    def start_charging(self, vehicle_id: str) -> Dict[str, Any]:
        return _NOT_SUPPORTED

    def stop_charging(self, vehicle_id: str) -> Dict[str, Any]:
        return _NOT_SUPPORTED

    def flash_lights(self, vehicle_id: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        return _NOT_SUPPORTED

    def honk_and_flash(self, vehicle_id: str, duration_seconds: Optional[int] = None) -> Dict[str, Any]:
        return _NOT_SUPPORTED

    def start_window_heating(self, vehicle_id: str) -> Dict[str, Any]:
        return _NOT_SUPPORTED

    def stop_window_heating(self, vehicle_id: str) -> Dict[str, Any]:
        return _NOT_SUPPORTED
