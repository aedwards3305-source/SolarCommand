"""Tests for the Solar Readiness Scoring Engine."""

import pytest

from app.models.schema import Property, PropertyType
from app.services.scoring import ScoringResult, compute_score


def _make_property(**overrides) -> Property:
    """Create a Property instance with sensible defaults."""
    defaults = {
        "id": 1,
        "address_line1": "123 Test St",
        "city": "Annapolis",
        "state": "MD",
        "zip_code": "21401",
        "county": "Anne Arundel",
        "property_type": PropertyType.sfh,
        "year_built": 2015,
        "roof_area_sqft": 1800.0,
        "assessed_value": 400000.0,
        "utility_zone": "BGE",
        "tree_cover_pct": 5.0,
        "neighborhood_solar_pct": 12.0,
        "has_existing_solar": False,
        "owner_occupied": True,
        "median_household_income": 95000.0,
    }
    defaults.update(overrides)
    prop = Property.__new__(Property)
    for k, v in defaults.items():
        setattr(prop, k, v)
    return prop


class TestScoringResult:
    def test_total_caps_at_100(self):
        result = ScoringResult()
        # Manually set all to max
        result.roof_age_score = 15
        result.ownership_score = 15
        result.roof_area_score = 15
        result.home_value_score = 10
        result.utility_rate_score = 10
        result.shade_score = 10
        result.neighborhood_score = 10
        result.income_score = 8
        result.property_type_score = 5
        result.existing_solar_score = 2
        assert result.total == 100


class TestComputeScore:
    def test_ideal_property_scores_high(self):
        prop = _make_property(
            year_built=2020,
            owner_occupied=True,
            roof_area_sqft=2000,
            assessed_value=400000,
            utility_zone="BGE",
            tree_cover_pct=5,
            neighborhood_solar_pct=12,
            median_household_income=95000,
            property_type=PropertyType.sfh,
            has_existing_solar=False,
        )
        result = compute_score(prop)
        assert result.total >= 85

    def test_poor_property_scores_low(self):
        prop = _make_property(
            year_built=1950,
            owner_occupied=False,
            roof_area_sqft=300,
            assessed_value=80000,
            utility_zone="PEPCO",
            tree_cover_pct=75,
            neighborhood_solar_pct=0.5,
            median_household_income=30000,
            property_type=PropertyType.condo,
            has_existing_solar=True,
        )
        result = compute_score(prop)
        assert result.total <= 30

    def test_bge_utility_scores_higher(self):
        bge_prop = _make_property(utility_zone="BGE")
        other_prop = _make_property(utility_zone="PEPCO")
        bge_result = compute_score(bge_prop)
        other_result = compute_score(other_prop)
        assert bge_result.utility_rate_score > other_result.utility_rate_score

    def test_owner_occupied_matters(self):
        owner = _make_property(owner_occupied=True)
        renter = _make_property(owner_occupied=False)
        assert compute_score(owner).ownership_score == 15
        assert compute_score(renter).ownership_score == 0

    def test_existing_solar_reduces_score(self):
        no_solar = _make_property(has_existing_solar=False)
        has_solar = _make_property(has_existing_solar=True)
        assert compute_score(no_solar).existing_solar_score == 2
        assert compute_score(has_solar).existing_solar_score == 0

    def test_sfh_scores_higher_than_townhome(self):
        sfh = _make_property(property_type=PropertyType.sfh)
        town = _make_property(property_type=PropertyType.townhome)
        assert compute_score(sfh).property_type_score > compute_score(town).property_type_score

    def test_none_values_handled_gracefully(self):
        prop = _make_property(
            year_built=None,
            roof_area_sqft=None,
            assessed_value=None,
            utility_zone=None,
            tree_cover_pct=None,
            neighborhood_solar_pct=None,
            median_household_income=None,
        )
        result = compute_score(prop)
        assert 0 <= result.total <= 100
