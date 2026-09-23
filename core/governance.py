"""
Material Master Governance, Review Workflow, and Immutable Audit Trail.
Tracks multi-tier stakeholder reviews and changes across participating CPSEs.
"""

import datetime
from typing import List, Dict, Any, Optional

class GovernanceEngine:
    ALLOWED_STATUSES = [
        "AI_RECOMMENDED",
        "CPSE_REVIEW",
        "COMMITTEE_EVALUATION",
        "APPROVED_NATIONAL_CODE",
        "REJECTED"
    ]

    def __init__(self):
        # Pre-populated realistic audit trail events
        self.audit_log: List[Dict[str, Any]] = [
            {
                "id": "AUD-001",
                "timestamp": "2026-03-20T10:15:00",
                "cnmc": "IN-NMC-7304-PIPS-150-A106-9",
                "action": "CODE_RATIFIED",
                "actor": "Shri R. K. Sharma (Director - Standardisation, Ministry of Steel / CPSE Cell)",
                "actor_org": "National Material Standardization Directorate",
                "previous_status": "COMMITTEE_EVALUATION",
                "new_status": "APPROVED_NATIONAL_CODE",
                "remarks": "Harmonized Seamless Pipe 6\" SCH 40 A106 Gr B across ONGC, IOCL, BPCL, GAIL, and SAIL.",
                "affected_legacy_codes": ["32018844 (ONGC)", "PIP-CS-06-040 (IOCL)", "BP-PIP-150-40 (BPCL)", "GAIL-PIP-6S40 (GAIL)", "SAIL-P-640106 (SAIL)"]
            },
            {
                "id": "AUD-002",
                "timestamp": "2026-04-10T14:30:00",
                "cnmc": "IN-NMC-8481-VLVG-100-WCB-4",
                "action": "CODE_RATIFIED",
                "actor": "Dr. Ananya Sen (Chief General Manager - Materials, IOCL)",
                "actor_org": "Indian Oil Corporation Ltd.",
                "previous_status": "COMMITTEE_EVALUATION",
                "new_status": "APPROVED_NATIONAL_CODE",
                "remarks": "Approved Gate Valve 4\" 150# WCB OS&Y common code. Inter-CPSE valve compatibility verified.",
                "affected_legacy_codes": ["31045821 (ONGC)", "MAT-GLV-004-150 (IOCL)", "GAIL-VLV-4-150-CS (GAIL)", "NTPC-44019283 (NTPC)", "BP-V-0415-WCB (BPCL)"]
            },
            {
                "id": "AUD-003",
                "timestamp": "2026-05-02T11:45:00",
                "cnmc": "IN-NMC-8428-BLTC-1200-800-8",
                "action": "CODE_RATIFIED",
                "actor": "Shri V. P. Reddy (Executive Director - Procurement, Coal India Ltd.)",
                "actor_org": "Coal India Ltd.",
                "previous_status": "COMMITTEE_EVALUATION",
                "new_status": "APPROVED_NATIONAL_CODE",
                "remarks": "Conveyor Belt 1200mm NN 800/4 harmonized for CIL, NMDC, SAIL, and NTPC Coal Handling Plants.",
                "affected_legacy_codes": ["CIL-BLT-1200-800", "NMDC-CNV-1200-NN", "SAIL-CV-120800", "NTPC-CHP-BLT-1200"]
            },
            {
                "id": "AUD-004",
                "timestamp": "2026-09-01T09:20:00",
                "cnmc": "IN-NMC-8481-VLVB-050-WCB-1",
                "action": "AI_RECOMMENDATION_GENERATED",
                "actor": "AI Unified Matching Engine v2.4",
                "actor_org": "National Master Portal Core",
                "previous_status": "DRAFT",
                "new_status": "AI_RECOMMENDED",
                "remarks": "Cluster detected across BHEL (BHEL-VLV-BALL-2-300), GAIL (GAIL-BLV-50-300), and ONGC (31049920). 96.4% technical attribute match.",
                "affected_legacy_codes": ["BHEL-VLV-BALL-2-300", "GAIL-BLV-50-300", "31049920"]
            }
        ]

    def log_action(
        self,
        cnmc: str,
        action: str,
        actor: str,
        actor_org: str,
        previous_status: str,
        new_status: str,
        remarks: str,
        affected_legacy_codes: Optional[List[str]] = None
    ) -> Dict[str, Any]:
        """Appends a new audit record to the tamper-evident log."""
        record_id = f"AUD-{len(self.audit_log) + 1:03d}"
        now_iso = datetime.datetime.now().strftime("%Y-%m-%dT%H:%M:%S")

        record = {
            "id": record_id,
            "timestamp": now_iso,
            "cnmc": cnmc,
            "action": action,
            "actor": actor,
            "actor_org": actor_org,
            "previous_status": previous_status,
            "new_status": new_status,
            "remarks": remarks,
            "affected_legacy_codes": affected_legacy_codes or []
        }
        self.audit_log.insert(0, record)  # latest first
        return record

    def get_audit_trail(self, cnmc: Optional[str] = None) -> List[Dict[str, Any]]:
        """Returns the full audit trail or filtered by CNMC."""
        if cnmc:
            return [rec for rec in self.audit_log if rec.get("cnmc") == cnmc]
        return self.audit_log

governance_engine = GovernanceEngine()
