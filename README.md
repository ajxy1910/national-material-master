# National Unified Material Master (NUMM) Framework
### "One Nation – One Material Code"

An AI-driven enterprise material master standardization, harmonization, deduplication, and collaborative procurement platform built for Central Public Sector Enterprises (CPSEs) in India (Oil & Gas, Power, Steel, Mining, and Heavy Engineering).

---

## 🇮🇳 Sponsoring & Participating CPSEs
- **Oil & Gas**: ONGC, IOCL, BPCL, GAIL, HPCL
- **Power Generation & Transmission**: NTPC, PowerGrid (PGCIL)
- **Steel & Metals**: SAIL, RINL
- **Mining & Minerals**: Coal India Ltd. (CIL), NMDC
- **Heavy Engineering**: BHEL

---

## Key Capabilities

1. **AI Material Matching & Recommendation Engine**:
   - NLP-driven abbreviation normalizer expanding 100+ industrial shorthands (`SMLS`, `FLGD`, `CS`, `WCB`, `OS&Y`, `NB`, `DGBB`, `XLPE`).
   - 7-point parametric engineering entity extraction (Item Type, Size, Rating, Material Grade, End Connection, Standard).
   - Hybrid similarity scoring (Attribute Compatibility Matrix + TF-IDF Vector Cosine + Levenshtein fuzzy ratio).

2. **Material Standardization & Classification**:
   - Automated conversion of noisy legacy text into formulaic Master Descriptions.
   - Dual output generation: SAP 40-character short description (`MARA-MAKTX`) and GeM e-Procurement long description.
   - Standardized UNSPSC, HSN/SAC, and CPSE taxonomy alignment.

3. **Duplicate, Near-Duplicate & Functional Equivalency Clustering**:
   - Automated grouping into Exact Duplicates (100% parameter parity), Near-Duplicates (minor wording variances), and Functional Equivalents (swappable in plant operations).
   - Cross-CPSE procurement price variance detection (revealing divergence where one CPSE pays ₹18,500 and another pays ₹23,500 for identical items).

4. **Common National Material Code (CNMC) Generation**:
   - Hierarchical format: `IN-NMC-[HSN_4D]-[TYPE_4C]-[SIZE_3D]-[SPEC_4C]-[CHECK_DIGIT]`.
   - ISO 7064 / Mod-10 Check Digit verification.

5. **CPSE Master Cross-Walk & Legacy Migration Workbench**:
   - Bidirectional cross-walk connecting National Codes to legacy codes across all 10 CPSEs.
   - Drag-and-drop CSV batch upload with real-time harmonization, mapping reports, and downloadable reconciled CSV.

6. **Demand Aggregation Savings & Inter-CPSE Surplus Inventory**:
   - Dynamic calculator projecting bulk purchasing discounts (₹ Crores) from pooled procurement tenders.
   - Inter-enterprise inventory locator allowing CPSEs to transfer surplus stock rather than initiating redundant emergency imports.

7. **Multi-Tier Governance & Immutable Audit Trail**:
   - Workflow state machine: `AI_RECOMMENDED` → `CPSE_REVIEW` → `COMMITTEE_EVALUATION` → `APPROVED_NATIONAL_CODE` → `REJECTED`.
   - Tamper-evident audit log recording timestamps, officer credentials, before/after values, and technical rationale.

8. **SAP / ERP S/4HANA & ECC 6.0 Integration**:
   - RFC `BAPI_MATERIAL_SAVEDATA` payload generation.
   - Standard SAP IDoc `MATMAS05` XML generation with custom national master extension segments (`ZE1CPSE_CNMC`).
   - SAP S/4HANA Cloud OData API v4 support and live simulated sync.

---

##  Quick Start Guide

### 1. Requirements
- Python 3.10+ (Tested on Python 3.14)
- Flask, Scikit-learn, Pandas, NumPy, Pytest

### 2. Run the National Portal Web Server
```powershell
python app.py
```
Open your browser at: **`http://127.0.0.1:5000`**

### 3. Run Automated Tests
```powershell
python -m pytest tests/ -v
```
All 17 tests validate AI attribute extraction, code generation, check digit validation, and REST API routes.

### 4. Use the CPSE Engineer CLI
```powershell
# Display Executive Summary & Redundancy Statistics
python cli.py stats

# Match a free-text description against National Masters
python cli.py match "GATE VALVE 4 INCH 150# WCB FLANGED RF"

# Standardize description and generate National Code
python cli.py standardize "PIPE CS SMLS 6 INCH SCH 40 A106B"

# Batch harmonize legacy CPSE catalog CSV
python cli.py harmonize data/sample_legacy_upload.csv --output harmonized_catalog.csv
```

---

## REST API Reference

| Endpoint | Method | Description |
|---|---|---|
| `/` | GET | Single-Page National Portal Interface |
| `/api/overview` | GET | Executive KPIs, rationalization rate, CPSE distribution |
| `/api/match` | POST | Live AI parametric extraction & National Master matching |
| `/api/standardize` | POST | Generates standardized descriptions & Common National Code |
| `/api/clusters` | GET | Duplicate clusters with price variance and savings |
| `/api/crosswalk` | GET | Multi-CPSE mapping table linking National & legacy codes |
| `/api/upload` | POST | Upload CSV of legacy materials for batch AI harmonization |
| `/api/export` | GET | Download harmonized catalog as CSV or JSON |
| `/api/governance/status` | GET | Review queue and status filters |
| `/api/governance/update` | POST | Committee approval/ratification and audit log append |
| `/api/governance/audit` | GET | Full chronological audit trail |
| `/api/sap/payload` | GET | Preview SAP BAPI, IDoc XML, or OData JSON |
| `/api/sap/sync` | POST | Simulate real-time synchronization with CPSE SAP system |

---

##  Architecture & Folder Structure

```
national-material-master/
├── app.py                          # Flask web server & REST API
├── cli.py                          # Command-line utility for CPSE data stewards
├── requirements.txt                # Python dependencies
├── core/
│   ├── ai_engine.py                # NLP parser, abbreviation normalizer, TF-IDF matcher
│   ├── code_generator.py           # CNMC generation & ISO check digit validation
│   ├── deduplicator.py             # Duplicate clustering & demand aggregation calculator
│   ├── governance.py               # Committee review workflow & audit trail engine
│   └── sap_connector.py            # SAP BAPI, IDoc MATMAS05, and OData simulator
├── data/
│   ├── taxonomies.py               # UNSPSC, HSN, CPSE entities, and industrial abbreviations
│   ├── cpse_catalog.py             # Realistic material master records across 10 CPSEs
│   └── sample_legacy_upload.csv    # Sample CSV for testing batch ingestion
├── static/
│   ├── css/style.css               # Vanilla CSS design system (glassmorphism & dark theme)
│   └── js/app.js                   # Interactive client-side SPA controller
├── templates/
│   └── index.html                  # Main National Unified Portal HTML
└── tests/
    ├── test_ai_engine.py           # AI and NLP unit tests
    ├── test_code_generator.py      # National code and check digit tests
    └── test_api.py                 # Flask integration tests (17 passed)
```
