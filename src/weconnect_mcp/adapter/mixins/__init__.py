"""Mixins for adapters.

This module provides mixins that add specific functionality to adapters:
- CacheMixin: Data caching and freshness management
- TibberStateExtractionMixin: Vehicle state extraction (Tibber Data API)

Vehicle identifier resolution (VIN/name/license plate) lives directly on
AbstractAdapter as a concrete default method — it used to be a separate
mixin here too, but that duplicate had different (and buggy) matching
semantics from the AbstractAdapter version and was never actually used by
TibberAdapter's MRO consistently with what tests/examples exercised. One
implementation now, inherited by every adapter.
"""

from .cache_mixin import CacheMixin
from .tibber_state_extraction_mixin import TibberStateExtractionMixin

__all__ = [
    'CacheMixin',
    'TibberStateExtractionMixin',
]
