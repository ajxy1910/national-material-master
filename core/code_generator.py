"""
Common National Material Code (CNMC) Generator & Validation Engine.
Enforces the 'One Nation – One Material Code' hierarchical numbering standard with Check-Digit verification.
"""

import hashlib
import re
from typing import Dict, Any, Tuple
from data.taxonomies import COMMODITY_TAXONOMIES

class CodeGenerator:
    """
    Code Structure:
    IN-NMC-[HSN_4D]-[TYPE_4C]-[SIZE_3D]-[SPEC_4C]-[CHECK_DIGIT]
    Example:
    IN-NMC-8481-VLVG-100-WCB-4
    """

    PREFIX = "IN-NMC"

    TYPE_ABBREVIATIONS = {
        "GATE VALVE": "VLVG",
        "BALL VALVE": "VLVB",
        "GLOBE VALVE": "VLVL",
        "CHECK VALVE": "VLVC",
        "SEAMLESS PIPE": "PIPS",
        "WELD NECK FLANGE": "FLGW",
        "DEEP GROOVE BALL BEARING": "BRGD",
        "ANGULAR CONTACT BALL BEARING": "BRGA",
        "XLPE POWER CABLE": "CBLX",
        "CONVEYOR BELTING": "BLTC",
        "SPIRAL WOUND GASKET": "GKTS"
    }

    @staticmethod
    def calculate_check_digit(base_code: str) -> int:
        """
        Calculates ISO 7064 / Mod-10 check digit over alphanumeric characters.
        """
        clean_code = re.sub(r'[^A-Z0-9]', '', base_code.upper())
        total = 0
        for i, char in enumerate(reversed(clean_code)):
            val = int(char) if char.isdigit() else (ord(char) - ord('A') + 10)
            weight = 2 if (i % 2 == 0) else 1
            prod = val * weight
            total += (prod // 10) + (prod % 10)
        return (10 - (total % 10)) % 10

    @classmethod
    def generate_cnmc(cls, attributes: Dict[str, Any]) -> str:
        """
        Generates a deterministic, standardized National Material Code from parsed technical attributes.
        """
        category = attributes.get("category", "VALVES")
        item_type = attributes.get("item_type", "GATE VALVE")
        size_num = attributes.get("size_numeric_mm")
        grade = attributes.get("material_grade", "WCB").upper()
        rating = attributes.get("rating", "").upper()

        tax_info = COMMODITY_TAXONOMIES.get(category, COMMODITY_TAXONOMIES["VALVES"])
        hsn_prefix = tax_info["code_prefix"]

        type_code = cls.TYPE_ABBREVIATIONS.get(item_type, "GENM")

        if size_num:
            size_code = f"{int(size_num):03d}" if size_num < 1000 else f"{int(size_num)}"
        else:
            size_code = "000"

        if "WCB" in grade:
            spec_code = "WCB"
        elif "A106" in grade:
            spec_code = "A106"
        elif "A105" in grade:
            spec_code = "A105"
        elif "316" in grade:
            spec_code = "S316"
        elif "ALUMINIUM" in grade or "11KV" in rating:
            spec_code = "11KV"
        elif "6310" in str(attributes) or "CHROME" in grade:
            spec_code = "6310"
        elif "800" in rating or "NN" in grade:
            spec_code = "800"
        else:
            spec_code = hashlib.md5(grade.encode()).hexdigest()[:4].upper()

        base_str = f"{cls.PREFIX}-{hsn_prefix}-{type_code}-{size_code}-{spec_code}"
        check_digit = cls.calculate_check_digit(base_str)
        cnmc = f"{base_str}-{check_digit}"
        return cnmc

    @classmethod
    def validate_cnmc(cls, cnmc: str) -> Tuple[bool, str]:
        """
        Validates code structure, components, and check digit.
        Format: IN-NMC-[HSN]-[TYPE]-[SIZE]-[SPEC]-[CHECK] (7 tokens separated by '-')
        """
        parts = cnmc.strip().split("-")
        if len(parts) != 7 or parts[0] != "IN" or parts[1] != "NMC":
            return False, "Invalid format. Expected IN-NMC-[HSN]-[TYPE]-[SIZE]-[SPEC]-[CHECK]"
        
        base_code = "-".join(parts[:6])
        expected_check = cls.calculate_check_digit(base_code)
        
        try:
            actual_check = int(parts[6])
            if actual_check != expected_check:
                return False, f"Check digit mismatch: expected {expected_check}, found {actual_check}"
        except ValueError:
            return False, "Check digit must be an integer between 0 and 9"

        return True, "Valid Common National Material Code"

code_generator = CodeGenerator()
