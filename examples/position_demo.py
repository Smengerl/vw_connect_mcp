#!/usr/bin/env python3
"""
Demo script showing how to use the get_position tool.

This demonstrates retrieving GPS coordinates and heading information
for vehicles in your WeConnect account.
"""

import sys
import os

# Add the src directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from tests.test_adapter import TestAdapter


def format_heading(degrees):
    """Convert heading degrees to compass direction."""
    if degrees is None:
        return "Unknown"
    
    directions = ["N", "NE", "E", "SE", "S", "SW", "W", "NW"]
    index = round(degrees / 45) % 8
    return f"{directions[index]} ({degrees}°)"


def format_coordinates(lat, lon):
    """Format GPS coordinates in a human-readable way."""
    if lat is None or lon is None:
        return "Unknown location"
    
    lat_dir = "N" if lat >= 0 else "S"
    lon_dir = "E" if lon >= 0 else "W"
    
    return f"{abs(lat):.4f}°{lat_dir}, {abs(lon):.4f}°{lon_dir}"


def main():
    print("=" * 60)
    print("Vehicle Position Demo")
    print("=" * 60)
    print()
    
    # Create adapter with mock data
    adapter = TestAdapter()
    
    # List all vehicles
    vehicles = adapter.list_vehicles()
    print(f"Found {len(vehicles)} vehicles:\n")
    
    for vehicle in vehicles:
        print(f"Vehicle: {vehicle.name} ({vehicle.model})")
        print(f"VIN: {vehicle.vin}")
        print("-" * 60)
        
        # Get position
        position = adapter.get_position(vehicle.vin)
        
        if position:
            print(f"📍 Location: {format_coordinates(position.latitude, position.longitude)}")
            print(f"🧭 Heading: {format_heading(position.heading)}")
            
            # Additional context based on coordinates
            if position.latitude and position.longitude:
                # Simple city detection (for demo purposes)
                if 48.0 < position.latitude < 48.3 and 11.3 < position.longitude < 11.8:
                    print(f"🏙️  Area: Munich, Germany")
                elif 52.3 < position.latitude < 52.7 and 13.2 < position.longitude < 13.6:
                    print(f"🏙️  Area: Berlin, Germany")
                
                # Generate Google Maps link
                maps_link = f"https://www.google.com/maps?q={position.latitude},{position.longitude}"
                print(f"🗺️  Map: {maps_link}")
        else:
            print("❌ Position unavailable")
        
        print()
    
    print("=" * 60)
    print("Demo: Advanced Position Usage")
    print("=" * 60)
    print()
    
    # Example: Calculate distance between vehicles
    if len(vehicles) >= 2:
        pos1 = adapter.get_position(vehicles[0].vin)
        pos2 = adapter.get_position(vehicles[1].vin)
        
        if pos1 and pos2 and pos1.latitude and pos2.latitude:
            # Simple distance calculation (Haversine formula)
            from math import radians, sin, cos, sqrt, atan2
            
            lat1, lon1 = radians(pos1.latitude), radians(pos1.longitude)
            lat2, lon2 = radians(pos2.latitude), radians(pos2.longitude)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            
            # Earth's radius in kilometers
            distance_km = 6371 * c
            
            print(f"Distance between {vehicles[0].name} and {vehicles[1].name}:")
            print(f"  {distance_km:.1f} km ({distance_km * 0.621371:.1f} miles)")
            print()
    
    # Example: Check if vehicle is in a specific area
    print("Example: Geofencing Check")
    print("-" * 60)
    
    home_location = {"lat": 48.1351, "lon": 11.5820, "name": "Home (Munich)"}
    radius_km = 1.0  # 1 km radius
    
    for vehicle in vehicles:
        position = adapter.get_position(vehicle.vin)
        
        if position and position.latitude:
            from math import radians, sin, cos, sqrt, atan2
            
            lat1, lon1 = radians(home_location["lat"]), radians(home_location["lon"])
            lat2, lon2 = radians(position.latitude), radians(position.longitude)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance_km = 6371 * c
            
            if distance_km <= radius_km:
                print(f"✅ {vehicle.name} is at {home_location['name']} ({distance_km:.2f} km)")
            else:
                print(f"❌ {vehicle.name} is away from {home_location['name']} ({distance_km:.1f} km)")
    
    print()
    print("=" * 60)


if __name__ == "__main__":
    main()
