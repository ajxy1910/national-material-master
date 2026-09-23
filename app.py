import os
import sys
import io
import csv
import json
import datetime
from flask import Flask, render_template, request, jsonify, send_file, Response

if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from data.taxonomies import CPSE_ENTITIES, COMMODITY_TAXONOMIES
from data.cpse_catalog import CPSE_RAW_MATERIALS, NATIONAL_MASTER_CATALOG
from core.ai_engine import ai_engine
from core.code_generator import code_generator
from core.deduplicator import deduplicator
from core.governance import governance_engine
from core.sap_connector import sap_connector

app = Flask(__name__, static_folder="static", template_folder="templates")
app.config['JSON_SORT_KEYS'] = False
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16 MB max upload

# In-memory storage with initial data
raw_materials = list(CPSE_RAW_MATERIALS)
national_masters = list(NATIONAL_MASTER_CATALOG)

@app.route("/")
def index():
    """Renders the National Unified Material Master Portal."""
    return render_template(
        "index.html",
        cpse_entities=CPSE_ENTITIES,
        commodity_taxonomies=COMMODITY_TAXONOMIES
    )

@app.route("/api/overview", methods=["GET"])
def api_overview():
    """Returns executive dashboard KPIs and analytics."""
    summary = deduplicator.get_summary_metrics()
    return jsonify({
        "status": "success",
        "timestamp": datetime.datetime.now().isoformat(),
        "metrics": summary,
        "cpse_metadata": CPSE_ENTITIES,
        "taxonomies": COMMODITY_TAXONOMIES
    })

@app.route("/api/clusters", methods=["GET"])
def api_clusters():
    """Returns duplicate clusters with pricing variance and potential savings."""
    clusters = deduplicator.build_clusters()
    return jsonify({
        "status": "success",
        "total_clusters": len(clusters),
        "clusters": clusters
    })

@app.route("/api/catalog", methods=["GET"])
def api_catalog():
    """
    Returns CPSE raw materials with optional filters:
    - cpse (e.g. ONGC, IOCL)
    - query (search term)
    - category
    """
    cpse_filter = request.args.get("cpse", "").strip().upper()
    query_filter = request.args.get("q", "").strip().lower()
    cat_filter = request.args.get("category", "").strip().upper()

    filtered = []
    for item in raw_materials:
        if cpse_filter and item["cpse"] != cpse_filter:
            continue
        if cat_filter:
            # check if linked national master matches category
            pass
        if query_filter:
            match_str = f"{item['legacy_code']} {item['description']} {item['cpse']} {item['plant_location']}".lower()
            if query_filter not in match_str:
                continue
        filtered.append(item)

    return jsonify({
        "status": "success",
        "count": len(filtered),
        "items": filtered
    })

@app.route("/api/match", methods=["POST"])
def api_match():
    """
    Performs AI-based matching and recommendation on an input material description.
    """
    data = request.get_json(force=True) or {}
    query_text = data.get("query_text", "").strip()
    threshold = float(data.get("threshold", 50.0))

    if not query_text:
        return jsonify({"status": "error", "message": "query_text is required"}), 400

    extracted_attrs = ai_engine.extract_attributes(query_text)
    standard_desc = ai_engine.build_standardized_descriptions(extracted_attrs)
    proposed_code = code_generator.generate_cnmc(extracted_attrs)

    matches = ai_engine.match_against_national_masters(
        query_text=query_text,
        national_masters=national_masters,
        threshold=threshold
    )

    return jsonify({
        "status": "success",
        "input_query": query_text,
        "extracted_attributes": extracted_attrs,
        "standardized_descriptions": standard_desc,
        "recommended_national_code": proposed_code,
        "matches_count": len(matches),
        "matches": matches
    })

@app.route("/api/standardize", methods=["POST"])
def api_standardize():
    """
    Automated standardization of material descriptions and generation of Common National Code.
    """
    data = request.get_json(force=True) or {}
    raw_text = data.get("raw_text", "").strip()
    cpse = data.get("cpse", "GENERAL").strip().upper()

    if not raw_text:
        return jsonify({"status": "error", "message": "raw_text is required"}), 400

    attrs = ai_engine.extract_attributes(raw_text)
    descriptions = ai_engine.build_standardized_descriptions(attrs)
    cnmc = code_generator.generate_cnmc(attrs)
    is_valid, validation_msg = code_generator.validate_cnmc(cnmc)

    return jsonify({
        "status": "success",
        "cpse": cpse,
        "raw_text": raw_text,
        "normalized_text": attrs.get("normalized_text"),
        "attributes": attrs,
        "descriptions": descriptions,
        "cnmc": cnmc,
        "code_validation": {
            "valid": is_valid,
            "message": validation_msg
        }
    })

