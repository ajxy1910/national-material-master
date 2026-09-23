"""
Unit tests for Common National Material Code (CNMC) generation and check digit validation.
"""

import pytest
from core.code_generator import code_generator

def test_cnmc_generation():
    attrs = {
        "category": "VALVES",
        "item_type": "GATE VALVE",
        "size_numeric_mm": 100,
        "material_grade": "ASTM A216 GR WCB",
        "rating": "ASME CLASS 150"
    }
    cnmc = code_generator.generate_cnmc(attrs)
    assert cnmc.startswith("IN-NMC-8481-VLVG-100-WCB-")
    
    is_valid, msg = code_generator.validate_cnmc(cnmc)
    assert is_valid is True
    assert msg == "Valid Common National Material Code"

def test_cnmc_validation_invalid_tampered_digit():
    tampered_code = "IN-NMC-8481-VLVG-100-WCB-9"
    is_valid, msg = code_generator.validate_cnmc(tampered_code)
    assert is_valid is False
    assert "Check digit mismatch" in msg

def test_cnmc_validation_invalid_format():
    invalid_code = "MAT-1234-VALVE"
    is_valid, msg = code_generator.validate_cnmc(invalid_code)
    assert is_valid is False
    assert "Invalid format" in msg
