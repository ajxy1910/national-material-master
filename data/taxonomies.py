"""
Taxonomies, dictionaries, and sector classifications for CPSE Material Masters.
Standardizes UNSPSC, HSN/SAC, UOM, and industrial abbreviations across Indian CPSEs.
"""

CPSE_ENTITIES = {
    "ONGC": {
        "name": "Oil and Natural Gas Corporation Ltd.",
        "sector": "Oil & Gas",
        "short_name": "ONGC",
        "erp_system": "SAP S/4HANA (ECC Legacy)",
        "badge_color": "#D97706"
    },
    "IOCL": {
        "name": "Indian Oil Corporation Ltd.",
        "sector": "Oil & Gas",
        "short_name": "IOCL",
        "erp_system": "SAP ECC 6.0",
        "badge_color": "#EA580C"
    },
    "BPCL": {
        "name": "Bharat Petroleum Corporation Ltd.",
        "sector": "Oil & Gas",
        "short_name": "BPCL",
        "erp_system": "SAP S/4HANA",
        "badge_color": "#CA8A04"
    },
    "GAIL": {
        "name": "GAIL (India) Ltd.",
        "sector": "Oil & Gas",
        "short_name": "GAIL",
        "erp_system": "SAP S/4HANA",
        "badge_color": "#2563EB"
    },
    "NTPC": {
        "name": "NTPC Ltd.",
        "sector": "Power Generation",
        "short_name": "NTPC",
        "erp_system": "SAP S/4HANA Enterprise",
        "badge_color": "#059669"
    },
    "POWERGRID": {
        "name": "Power Grid Corporation of India Ltd.",
        "sector": "Power Transmission",
        "short_name": "POWERGRID",
        "erp_system": "SAP ECC 6.0 / Oracle Cloud",
        "badge_color": "#0D9488"
    },
    "SAIL": {
        "name": "Steel Authority of India Ltd.",
        "sector": "Steel & Metallurgy",
        "short_name": "SAIL",
        "erp_system": "SAP ERP / Custom Mainframe",
        "badge_color": "#4F46E5"
    },
    "BHEL": {
        "name": "Bharat Heavy Electricals Ltd.",
        "sector": "Heavy Engineering",
        "short_name": "BHEL",
        "erp_system": "SAP ECC 6.0",
        "badge_color": "#7C3AED"
    },
    "COAL_INDIA": {
        "name": "Coal India Ltd. (CIL)",
        "sector": "Mining & Minerals",
        "short_name": "CIL",
        "erp_system": "SAP S/4HANA",
        "badge_color": "#475569"
    },
    "NMDC": {
        "name": "NMDC Ltd.",
        "sector": "Mining & Iron Ore",
        "short_name": "NMDC",
        "erp_system": "SAP ERP",
        "badge_color": "#B45309"
    }
}

COMMODITY_TAXONOMIES = {
    "VALVES": {
        "code_prefix": "8481",
        "unspsc_family": "40141600",
        "unspsc_name": "Valves and internal components",
        "hsn_code": "8481.80.30",
        "standard_uom": "EA",
        "mandatory_attributes": ["item_type", "subtype", "size", "rating", "material_grade", "end_connection", "standard"]
    },
    "PIPES_TUBES": {
        "code_prefix": "7304",
        "unspsc_family": "40171500",
        "unspsc_name": "Industrial pipe and piping accessories",
        "hsn_code": "7304.19.10",
        "standard_uom": "MTR",
        "mandatory_attributes": ["item_type", "subtype", "size", "schedule", "material_grade", "end_connection", "standard"]
    },
    "BEARINGS": {
        "code_prefix": "8482",
        "unspsc_family": "31171500",
        "unspsc_name": "Bearings and bushings and wheels",
        "hsn_code": "8482.10.11",
        "standard_uom": "EA",
        "mandatory_attributes": ["item_type", "subtype", "bearing_number", "clearance", "shield_type", "bore_mm", "standard"]
    },
    "CABLES_ELECTRICAL": {
        "code_prefix": "8544",
        "unspsc_family": "26121600",
        "unspsc_name": "Electrical wire and cable and harness",
        "hsn_code": "8544.60.90",
        "standard_uom": "MTR",
        "mandatory_attributes": ["item_type", "cores", "cross_section", "voltage_grade", "conductor", "insulation", "armouring", "standard"]
    },
    "FLANGES_FITTINGS": {
        "code_prefix": "7307",
        "unspsc_family": "40171600",
        "unspsc_name": "Industrial pipe fittings and flanges",
        "hsn_code": "7307.21.00",
        "standard_uom": "EA",
        "mandatory_attributes": ["item_type", "subtype", "size", "rating", "material_grade", "facing", "standard"]
    },
    "MINING_CONVEYORS": {
        "code_prefix": "8428",
        "unspsc_family": "24101700",
        "unspsc_name": "Conveyors and accessories",
        "hsn_code": "8428.33.00",
        "standard_uom": "MTR",
        "mandatory_attributes": ["item_type", "width_mm", "carcass_type", "rating_kn", "top_cover_mm", "bottom_cover_mm", "grade"]
    }
}

