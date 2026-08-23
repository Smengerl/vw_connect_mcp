"""Mixins for adapters.

This module provides mixins that add specific functionality to adapters:
- CacheMixin: Data caching and freshness management
- VehicleResolutionMixin: VIN/name/license plate resolution
- TibberStateExtractionMixin: Vehicle state extraction (Tibber Data API)
"""

from .cache_mixin import CacheMixin
from .vehicle_resolution_mixin import VehicleResolutionMixin
from .tibber_state_extraction_mixin import TibberStateExtractionMixin

__all__ = [
    'CacheMixin',
    'VehicleResolutionMixin',
    'TibberStateExtractionMixin',
]
