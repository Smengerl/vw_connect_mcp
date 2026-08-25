"""Mixins for adapters.

This module provides mixins that add specific functionality to adapters:
- CacheMixin: Data caching and freshness management

CacheMixin is the only one left: it's genuinely backend-agnostic (knows
nothing about Tibber), unlike Tibber's device-detail extraction, which
used to live here as a second mixin (TibberStateExtractionMixin) despite
being 100% Tibber-specific and used by exactly one class -- composing it
in via multiple inheritance never bought anything a plain module-level
function in tibber_adapter.py doesn't already give for free. See that
module for where the extraction logic moved to.

Vehicle identifier resolution (VIN/name) lives directly on
AbstractAdapter as a concrete default method — it used to be a separate
mixin here too, but that duplicate had different (and buggy) matching
semantics from the AbstractAdapter version and was never actually used by
TibberAdapter's MRO consistently with what tests/examples exercised. One
implementation now, inherited by every adapter.
"""

from .cache_mixin import CacheMixin

__all__ = [
    'CacheMixin',
]
