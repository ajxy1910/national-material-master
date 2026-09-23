"""
Integration tests for Flask application and REST endpoints.
"""

import io
import json
import pytest
from app import app

@pytest.fixture
def client():
    app.config['TESTING'] = True
    with app.test_client() as client:
        yield client

def test_api_overview(client):
    res = client.get("/api/overview")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert "metrics" in data
    assert data["metrics"]["total_raw_materials_ingested"] >= 30
    assert data["metrics"]["total_national_master_codes"] >= 7
    assert data["metrics"]["rationalization_rate_pct"] > 50

def test_api_clusters(client):
    res = client.get("/api/clusters")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert len(data["clusters"]) >= 7

def test_api_catalog(client):
    res = client.get("/api/catalog?cpse=ONGC")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert all(item["cpse"] == "ONGC" for item in data["items"])

def test_api_match(client):
    payload = {
        "query_text": "GATE VALVE 4 INCH 150# WCB FLANGED RF",
        "threshold": 60.0
    }
    res = client.post("/api/match", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["matches_count"] > 0
    assert data["matches"][0]["national_master"]["cnmc"] == "IN-NMC-8481-VLVG-100-WCB-4"

def test_api_standardize(client):
    payload = {
        "raw_text": "CS SMLS PIPE 6IN SCH 40 A106-B BEV",
        "cpse": "ONGC"
    }
    res = client.post("/api/standardize", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["cnmc"].startswith("IN-NMC-7304-PIPS-")
    assert data["code_validation"]["valid"] is True

def test_api_crosswalk(client):
    res = client.get("/api/crosswalk")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["total_national_items"] >= 7

def test_api_governance_workflow(client):
    # Fetch status
    res = client.get("/api/governance/status")
    assert res.status_code == 200
    
    # Update status
    payload = {
        "cnmc": "IN-NMC-8481-VLVB-050-WCB-1",
        "new_status": "APPROVED_NATIONAL_CODE",
        "actor": "Shri Test Officer",
        "actor_org": "BHEL / Ministry of Heavy Industries",
        "remarks": "Test ratification approved"
    }
    res = client.post("/api/governance/update", data=json.dumps(payload), content_type="application/json")
    assert res.status_code == 200
    data = res.get_json()
    assert data["status"] == "success"
    assert data["updated_master"]["harmonization_status"] == "APPROVED_NATIONAL_CODE"

    # Verify audit log
    audit_res = client.get("/api/governance/audit?cnmc=IN-NMC-8481-VLVB-050-WCB-1")
    assert audit_res.status_code == 200
    audit_data = audit_res.get_json()
    assert len(audit_data["audit_trail"]) > 0

def test_api_sap_integration(client):
    # Payload preview
    res_bapi = client.get("/api/sap/payload?cnmc=IN-NMC-8481-VLVG-100-WCB-4&type=bapi")
    assert res_bapi.status_code == 200
    assert "BAPI_MATERIAL_SAVEDATA" in str(res_bapi.data)

    res_idoc = client.get("/api/sap/payload?cnmc=IN-NMC-8481-VLVG-100-WCB-4&type=idoc")
    assert res_idoc.status_code == 200
    assert b"<MATMAS05>" in res_idoc.data

    # ERP sync simulation
    sync_payload = {
        "cnmc": "IN-NMC-8481-VLVG-100-WCB-4",
        "cpse": "IOCL"
    }
    res_sync = client.post("/api/sap/sync", data=json.dumps(sync_payload), content_type="application/json")
    assert res_sync.status_code == 200
    sync_data = res_sync.get_json()
    assert sync_data["status"] == "SUCCESS"
    assert "MATDOC-" in sync_data["sap_document_number"]

def test_api_upload_csv(client):
    csv_content = """legacy_code,cpse_name,description,uom,unit_price_inr,plant_location,annual_consumption
TEST-VLV-100,TEST_CPSE,GATE VALVE 4 INCH 150# CS WCB FLANGED RF,NOS,19000,Test Refinery,200
"""
    data = {
        'file': (io.BytesIO(csv_content.encode("utf-8")), 'test_upload.csv')
    }
    res = client.post("/api/upload", data=data, content_type='multipart/form-data')
    assert res.status_code == 200
    res_json = res.get_json()
    assert res_json["status"] == "success"
    assert res_json["total_records_processed"] == 1
    assert res_json["results"][0]["assigned_cnmc"] == "IN-NMC-8481-VLVG-100-WCB-4"
