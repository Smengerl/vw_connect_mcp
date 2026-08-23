"""Tibber Data API adapter for vehicles (read-only, charging/range only).

Reads vehicle data via the Tibber Data API — see ARCHITECTURE.md for the
full API research and the current architecture (§4) this adapter
implements. Not VW-specific despite the project's origins (ARCHITECTURE.md
§1.1) — Tibber's vehicle integration covers 30+ EV brands via Enode. This
is now the project's only backend; the previous VW-direct carconnectivity
backend was removed after VW blocked third-party access (see the permanent
`carconnectivity` branch for that code).

Two hard limitations, by design, not oversight — both confirmed live and
documented in ARCHITECTURE.md:
- Read coverage: Tibber exposes only 11 of the ~51 data points the old
  carconnectivity/VW-direct backend provided (identity fields + SoC/range/
  charging/plug status). Doors, windows, tyres, lights, climatization,
  position, and maintenance have no Tibber equivalent at all, which is why
  AbstractAdapter no longer declares methods/models for any of them.
- Write coverage: the Tibber Data API is entirely read-only (confirmed via
  its OpenAPI schema, no command endpoint exists) — AbstractAdapter has no
  command methods at all as a result.

Auth: TibberDataAPI is constructed with allow_interactive_login=False, so
this adapter's __init__ never opens a browser or blocks on user input — it
requires a token file already produced by the one-time interactive setup
tool (weconnect_mcp.cli.tibber_login_cli). If that file is missing or its
refresh token is unusable, __init__ raises TibberAuthError with a clear
remediation message.
"""

from __future__ import annotations

import logging
from typing import Any, Dict, List, Optional

from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, VehicleModel, VehicleListItem, VehicleDetailLevel,
    EnergyStatusModel, RangeInfo, ElectricDriveInfo,
)
from weconnect_mcp.adapter.mixins import CacheMixin, TibberStateExtractionMixin
from weconnect_mcp.adapter.tibber_client import (
    TibberDataAPI, TokenStore, vin_from_external_id,
)

logger = logging.getLogger(__name__)


class TibberAdapter(CacheMixin, TibberStateExtractionMixin, AbstractAdapter):
    """Adapter for vehicles using the Tibber Data API.

    Composed of mixins for its concerns:
    - CacheMixin: data caching to avoid hammering Tibber's API
    - TibberStateExtractionMixin: extract charging/range state from a
      Tibber device-detail response

    Vehicle identifier resolution (VIN/name/license plate) comes from
    AbstractAdapter's own concrete `resolve_vehicle_id` — no separate
    mixin needed for that.
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
        super().__init__()

        self.client = TibberDataAPI(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            store=TokenStore(token_path),
            allow_interactive_login=False,
        )
        self._vehicles_cache: List[Dict[str, Any]] = []
        self._fetch_data()  # initial fetch

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
            # model_year: no Tibber equivalent (ARCHITECTURE.md §5 table)
        )

    def get_energy_status(self, vehicle_id: str) -> Optional[EnergyStatusModel]:
        """Get energy and range info from Tibber's charging capabilities."""
        detail = self._get_device_detail(vehicle_id)
        if detail is None:
            return None

        charging = self._get_tibber_charging_state(detail)
        range_km = self._get_tibber_range_km(detail)
        if charging is None and range_km is None:
            return None

        electric_info = ElectricDriveInfo(
            battery_level_percent=charging.current_soc_percent if charging else None,
            battery_temperature_kelvin=None,  # not exposed by Tibber
            charging=charging,
        )
        range_model = RangeInfo(
            total_km=range_km,
            electric_km=range_km,
            combustion_km=None,  # Tibber only ever reports EVs
        )

        return EnergyStatusModel(
            vehicle_type="electric",
            range=range_model,
            electric=electric_info,
            combustion=None,
        )
