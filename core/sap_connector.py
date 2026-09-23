"""
SAP / ERP Integration Connector & Payload Generator.
Simulates SAP S/4HANA and ECC 6.0 interfaces:
- BAPI_MATERIAL_SAVEDATA (RFC)
- IDoc MATMAS05 (XML)
- OData API v4 (JSON REST)
"""

import datetime
import json
from typing import Dict, Any, List

class SAPConnector:
    def __init__(self):
        self.systems = {
            "ONGC_PRD": {"system_id": "OG1", "client": "400", "host": "sap-s4-ongc.internal.net:3300", "type": "SAP S/4HANA 2023"},
            "IOCL_PRD": {"system_id": "IC1", "client": "500", "host": "sap-ecc-iocl.internal.net:3300", "type": "SAP ECC 6.0 EHP8"},
            "NTPC_PRD": {"system_id": "NT1", "client": "300", "host": "sap-s4-ntpc.internal.net:3300", "type": "SAP S/4HANA 2022"},
            "SAIL_PRD": {"system_id": "SL1", "client": "200", "host": "sap-erp-sail.internal.net:3300", "type": "SAP ECC 6.0"},
            "CIL_PRD":  {"system_id": "CL1", "client": "600", "host": "sap-s4-cil.internal.net:3300", "type": "SAP S/4HANA 2023"}
        }

    def generate_bapi_payload(self, national_item: Dict[str, Any], target_cpse: str) -> Dict[str, Any]:
        """
        Generates standard SAP BAPI_MATERIAL_SAVEDATA structure with Common National Code extension.
        """
        cnmc = national_item.get("cnmc", "")
        short_desc = national_item.get("standard_short_desc", "")[:40]
        uom = national_item.get("standard_uom", "EA")
        mat_type = "ERSA"  # Spare Parts

        bapi_call = {
            "FUNCTION": "BAPI_MATERIAL_SAVEDATA",
            "PARAMETERS": {
                "HEADDATA": {
                    "MATERIAL": cnmc,
                    "IND_SECTOR": "M",  # Mechanical / Mining
                    "MATL_TYPE": mat_type,
                    "BASIC_VIEW": "X",
                    "PURCHASE_VIEW": "X"
                },
                "CLIENTDATA": {
                    "BASE_UOM": uom,
                    "MATL_GROUP": national_item.get("category", "VALVES"),
                    "DIVISION": "01",
                    "OLD_MAT_NO": f"CPSE-LEGACY-{target_cpse}"
                },
                "CLIENTDATAX": {
                    "BASE_UOM": "X",
                    "MATL_GROUP": "X",
                    "DIVISION": "X",
                    "OLD_MAT_NO": "X"
                },
                "MATERIALDESCRIPTION": [
                    {
                        "LANGU": "EN",
                        "LANGU_ISO": "EN",
                        "MATL_DESC": short_desc
                    }
                ],
                "EXTENSIONIN": [
                    {
                        "STRUCTURE": "BAPI_TE_MARA",
                        "VALUEPART1": f"CNMC={cnmc};GOV_STATUS={national_item.get('harmonization_status')};RATIFIED_BY=NMSD"
                    }
                ]
            }
        }
        return bapi_call

    def generate_idoc_xml(self, national_item: Dict[str, Any], target_cpse: str) -> str:
        """
        Generates standard SAP IDoc MATMAS05 XML document.
        """
        now_str = datetime.datetime.now().strftime("%Y%m%d%H%M%S")
        cnmc = national_item.get("cnmc", "")
        short_desc = national_item.get("standard_short_desc", "")[:40]
        uom = national_item.get("standard_uom", "EA")
        category = national_item.get("category", "VALVES")
        hsn = national_item.get("hsn_code", "8481.80.30")

        xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<MATMAS05>
  <IDOC BEGIN="1">
    <EDI_DC40 SEGMENT="1">
      <TABNAM>EDI_DC40</TABNAM>
      <MANDT>400</MANDT>
      <DOCNUM>00000004928104</DOCNUM>
      <MESTYP>MATMAS</MESTYP>
      <IDOCTYP>MATMAS05</IDOCTYP>
      <SNDPOR>SAPPORT_ONMC</SNDPOR>
      <SNDPRT>LS</SNDPRT>
      <SNDPRN>NAT_MASTER_PORTAL</SNDPRN>
      <RCVPOR>SAP_CPSE</RCVPOR>
      <RCVPRN>{target_cpse}_ERP</RCVPRN>
      <CREDAT>{now_str[:8]}</CREDAT>
      <CRETIM>{now_str[8:]}</CRETIM>
    </EDI_DC40>
    <E1MARAM SEGMENT="1">
      <MSGFN>005</MSGFN>
      <MATNR>{cnmc}</MATNR>
      <MTART>ERSA</MTART>
      <MBRSH>M</MBRSH>
      <MEINS>{uom}</MEINS>
      <MATKL>{category}</MATKL>
      <NUMM_HSN>{hsn}</NUMM_HSN>
      <E1MAKTM SEGMENT="1">
        <MSGFN>005</MSGFN>
        <SPRAS>E</SPRAS>
        <SPRAS_ISO>EN</SPRAS_ISO>
        <MAKTX>{short_desc}</MAKTX>
      </E1MAKTM>
      <!-- Custom CPSE National Unified Master Extension -->
      <ZE1CPSE_CNMC SEGMENT="1">
        <CNMC_CODE>{cnmc}</CNMC_CODE>
        <GOV_STATUS>{national_item.get('harmonization_status', 'APPROVED')}</GOV_STATUS>
        <SYNC_TIMESTAMP>{datetime.datetime.now().isoformat()}</SYNC_TIMESTAMP>
      </ZE1CPSE_CNMC>
    </E1MARAM>
  </IDOC>
