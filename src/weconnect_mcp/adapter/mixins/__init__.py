"""Mixins for adapters.

This module provides mixins that add specific functionality to adapters:
- CacheMixin: Data caching and freshness management
- VehicleResolutionMixin: VIN/name/license plate resolution
- CommandMixin: Vehicle control commands (carconnectivity)
- StateExtractionMixin: Vehicle state extraction (carconnectivity)
- TibberStateExtractionMixin: Vehicle state extraction (Tibber Data API)
"""

from .cache_mixin import CacheMixin
from .vehicle_resolution_mixin import VehicleResolutionMixin
from .command_mixin import CommandMixin
from .state_extraction_mixin import StateExtractionMixin
from .tibber_state_extraction_mixin import TibberStateExtractionMixin

__all__ = [
    'CacheMixin',
    'VehicleResolutionMixin',
    'CommandMixin',
    'StateExtractionMixin',
    'TibberStateExtractionMixin',
]
