"""
AI & NLP Material Standardization, Entity Extraction, and Hybrid Matching Engine.
Powered by Scikit-learn TF-IDF, Regex entity extraction, and multi-factor similarity.
"""

import re
import difflib
from typing import Dict, List, Any, Tuple
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from data.taxonomies import (
    ABBREVIATION_EXPANSIONS,
    COMMODITY_TAXONOMIES,
    UOM_NORMALIZATION,
    SIZE_CONVERSIONS
)

class AIEngine:
    def __init__(self):
        self.abbreviation_patterns = [
            (re.compile(pattern, re.IGNORECASE), replacement)
            for pattern, replacement in ABBREVIATION_EXPANSIONS.items()
        ]
        self.vectorizer = TfidfVectorizer(ngram_range=(1, 2), token_pattern=r'(?u)\b[\w\-\/\#\.]+\b')
        self._fitted = False
        self.corpus_descriptions = []
        self.corpus_ids = []

    def normalize_text(self, text: str) -> str:
        """Expands abbreviations, normalizes whitespace and punctuation."""
        if not text:
            return ""
        normalized = text.strip()
        # Expand known CPSE industrial abbreviations
        for regex, replacement in self.abbreviation_patterns:
            normalized = regex.sub(replacement, normalized)
        # Normalize punctuation and spacing
        normalized = re.sub(r'[,;:\/\\]', ' ', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip().upper()
        return normalized

    def extract_attributes(self, text: str) -> Dict[str, Any]:
        """
        Parses unstructured industrial text and extracts core engineering parameters:
        Category, Item Type, Size/Dimension, Rating/Class, Material Grade, End Connection, Standard.
        """
        raw_upper = text.upper()
        norm = self.normalize_text(text)

        extracted = {
            "category": "GENERAL_SPARES",
            "item_type": "UNKNOWN",
            "size": "N/A",
            "size_numeric_mm": None,
            "rating": "N/A",
            "material_grade": "N/A",
            "end_connection": "N/A",
            "standard": "N/A",
            "normalized_text": norm
        }

        # 1. Category and Item Type Detection
        if re.search(r'\bGATE VALVE\b|\bGT VLV\b|\bVALVE GATE\b|\bGATE\b.*\bVALVE\b', norm):
            extracted["category"] = "VALVES"
            extracted["item_type"] = "GATE VALVE"
        elif re.search(r'\bBALL VALVE\b|\bBL VLV\b|\bVALVE BALL\b|\bBALL\b.*\bVALVE\b', norm):
            extracted["category"] = "VALVES"
            extracted["item_type"] = "BALL VALVE"
        elif re.search(r'\bGLOBE VALVE\b|\bGL VLV\b|\bVALVE GLOBE\b', norm):
            extracted["category"] = "VALVES"
            extracted["item_type"] = "GLOBE VALVE"
        elif re.search(r'\bCHECK VALVE\b|\bNON RETURN VALVE\b|\bNRV\b', norm):
            extracted["category"] = "VALVES"
            extracted["item_type"] = "CHECK VALVE"
        elif re.search(r'\bPIPE\b.*\bSEAMLESS\b|\bSEAMLESS\b.*\bPIPE\b|\bLINE PIPE\b|\bPIPE\b', norm):
            extracted["category"] = "PIPES_TUBES"
            extracted["item_type"] = "SEAMLESS PIPE" if "ERW" not in norm else "ERW PIPE"
        elif re.search(r'\bWELD NECK FLANGE\b|\bWN FLANGE\b|\bFLG WN\b|\bFLANGE WELD NECK\b|\bFLG.*WN\b', norm):
            extracted["category"] = "FLANGES_FITTINGS"
            extracted["item_type"] = "WELD NECK FLANGE"
        elif re.search(r'\bBALL BEARING\b|\bDEEP GROOVE\b|\bDGBB\b|\bBEARING\b', norm):
            extracted["category"] = "BEARINGS"
            if re.search(r'ANGULAR CONTACT', norm):
                extracted["item_type"] = "ANGULAR CONTACT BALL BEARING"
            elif re.search(r'SPHERICAL ROLLER', norm):
                extracted["item_type"] = "SPHERICAL ROLLER BEARING"
            else:
                extracted["item_type"] = "DEEP GROOVE BALL BEARING"
        elif re.search(r'\bCABLE\b|\bXLPE\b|\bPOWER CABLE\b', norm):
            extracted["category"] = "CABLES_ELECTRICAL"
            extracted["item_type"] = "XLPE POWER CABLE"
        elif re.search(r'\bCONVEYOR BELT\b|\bBELT CONVEYOR\b|\bCONVEYOR BELTING\b', norm):
            extracted["category"] = "MINING_CONVEYORS"
            extracted["item_type"] = "CONVEYOR BELTING"
        elif re.search(r'\bGASKET\b|\bSPIRAL WOUND GASKET\b|\bSWG\b', norm):
            extracted["category"] = "FLANGES_FITTINGS"
            extracted["item_type"] = "SPIRAL WOUND GASKET"

        # 2. Size / Dimension Extraction
        size_match = re.search(r'(\d+[\.\/]?\d*)\s*(INCH|\"|IN\b|MM\s*NB|NB\b|MM\b)', raw_upper)
        if size_match:
            val, unit = size_match.groups()
            if "INCH" in unit or "\"" in unit or unit == "IN":
                try:
                    num_val = float(val) if "/" not in val else eval(val)
                    # Standard Nominal Bore (NB) mapping for process piping
                    nb_standard_map = {
                        0.5: 15, 0.75: 20, 1.0: 25, 1.25: 32, 1.5: 40,
                        2.0: 50, 2.5: 65, 3.0: 80, 4.0: 100, 5.0: 125,
                        6.0: 150, 8.0: 200, 10.0: 250, 12.0: 300
                    }
                    mm_equiv = nb_standard_map.get(round(num_val, 2), int(num_val * 25.4))
                    extracted["size"] = f"{val}\" ({mm_equiv}MM NB)"
                    extracted["size_numeric_mm"] = mm_equiv
                except:
                    extracted["size"] = f"{val} INCH"
            else:
                try:
                    extracted["size"] = f"{val}MM NB"
                    extracted["size_numeric_mm"] = int(val)
                except:
                    extracted["size"] = f"{val} MM"
        elif re.search(r'\b6310\b', raw_upper):
            extracted["size"] = "50MM BORE (50X110X27 MM)"
            extracted["size_numeric_mm"] = 50
        elif re.search(r'\b7312\b', raw_upper):
            extracted["size"] = "60MM BORE (60X130X31 MM)"
            extracted["size_numeric_mm"] = 60
        elif re.search(r'1200\s*MM', raw_upper):
            extracted["size"] = "WIDTH 1200 MM"
            extracted["size_numeric_mm"] = 1200
        elif re.search(r'3\s*C\s*X\s*240|3CX240|3\s*CORE\s*X\s*240', raw_upper):
            extracted["size"] = "3C X 240 SQ.MM"
            extracted["size_numeric_mm"] = 240

        # 3. Pressure Rating / Class / Schedule / Voltage Extraction
        rating_match = re.search(r'(CLASS\s*\d+|ASME\s*\d+#?|\d+#|\d+\s*LBS|SCH\s*\d+[A-Z]?|SCHEDULE\s*\d+|11\s*KV|33\s*KV|800\/4)', norm)
        if rating_match:
            extracted["rating"] = rating_match.group(1).upper()
            if "#" in extracted["rating"] or "LBS" in extracted["rating"]:
                clean_num = re.sub(r'[^\d]', '', extracted["rating"])
                extracted["rating"] = f"ASME CLASS {clean_num}"
        elif re.search(r'\b150#|\b150\s*LBS|\bCLASS\s*150', raw_upper):
            extracted["rating"] = "ASME CLASS 150"
        elif re.search(r'\b300#|\b300\s*LBS|\bCLASS\s*300', raw_upper):
            extracted["rating"] = "ASME CLASS 300"
        elif re.search(r'\bSCH\s*40\b|\bSCHEDULE\s*40\b', raw_upper):
            extracted["rating"] = "SCHEDULE 40"
        elif re.search(r'\b11\s*KV\b', raw_upper):
            extracted["rating"] = "11 KV"

        # 4. Material Grade Extraction
        if re.search(r'ASTM\s*A216\s*(GR\s*)?WCB|WCB\b', norm):
            extracted["material_grade"] = "ASTM A216 GR WCB"
        elif re.search(r'ASTM\s*A106\s*(GR\s*)?B|A106-B\b|A106B\b', norm):
            extracted["material_grade"] = "ASTM A106 GRADE B"
        elif re.search(r'ASTM\s*A105\b|A-105\b|A105\b', norm):
            extracted["material_grade"] = "FORGED CS ASTM A105"
        elif re.search(r'A312.*316L|TP316L|SS316L|STAINLESS STEEL 316', norm):
            extracted["material_grade"] = "STAINLESS STEEL 316 / 316L"
        elif re.search(r'CHROME STEEL|100CR6|52100|SKF|FAG', norm):
            extracted["material_grade"] = "CHROME STEEL (SAE 52100)"
        elif re.search(r'ALUMINIUM|COND AL', norm):
            extracted["material_grade"] = "STRANDED ALUMINIUM (EC GRADE)"
        elif re.search(r'NYLON-NYLON|NN FABRIC|NN 4-PLY', norm):
            extracted["material_grade"] = "NYLON-NYLON (NN) FABRIC + GRADE X"

        # 5. End Connection / Interface Extraction
        if re.search(r'FLANGED.*RAISED FACE|FLGD.*RF|RF ENDS|RAISED FACE', norm):
            extracted["end_connection"] = "FLANGED RAISED FACE (RF)"
        elif re.search(r'BEVELLED END|BE ENDS|BEV\b|BW\b|BUTT WELD', norm):
            extracted["end_connection"] = "BEVELLED ENDS (BE)"
        elif re.search(r'RUBBER SEAL|2RS|2RS1', norm):
            extracted["end_connection"] = "DOUBLE RUBBER SEAL (2RS1)"
        elif re.search(r'ARMOURED|FLAT STEEL WIRE', norm):
            extracted["end_connection"] = "STEEL WIRE ARMOURED"

        # 6. Standards Extraction
        std_match = re.search(r'(API\s*600|API\s*6D|ASME\s*B16\.5|ASME\s*B16\.34|ASME\s*B36\.10M?|IS\s*7098|DIN\s*22102|IS\s*1891|ASME\s*B16\.20)', norm)
        if std_match:
            extracted["standard"] = std_match.group(1).upper()
        else:
            if extracted["category"] == "VALVES":
                extracted["standard"] = "API 600 / ASME B16.34"
            elif extracted["category"] == "PIPES_TUBES":
                extracted["standard"] = "ASME B36.10M / ASTM A106"
            elif extracted["category"] == "BEARINGS":
                extracted["standard"] = "ISO 15 / DIN 625-1"
            elif extracted["category"] == "CABLES_ELECTRICAL":
                extracted["standard"] = "IS:7098 PART 2"
            elif extracted["category"] == "FLANGES_FITTINGS":
                extracted["standard"] = "ASME B16.5"
            elif extracted["category"] == "MINING_CONVEYORS":
                extracted["standard"] = "DIN 22102 / IS 1891"

        return extracted

    def build_standardized_descriptions(self, attributes: Dict[str, Any]) -> Dict[str, str]:
        """
        Generates standard master, short (SAP 40-char), and GeM long descriptions.
        """
        item_type = attributes.get("item_type", "ITEM")
        size = attributes.get("size", "").replace("\"", "IN")
        rating = attributes.get("rating", "")
        grade = attributes.get("material_grade", "")
        end_conn = attributes.get("end_connection", "")
        standard = attributes.get("standard", "")

        parts = [p for p in [item_type, size, rating, grade, end_conn, standard] if p and p != "N/A"]
        standard_master = ", ".join(parts)

        # SAP 40-character Short Description
        short_tokens = []
        if "GATE" in item_type:
            short_tokens.append("VLV GATE")
        elif "BALL" in item_type:
            short_tokens.append("VLV BALL")
        elif "SEAMLESS" in item_type:
            short_tokens.append("PIPE SMLS")
        elif "BEARING" in item_type:
            short_tokens.append("BRG DGBB")
        elif "CABLE" in item_type:
            short_tokens.append("CBL 11KV")
        elif "FLANGE" in item_type:
            short_tokens.append("FLG WN")
        else:
            short_tokens.append(item_type[:8])

        # Add size
        if "100MM" in size or "4" in size:
            short_tokens.append("100NB")
        elif "150MM" in size or "6" in size:
            short_tokens.append("150NB")
        elif "50MM" in size or "2" in size:
            short_tokens.append("50NB")
        elif "1200" in size:
            short_tokens.append("1200MM")
        elif "240" in size:
            short_tokens.append("3CX240")

        # Add rating
        if "150" in rating:
            short_tokens.append("150#")
        elif "300" in rating:
            short_tokens.append("300#")
        elif "SCH 40" in rating:
            short_tokens.append("SCH40")

        # Add grade
        if "WCB" in grade:
            short_tokens.append("WCB")
        elif "A106" in grade:
            short_tokens.append("A106B")
        elif "A105" in grade:
            short_tokens.append("A105")
        elif "6310" in grade or "6310" in standard_master:
            short_tokens.append("6310-2RS")

        short_desc = " ".join(short_tokens)[:40].strip()

        # Detailed Long Description for GeM / e-Procurement
        long_desc = f"{item_type}, NOMINAL SPECIFICATION: {size}, RATING/DUTY: {rating}, BODY MATERIAL: {grade}, CONNECTION/SEALING: {end_conn}, SPECIFICATION STANDARD: {standard}"

        return {
            "standard_master": standard_master,
            "sap_short_desc": short_desc,
            "gem_long_desc": long_desc
        }

    def fit_corpus(self, catalog_items: List[Dict[str, Any]]):
        """Fits TF-IDF vectorizer over existing descriptions."""
        self.corpus_descriptions = [self.normalize_text(item["description"]) for item in catalog_items]
        self.corpus_ids = [item.get("id") or item.get("cnmc") for item in catalog_items]
        if self.corpus_descriptions:
            self.vectorizer.fit(self.corpus_descriptions)
            self._fitted = True

    def calculate_similarity(
        self,
        query_text: str,
        target_item: Dict[str, Any],
        query_attrs: Dict[str, Any] = None
    ) -> Dict[str, Any]:
        """
        Computes composite similarity between an input text and a target catalog record:
        - Technical Attribute Compatibility (Weighted 60-70%)
        - TF-IDF Vector Cosine Similarity (Weighted 20%)
        - String Fuzzy & Token Overlap (Weighted 10-20%)
        """
        if query_attrs is None:
            query_attrs = self.extract_attributes(query_text)

        target_short = target_item.get("standard_short_desc", "")
        target_long = target_item.get("standard_long_desc") or target_item.get("description", "")
        target_attrs = dict(target_item.get("attributes") or self.extract_attributes(target_long or target_short))
        
        # Ensure category is present in target_attrs
        target_cat = target_attrs.get("category") or target_item.get("category", "GENERAL_SPARES")
        target_attrs["category"] = target_cat
        query_cat = query_attrs.get("category", "GENERAL_SPARES")

        # 1. Attribute Match Score (0.0 to 1.0)
        attr_scores = []
        # Category & Item Type
        if query_cat != "GENERAL_SPARES" and target_cat != "GENERAL_SPARES":
            attr_scores.append(1.0 if query_cat == target_cat else 0.0)

        q_type = query_attrs.get("item_type", "UNKNOWN")
        t_type = target_attrs.get("item_type", "UNKNOWN")
        if q_type != "UNKNOWN" and t_type != "UNKNOWN":
            attr_scores.append(1.0 if q_type == t_type else 0.0)

        # Size Compatibility (checks metric vs imperial equivalents)
        q_size_num = query_attrs.get("size_numeric_mm")
        t_size_num = target_attrs.get("size_numeric_mm")
        if q_size_num and t_size_num:
            diff_ratio = abs(q_size_num - t_size_num) / max(q_size_num, t_size_num)
            attr_scores.append(1.0 if diff_ratio <= 0.08 else 0.0)
        elif query_attrs.get("size") != "N/A" and target_attrs.get("size") != "N/A":
            attr_scores.append(1.0 if query_attrs["size"] in target_attrs["size"] or target_attrs["size"] in query_attrs["size"] else 0.0)

        # Rating Compatibility
        q_rating = query_attrs.get("rating", "")
        t_rating = target_attrs.get("rating", "")
        if q_rating != "N/A" and t_rating != "N/A":
            q_clean_rat = re.sub(r'[^\w]', '', q_rating.upper())
            t_clean_rat = re.sub(r'[^\w]', '', t_rating.upper())
            attr_scores.append(1.0 if q_clean_rat in t_clean_rat or t_clean_rat in q_clean_rat else 0.0)

        # Material Grade Compatibility
        q_grade = query_attrs.get("material_grade", "")
        t_grade = target_attrs.get("material_grade", "")
        if q_grade != "N/A" and t_grade != "N/A":
            q_clean_grd = re.sub(r'[^\w]', '', q_grade.upper())
            t_clean_grd = re.sub(r'[^\w]', '', t_grade.upper())
            attr_scores.append(1.0 if q_clean_grd in t_clean_grd or t_clean_grd in q_clean_grd else 0.0)

        attribute_score = np.mean(attr_scores) if attr_scores else 0.5

        # 2. String Fuzzy Similarity & Token Overlap (evaluated against both short & long descriptions)
        query_norm = query_attrs.get("normalized_text", self.normalize_text(query_text))
        target_norm_short = self.normalize_text(target_short)
        target_norm_long = self.normalize_text(target_long)

        fuzzy_short = difflib.SequenceMatcher(None, query_norm, target_norm_short).ratio() if target_norm_short else 0
        fuzzy_long = difflib.SequenceMatcher(None, query_norm, target_norm_long).ratio() if target_norm_long else 0
        fuzzy_score = max(fuzzy_short, fuzzy_long)

        # Token Overlap (Jaccard)
        q_tokens = set(query_norm.split())
        t_tokens_short = set(target_norm_short.split()) if target_norm_short else set()
        t_tokens_long = set(target_norm_long.split()) if target_norm_long else set()

        overlap_short = len(q_tokens.intersection(t_tokens_short)) / max(len(q_tokens), 1) if t_tokens_short else 0
        overlap_long = len(q_tokens.intersection(t_tokens_long)) / max(len(q_tokens), 1) if t_tokens_long else 0
        token_overlap = max(overlap_short, overlap_long)

        # 3. TF-IDF Cosine Similarity
        cosine_score = token_overlap
        if self._fitted:
            try:
                targets_to_test = [t for t in [target_norm_short, target_norm_long] if t]
                if targets_to_test:
                    tfidf_mat = self.vectorizer.transform([query_norm] + targets_to_test)
                    cos_sims = cosine_similarity(tfidf_mat[0:1], tfidf_mat[1:])
                    cosine_score = float(np.max(cos_sims))
            except Exception:
                cosine_score = token_overlap

        # Weighted Composite Score
        if attribute_score >= 0.85:
            composite_score = (attribute_score * 0.70) + (max(cosine_score, token_overlap) * 0.20) + (fuzzy_score * 0.10)
        else:
            composite_score = (attribute_score * 0.45) + (max(cosine_score, token_overlap) * 0.35) + (fuzzy_score * 0.20)

        confidence_pct = round(composite_score * 100, 1)

        # Classification into Match Type
        if attribute_score >= 0.90 and (confidence_pct >= 80.0 or token_overlap >= 0.65):
            match_type = "EXACT_DUPLICATE"
            recommendation = "Harmonize under identical National Material Code. Consolidate legacy code."
        elif attribute_score >= 0.75 or confidence_pct >= 70.0:
            match_type = "NEAR_DUPLICATE"
            recommendation = "Near-identical specification. Standardize description and map to National Code."
        elif attribute_score >= 0.55 and query_attrs.get("category") == target_attrs.get("category"):
            match_type = "FUNCTIONAL_EQUIVALENT"
            recommendation = "Functionally interchangeable in plant operations. Suitable for inter-CPSE stock sharing."
        else:
            match_type = "DISTINCT_ITEM"
            recommendation = "Specifications diverge significantly. Requires new National Code or separate entry."

        return {
            "confidence_pct": confidence_pct,
            "match_type": match_type,
            "recommendation": recommendation,
            "score_breakdown": {
                "attribute_compatibility": round(attribute_score * 100, 1),
                "semantic_cosine": round(cosine_score * 100, 1),
                "string_fuzzy": round(fuzzy_score * 100, 1)
            },
            "query_attributes": query_attrs,
            "target_attributes": target_attrs
        }

    def match_against_national_masters(
        self,
        query_text: str,
        national_masters: List[Dict[str, Any]],
        threshold: float = 60.0
    ) -> List[Dict[str, Any]]:
        """Finds closest matching National Master codes for a given CPSE description."""
        query_attrs = self.extract_attributes(query_text)
        results = []

        for master in national_masters:
            sim = self.calculate_similarity(query_text, master, query_attrs)
            if sim["confidence_pct"] >= threshold:
                results.append({
                    "national_master": master,
                    "confidence_pct": sim["confidence_pct"],
                    "match_type": sim["match_type"],
                    "recommendation": sim["recommendation"],
                    "score_breakdown": sim["score_breakdown"],
                    "query_attributes": sim["query_attributes"],
                    "target_attributes": sim["target_attributes"]
                })

        # Sort descending by confidence
        results.sort(key=lambda x: x["confidence_pct"], reverse=True)
        return results

# Singleton instance
ai_engine = AIEngine()
