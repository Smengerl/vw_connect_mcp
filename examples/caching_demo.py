#!/usr/bin/env python3
"""
Demo: Caching System

This script demonstrates the caching mechanism that prevents excessive
API calls to the Tibber Data API and helps stay within Tibber's polite-
polling recommendation.

Key features:
- Configurable cache duration (default: 300 seconds / 5 minutes)
- Automatic cache expiration check
- Transparent caching (no code changes needed)
- Logs cache hits/misses for debugging
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from weconnect_mcp.adapter.mixins.cache_mixin import CACHE_DURATION_SECONDS


def print_section(title: str):
    """Print a formatted section header"""
    print(f"\n{'='*70}")
    print(f"  {title}")
    print(f"{'='*70}\n")


def demo_cache_configuration():
    """Show cache configuration"""
    print_section("⚙️ CACHE CONFIGURATION")

    print(f"Cache Duration: {CACHE_DURATION_SECONDS} seconds ({CACHE_DURATION_SECONDS/60:.1f} minutes)")
    print()
    print("How it works:")
    print("  1. First API call: Fetches data from the Tibber Data API")
    print("  2. Subsequent calls within cache window: Use cached data")
    print("  3. After cache expires: Automatically fetches fresh data")
    print()
    print("Benefits:")
    print("  • Stays within Tibber's polite-polling recommendation")
    print("  • Faster response times for repeated queries")
    print("  • No code changes needed (automatic)")


def demo_cache_behavior():
    """Demonstrate cache hit/miss behavior"""
    print_section("🔄 CACHE BEHAVIOR DEMONSTRATION")

    print("NOTE: This demo requires a valid Tibber token file (see")
    print("      weconnect_mcp.cli.tibber_login_cli). For testing without")
    print("      real credentials, use the mock adapter in other examples\n")

    print("Example with the real adapter (requires a Tibber token file):")
    print("-" * 70)
    print("""
    # Initial call - fetches from server
    adapter = TibberAdapter(client_id, client_secret, redirect_uri, token_path)
    vehicles1 = adapter.list_vehicles()
    # → Logs: "Fetched fresh vehicle list from Tibber (N vehicle(s))"

    # Immediate second call - uses cache
    vehicles2 = adapter.list_vehicles()
    # → No fetch log; cached data is returned

    # Wait for cache to expire (300+ seconds)
    time.sleep(301)

    # Call after expiration - fetches fresh data
    vehicles3 = adapter.list_vehicles()
    # → Logs: "Fetched fresh vehicle list from Tibber (N vehicle(s))"
    """)


def demo_cache_internals():
    """Show internal cache mechanism"""
    print_section("🔍 CACHE INTERNALS")

    print("Cache State Variables:")
    print("-" * 70)
    print("  _last_fetch_time: datetime")
    print("      → Timestamp of last successful data fetch")
    print()
    print("  _cache_duration: timedelta")
    print(f"      → Configured duration ({CACHE_DURATION_SECONDS}s)")
    print()

    print("Cache Check Flow:")
    print("-" * 70)
    print("  1. API method called (e.g., list_vehicles())")
    print("  2. Calls _ensure_fresh_data() (from CacheMixin)")
    print("  3. Checks _is_cache_expired()")
    print("  4a. If expired: Calls _fetch_data() → Updates timestamp")
    print("  4b. If fresh: Returns immediately (uses cached data)")
    print()

    print("Affected Methods:")
    print("-" * 70)
    print("  • list_vehicles()")
    print("  • get_vehicle()")
    print("  • get_energy_status()")
    print("  → All read operations benefit from caching")


def demo_cache_customization():
    """Show how to customize cache duration"""
    print_section("🛠️ CUSTOMIZING CACHE DURATION")

    print("Current Setting:")
    print("-" * 70)
    print("  File: src/weconnect_mcp/adapter/mixins/cache_mixin.py")
    print(f"  Constant: CACHE_DURATION_SECONDS = {CACHE_DURATION_SECONDS}")
    print()

    print("To Change Cache Duration:")
    print("-" * 70)
    print("  1. Edit cache_mixin.py")
    print("  2. Modify CACHE_DURATION_SECONDS constant:")
    print()
    print("     # Fast refresh (1 minute)")
    print("     CACHE_DURATION_SECONDS = 60")
    print()
    print("     # Default (5 minutes)")
    print("     CACHE_DURATION_SECONDS = 300")
    print()
    print("     # Slow refresh (15 minutes)")
    print("     CACHE_DURATION_SECONDS = 900")
    print()
    print("  3. Restart the MCP server")
    print()

    print("Recommendations:")
    print("-" * 70)
    print("  • Too short: unnecessary load against Tibber's API")
    print("  • Too long (>600s): Data may be stale")
    print("  • Default (300s): Good balance for most use cases")


def demo_cache_logging():
    """Show cache-related log messages"""
    print_section("📝 CACHE LOGGING")

    print("Log Levels (configured in tibber_adapter.py):")
    print("-" * 70)
    print("  INFO:  Fetch events (fresh data pulled from Tibber)")
    print()

    print("Example Log Message:")
    print("-" * 70)
    print("  [INFO] Fetched fresh vehicle list from Tibber (1 vehicle(s))")
    print("      → New data retrieved from the Tibber Data API")


def main():
    print("\n" + "="*70)
    print("  CACHING SYSTEM DEMONSTRATION")
    print("  Polite polling against the Tibber Data API")
    print("="*70)

    demo_cache_configuration()
    demo_cache_behavior()
    demo_cache_internals()
    demo_cache_customization()
    demo_cache_logging()

    print("\n" + "="*70)
    print("  Demo completed!")
    print("="*70 + "\n")


if __name__ == "__main__":
    main()
