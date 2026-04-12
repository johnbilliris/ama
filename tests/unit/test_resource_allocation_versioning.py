"""Unit tests for version counter.

Covers:
- First version = 1
- Monotonic increment per incident
- Separate version sequences per incident ID
- Local counter (no Cosmos DB) behavior
"""

from __future__ import annotations

import pytest
from resource_allocation.versioning import VersionConflictError, VersionCounter


class TestVersionCounter:
    def test_first_version_is_1(self):
        counter = VersionCounter()  # No Cosmos — uses local counter
        version = counter.assign_version("inc001")
        assert version == 1

    def test_monotonic_increment(self):
        counter = VersionCounter()
        v1 = counter.assign_version("inc001")
        v2 = counter.assign_version("inc001")
        v3 = counter.assign_version("inc001")
        assert v1 == 1
        assert v2 == 2
        assert v3 == 3

    def test_separate_sequences_per_incident(self):
        counter = VersionCounter()
        v1_inc1 = counter.assign_version("inc001")
        v1_inc2 = counter.assign_version("inc002")
        v2_inc1 = counter.assign_version("inc001")

        assert v1_inc1 == 1
        assert v1_inc2 == 1
        assert v2_inc1 == 2

    def test_version_conflict_error_class(self):
        with pytest.raises(VersionConflictError):
            raise VersionConflictError("test conflict")

    def test_custom_max_retries(self):
        counter = VersionCounter(max_retries=5)
        assert counter._max_retries == 5
