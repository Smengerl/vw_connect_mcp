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

import functools
import logging
from typing import Any, Dict, List, Optional

from weconnect_mcp.adapter.abstract_adapter import (
    AbstractAdapter, AdapterUnavailableError, ChargingModel, VehicleModel, VehicleListItem,
    VehicleDetailLevel, EnergyStatusModel, RangeInfo, ElectricDriveInfo,
)
from weconnect_mcp.adapter.mixins import CacheMixin
from weconnect_mcp.adapter.tibber_client import (
    TibberAuthError, TibberDataAPI, TokenStore, default_login_command, vin_from_external_id,
)

logger = logging.getLogger(__name__)

# ── Tibber device-detail extraction ──────────────────────────────────────────
# Converts a Tibber Data API device-detail response (a flat list of
# capability dicts) into ChargingModel plus a plain range-in-km float.
# Tibber's confirmed capability set is 5 fields (ARCHITECTURE.md §3.1), all
# charging/range related -- no doors/windows/tyres/lights/climatization/
# position/maintenance equivalent exists, so those categories are simply not
# implemented here at all (get_energy_status returns None for them directly).
#
# Plain module-level functions, not methods: neither uses any adapter state,
# so there's nothing a class (or the mixin this used to be, back when it
# pretended to be reusable across a second backend that was never built --
# see CLAUDE.md's no-dual-backend note) would add over just calling them.
_ID_SOC = "storage.stateOfCharge"          # %
_ID_TARGET_SOC = "storage.targetStateOfCharge"  # %
_ID_RANGE = "range.remaining"              # m
_ID_CONNECTOR = "connector.status"         # connected/disconnected/unknown
_ID_CHARGING = "charging.status"           # charging/idle/unknown

_STATUS_CONNECTED = "connected"
_STATUS_CHARGING = "charging"


def _capability(detail: Dict[str, Any], capability_id: str) -> Optional[Dict[str, Any]]:
    for cap in detail.get("capabilities", []):
        if cap.get("id") == capability_id:
            return cap
    return None


def _get_tibber_charging_state(detail: Dict[str, Any]) -> Optional[ChargingModel]:
    """Extract charging info from a Tibber device-detail response."""
    soc_cap = _capability(detail, _ID_SOC)
    target_cap = _capability(detail, _ID_TARGET_SOC)
    connector_cap = _capability(detail, _ID_CONNECTOR)
    charging_cap = _capability(detail, _ID_CHARGING)

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
        charging_state=charging_state_str,
        target_soc_percent=target_soc,
        current_soc_percent=current_soc,
    )


def _get_tibber_range_km(detail: Dict[str, Any]) -> Optional[float]:
    """Extract remaining range (in km) from a Tibber device-detail response."""
    range_cap = _capability(detail, _ID_RANGE)
    if range_cap is None or range_cap.get("value") is None:
        return None

    value = float(range_cap["value"])
    unit = range_cap.get("unit")
    return value / 1000 if unit == "m" else value


def _translate_auth_errors(fn):
    """Convert any Tibber-specific auth failure into the adapter port's
    generic AdapterUnavailableError, so callers (the MCP tool layer) don't
    need to know this adapter happens to be backed by Tibber. See
    ARCHITECTURE.md §2.4.

    Catches the TibberAuthError base class: every auth failure (not
    configured, invalid client credentials, network error, reauth
    required, ...) is one of these, distinguished only by its error_type
    attribute, not by subclass -- see TibberAuthError's own docstring in
    tibber_client.py. All of it needs to reach the MCP client as a clear
    "server_unavailable" response with its differentiated message and
    error_type, not escape as a raw exception that crashes the tool call.
    """
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            return fn(*args, **kwargs)
        except TibberAuthError as exc:
            raise AdapterUnavailableError(str(exc), error_type=exc.error_type) from exc
    return wrapper


class TibberAdapter(CacheMixin, AbstractAdapter):
    """Adapter for vehicles using the Tibber Data API.

    Uses CacheMixin for data caching (to avoid hammering Tibber's API) --
    the one piece of behavior here that's genuinely reusable, since it
    doesn't know anything about Tibber. Device-detail extraction is a set
    of plain module-level functions above instead of a second mixin: they
    were Tibber-specific either way, so composing them in via multiple
    inheritance never bought anything over calling them directly.

    Vehicle identifier resolution (VIN/name) comes from
    AbstractAdapter's own concrete `resolve_vehicle_id` — no separate
    mixin needed for that either.
    """

    def __init__(
        self,
        client_id: str,
        client_secret: Optional[str],
        redirect_uri: str,
        token_path: str,
        login_command: Optional[str] = None,
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
            login_command: Exact, copy-paste-runnable command that performs
                the one-time interactive login, baked into auth-error
                messages instead of a generic hint (see
                tibber_client.default_login_command and its caller,
                mcp_server_cli._build_tibber_adapter, which knows the real
                credentials-file path this deployment uses). None falls
                back to TibberDataAPI's own generic default.
        """
        super().__init__()

        self.client = TibberDataAPI(
            client_id=client_id,
            client_secret=client_secret,
            redirect_uri=redirect_uri,
            login_command=login_command if login_command is not None else default_login_command(),
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

    @_translate_auth_errors
    def list_vehicles(self) -> list[VehicleListItem]:
        """Get list of vehicles with VIN, name, model."""
        self._ensure_fresh_data()
        items = []
        for entry in self._vehicles_cache:
            info = entry.get("info", {})
            vin = vin_from_external_id(entry.get("externalId", ""))
            items.append(VehicleListItem(
                vin=vin,
                name=info.get("name"),
                model=info.get("model"),
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

    @_translate_auth_errors
    def get_vehicle(self, vehicle_id: str, details: VehicleDetailLevel = VehicleDetailLevel.FULL) -> Optional[VehicleModel]:
        """Get vehicle info. Fields with no Tibber equivalent stay None."""
        entry = self._find_vehicle_entry(vehicle_id)
        if entry is None:
            return None

        info = entry.get("info", {})
        vin = vin_from_external_id(entry.get("externalId", ""))

        connection_state = None
        last_seen = None
        if details != VehicleDetailLevel.BASIC:
            detail = self.client.device(entry["homeId"], entry["id"])
            for attr in detail.get("attributes", []):
                if attr.get("id") == "isOnline":
                    connection_state = "online" if attr.get("value") else "offline"
            last_seen = detail.get("status", {}).get("lastSeen")

        return VehicleModel(
            vin=vin,
            model=info.get("model"),
            name=info.get("name"),
            manufacturer=info.get("brand"),
            connection_state=connection_state,
            last_seen=last_seen,
        )

    @_translate_auth_errors
    def get_energy_status(self, vehicle_id: str) -> Optional[EnergyStatusModel]:
        """Get energy and range info from Tibber's charging capabilities."""
        detail = self._get_device_detail(vehicle_id)
        if detail is None:
            return None

        charging = _get_tibber_charging_state(detail)
        range_km = _get_tibber_range_km(detail)
        if charging is None and range_km is None:
            return None

        electric_info = ElectricDriveInfo(
            battery_level_percent=charging.current_soc_percent if charging else None,
            battery_temperature_kelvin=None,  # not exposed by Tibber
            charging=charging,
        )
        range_model = RangeInfo(total_km=range_km)

        return EnergyStatusModel(
            range=range_model,
            electric=electric_info,
            last_seen=detail.get("status", {}).get("lastSeen"),
        )