@app.route("/api/crosswalk", methods=["GET"])
def api_crosswalk():
    """
    Returns multi-CPSE cross-walk matrix linking National Codes to individual CPSE legacy codes.
    """
    crosswalk = []
    for master in national_masters:
        mapped_ids = set(master.get("mapped_cpse_items", []))
        cpse_mappings = {}

        # Initialize all major CPSEs
        for cpse_key in CPSE_ENTITIES.keys():
            cpse_mappings[cpse_key] = None

        for item in raw_materials:
            if item["id"] in mapped_ids:
                cpse_mappings[item["cpse"]] = {
                    "legacy_code": item["legacy_code"],
                    "description": item["description"],
                    "uom": item["uom"],
                    "unit_price_inr": item["unit_price_inr"],
                    "stock_on_hand": item["stock_on_hand"],
                    "plant_location": item["plant_location"]
                }

        crosswalk.append({
            "cnmc": master["cnmc"],
            "category": master["category"],
            "standard_short_desc": master["standard_short_desc"],
            "standard_long_desc": master["standard_long_desc"],
            "standard_uom": master["standard_uom"],
            "harmonization_status": master["harmonization_status"],
            "governance": master.get("governance", {}),
            "benchmark_price_inr": master["benchmark_price_inr"],
            "annual_national_demand": master["annual_national_demand"],
            "cpse_mappings": cpse_mappings
        })

    return jsonify({
        "status": "success",
        "total_national_items": len(crosswalk),
        "crosswalk": crosswalk
    })

@app.route("/api/governance/status", methods=["GET"])
def api_governance_status():
    """Returns items pending review or active in governance."""
    status_filter = request.args.get("status", "").strip().upper()
    items = []
    for m in national_masters:
        if status_filter and m.get("harmonization_status") != status_filter:
            continue
        items.append({
            "cnmc": m["cnmc"],
            "standard_short_desc": m["standard_short_desc"],
            "category": m["category"],
            "harmonization_status": m["harmonization_status"],
            "governance": m.get("governance", {}),
            "mapped_cpse_count": len(m.get("mapped_cpse_items", []))
        })
    return jsonify({
        "status": "success",
        "items": items,
        "allowed_statuses": governance_engine.ALLOWED_STATUSES
    })

@app.route("/api/governance/update", methods=["POST"])
def api_governance_update():
    """
    Updates the governance status of a National Material Code and appends to the audit trail.
    """
    data = request.get_json(force=True) or {}
    cnmc = data.get("cnmc", "").strip()
    new_status = data.get("new_status", "").strip().upper()
    actor = data.get("actor", "CPSE Officer").strip()
    actor_org = data.get("actor_org", "Ministry of Petroleum & Natural Gas").strip()
    remarks = data.get("remarks", "Status updated via governance portal").strip()

    if not cnmc or not new_status:
        return jsonify({"status": "error", "message": "cnmc and new_status are required"}), 400

    if new_status not in governance_engine.ALLOWED_STATUSES:
        return jsonify({"status": "error", "message": f"Invalid status: {new_status}"}), 400

    target_master = next((m for m in national_masters if m["cnmc"] == cnmc), None)
    if not target_master:
        return jsonify({"status": "error", "message": f"National code {cnmc} not found"}), 404

    prev_status = target_master.get("harmonization_status", "UNKNOWN")
    target_master["harmonization_status"] = new_status
    if "governance" not in target_master:
        target_master["governance"] = {}
    target_master["governance"]["approved_by"] = actor
    target_master["governance"]["approval_date"] = datetime.date.today().isoformat()

    # Log to audit trail
    log_rec = governance_engine.log_action(
        cnmc=cnmc,
        action="STATUS_UPDATED",
        actor=actor,
        actor_org=actor_org,
        previous_status=prev_status,
        new_status=new_status,
        remarks=remarks,
        affected_legacy_codes=target_master.get("mapped_cpse_items", [])
    )

    return jsonify({
        "status": "success",
        "message": f"Status for {cnmc} updated to {new_status}",
        "audit_record": log_rec,
        "updated_master": target_master
    })

@app.route("/api/governance/audit", methods=["GET"])
def api_governance_audit():
    """Returns the complete tamper-evident audit trail."""
    cnmc_filter = request.args.get("cnmc", "").strip()
    trail = governance_engine.get_audit_trail(cnmc_filter if cnmc_filter else None)
    return jsonify({
        "status": "success",
        "total_records": len(trail),
        "audit_trail": trail
    })

