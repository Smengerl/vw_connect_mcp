"""MCP Prompts for WeConnect vehicle workflows.

Provides pre-built prompt templates for common agentic vehicle operations.
Each prompt guides the AI through a complete workflow with safety checks.
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
        description="Start vehicle charging with battery level and connection checks",
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
        description="Pre-heat cabin and unlock vehicle for immediate departure",
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
        description="Comprehensive health check with battery, doors, climate, and location",
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
        description="Stop charging session and immediately prepare vehicle for departure",
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
        description="Monitor charging progress until target SOC is reached",
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
        description="Lock vehicle and stop climate systems for safe parking",
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
        description="Get vehicle position and flash lights to help find it in parking lot",
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
        description="Evaluate parking location safety using vehicle position and external crime/safety data",
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
        description="Prepare vehicle considering current and forecasted weather conditions",
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
        description="Verify if current charging allows meeting user's schedule considering travel time",
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
        description="Assess range adequacy for planned trip using battery status, route, weather, and charging infrastructure",
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
        description="Optimize battery preconditioning based on weather, trip requirements, and electricity pricing",
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
        description="Comprehensive pre-departure check combining vehicle state, weather, traffic, and route conditions",
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

    logger.info("Registered 13 workflow prompts (7 basic + 6 advanced with external data)")