</MATMAS05>"""
        return xml

    def generate_odata_json(self, national_item: Dict[str, Any], target_cpse: str) -> Dict[str, Any]:
        """
        Generates SAP S/4HANA OData API v4 Material Product Master JSON.
        """
        cnmc = national_item.get("cnmc", "")
        return {
            "@odata.context": f"$metadata#{target_cpse}_A_Product/$entity",
            "Product": cnmc,
            "ProductType": "ERSA",
            "BaseUnit": national_item.get("standard_uom", "EA"),
            "ProductGroup": national_item.get("category", "VALVES"),
            "IndustrySector": "M",
            "CountryOfOrigin": "IN",
            "HarmonizedSystemCode": national_item.get("hsn_code", "8481.80.30"),
            "to_Description": [
                {
                    "Language": "EN",
                    "ProductDescription": national_item.get("standard_short_desc", "")[:40]
                }
            ],
            "to_NationalMasterMapping": {
                "CommonNationalMaterialCode": cnmc,
                "NationalStandardLongDescription": national_item.get("standard_long_desc", ""),
                "GoverningAgency": "National Material Standardization Directorate",
                "RatificationStatus": national_item.get("harmonization_status", "APPROVED")
            }
        }

    def simulate_erp_sync(self, cnmc: str, target_cpse: str) -> Dict[str, Any]:
        """
        Simulates two-way sync between National Unified Portal and target CPSE SAP System.
        """
        now = datetime.datetime.now()
        timestamp = now.strftime("%Y-%m-%d %H:%M:%S")
        doc_no = f"MATDOC-{now.strftime('%y%m%d')}-{abs(hash(cnmc + target_cpse)) % 90000 + 10000}"

        return {
            "status": "SUCCESS",
            "http_code": 200,
            "target_cpse": target_cpse,
            "system_id": self.systems.get(f"{target_cpse}_PRD", {}).get("system_id", "CP1"),
            "cnmc": cnmc,
            "sap_document_number": doc_no,
            "rfc_bapi_return": {
                "TYPE": "S",
                "ID": "M3",
                "NUMBER": "800",
                "MESSAGE": f"Material {cnmc} successfully synchronized and committed in {target_cpse} SAP S/4HANA master.",
                "LOG_NO": f"SLG1-{doc_no}",
                "COMMIT_WORK": True
            },
            "idoc_status": {
                "status_code": "53",
                "description": "Application document posted successfully via IDoc MATMAS05",
                "idoc_number": f"000000{abs(hash(cnmc)) % 8000000 + 1000000}"
            },
            "timestamp": timestamp
        }

sap_connector = SAPConnector()
