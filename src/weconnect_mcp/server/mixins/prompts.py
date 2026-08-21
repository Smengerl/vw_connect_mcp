"""MCP Prompts for WeConnect vehicle workflows.

Provides pre-built prompt templates for common agentic vehicle operations.
Each prompt guides the AI through a complete workflow with safety checks.

With the Tibber backend, every prompt below relies on at least one of:
control commands (lock/unlock, climatization, charging start/stop, lights,
window heating), GPS position, door/window/tyre/light status, or
maintenance data — none of which the Tibber Data API provides (it is
read-only and limited to identity + SoC/range/charging-state, see
experiment/tibber-integration/TIBBER_API.md §5.2). Every prompt's
`description` below is prefixed with its actual usability against the
Tibber backend: NOT USABLE (depends entirely on unsupported
tools/data), PARTIALLY USABLE (some steps work, others will fail), or
USABLE (read-only, no unsupported dependency). The step-by-step prompt
bodies themselves are unchanged from the CarConnectivity-oriented design
— steps referencing unsupported tools will simply get a "not supported"
or "not found" response from the tool, which the AI assistant should
surface to the user rather than treat as a bug.
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
        title="Safe Start Charging",
        description="[PARTIALLY USABLE with Tibber: status checks work, but the actual start_charging step always fails — read-only backend] Start vehicle charging with battery level and connection checks",
        tags={"charging", "battery", "safety", "workflow"}
    )
    def safe_start_charging(vehicle_id: str) -> str:
        """Start vehicle charging with safety checks.
        
        Args:
            vehicle_id: Vehicle name or VIN to charge
            
        Returns:
            Prompt template for safe charging workflow
        """
        return f"""Start charging for vehicle {vehicle_id} with the following steps:

