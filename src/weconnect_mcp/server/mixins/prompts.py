"""MCP Prompts for WeConnect vehicle workflows.

Provides pre-built prompt templates for common agentic vehicle operations.
Each prompt guides the AI through a complete workflow with safety checks.

The Tibber Data API is read-only and limited to identity + SoC/range/
charging-state (see experiment/tibber-integration/TIBBER_API.md §5.2) — it
has no command endpoints and no door/window/tyre/light/climate/position/
maintenance data at all. Prompts that depended entirely on those (vehicle
control, GPS position, door/climate status) have been removed; the
remaining prompts below only reference tools that actually exist. Where a
step used to rely on vehicle GPS position, it now asks the user for the
location instead; where a step used to execute a command (start/stop
charging, climate control), it is now advisory only — the AI should tell
the user to perform that action in the vehicle's own app, since the Tibber
Data API cannot do it. Each prompt's `description` is prefixed with its
usability: USABLE (fully supported) or PARTIALLY USABLE (advisory steps
replace what would otherwise be a command).
"""

from fastmcp import FastMCP
from weconnect_mcp.cli import logging_config

logger = logging_config.get_logger(__name__)


def register_prompts(mcp: FastMCP) -> None:
    """Register all workflow prompts with the MCP server.

    Args:
        mcp: FastMCP server instance to register prompts with
    """

    @mcp.prompt(
        name="safe_start_charging",
        title="Check Charging Readiness",
        description="[USABLE with Tibber: read-only check — actually starting the charge is not possible via the Tibber Data API (no write endpoint); the user must do it from the vehicle's own app] Check whether the vehicle is ready to begin charging",
        tags={"charging", "battery", "safety", "workflow"}
    )
    def safe_start_charging(vehicle_id: str) -> str:
        """Check charging readiness for a vehicle.

        Args:
            vehicle_id: Vehicle name or VIN to check

        Returns:
            Prompt template for the charging-readiness check
        """
        return f"""Check whether vehicle {vehicle_id} is ready to start charging:

1. Get current battery status using get_battery_status
2. Get current charging status using get_charging_status
3. Check if battery level is well below target SOC, which is typically 80% (don't bother charging if already full)
4. Check if vehicle is plugged in (charging_state == "connected" or "charging")
5. Report readiness to the user; if not plugged in or already full/charging, explain why

Note: the Tibber Data API is read-only. To actually start charging, the user must use the vehicle's own app or the charge point — this tool can only report status, not issue the command."""

    @mcp.prompt(
        name="check_vehicle_health",
        title="Check Vehicle Health",
        description="[USABLE with Tibber: vehicle info, state, and battery status are all supported] Health check with vehicle identity, connection state, and battery status",
        tags={"diagnostics", "health", "status", "monitoring"}
    )
    def check_vehicle_health(vehicle_id: str) -> str:
        """Vehicle health check using the data Tibber actually provides.

        Args:
            vehicle_id: Vehicle name or VIN to check

        Returns:
            Prompt template for the health check workflow
        """
        return f"""Perform a health check for vehicle {vehicle_id}:

1. Get basic vehicle info using get_vehicle_info
2. Get current vehicle state using get_vehicle_state
3. Get battery status using get_battery_status (if BEV/PHEV)

Analyze results and provide a summary:
- Connection/online state
- Battery level and range (for electric vehicles)
- Active charging state
- Any issues requiring attention

Format as a structured report. Doors, climate, and location have no Tibber equivalent, so they are not part of this check."""

    @mcp.prompt(
        name="monitor_charging_session",
        title="Monitor Charging Session",
        description="[USABLE with Tibber: read-only status polling — actually stopping charging must be done via the vehicle's own app, since the Tibber Data API has no write endpoint] Monitor charging progress until target SOC is reached",
        tags={"charging", "monitoring", "battery", "automation"}
    )
    def monitor_charging_session(vehicle_id: str, target_soc_percent: int = 80) -> str:
        """Monitor an ongoing charging session until the target is reached.

        Args:
            vehicle_id: Vehicle name or VIN to monitor
            target_soc_percent: Target state of charge percentage (default: 80%)

        Returns:
            Prompt template for the charging monitoring workflow
        """
        return f"""Monitor charging session for {vehicle_id} until {target_soc_percent}% SOC:

1. Check initial charging status using get_charging_status
2. Verify vehicle is actively charging (not just connected)
3. Report initial SOC and estimated time to {target_soc_percent}%
4. Poll get_charging_status every 5 minutes
5. Report progress updates (current SOC, plug/charging state)
6. When SOC >= {target_soc_percent}%, tell the user to stop charging via the vehicle's own app — the Tibber Data API is read-only and cannot issue that command
7. Report final status once the user confirms charging has stopped

Note: This is a monitoring workflow — explain to the user it requires periodic checks, not continuous blocking."""

    @mcp.prompt(
        name="charging_schedule_feasibility",
        title="Check Charging Schedule Feasibility",
        description="[PARTIALLY USABLE with Tibber: charging/battery status works; the vehicle's current location must come from the user since Tibber has no GPS data] Verify if current charging allows meeting user's schedule considering travel time",
        tags={"charging", "planning", "schedule", "navigation", "external-data"}
    )
    def charging_schedule_feasibility(vehicle_id: str, destination_address: str, required_arrival_time: str) -> str:
        """Check if charging schedule allows meeting user's appointment.

        Args:
            vehicle_id: Vehicle name or VIN being charged
            destination_address: Where user needs to go
            required_arrival_time: When user needs to arrive (e.g., "14:30" or "2:30 PM")

        Returns:
            Prompt template for schedule feasibility check
        """
        return f"""Check if {vehicle_id} charging allows reaching {destination_address} by {required_arrival_time}:

1. Get current charging status using get_charging_status
   - Current SOC (State of Charge)
   - Estimated time to 80% SOC
2. Get battery status using get_battery_status
   - Current range estimate
3. Ask the user for the vehicle's current location (Tibber has no GPS data)
4. Calculate route to destination using navigation API:
   - Distance to {destination_address}
   - Estimated driving time with current traffic
   - Energy consumption estimate based on distance
5. Determine required SOC for trip:
   - Calculate energy needed for journey
   - Add 20% buffer for safety
   - Check if current SOC is sufficient or charging needed
6. Calculate time budget:
   - Current time to required arrival time: {required_arrival_time}
   - Subtract driving time
   - Remaining time available for charging
7. Compare charging time needed vs. available:
   - If sufficient: "You have enough time. Can depart at [time] with [SOC]%"
   - If tight: "Schedule is tight. Monitor charging. Depart by [time] at minimum [SOC]%"
   - If insufficient: "Cannot meet schedule. Options: fast charger, alternative transport, reschedule"
8. Provide recommendations:
   - Optimal departure time
   - Minimum SOC needed
   - Whether to stop charging early or continue (the user must do this themselves — the Tibber Data API cannot)

Combines charging data, navigation, and time management for schedule feasibility."""

    @mcp.prompt(
        name="range_anxiety_advisor",
        title="Range Anxiety Advisor",
        description="[PARTIALLY USABLE with Tibber: battery status works; the vehicle's current location must come from the user since Tibber has no GPS data] Assess range adequacy for planned trip using battery status, route, weather, and charging infrastructure",
        tags={"range", "battery", "planning", "charging", "external-data", "navigation"}
    )
    def range_anxiety_advisor(vehicle_id: str, destination_address: str) -> str:
        """Comprehensive range assessment for planned journey.

        Args:
            vehicle_id: Vehicle name or VIN for trip
            destination_address: Destination for journey

        Returns:
            Prompt template for range anxiety assessment
        """
        return f"""Assess range adequacy for {vehicle_id} trip to {destination_address}:

1. Get current battery status using get_battery_status
   - Current SOC percentage
   - Estimated range (km/miles)
2. Ask the user for the vehicle's current location (Tibber has no GPS data)
3. Calculate route to destination:
   - Total distance
   - Elevation changes (uphill increases consumption)
   - Expected driving time
4. Get weather forecast for route:
   - Temperature (cold weather reduces range by 20-30%)
   - Wind conditions (headwind increases consumption)
   - Rain/snow (increases consumption by 5-10%)
5. Estimate actual range considering:
   - Base range from battery
   - Weather impact (cold = -25%, hot AC use = -10%)
   - Elevation (uphill = -15%, downhill = +10%)
   - Driving style (highway = -10%, city = optimal)
6. Calculate range buffer:
   - Needed range: distance to destination
   - Available range: adjusted for conditions
   - Safety buffer: 20% (never arrive at 0%)
7. Find charging stations along route:
   - Search for fast chargers within 20km of route
   - Check if charging needed for round trip
   - Identify fallback charging locations
8. Provide comprehensive assessment:
   - "Range adequate" / "Charging recommended" / "Charging required"
   - Optimal charging stops if needed
   - Alternative routes with better charging infrastructure
   - Estimated arrival SOC

Eliminates range anxiety with comprehensive multi-factor analysis."""

    @mcp.prompt(
        name="smart_preconditioning_advisor",
        title="Smart Battery Preconditioning Advisor",
        description="[PARTIALLY USABLE with Tibber: battery/charging status works; vehicle location must come from the user, and preconditioning itself is advisory only — the Tibber Data API cannot start climate control] Optimize battery preconditioning based on weather, trip requirements, and electricity pricing",
        tags={"battery", "charging", "optimization", "weather", "external-data", "cost"}
    )
    def smart_preconditioning_advisor(vehicle_id: str, planned_departure_time: str) -> str:
        """Optimize battery preconditioning for efficiency and cost.

        Args:
            vehicle_id: Vehicle name or VIN
            planned_departure_time: When user plans to leave (e.g., "07:30 tomorrow")

        Returns:
            Prompt template for smart preconditioning
        """
        return f"""Optimize battery preconditioning for {vehicle_id} departing at {planned_departure_time}:

1. Get current battery and charging status:
   - get_battery_status: Current SOC
   - get_charging_status: Charging state
2. Ask the user for the vehicle's current location (Tibber has no GPS data)
3. Get weather forecast for departure time:
   - Temperature at {planned_departure_time}
   - If below 5°C, battery preconditioning highly beneficial
   - If below -10°C, preconditioning critical for range
4. Check electricity pricing:
   - Get current and forecasted electricity rates
   - Identify cheapest charging periods before departure
   - Calculate cost savings of off-peak charging
5. Calculate optimal preconditioning strategy:
   - Cold weather (<0°C): Start preconditioning 2 hours before departure
   - Moderate (0-15°C): Start 30-60 min before departure
   - Warm (>15°C): Minimal preconditioning needed
6. Determine charging schedule:
   - If SOC low and cheap electricity available: Charge now
   - If SOC adequate and rates high: Wait for off-peak hours
   - Always complete charging 1 hour before departure for preconditioning
7. Provide the optimization plan and tell the user to start preconditioning/charging via the vehicle's own app — the Tibber Data API is read-only and cannot issue these commands itself:
   - "Start charging at [time] for optimal rates (€{{price}}/kWh)"
   - "Begin preconditioning at [time] for {{temp}}°C weather"
   - "Estimated cost: €{{amount}} vs €{{amount_peak}} during peak hours"

Combines weather and electricity pricing for optimal efficiency; execution is left to the user."""

    @mcp.prompt(
        name="automated_travel_readiness_check",
        title="Automated Travel Readiness Check",
        description="[PARTIALLY USABLE with Tibber: battery status works; vehicle location must come from the user, and any preparation (climate, door check) is advisory only — Tibber has no door/GPS/climate data or commands] Comprehensive pre-departure check combining vehicle state, weather, traffic, and route conditions",
        tags={"departure", "readiness", "comprehensive", "external-data", "automation"}
    )
    def automated_travel_readiness_check(vehicle_id: str, destination_address: str, departure_time: str) -> str:
        """Complete travel readiness assessment with all relevant factors.

        Args:
            vehicle_id: Vehicle name or VIN
            destination_address: Destination address
            departure_time: Planned departure time

        Returns:
            Prompt template for comprehensive readiness check
        """
        return f"""Perform a travel readiness check for {vehicle_id} to {destination_address} at {departure_time}:

**VEHICLE STATUS:**
1. Get vehicle state using get_vehicle_state
2. Get battery status using get_battery_status (if electric)
   - SOC percentage and range
   - Check if charging needed
3. Ask the user for the vehicle's current location (Tibber has no GPS data) and to confirm doors/windows are closed (Tibber has no door/window sensors)

**ROUTE ANALYSIS:**
4. Calculate route to {destination_address}:
   - Distance and estimated time
   - Current traffic conditions
   - Accidents or road closures
   - Alternative routes available
5. Check construction zones or delays on route
6. For electric vehicles: Identify charging stations along route

**WEATHER CONDITIONS:**
7. Get weather forecast for:
   - Departure location at {departure_time}
   - Route conditions
   - Destination weather
8. Check for weather warnings:
   - Heavy rain, snow, ice, fog
   - Extreme temperatures
   - Storm warnings

**TIMING ANALYSIS:**
9. Calculate if departure time is realistic:
   - If charging: time remaining vs. departure time
   - Traffic delays vs. available time buffer
   - Weather impact on driving time (+20% in bad weather)

**PREPARATION ADVICE:**
10. If needed, advise the user to start climatization or window defrosting themselves via the vehicle's own app (the Tibber Data API cannot issue these commands)

**COMPREHENSIVE REPORT:**
Provide a structured readiness report:
- ✅/⚠️/❌ Vehicle Status (battery)
- ✅/⚠️/❌ Route Conditions (traffic, weather, delays)
- ✅/⚠️/❌ Timing Feasibility (enough time for charging/driving)
- 📋 Action Items:
  - "Start charging now" / "Depart in 5 minutes" / "Delay departure by X minutes"
  - Weather warnings: "Heavy rain expected - allow extra time"
  - Route issues: "Accident on A3 - use alternative route via B12"
- 🚗 Final Recommendation: "Ready to depart" / "Wait for charging" / "Reschedule advised"

Combines vehicle battery data with external route/weather sources; execution of any vehicle command is left to the user."""

    @mcp.prompt(
        name="intelligent_charging_plan",
        title="Intelligent Cost-Optimised Charging Plan",
        description=(
            "[PARTIALLY USABLE with Tibber: charging/battery status works; vehicle location must come "
            "from the user, and starting/stopping charging is advisory only — Tibber has no write endpoint] "
            "Create a cost-optimised charging schedule considering electricity spot prices, "
            "weather (cold reduces range), vehicle state, and user calendar."
        ),
        tags={"charging", "cost", "optimization", "weather", "calendar", "external-data", "proactive"}
    )
    def intelligent_charging_plan(vehicle_id: str, target_departure_time: str = "tomorrow 07:00") -> str:
        """Intelligent charging plan combining prices, weather, and vehicle state.

        Args:
            vehicle_id: Vehicle name or VIN
            target_departure_time: When the vehicle is needed next (e.g. "tomorrow 07:00")

        Returns:
            Prompt template for cost-optimised charging planning
        """
        return f"""Create an intelligent, cost-optimised charging plan for {vehicle_id} with departure at {target_departure_time}:

**NOTE**: The Tibber Data API is read-only — charging must be started/stopped by the user via the vehicle's own app. This prompt produces a recommendation, not an executed action.

**STEP 1 – CURRENT VEHICLE STATE**
1. Get charging status using get_charging_status
   - Is the vehicle currently plugged in? (is_plugged_in)
   - Current SOC and target SOC
2. Get battery status using get_battery_status
   - Current range estimate
3. Ask the user for the vehicle's current location (needed for weather and electricity price lookup — Tibber has no GPS data)

**STEP 2 – WEATHER FORECAST**
4. Get weather forecast for the vehicle location:
   - Overnight low temperature (between now and {target_departure_time})
   - Temperature at {target_departure_time}
   - Precipitation (rain, snow, frost)
5. Estimate weather impact on battery range:
   - Below 0°C: range reduced by ~25–35 %, battery needs preconditioning
   - 0–10°C: range reduced by ~10–20 %
   - Above 20°C (with AC): range reduced by ~5–10 %

**STEP 3 – ELECTRICITY PRICE FORECAST**
6. Fetch electricity spot prices or time-of-use tariffs for the overnight period:
   - Use location (country/region) from the user
   - Search for ENTSO-E day-ahead prices, Tibber, aWATTar, or similar for the region
   - Identify cheapest 4-hour window between now and {target_departure_time}
   - Identify most expensive periods to avoid
7. Calculate cost comparison:
   - Cheapest window price per kWh
   - Average/peak price per kWh
   - Potential savings by shifting charging

**STEP 4 – REQUIRED ENERGY CALCULATION**
8. Calculate energy needed:
   - Target SOC for departure (80 % default, 100 % if long trip)
   - Weather-adjusted range target (add buffer for cold weather)
   - Energy gap = (target_soc - current_soc) × battery_capacity_kWh
9. Include preconditioning energy if temperature < 5°C (approx. 3–5 kWh extra)

**STEP 5 – OPTIMAL SCHEDULE**
10. Calculate optimal charging schedule:
    - Fit charging window into cheapest electricity period
    - Ensure charging completes at least 30 min before {target_departure_time} (for preconditioning)
    - If not plugged in: remind user to connect cable

**STEP 6 – RECOMMENDATION**
11. Present the plan, and tell the user to start/stop charging themselves at the recommended times (via the vehicle's own app):

```
⚡ CHARGING PLAN FOR {{vehicle_name}}
────────────────────────────────────────────────
🔋 Current SOC: {{soc}}% → Target: {{target_soc}}% ({{energy_needed}} kWh)
🌡️  Overnight low: {{temp}}°C → Range impact: {{impact}}%
💶 Cheapest window: {{start_time}}–{{end_time}} @ {{price}} ct/kWh
💰 Estimated cost: €{{cost}} (saving €{{saving}} vs. charging now)

📅 RECOMMENDED SCHEDULE:
  {{start_time}}: Start charging via the vehicle's app ({{charging_power}} kW)
  {{end_time}}: Charging should be complete at {{target_soc}}%

⚠️  ALERTS:
  [Weather: Frost expected – preconditioning recommended]

✅ NEXT STEP: user starts/stops charging at the times above
```"""

    @mcp.prompt(
        name="trip_optimizer",
        title="Trip Departure & Charging Stop Optimizer",
        description=(
            "[PARTIALLY USABLE with Tibber: energy/range status works; vehicle location must come from "
            "the user, and starting charging is advisory only — Tibber has no write endpoint] "
            "Optimise departure timing, en-route charging stops, or fuel stops "
            "based on user calendar, vehicle range, and live traffic."
        ),
        tags={"trip", "planning", "charging", "navigation", "calendar", "range", "external-data", "proactive"}
    )
    def trip_optimizer(vehicle_id: str, destination: str) -> str:
        """Optimise departure time and charging/fuel stops for a trip.

        Args:
            vehicle_id: Vehicle name or VIN
            destination: Trip destination (address or place name)

        Returns:
            Prompt template for intelligent trip optimisation
        """
        return f"""Optimise the trip to {destination} for {vehicle_id}:

**STEP 1 – VEHICLE ENERGY STATE**
1. Get energy status using get_energy_status
   - Current SOC / fuel level and estimated range
   - Vehicle type (electric / hybrid / combustion)
2. Ask the user for the vehicle's current location (starting point) — Tibber has no GPS data

**STEP 2 – CALENDAR & TIME CONSTRAINTS**
3. Check user's calendar for constraints related to this trip:
   - Does the destination match a calendar event? → hard arrival deadline
   - Return trip? → note any scheduled return time
   - Meeting duration at destination?
4. If no calendar event matches, ask: "Is there a specific arrival time you need to meet?"

**STEP 3 – ROUTE & TRAFFIC ANALYSIS**
5. Calculate primary route to {destination}:
   - Total distance
   - Current estimated driving time (live traffic)
   - Toll roads, motorway vs. country road mix
6. Get traffic forecast for the next 1–4 hours:
   - Rush hour patterns for departure area
   - Any reported incidents or roadworks
   - Optimal departure window to minimise travel time
7. Calculate 2–3 alternative routes with time and distance comparison

**STEP 4 – ENERGY FEASIBILITY**
8. Determine if current range is sufficient for the trip:
   - For BEV/PHEV: estimate consumption (motorway ~20% more than city)
   - Apply weather correction (cold/heat, wind)
   - Safety buffer: always target ≥ 15–20% SOC / ≥ 50 km range on arrival
9. If range is insufficient:
   - For electric: find fast charging stations (CCS/CHAdeMO) along route
     → Search PlugShare, ABRP, or similar for stations within 5 km of route
     → Select optimal stop (minimise detour + charging time)
     → Calculate required charging time for enough range to reach destination
   - For combustion/hybrid: find petrol stations along route

**STEP 5 – PRE-DEPARTURE CHARGING (if needed)**
10. If more charge is needed before departure:
    - Calculate how much additional SOC is required
    - Estimate charging time at typical charging power
    - Advise the user to start charging themselves via the vehicle's own app (the Tibber Data API cannot issue this command)

**STEP 6 – OPTIMAL DEPARTURE TIME**
11. Calculate the optimal departure window:
    - Earliest: when sufficient charge reached (if charging)
    - Latest: arrival deadline − driving time − weather buffer − charging stop time (if needed)
    - Best: balances traffic avoidance, charge level, and time constraints

**STEP 7 – REPORT**
```
🗺️  TRIP PLAN: → {destination}
────────────────────────────────────────────────
🚗 Vehicle: {{vehicle_name}} | 🔋 {{soc}}% / {{range}} km
📅 Calendar constraint: {{event_or_none}}

⏱️  DEPARTURE OPTIONS:
  🟢 Optimal: {{optimal_time}} → Arrive {{arrival_time}} ({{drive_time}} drive)
  🟡 Latest:  {{latest_departure}} → Arrive {{latest_arrival}} (on time: {{yes_no}})

⚡ CHARGING NEEDED: {{yes_no}}
  {{if yes: "User should charge to {{target_soc}}% by {{ready_time}} (+{{charge_minutes}} min)"}}
  {{if charging_stop: "Stop at {{station_name}} ({{km_from_start}} km) – {{charge_minutes}} min break"}}

🛣️  BEST ROUTE: {{route_name}} ({{distance}} km, {{time}} min)
   Alternative: {{alt_route}} saves/costs {{diff}} min

⚠️  ALERTS: {{traffic_warnings, weather_warnings}}

✅ NEXT ACTION: {{user starts charging / depart now / wait until HH:MM}}
```"""

    @mcp.prompt(
        name="zone_entry_restriction_check",
        title="Zone Entry Restriction Check",
        description=(
            "[PARTIALLY USABLE with Tibber: manufacturer/model and battery status work, but "
            "model year (needed for Euro-standard lookup) is unsupported by the read-only Tibber backend] "
            "Check whether the vehicle is allowed to enter a destination area "
            "considering environmental zones, EV-only zones, and congestion zones."
        ),
        tags={"zones", "restrictions", "ev", "compliance", "external-data", "navigation"}
    )
    def zone_entry_restriction_check(vehicle_id: str, destination: str) -> str:
        """Check zone entry restrictions for a destination.

        Args:
            vehicle_id: Vehicle name or VIN
            destination: Destination city, area, or address to check

        Returns:
            Prompt template for zone restriction check
        """
        return f"""Check if {vehicle_id} is allowed to enter {destination} and identify any zone restrictions:

**STEP 1 – VEHICLE DETAILS**
1. Get vehicle info using get_vehicle_info
   - Manufacturer, model (model year is always null with Tibber — ask the user if the Euro standard lookup needs it)
   - Vehicle type (electric, hybrid, combustion) via get_energy_status
2. For electric/hybrid: Get current SOC via get_battery_status (relevant for PHEV electric range)

**STEP 2 – ZONE RESTRICTION RESEARCH**
3. Research entry restrictions for {destination}:

   a) **Environmental/Low Emission Zones (LEZ/Umweltzone)**:
      - Search for "{destination} Umweltzone" or "{destination} low emission zone"
      - Determine required Euro standard (Euro 4, 5, 6)
      - Check dates/times when restrictions apply
      - Check if exemptions apply (electric, hybrid, new vehicles)

   b) **Zero Emission Zones (ZEZ / EV-only zones)**:
      - Search for "{destination} zero emission zone" or "{destination} EV only zone"
      - Check if purely electric vehicles have advantages
      - Check if PHEVs qualify (depends on electric range requirements)
      - Increasingly common in city centres: check Oslo, Amsterdam, London, etc.

   c) **Congestion Charge / City Toll**:
      - Search for "{destination} congestion charge" or "{destination} Citymaut"
      - Check charge amount, operating hours
      - EV exemptions (London, Stockholm, Milan, etc.)
      - Daily, weekly caps

   d) **Diesel Driving Bans (Dieselfahrverbote)**:
      - Relevant for German cities (Stuttgart, Hamburg, Berlin, Frankfurt, Munich, etc.)
      - Check affected streets or entire zones
      - Euro 5 diesel bans in some cities

   e) **Temporary Restrictions**:
      - Event-based restrictions (large events, races, markets)
      - Construction-related road closures
      - Weather-related emergency restrictions

**STEP 3 – VEHICLE COMPLIANCE CHECK**
4. Cross-reference vehicle details with zone requirements:
   - Does the vehicle meet the emission standard?
   - Is an EV exemption applicable?
   - Does PHEV qualify (check electric range requirement, typically ≥ 50 km)
   - Are there sticker/vignette requirements (German Umweltplakette: green = Euro 4+)

**STEP 4 – COST IMPACT**
5. Calculate cost impact:
   - Congestion/city toll: €{{amount}} per entry or per day
   - Parking surcharges for non-compliant vehicles (where applicable)
   - Fine risk if restrictions violated (mention as risk, not to encourage violation)
   - EV benefits: free/reduced city tolls, free parking in some zones

**STEP 5 – ROUTE ALTERNATIVES**
6. If restrictions apply:
   - Identify alternative routes that avoid restricted zones
   - Suggest park-and-ride options on the zone boundary
   - For PHEV: confirm sufficient electric range to drive in ZEZ in EV mode

**STEP 6 – REPORT**
```
🚦 ZONE CHECK: {{vehicle_name}} → {destination}
────────────────────────────────────────────────
🚗 Vehicle: {{manufacturer}} {{model}} | {{vehicle_type}}
   Emission standard: Euro {{standard}} | {{compliance_badge}}

📋 RESTRICTIONS FOR {destination}:
  {{zone_type}}: {{allowed_or_restricted}} {{details}}
  {{congestion_charge}}: {{amount_or_free}} {{hours}}
  {{diesel_ban}}: {{applies_or_not}}

✅ VERDICT: {{vehicle_name}} is {{ALLOWED / RESTRICTED / ALLOWED WITH CONDITIONS}} in {destination}

💶 COSTS: {{toll_costs_summary}}

💡 RECOMMENDATIONS:
  {{exemptions_available}}
  {{ev_benefits}}
  {{alternative_routes_or_park_and_ride}}

⚠️  ACTION NEEDED: {{register_zone / buy_vignette / use_alt_route / no_action}}
```"""

    @mcp.prompt(
        name="battery_health_optimizer",
        title="Battery Health & Charging Optimiser",
        description=(
            "[PARTIALLY USABLE with Tibber: charging/battery status and model info work "
            "(this prompt is advisory-only, no commands needed); vehicle location for the "
            "temperature lookup must come from the user since Tibber has no GPS data] "
            "Analyse current and ongoing charging behaviour and suggest optimisations "
            "to maximise battery longevity: target SOC, charge rate, and schedule."
        ),
        tags={"battery", "charging", "health", "optimization", "bev-phev", "proactive", "external-data"}
    )
    def battery_health_optimizer(vehicle_id: str) -> str:
        """Optimise battery charging strategy for long-term health.

        Args:
            vehicle_id: Vehicle name or VIN (BEV/PHEV)

        Returns:
            Prompt template for battery health optimisation workflow
        """
        return f"""Analyse and optimise the charging strategy for {vehicle_id} to maximise battery longevity:

**NOTE**: This prompt is advisory only — the Tibber Data API is read-only, so any recommended action must be carried out by the user via the vehicle's own app.

**STEP 1 – CURRENT STATE**
1. Get charging status using get_charging_status
   - Current SOC, target SOC, charging state
   - Is vehicle currently charging?
2. Get battery status using get_battery_status
   - SOC percentage, estimated range
3. Get vehicle info using get_vehicle_info
   - Model → used to look up battery specs
4. Ask the user for the vehicle's current location (needed for weather — Tibber has no GPS data)

**STEP 2 – WEATHER & TEMPERATURE**
5. Get current temperature at the vehicle's location:
   - Below 10°C: lithium-ion batteries charge less efficiently, higher internal resistance
   - Below 0°C: charging at high rates can cause lithium plating (permanent damage)
   - Above 35°C: accelerated degradation during charging
6. Assess if temperature-related charging caution is needed

**STEP 3 – BATTERY HEALTH RESEARCH**
7. Look up battery health guidelines for this specific vehicle:
   - Search for "{{manufacturer}} {{model}} battery longevity tips" or "{{model}} charging recommendations"
   - Standard best practices for lithium-ion:
     * Daily charge target: 80% (not 100%) for regular use
     * 100% only for long trips (and drive soon after reaching 100%)
     * Avoid staying at 100% for extended periods (>2 h)
     * Avoid deep discharge below 10–15%
     * Preferred daily operating range: 20–80%
8. Check manufacturer-specific recommendations (e.g. VW ID series: "home charging" mode targets 80%)

**STEP 4 – CURRENT BEHAVIOUR ASSESSMENT**
9. Assess current charging settings vs. best practice:
   - Current target SOC vs. recommended daily target (80%)
   - Is vehicle often charged to 100%? (infer from current settings)
10. Note any active charging if running

**STEP 5 – USAGE CONTEXT**
11. Ask or infer from calendar/context:
    - Is the user taking a long trip soon? → 100% charge may be justified
    - Normal daily commute (<100 km)? → 80% is optimal
    - Vehicle parked for >24 h? → avoid high SOC
12. If charging is currently active and target SOC > 80% with no long trip planned:
    - Suggest the user reduce target SOC in the vehicle's own app

**STEP 6 – CHARGING RATE ADVICE**
13. Temperature-based advice:
    - Below 0°C: recommend the user precondition the battery via the vehicle's app before charging
    - Above 35°C: consider charging at a cooler time of day

**STEP 7 – REPORT & RECOMMENDATIONS**
```
🔋 BATTERY HEALTH REPORT: {{vehicle_name}}
────────────────────────────────────────────────
📊 Current SOC: {{soc}}% | Target: {{target_soc}}% | Range: {{range}} km
⚡ Charging: {{state}} | Mode: {{charge_mode}}
🌡️  Temperature: {{temp}}°C → {{temp_risk_level}}

🏥 HEALTH ASSESSMENT:
  Target SOC:   {{target_soc}}% → {{good_warning_critical}} (recommended: 80% daily)
  Temperature:  {{temp_assessment}}
  Current SOC habits: {{assessment_based_on_data}}

💡 OPTIMISATION RECOMMENDATIONS:
  1. {{most_important_action}} – Reason: {{why}}
  2. {{second_action}}
  3. {{third_action}}

🔧 SETTINGS TO CHANGE (by the user, in the vehicle's own app):
  → Set charge limit to 80% for daily use
  → Enable reduced AC charging if available for overnight charging
  → {{other_vehicle_specific_settings}}
```"""

    logger.info("Registered 11 workflow prompts")
