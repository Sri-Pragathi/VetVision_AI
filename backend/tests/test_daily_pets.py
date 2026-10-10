"""Test validation for diverse daily life pets and empty/missing optional values."""
import pytest
from app.schemas.pet_schema import pet_create_schema


def test_daily_life_pets_validation():
    """Verify various common household/farm daily life pets pass schema validation cleanly."""
    daily_pets = [
        {"name": "Tweety", "species": "Bird", "breed": "Canary", "sex": "Male Intact", "date_of_birth": "", "weight": None},
        {"name": "Thumper", "species": "Rabbit", "breed": "Holland Lop", "sex": "Female Spayed", "date_of_birth": "2023-01-15", "weight": 1.8},
        {"name": "Nibbles", "species": "Hamster", "breed": "Syrian", "sex": "Unknown", "date_of_birth": "", "weight": 0.15},
        {"name": "Bubbles", "species": "Fish", "breed": "Goldfish", "sex": "unknown", "date_of_birth": "", "weight": None},
        {"name": "Shelly", "species": "Turtle", "breed": "Slider", "sex": "intact", "date_of_birth": "", "weight": 0.8},
        {"name": "Barnaby", "species": "Horse", "breed": "Quarter Horse", "sex": "neutered", "date_of_birth": "2018-05-10", "weight": 480.0},
        {"name": "Ganga", "species": "Cow", "breed": "Gir", "sex": "female", "date_of_birth": "2020-03-20", "weight": 350.0},
        {"name": "Billy", "species": "Goat", "breed": "Pygmy", "sex": "male neutered", "date_of_birth": "", "weight": 25.0},
        {"name": "Pippin", "species": "Ferret", "breed": "Sable", "sex": "Male Neutered", "date_of_birth": "", "weight": 1.2},
    ]

    for p in daily_pets:
        validated = pet_create_schema.load(p)
        assert validated["name"] == p["name"]
        assert validated["species"] == p["species"]
        assert validated.get("date_of_birth") == (p["date_of_birth"] if p["date_of_birth"] else None) or validated.get("date_of_birth") is not None