@app.route("/api/upload", methods=["POST"])
def api_upload():
    """
    Handles CSV legacy batch upload, parses materials, and runs real-time AI harmonization.
    """
    if 'file' not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400

    file = request.files['file']
    if not file.filename.endswith('.csv'):
        return jsonify({"status": "error", "message": "Only CSV files are supported"}), 400

    stream = io.StringIO(file.stream.read().decode("utf-8-sig"), newline=None)
    csv_reader = csv.DictReader(stream)

    harmonized_results = []
    exact_matches = 0
    near_matches = 0
    new_proposals = 0

    for idx, row in enumerate(csv_reader):
        raw_desc = row.get("description", "").strip()
        legacy_code = row.get("legacy_code", f"LEG-{idx+1}").strip()
        cpse = row.get("cpse_name") or row.get("cpse") or "UPLOADED_CPSE"
        uom = row.get("uom", "EA").strip()
        price = float(row.get("unit_price_inr") or 0)
        annual_qty = int(row.get("annual_consumption") or 100)

        if not raw_desc:
            continue

        # Extract attributes & match
        attrs = ai_engine.extract_attributes(raw_desc)
        descs = ai_engine.build_standardized_descriptions(attrs)
        matches = ai_engine.match_against_national_masters(raw_desc, national_masters, threshold=60.0)

        if matches and (matches[0]["confidence_pct"] >= 80.0 or matches[0]["match_type"] in ["EXACT_DUPLICATE", "NEAR_DUPLICATE"]):
            best_match = matches[0]
            matched_cnmc = best_match["national_master"]["cnmc"]
            status = "MAPPED_EXISTING_CNMC"
            if best_match["match_type"] == "EXACT_DUPLICATE":
                exact_matches += 1
            else:
                near_matches += 1
        else:
            matched_cnmc = code_generator.generate_cnmc(attrs)
            status = "NEW_CNMC_PROPOSED"
            new_proposals += 1

        harmonized_results.append({
            "row_index": idx + 1,
            "legacy_code": legacy_code,
            "cpse": cpse,
            "original_description": raw_desc,
            "uom": uom,
            "unit_price_inr": price,
            "annual_consumption": annual_qty,
            "extracted_attributes": attrs,
            "standard_short_desc": descs["sap_short_desc"],
            "assigned_cnmc": matched_cnmc,
            "harmonization_status": status,
            "confidence_pct": matches[0]["confidence_pct"] if matches else 100.0,
            "top_match_type": matches[0]["match_type"] if matches else "NEW_RECOMMENDATION"
        })

    return jsonify({
        "status": "success",
        "file_name": file.filename,
        "total_records_processed": len(harmonized_results),
        "statistics": {
            "mapped_to_existing_exact": exact_matches,
            "mapped_to_existing_near": near_matches,
            "new_national_codes_generated": new_proposals
        },
        "results": harmonized_results
    })

@app.route("/api/export", methods=["GET"])
def api_export():
    """
    Exports the harmonized cross-walk matrix in CSV, JSON, or SAP format.
    """
    export_format = request.args.get("format", "csv").lower()

    if export_format == "json":
        return jsonify({
            "export_date": datetime.datetime.now().isoformat(),
            "framework": "National Unified Material Master (NUMM)",
            "initiative": "One Nation – One Material Code",
            "national_masters": national_masters,
            "cpse_materials": raw_materials
        })

    # Generate CSV
    si = io.StringIO()
    cw = csv.writer(si)
    cw.writerow([
        "CNMC",
        "Harmonization_Status",
        "Category",
        "Standard_Short_Description",
        "Standard_Long_Description",
        "Standard_UOM",
        "Benchmark_Price_INR",
        "Mapped_CPSE_Codes"
    ])

    for m in national_masters:
        mapped_codes = []
        for itm in raw_materials:
            if itm["id"] in m.get("mapped_cpse_items", []):
                mapped_codes.append(f"{itm['cpse']}:{itm['legacy_code']}")

        cw.writerow([
            m["cnmc"],
            m["harmonization_status"],
            m["category"],
            m["standard_short_desc"],
            m["standard_long_desc"],
            m["standard_uom"],
            m["benchmark_price_inr"],
            " | ".join(mapped_codes)
        ])

    output = io.BytesIO()
    output.write(si.getvalue().encode('utf-8-sig'))
    output.seek(0)
    return send_file(
        output,
        mimetype="text/csv",
        as_attachment=True,
        download_name=f"national_material_master_harmonized_{datetime.date.today()}.csv"
    )

@app.route("/api/sap/payload", methods=["GET"])
def api_sap_payload():
    """Generates preview of SAP BAPI, IDoc XML, or OData payloads."""
    cnmc = request.args.get("cnmc", "IN-NMC-8481-VLVG-100-WCB-4").strip()
    target_cpse = request.args.get("cpse", "IOCL").strip().upper()
    format_type = request.args.get("type", "bapi").strip().lower()

    master = next((m for m in national_masters if m["cnmc"] == cnmc), national_masters[0])

    if format_type == "idoc":
        xml_content = sap_connector.generate_idoc_xml(master, target_cpse)
        return Response(xml_content, mimetype='application/xml')
    elif format_type == "odata":
        odata_obj = sap_connector.generate_odata_json(master, target_cpse)
        return jsonify(odata_obj)
    else:
        bapi_obj = sap_connector.generate_bapi_payload(master, target_cpse)
        return jsonify(bapi_obj)

@app.route("/api/sap/sync", methods=["POST"])
def api_sap_sync():
    """Simulates real-time synchronization with a CPSE SAP instance."""
    data = request.get_json(force=True) or {}
    cnmc = data.get("cnmc", "").strip()
    target_cpse = data.get("cpse", "IOCL").strip().upper()

    if not cnmc:
        return jsonify({"status": "error", "message": "cnmc is required"}), 400

    result = sap_connector.simulate_erp_sync(cnmc, target_cpse)
    return jsonify(result)

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    print(f"🚀 Starting National Unified Material Master Framework on http://127.0.0.1:{port}")
    app.run(host="0.0.0.0", port=port, debug=True)