ABBREVIATION_EXPANSIONS = {
    r"\bCS\b": "CARBON STEEL",
    r"\bSS\b": "STAINLESS STEEL",
    r"\bMS\b": "MILD STEEL",
    r"\bCI\b": "CAST IRON",
    r"\bDI\b": "DUCTILE IRON",
    r"\bWCB\b": "ASTM A216 WCB",
    r"\bA106B\b": "ASTM A106 GR B",
    r"\bA106-B\b": "ASTM A106 GR B",
    r"\bA105\b": "ASTM A105",
    r"\bSS316\b": "STAINLESS STEEL 316",
    r"\bSS304\b": "STAINLESS STEEL 304",
    r"\b316L\b": "STAINLESS STEEL 316L",
    r"\bAL\b": "ALUMINIUM",
    r"\bCU\b": "COPPER",

    r"\bVLV\b": "VALVE",
    r"\bVALV\b": "VALVE",
    r"\bGT\s+VLV\b": "GATE VALVE",
    r"\bGL\s+VLV\b": "GLOBE VALVE",
    r"\bBL\s+VLV\b": "BALL VALVE",
    r"\bNRV\b": "NON RETURN VALVE",
    r"\bCK\s+VLV\b": "CHECK VALVE",
    r"\bFLGD\b": "FLANGED",
    r"\bFLG\b": "FLANGE",
    r"\bWN\s+FLG\b": "WELD NECK FLANGE",
    r"\bSO\s+FLG\b": "SLIP ON FLANGE",
    r"\bBLD\s+FLG\b": "BLIND FLANGE",
    r"\bRF\b": "RAISED FACE",
    r"\bFF\b": "FLAT FACE",
    r"\bRTJ\b": "RING TYPE JOINT",
    r"\bSMLS\b": "SEAMLESS",
    r"\bERW\b": "ELECTRIC RESISTANCE WELDED",
    r"\bOS&Y\b": "OUTSIDE SCREW AND YOKE",
    r"\bOS\s*&\s*Y\b": "OUTSIDE SCREW AND YOKE",
    r"\bBB\b": "BOLTED BONNET",
    r"\bBE\b": "BEVELLED END",
    r"\bBW\b": "BUTT WELD",
    r"\bSW\b": "SOCKET WELD",
    r"\bTHD\b": "THREADED",
    r"\bNPT\b": "NPT THREADED",
    r"\bSCH\b": "SCHEDULE",

    r"\bBRG\b": "BEARING",
    r"\bDGBB\b": "DEEP GROOVE BALL BEARING",
    r"\bSRB\b": "SPHERICAL ROLLER BEARING",
    r"\bTRB\b": "TAPERED ROLLER BEARING",
    r"\bCRB\b": "CYLINDRICAL ROLLER BEARING",
    r"\b2RS\b": "DOUBLE RUBBER SEALED",
    r"\b2RS1\b": "DOUBLE RUBBER SEALED",
    r"\bZZ\b": "DOUBLE METAL SHIELDED",

    r"\bCBL\b": "CABLE",
    r"\bXLPE\b": "CROSSLINKED POLYETHYLENE",
    r"\bPVC\b": "POLYVINYL CHLORIDE",
    r"\bARM\b": "ARMOURED",
    r"\bUNARM\b": "UNARMOURED",
    r"\bSQMM\b": "SQ.MM",
    r"\bSQ\s*MM\b": "SQ.MM",
    r"\bKV\b": "KV",

    r"\bBLT\b": "BOLT",
    r"\bNUT\b": "HEX NUT",
    r"\bWSH\b": "WASHER",
    r"\bSWG\b": "SPIRAL WOUND GASKET",
    r"\bGKT\b": "GASKET",
    r"\bCAF\b": "COMPRESSED ASBESTOS FIBRE",
    r"\bCNAF\b": "NON ASBESTOS FIBRE GASKET"
}

UOM_NORMALIZATION = {
    "INCH": "INCH",
    "IN": "INCH",
    "\"": "INCH",
    "MM": "MM",
    "MTR": "MTR",
    "M": "MTR",
    "METRE": "MTR",
    "METER": "MTR",
    "NOS": "EA",
    "NO": "EA",
    "NUM": "EA",
    "EA": "EA",
    "EACH": "EA",
    "PC": "EA",
    "PCS": "EA",
    "SET": "SET",
    "KG": "KG",
    "KGS": "KG",
    "MT": "MT",
    "TON": "MT",
    "TONNE": "MT"
}

SIZE_CONVERSIONS = {
    "1/2\"": "15MM NB",
    "1/2 INCH": "15MM NB",
    "3/4\"": "20MM NB",
    "3/4 INCH": "20MM NB",
    "1\"": "25MM NB",
    "1 INCH": "25MM NB",
    "1.5\"": "40MM NB",
    "1-1/2\"": "40MM NB",
    "1.5 INCH": "40MM NB",
    "2\"": "50MM NB",
    "2 INCH": "50MM NB",
    "3\"": "80MM NB",
    "3 INCH": "80MM NB",
    "4\"": "100MM NB",
    "4 INCH": "100MM NB",
    "6\"": "150MM NB",
    "6 INCH": "150MM NB",
    "8\"": "200MM NB",
    "8 INCH": "200MM NB",
    "10\"": "250MM NB",
    "10 INCH": "250MM NB",
    "12\"": "300MM NB",
    "12 INCH": "300MM NB"
}
