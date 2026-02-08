"""Mixins for CarConnectivityAdapter.

This module provides mixins that add specific functionality to the adapter:
- CacheMixin: Data caching and freshness management
- VehicleResolutionMixin: VIN/name/license plate resolution
- CommandMixin: Vehicle control commands
- StateExtractionMixin: Vehicle state extraction (getter methods)
"""

from .cache_mixin import CacheMixin
from .vehicle_resolution_mixin import VehicleResolutionMixin
from .command_mixin import CommandMixin
from .state_extraction_mixin import StateExtractionMixin

__all__ = [
    'CacheMixin',
    'VehicleResolutionMixin',
    'CommandMixin',
    'StateExtractionMixin',
]
