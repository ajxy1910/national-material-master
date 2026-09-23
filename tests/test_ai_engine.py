"""
Unit tests for AI & NLP entity extraction, normalization, and similarity matching.
"""

import pytest
from core.ai_engine import ai_engine
from data.cpse_catalog import NATIONAL_MASTER_CATALOG

def test_normalization_and_abbreviation():
    raw = "VLV GATE FLGD 4IN 150# CS A216 WCB RF OS&Y"
    norm = ai_engine.normalize_text(raw)
    assert "VALVE" in norm
    assert "GATE" in norm
    assert "FLANGED" in norm
    assert "CARBON STEEL" in norm
    assert "ASTM A216 WCB" in norm
    assert "OUTSIDE SCREW AND YOKE" in norm

def test_extract_valve_attributes():
    raw = "GATE VALVE 4 INCH CLASS 150 FLANGED END ASTM A216 GR WCB RAISED FACE BOLTED BONNET"
    attrs = ai_engine.extract_attributes(raw)
    assert attrs["category"] == "VALVES"
    assert attrs["item_type"] == "GATE VALVE"
    assert "4" in attrs["size"] or attrs["size_numeric_mm"] in [100, 101]
    assert "150" in attrs["rating"]
    assert "WCB" in attrs["material_grade"]
    assert "FLANGED" in attrs["end_connection"]

def test_extract_pipe_attributes():
    raw = "PIPE CS SMLS 6 INCH SCH 40 ASTM A106 GR B BEVELLED END"
    attrs = ai_engine.extract_attributes(raw)
    assert attrs["category"] == "PIPES_TUBES"
    assert attrs["item_type"] == "SEAMLESS PIPE"
    assert "6" in attrs["size"] or attrs["size_numeric_mm"] in [150, 152]
    assert "40" in attrs["rating"]
    assert "A106" in attrs["material_grade"]
    assert "BEVELLED" in attrs["end_connection"]

def test_extract_bearing_attributes():
    raw = "DEEP GROOVE BALL BEARING 6310 2RS C3 SKF/FAG"
    attrs = ai_engine.extract_attributes(raw)
    assert attrs["category"] == "BEARINGS"
    assert "BEARING" in attrs["item_type"]
    assert attrs["size_numeric_mm"] == 50
    assert "2RS" in attrs["end_connection"] or "RUBBER" in attrs["end_connection"]

def test_matching_exact_duplicate():
    # An ONGC description matching the first National Master
    raw = "VLV GATE FLGD 4IN 150# CS A216 WCB RF OS&Y"
    matches = ai_engine.match_against_national_masters(raw, NATIONAL_MASTER_CATALOG, threshold=70.0)
    assert len(matches) > 0
    top = matches[0]
    assert top["national_master"]["cnmc"] == "IN-NMC-8481-VLVG-100-WCB-4"
    assert top["confidence_pct"] >= 80.0
    assert top["match_type"] in ["EXACT_DUPLICATE", "NEAR_DUPLICATE"]