1. Get current battery status using get_battery_status tool
2. Check if battery level is well below target soc, which is typically 80% (don't charge if already full)
3. Check if vehicle is plugged in (charging_state == "connected" or "charging")
4. If checks pass, use start_charging tool
5. Wait 30 seconds
6. Verify charging started by checking get_charging_status again
7. Report final status to user

If any check fails, explain why charging cannot start and suggest next steps."""

    @mcp.prompt(
        name="prepare_vehicle_for_departure",
        title="Prepare Vehicle for Departure",
        description="[NOT USABLE with Tibber: climate control, unlock, and door status are all unsupported by the read-only Tibber backend] Pre-heat cabin and unlock vehicle for immediate departure",
        tags={"departure", "climate", "unlock", "comfort", "workflow"}
    )
    def prepare_vehicle_for_departure(vehicle_id: str, target_temp_celsius: float = 21.0) -> str:
        """Prepare vehicle for departure (climate + unlock).
        
        Args:
            vehicle_id: Vehicle name or VIN to prepare
            target_temp_celsius: Target cabin temperature (default: 21°C)
            
        Returns:
            Prompt template for departure preparation workflow
        """
        return f"""Prepare vehicle {vehicle_id} for departure with target temperature {target_temp_celsius}°C:

1. Check current vehicle state using get_vehicle_state
2. Verify vehicle is locked (for safety)
3. Start climatization at {target_temp_celsius}°C using start_climatization
4. Wait 2 minutes for climate to reach temperature
5. Check climatization status with get_climatization_status
6. Unlock vehicle using unlock_vehicle
7. Verify unlock succeeded with get_vehicle_doors
8. Report "Vehicle ready for departure" with current climate and door status

If any step fails, stop workflow and report issue to user."""

    @mcp.prompt(
        name="check_vehicle_health",
        title="Check Vehicle Health",
        description="[PARTIALLY USABLE with Tibber: battery/charging check works, but doors, climate, and location all return not-found — read-only backend, no such data] Comprehensive health check with battery, doors, climate, and location",
        tags={"diagnostics", "health", "status", "monitoring"}
    )
    def check_vehicle_health(vehicle_id: str) -> str:
        """Comprehensive vehicle health check.
        
        Args:
            vehicle_id: Vehicle name or VIN to check
            
        Returns:
            Prompt template for health check workflow
        """
        return f"""Perform comprehensive health check for vehicle {vehicle_id}:

1. Get basic vehicle info using get_vehicle_info
2. Get current vehicle state using get_vehicle_state
3. Get battery status using get_battery_status (if BEV/PHEV)
4. Get door/lock status using get_vehicle_doors
5. Get climatization status using get_climatization_status
6. Get current position using get_vehicle_position

Analyze results and provide summary:
- Overall health status (Good/Warning/Critical)
- Battery level and range (for electric vehicles)
- Security status (doors locked, windows closed)
- Active systems (climate, charging)
- Current location
- Any issues requiring attention

Format as structured report with sections."""

    @mcp.prompt(
        name="safe_stop_charging_and_prepare",
        title="Stop Charging and Prepare for Departure",
        description="[NOT USABLE with Tibber: stop_charging, climate control, and unlock are all unsupported by the read-only Tibber backend] Stop charging session and immediately prepare vehicle for departure",
        tags={"charging", "departure", "climate", "unlock", "workflow"}
    )
    def safe_stop_charging_and_prepare(vehicle_id: str) -> str:
        """Stop charging and prepare vehicle for immediate departure.
        
        Args:
            vehicle_id: Vehicle name or VIN
            
        Returns:
            Prompt template for stop charging + departure workflow
        """
        return f"""Stop charging and prepare {vehicle_id} for immediate departure:

1. Check if vehicle is currently charging using get_charging_status
2. If charging, stop it using stop_charging tool
3. Wait 10 seconds for charging to fully stop
4. Verify charging stopped (state should be "connected" not "charging")
5. Start climatization at 21°C using start_climatization
6. Unlock vehicle using unlock_vehicle
7. Report "Vehicle ready - charging stopped, climate started, doors unlocked"

Skip steps if preconditions not met (e.g., not charging)."""

    @mcp.prompt(
        name="monitor_charging_session",
        title="Monitor Charging Session",
        description="[PARTIALLY USABLE with Tibber: polling get_charging_status works, but the final stop_charging step always fails — read-only backend] Monitor charging progress until target SOC is reached",
        tags={"charging", "monitoring", "battery", "automation"}
    )
    def monitor_charging_session(vehicle_id: str, target_soc_percent: int = 80) -> str:
        """Monitor ongoing charging session until target reached.
        
        Args:
            vehicle_id: Vehicle name or VIN to monitor
            target_soc_percent: Target state of charge percentage (default: 80%)
            
        Returns:
            Prompt template for charging monitoring workflow
        """
        return f"""Monitor charging session for {vehicle_id} until {target_soc_percent}% SOC:

1. Check initial charging status using get_charging_status
2. Verify vehicle is actively charging (not just connected)
3. Report initial SOC and estimated time to {target_soc_percent}%
4. Poll get_charging_status every 5 minutes
5. Report progress updates (current SOC, charging power, time remaining)
6. When SOC >= {target_soc_percent}%, use stop_charging
7. Verify charging stopped successfully
8. Report final status (SOC reached, total time, energy added)

Note: This is a monitoring workflow - explain to user it requires periodic checks, not continuous blocking."""

    @mcp.prompt(
        name="secure_vehicle",
        title="Secure Vehicle",
        description="[NOT USABLE with Tibber: lock, climate control, and door status are all unsupported by the read-only Tibber backend] Lock vehicle and stop climate systems for safe parking",
        tags={"security", "lock", "climate", "safety", "workflow"}
    )
    def secure_vehicle(vehicle_id: str) -> str:
        """Secure vehicle (lock, stop climate, verify).
        
        Args:
            vehicle_id: Vehicle name or VIN to secure
            
        Returns:
            Prompt template for vehicle securing workflow
        """
        return f"""Secure vehicle {vehicle_id} for leaving unattended:

1. Check current climatization status using get_climatization_status
2. If climate is running, stop it using stop_climatization
3. Wait 5 seconds
4. Lock vehicle using lock_vehicle
5. Wait 5 seconds for lock command to complete
6. Verify all doors locked using get_vehicle_doors
7. Verify climate stopped using get_climatization_status again
8. Report "Vehicle secured - all doors locked, climate off"

If lock verification fails, retry once, then report security issue to user."""

    @mcp.prompt(
        name="locate_and_flash",
        title="Locate and Flash Lights",
        description="[NOT USABLE with Tibber: GPS position and light control are both unsupported by the read-only Tibber backend] Get vehicle position and flash lights to help find it in parking lot",
        tags={"location", "lights", "parking", "convenience"}
    )
    def locate_and_flash(vehicle_id: str, duration_seconds: int = 10) -> str:
        """Get vehicle position and flash lights to help locate it.
        
        Args:
            vehicle_id: Vehicle name or VIN to locate
            duration_seconds: How long to flash lights (default: 10 seconds)
            
        Returns:
            Prompt template for locate vehicle workflow
        """
        return f"""Help user locate vehicle {vehicle_id}:

1. Get current position using get_vehicle_position
2. Report coordinates and formatted address to user
3. Flash lights for {duration_seconds} seconds using flash_lights
4. Report "Lights flashing for {duration_seconds}s at [address]"
5. Optionally suggest opening maps app with coordinates

This helps user find vehicle in parking lot or unfamiliar location."""

    @mcp.prompt(
        name="assess_parking_safety",
        title="Assess Parking Location Safety",
        description="[NOT USABLE with Tibber: this prompt depends entirely on GPS position and door-lock status, both unsupported by the read-only Tibber backend] Evaluate parking location safety using vehicle position and external crime/safety data",
        tags={"safety", "location", "security", "parking", "external-data"}
    )
    def assess_parking_safety(vehicle_id: str) -> str:
        """Assess whether parking location is safe using external data sources.
        
        Args:
            vehicle_id: Vehicle name or VIN to check
            
        Returns:
            Prompt template for parking safety assessment
        """
        return f"""Assess parking safety for vehicle {vehicle_id}:

1. Get current vehicle position using get_vehicle_position
2. Extract coordinates and address from position data
3. Search for local crime statistics and safety ratings for this area
   - Use web search or crime database APIs
   - Look for recent incidents within 0.5km radius
   - Check neighborhood safety ratings
4. Check time of day and lighting conditions
   - Is it getting dark soon? Check sunset time for location
5. Assess parking type (street parking, garage, private lot)
6. Get vehicle lock status using get_vehicle_doors
7. Provide safety assessment:
   - Safety rating (Safe/Moderate/Unsafe)
   - Specific concerns if any (high crime area, poor lighting, etc.)
   - Recommendations (lock vehicle, avoid overnight parking, etc.)
8. If unsafe, suggest alternative parking locations nearby

Combine vehicle data with external safety information to provide comprehensive assessment."""

    @mcp.prompt(
        name="weather_optimized_departure",
        title="Weather-Optimized Departure Preparation",
        description="[NOT USABLE with Tibber: GPS position, climate control, window heating, and unlock are all unsupported by the read-only Tibber backend] Prepare vehicle considering current and forecasted weather conditions",
        tags={"weather", "departure", "climate", "comfort", "external-data"}
    )
    def weather_optimized_departure(vehicle_id: str, departure_time_minutes: int = 15) -> str:
        """Prepare vehicle for departure optimized for weather conditions.
        
        Args:
            vehicle_id: Vehicle name or VIN to prepare
            departure_time_minutes: Minutes until departure (default: 15)
            
        Returns:
            Prompt template for weather-optimized departure
        """
        return f"""Prepare {vehicle_id} for departure in {departure_time_minutes} minutes with weather optimization:

1. Get vehicle position using get_vehicle_position
2. Get current weather and forecast for vehicle location
   - Current temperature, precipitation, humidity
   - Forecast for next 2 hours
   - Check for rain, snow, ice, extreme heat/cold
3. Calculate optimal cabin temperature based on:
   - Outside temperature
   - Weather conditions (add 2°C if raining/cold)
   - User comfort preferences
4. Determine pre-heating/cooling strategy:
   - Cold weather (<5°C): Start climate {departure_time_minutes} min early, target 22°C
   - Hot weather (>28°C): Start climate {departure_time_minutes} min early, target 20°C
   - Moderate: Start climate 5-10 min before departure
5. Start climatization using start_climatization with calculated temperature
6. If rain/snow expected, check if window heating needed using start_window_heating
7. Unlock vehicle 2 minutes before departure using unlock_vehicle
8. Report preparation status with weather context:
   - "Vehicle prepared for departure. Outside: {{temp}}°C and {{conditions}}. Cabin: {{target_temp}}°C"

Combines real-time weather with vehicle climate control for optimal comfort."""

    @mcp.prompt(
        name="charging_schedule_feasibility",
        title="Check Charging Schedule Feasibility",
        description="[PARTIALLY USABLE with Tibber: charging/battery status works, but GPS position (needed for route calculation) is unsupported by the read-only Tibber backend] Verify if current charging allows meeting user's schedule considering travel time",
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
   - Charging power (kW)
   - Estimated time to 80% SOC
2. Get battery status using get_battery_status
   - Current range estimate
3. Get current vehicle position using get_vehicle_position
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
   - Whether to stop charging early or continue
   - Alternative routes if faster

Combines charging data, navigation, and time management for schedule feasibility."""

    @mcp.prompt(
        name="range_anxiety_advisor",
        title="Range Anxiety Advisor",
        description="[PARTIALLY USABLE with Tibber: battery status works, but GPS position (needed for the route/weather lookup) is unsupported by the read-only Tibber backend] Assess range adequacy for planned trip using battery status, route, weather, and charging infrastructure",
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
2. Get vehicle position using get_vehicle_position
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
        description="[PARTIALLY USABLE with Tibber: battery/charging status works, but GPS position and the actual start_climatization step are unsupported by the read-only Tibber backend] Optimize battery preconditioning based on weather, trip requirements, and electricity pricing",
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
   - get_battery_status: Current SOC, temperature
   - get_charging_status: Charging state, power level
2. Get vehicle location using get_vehicle_position
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
7. Check if cabin preheating needed using start_climatization
8. Provide optimization plan:
   - "Start charging at [time] for optimal rates (€{{price}}/kWh)"
   - "Begin preconditioning at [time] for {{temp}}°C weather"
   - "Estimated cost: €{{amount}} vs €{{amount_peak}} during peak hours"
   - "Expected range: {{range}}km (vs {{reduced_range}}km without preconditioning)"

Combines weather, electricity pricing, and battery thermal management for optimal efficiency."""

    @mcp.prompt(
        name="automated_travel_readiness_check",
        title="Automated Travel Readiness Check",
        description="[PARTIALLY USABLE with Tibber: battery status works, but door status, GPS position, and climate control are unsupported by the read-only Tibber backend] Comprehensive pre-departure check combining vehicle state, weather, traffic, and route conditions",
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
        return f"""Perform complete travel readiness check for {vehicle_id} to {destination_address} at {departure_time}:

**VEHICLE STATUS:**
1. Get vehicle state using get_vehicle_state
2. Get battery status using get_battery_status (if electric)
   - SOC percentage and range
   - Check if charging needed
3. Get door/lock status using get_vehicle_doors
   - Verify all doors closed properly
4. Get vehicle position using get_vehicle_position

**ROUTE ANALYSIS:**
5. Calculate route to {destination_address}:
   - Distance and estimated time
   - Current traffic conditions
   - Accidents or road closures
   - Alternative routes available
6. Check construction zones or delays on route
7. For electric vehicles: Identify charging stations along route

**WEATHER CONDITIONS:**
8. Get weather forecast for:
   - Departure location at {departure_time}
   - Route conditions
   - Destination weather
9. Check for weather warnings:
   - Heavy rain, snow, ice, fog
   - Extreme temperatures
   - Storm warnings

**TIMING ANALYSIS:**
10. Calculate if departure time is realistic:
    - If charging: time remaining vs. departure time
    - Traffic delays vs. available time buffer
    - Weather impact on driving time (+20% in bad weather)

**PREPARATION ACTIONS:**
11. If needed, start climatization for comfort
12. If weather is bad, suggest starting window heating
13. Verify vehicle is unlocked if departure imminent

**COMPREHENSIVE REPORT:**
Provide structured readiness report:
- ✅/⚠️/❌ Vehicle Status (battery, doors, systems)
- ✅/⚠️/❌ Route Conditions (traffic, weather, delays)
- ✅/⚠️/❌ Timing Feasibility (enough time for charging/driving)
- 📋 Action Items:
  - "Start charging now" / "Depart in 5 minutes" / "Delay departure by X minutes"
  - Weather warnings: "Heavy rain expected - allow extra time"
  - Route issues: "Accident on A3 - use alternative route via B12"
- 🚗 Final Recommendation: "Ready to depart" / "Wait for charging" / "Reschedule advised"

Ultimate comprehensive check combining all vehicle and external data sources."""

    # ─────────────────────────────────────────────────────────────────────────
    # INTELLIGENT PROACTIVE PROMPTS  (new)
    # ─────────────────────────────────────────────────────────────────────────

    @mcp.prompt(
        name="service_planning_advisor",
        title="Service & Maintenance Planning Advisor",
        description=(
            "[NOT USABLE with Tibber: maintenance data, odometer, tyre status, and GPS position "
            "(for workshop search) are all unsupported by the read-only Tibber backend] "
            "Evaluate upcoming service needs based on odometer, maintenance data, "
            "and manufacturer intervals. Optionally find nearby workshops and book appointments."
        ),
        tags={"maintenance", "service", "planning", "external-data", "proactive"}
    )
    def service_planning_advisor(vehicle_id: str) -> str:
        """Proactive service planning combining vehicle maintenance data with workshop search.

        Args:
            vehicle_id: Vehicle name or VIN

        Returns:
            Prompt template for intelligent service planning workflow
        """
        return f"""Perform intelligent service and maintenance planning for {vehicle_id}:

**NOTE**: All vehicle tools only work reliably when the vehicle is parked and not in active use.

**STEP 1 – VEHICLE DATA**
1. Get vehicle info using get_vehicle_info
   - Manufacturer, model, year, current odometer (km)
2. Get maintenance info using get_maintenance_info
   - Next inspection due date and distance
   - Oil-service due date and distance (if combustion/hybrid)
3. Get energy status using get_energy_status
   - For electric vehicles: note battery health indicators
4. Get current position using get_vehicle_position (needed for workshop search later)

**STEP 2 – URGENCY ASSESSMENT**
5. Calculate urgency for each maintenance item:
   - Distance remaining to next service (from odometer vs. due distance)
   - Days remaining to next service date (from today vs. due date)
   - Classify urgency:
     - 🔴 URGENT: ≤ 500 km or ≤ 14 days remaining
     - 🟡 DUE SOON: ≤ 2 000 km or ≤ 30 days remaining
     - 🟢 OK: > 2 000 km and > 30 days remaining
6. Check for any active warnings reported by the vehicle (from vehicle state or maintenance data)
7. For electric vehicles additionally assess:
   - Battery degradation hints (if available)
   - Tyre pressure status (from get_physical_status)

**STEP 3 – MANUFACTURER INTERVAL LOOKUP**
8. Look up the manufacturer-recommended service intervals for this vehicle:
   - Search web for "{{manufacturer}} {{model}} {{year}} Inspektionsintervall" or service schedule
   - Standard VW/Audi/Skoda/Seat intervals: 30 000 km or 12 months (Longlife: up to 30 000 km / 2 years)
   - If found, compare with current maintenance data and flag any discrepancy

**STEP 4 – WORKSHOP SEARCH (if urgency is URGENT or DUE SOON)**
9. Use vehicle position for a nearby workshop search:
   - Search for authorised {{manufacturer}} dealers within 20 km
   - Also consider independent workshops with good ratings
   - Collect: name, address, phone number, opening hours, rating, distance
   - Prioritise authorised dealers for warranty-relevant work
10. Check online booking availability for top 3 workshops

**STEP 5 – REPORT & RECOMMENDATIONS**
Provide a structured report:

```
🔧 SERVICE STATUS FOR {{vehicle_name}} ({{odometer}} km)
────────────────────────────────────────────────
{{urgency_icon}} Next Inspection: {{due_date}} (in {{days_left}} days / {{km_left}} km)
{{urgency_icon}} Oil Service: {{due_date}} (in {{days_left}} days / {{km_left}} km) [if applicable]

📋 RECOMMENDED ACTIONS:
  1. [Action] – Reason
  2. ...

🏭 NEARBY WORKSHOPS:
  1. {{name}} ({{distance}} km) – {{rating}}⭐ – Tel: {{phone}}
     Available slots: [date/time if found]
  2. ...

💡 TIPS:
  - [Manufacturer-specific advice, e.g. Longlife oil, tyre rotation]
  - [Cost estimate if available]
```

If no action is needed, confirm: "Vehicle {{vehicle_id}} is up to date – next service in {{km}} km / {{days}} days." """

    @mcp.prompt(
        name="intelligent_charging_plan",
        title="Intelligent Cost-Optimised Charging Plan",
        description=(
            "[PARTIALLY USABLE with Tibber: charging/battery status works, but GPS position and "
            "the actual start_charging/stop_charging steps are unsupported by the read-only Tibber backend] "
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

**NOTE**: Vehicle commands (start_charging, stop_charging) only work when the vehicle is parked and plugged in.

**STEP 1 – CURRENT VEHICLE STATE**
1. Get charging status using get_charging_status
   - Is the vehicle currently plugged in? (is_plugged_in)
   - Current SOC and target SOC
   - Current charging power (kW)
2. Get battery status using get_battery_status
   - Current range estimate
3. Get vehicle position using get_vehicle_position
   - Needed for weather and electricity price lookup

**STEP 2 – WEATHER FORECAST**
4. Get weather forecast for the vehicle location:
   - Overnight low temperature (between now and {target_departure_time})
   - Temperature at {target_departure_time}
   - Precipitation (rain, snow, frost)
5. Estimate weather impact on battery range:
   - Below 0°C: range reduced by ~25–35 %, battery needs preconditioning
   - 0–10°C: range reduced by ~10–20 %
   - Above 20°C (with AC): range reduced by ~5–10 %
6. Determine if windows are closed and vehicle secured (get_physical_status)
   - Open windows in cold/wet weather = additional climate load

**STEP 3 – ELECTRICITY PRICE FORECAST**
7. Fetch electricity spot prices or time-of-use tariffs for the overnight period:
   - Use location (country/region) from vehicle position
   - Search for ENTSO-E day-ahead prices, Tibber, aWATTar, or similar for the region
   - Identify cheapest 4-hour window between now and {target_departure_time}
   - Identify most expensive periods to avoid
8. Calculate cost comparison:
   - Cheapest window price per kWh
   - Average/peak price per kWh
   - Potential savings by shifting charging

**STEP 4 – REQUIRED ENERGY CALCULATION**
9. Calculate energy needed:
   - Target SOC for departure (80 % default, 100 % if long trip)
   - Weather-adjusted range target (add buffer for cold weather)
   - Energy gap = (target_soc - current_soc) × battery_capacity_kWh
   - Charging time at current power = energy_gap / charging_power_kW
10. Include preconditioning energy if temperature < 5°C (approx. 3–5 kWh extra)

**STEP 5 – OPTIMAL SCHEDULE**
11. Calculate optimal charging schedule:
    - Fit charging window into cheapest electricity period
    - Ensure charging completes at least 30 min before {target_departure_time} (for preconditioning)
    - If vehicle is already charging: assess whether to pause and restart at cheaper time
    - If not plugged in: remind user to connect cable

**STEP 6 – ACTIONS & REPORT**
12. If vehicle is plugged in and charging should start/stop now:
    - Use start_charging or stop_charging as appropriate
    - Verify with get_charging_status
13. Provide the plan:

```
⚡ CHARGING PLAN FOR {{vehicle_name}}
────────────────────────────────────────────────
🔋 Current SOC: {{soc}}% → Target: {{target_soc}}% ({{energy_needed}} kWh)
🌡️  Overnight low: {{temp}}°C → Range impact: {{impact}}%
💶 Cheapest window: {{start_time}}–{{end_time}} @ {{price}} ct/kWh
💰 Estimated cost: €{{cost}} (saving €{{saving}} vs. charging now)

📅 RECOMMENDED SCHEDULE:
  {{start_time}}: Start charging ({{charging_power}} kW)
  {{end_time}}: Charging complete at {{target_soc}}%
  {{precondition_time}}: Begin cabin preconditioning ({{target_temp}}°C)

⚠️  ALERTS:
  [Weather: Frost expected – preconditioning recommended]
  [Windows: Check if closed before overnight parking]

✅ ACTION TAKEN: [charging started / scheduled / no action needed]
```"""

    @mcp.prompt(
        name="proactive_preconditioning_suggestion",
        title="Proactive Preconditioning Suggestion",
        description=(
            "[NOT USABLE with Tibber: GPS position, climate status/control, and window heating "
            "are all unsupported by the read-only Tibber backend] "
            "Suggest and optionally start cabin preconditioning based on weather forecast, "
            "user calendar events, and current vehicle state."
        ),
        tags={"climate", "preconditioning", "weather", "calendar", "comfort", "proactive", "external-data"}
    )
    def proactive_preconditioning_suggestion(vehicle_id: str) -> str:
        """Suggest proactive preconditioning based on weather and calendar.

        Args:
            vehicle_id: Vehicle name or VIN

        Returns:
            Prompt template for proactive preconditioning workflow
        """
        return f"""Proactively suggest and manage cabin preconditioning for {vehicle_id}:

**NOTE**: Climatization commands only work when the vehicle is parked (not in use).

**STEP 1 – USER CALENDAR CHECK**
1. Check the user's calendar for upcoming appointments or events in the next 4 hours:
   - Departure times, meeting locations, travel events
   - Look for keywords: "car", "drive", "pick up", address fields
   - Identify the most imminent planned departure
2. Ask the user if no calendar is available: "When do you next plan to use the vehicle?"

**STEP 2 – VEHICLE STATE**
3. Get vehicle position using get_vehicle_position
4. Get climate status using get_climate_status
   - Is climatization already running?
   - Current settings
5. Get charging status using get_charging_status (BEV/PHEV)
   - Using external power for preconditioning saves battery range

**STEP 3 – WEATHER AT DEPARTURE TIME**
6. Get weather forecast for vehicle location at planned departure time:
   - Current outside temperature
   - Temperature at planned departure
   - Precipitation: rain, snow, frost, fog, hail
   - Wind chill factor
7. Determine preconditioning need:
   - ❄️  Below 0°C: STRONGLY recommended (cabin comfort + battery warmup for BEV)
   - 🌧️  Rain/snow: Recommended (defogging, defrost)
   - ☀️  Above 28°C: Recommended (cabin cooling before entry)
   - 🟢 Mild conditions: Optional comfort improvement
8. For BEV/PHEV: preconditioning while plugged in saves significant range (up to 15%)

**STEP 4 – OPTIMAL START TIME**
9. Calculate when to start preconditioning:
   - Cold weather (<0°C): 20–30 min before departure
   - Moderate cold (0–10°C): 10–15 min before departure
   - Rain/fog: 5–10 min before departure (defogging)
   - Hot weather (>28°C): 10–15 min before departure
   - Heating speed: cabin reaches target in ~10–15 min under normal conditions

**STEP 5 – TARGET TEMPERATURE**
10. Determine optimal target temperature:
    - Standard comfort: 21°C
    - Cold weather: 22–23°C (slightly warmer for comfort)
    - Hot weather: 19–20°C (cooler for relief from heat)
    - User preference: check previous settings in climate status if available

**STEP 6 – SUGGESTION & ACTION**
11. Present suggestion to user:
    "Based on {{weather_conditions}} at {{departure_time}}, I recommend starting preconditioning at {{start_time}} to reach {{target_temp}}°C.
     {{vehicle_is_plugged_in ? 'Vehicle is plugged in – preconditioning will use grid power (no range loss).' : 'Note: Vehicle is not plugged in – preconditioning uses ~3–5 kWh of battery.'}}
    Shall I start it automatically?"

12. If user confirms (or if this is automated):
    - Use start_climatization with target temperature
    - For frost/fog: also start_window_heating
    - Verify with get_climate_status

**STEP 7 – REPORT**
```
🌡️  PRECONDITIONING PLAN FOR {{vehicle_name}}
────────────────────────────────────────────────
📅 Next departure: {{departure_time}} (from calendar: "{{event_title}}")
🌤️  Weather: {{temp}}°C, {{conditions}}
🔌 Power source: {{grid_or_battery}}

▶️  Start preconditioning: {{start_time}}
🎯 Target temperature: {{target_temp}}°C
🪟 Window heating: {{yes_no}}

✅ Status: {{action_taken}}
``` """

    @mcp.prompt(
        name="trip_optimizer",
        title="Trip Departure & Charging Stop Optimizer",
        description=(
            "[PARTIALLY USABLE with Tibber: energy/range status works, but GPS position and the "
            "actual start_charging step are unsupported by the read-only Tibber backend] "
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
        return f"""Optimise the trip from current location to {destination} for {vehicle_id}:

**STEP 1 – VEHICLE ENERGY STATE**
1. Get energy status using get_energy_status
   - Current SOC / fuel level and estimated range
   - Vehicle type (electric / hybrid / combustion)
2. Get vehicle position using get_vehicle_position (starting point)

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
10. If vehicle is plugged in and more charge is needed:
    - Calculate how much additional SOC is required
    - Estimate charging time at current power
    - If plugged in, check whether to charge more before departure
    - Use start_charging if needed, with verification via get_charging_status

**STEP 6 – OPTIMAL DEPARTURE TIME**
11. Calculate the optimal departure window:
    - Earliest: when sufficient charge reached (if charging) + 5 min preconditioning buffer
    - Latest: arrival deadline − driving time − weather buffer − charging stop time (if needed)
    - Best: balances traffic avoidance, charge level, and time constraints
12. If cold (<5°C): add preconditioning start 15–20 min before optimal departure

**STEP 7 – REPORT**
```
🗺️  TRIP PLAN: {{start}} → {destination}
────────────────────────────────────────────────
🚗 Vehicle: {{vehicle_name}} | 🔋 {{soc}}% / {{range}} km
📅 Calendar constraint: {{event_or_none}}

⏱️  DEPARTURE OPTIONS:
  🟢 Optimal: {{optimal_time}} → Arrive {{arrival_time}} ({{drive_time}} drive)
  🟡 Latest:  {{latest_departure}} → Arrive {{latest_arrival}} (on time: {{yes_no}})

⚡ CHARGING NEEDED: {{yes_no}}
  {{if yes: "Charge to {{target_soc}}% by {{ready_time}} (+{{charge_minutes}} min)"}}
  {{if charging_stop: "Stop at {{station_name}} ({{km_from_start}} km) – {{charge_minutes}} min break"}}

🛣️  BEST ROUTE: {{route_name}} ({{distance}} km, {{time}} min)
   Alternative: {{alt_route}} saves/costs {{diff}} min

⚠️  ALERTS: {{traffic_warnings, weather_warnings}}

✅ NEXT ACTION: {{start charging / start preconditioning / depart now / wait until HH:MM}}
``` """

    @mcp.prompt(
        name="parking_time_monitor",
        title="Parking Time & Cost Monitor",
        description=(
            "[NOT USABLE with Tibber: this prompt depends entirely on GPS position, "
            "unsupported by the read-only Tibber backend] "
            "Monitor parking duration and costs based on vehicle position, "
            "local parking regulations, and remind the user before time expires."
        ),
        tags={"parking", "location", "cost", "reminder", "external-data", "proactive"}
    )
    def parking_time_monitor(vehicle_id: str, max_parking_minutes: int = 120) -> str:
        """Monitor parking time and costs with reminders.

        Args:
            vehicle_id: Vehicle name or VIN
            max_parking_minutes: Maximum allowed or desired parking time in minutes (default: 120)

        Returns:
            Prompt template for parking time monitoring workflow
        """
        return f"""Monitor parking time and costs for {vehicle_id} (limit: {max_parking_minutes} min):

**STEP 1 – VEHICLE POSITION**
1. Get current vehicle position using get_vehicle_position
   - Latitude, longitude, heading
   - Derive street address from coordinates (reverse geocoding)
2. Verify vehicle is parked (heading/speed context if available, or assume parked)

**STEP 2 – PARKING REGULATIONS LOOKUP**
3. Look up parking regulations for the current location:
   - Search for local parking rules: maximum stay, time restrictions, permit zones
   - Check for blue zones, resident-only zones, loading zones
   - Check operating hours of paid parking in this area
   - Sources: city council websites, ParkingEye, OpenStreetMap parking data, Google Maps
4. Determine parking type:
   - Free unlimited parking
   - Time-limited free parking (e.g. max 2h)
   - Paid parking (hourly rate)
   - Permit/resident zone (check if user has permit)
   - No-parking or restricted zone (ALERT immediately if so!)

**STEP 3 – COST ESTIMATION**
5. Calculate parking costs:
   - Find current hourly/daily rate for this location (search parking operators)
   - Calculate cost for {max_parking_minutes} minutes
   - Calculate cost for full day if relevant
   - Check if cheaper alternatives exist within 200 m (search nearby parking)
6. For electric vehicles: Check if charging is available at this parking spot
   - Parking with free/paid charging
   - Compare charging cost vs. energy needed

**STEP 4 – ZONE RESTRICTIONS & ENTRY RESTRICTIONS**
7. Check for any area-specific entry or parking restrictions:
   - Environmental zones (Umweltzone, LEZ) – does the vehicle meet the requirements?
   - EV-only or zero-emission zones
   - Time-based restrictions (e.g. market day, snow clearing)
   - Get vehicle type from get_vehicle_info to verify zone eligibility

**STEP 5 – REMINDER CALCULATION**
8. Calculate reminder times based on parking limit of {max_parking_minutes} minutes:
   - First reminder: at 75% of allowed time (or 15 min before limit)
   - Final reminder: 10 minutes before limit
   - Urgent alert: at limit / when payment runs out
9. Note parking start time (current time) and calculate expiry

**STEP 6 – REPORT & MONITORING**
Provide initial parking status report:

```
🅿️  PARKING STATUS FOR {{vehicle_name}}
────────────────────────────────────────────────
📍 Location: {{address}}
🕐 Parked at: {{park_time}} | Limit: {max_parking_minutes} min → Expires: {{expiry_time}}
💶 Estimated cost: €{{cost}} ({{rate}}/h) [or: FREE]

📋 REGULATIONS:
  {{parking_type}} – {{restrictions_summary}}
  {{zone_restrictions_if_any}}

⏰ REMINDERS SET:
  🟡 First warning: {{warning_time}} (15 min before expiry)
  🔴 Final alert:   {{alert_time}} (10 min before expiry)

⚡ NEARBY CHARGING: {{yes_no_with_details}}

⚠️  ALERTS: {{any_immediate_issues}}

💡 TIP: {{cheaper_alternative_if_found}}
```

10. When reminder times are reached (if this is an automated monitoring loop):
    - Send reminder: "⏰ Parking for {{vehicle_name}} expires in {{minutes}} min at {{location}}!"
    - At expiry: "🔴 Parking time expired for {{vehicle_name}} at {{location}}. Please return or pay."
    - Suggest: move vehicle, extend ticket, or nearby alternative parking"""

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
   - Manufacturer, model, year
   - Vehicle type (electric, hybrid, combustion) via get_energy_status
   - Euro emission standard (derive from year + manufacturer if not directly available)
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
🚗 Vehicle: {{manufacturer}} {{model}} {{year}} | {{vehicle_type}}
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
``` """

    @mcp.prompt(
        name="battery_health_optimizer",
        title="Battery Health & Charging Optimiser",
        description=(
            "[PARTIALLY USABLE with Tibber: charging/battery status and model info work "
            "(this prompt is advisory-only, no commands needed), but GPS position (for the "
            "temperature lookup) is unsupported by the read-only Tibber backend] "
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

**NOTE**: This prompt is for BEV/PHEV vehicles only. Commands only execute when vehicle is parked.

**STEP 1 – CURRENT STATE**
1. Get charging status using get_charging_status
   - Current SOC, target SOC, charging state
   - Charging power (kW), charge mode
   - Is vehicle currently charging?
2. Get battery status using get_battery_status
   - SOC percentage, estimated range
3. Get vehicle info using get_vehicle_info
   - Model, year → used to look up battery specs
4. Get vehicle position using get_vehicle_position
   - Needed for weather (temperature affects battery chemistry)

**STEP 2 – WEATHER & TEMPERATURE**
5. Get current temperature at vehicle location:
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
   - Vehicle-specific: some models have built-in buffer (e.g. Tesla reports 100% but actual is ~95%)
8. Check manufacturer-specific recommendations (e.g. VW ID series: "home charging" mode targets 80%)

**STEP 4 – CURRENT BEHAVIOUR ASSESSMENT**
9. Assess current charging settings vs. best practice:
   - Current target SOC vs. recommended daily target (80%)
   - Is vehicle often charged to 100%? (infer from current settings)
   - Charging speed: AC (gentle, preferred for daily) vs. DC fast charging (limit when possible)
   - Is vehicle left plugged in at 100% for long periods?
10. Note any active charging if running (and current power level)

**STEP 5 – USAGE CONTEXT**
11. Ask or infer from calendar/context:
    - Is the user taking a long trip soon? → 100% charge may be justified
    - Normal daily commute (<100 km)? → 80% is optimal
    - Vehicle parked for >24 h? → avoid high SOC
12. If charging is currently active and target SOC > 80% with no long trip planned:
    - Suggest reducing target SOC (user action in vehicle app, as direct SOC target setting
      may not be available via this API)

**STEP 6 – CHARGING RATE OPTIMISATION**
13. Assess current charging power:
    - For overnight charging: slower AC charging (7–11 kW) preferred over fast DC
    - DC fast charging generates more heat → use sparingly
    - If available: check if vehicle supports reduced charging current setting
14. Temperature-based rate advice:
    - Below 0°C: recommend preconditioning battery before charging (start_climatization)
    - Above 35°C: consider charging at cooler time of day

**STEP 7 – REPORT & RECOMMENDATIONS**
```
🔋 BATTERY HEALTH REPORT: {{vehicle_name}}
────────────────────────────────────────────────
📊 Current SOC: {{soc}}% | Target: {{target_soc}}% | Range: {{range}} km
⚡ Charging: {{state}} @ {{power}} kW | Mode: {{charge_mode}}
🌡️  Temperature: {{temp}}°C → {{temp_risk_level}}

🏥 HEALTH ASSESSMENT:
  Target SOC:   {{target_soc}}% → {{good_warning_critical}} (recommended: 80% daily)
  Charge speed: {{ac_dc}} → {{good_warning}}
  Temperature:  {{temp_assessment}}
  Current SOC habits: {{assessment_based_on_data}}

💡 OPTIMISATION RECOMMENDATIONS:
  1. {{most_important_action}} – Reason: {{why}}
  2. {{second_action}}
  3. {{third_action}}

📈 ESTIMATED IMPACT:
  Following these recommendations can extend battery life by {{X}}% over {{Y}} years.
  (Based on manufacturer data and EV battery longevity research)

🔧 SETTINGS TO CHANGE:
  → In VW ID / MyVW app: Set charge limit to 80% for daily use
  → Enable "Reduced AC charging" if available for overnight charging
  → {{other_vehicle_specific_settings}}

✅ IMMEDIATE ACTION: {{any_action_taken_via_api}}
``` """

    logger.info("Registered 20 workflow prompts (7 basic + 6 advanced + 7 intelligent proactive)")

