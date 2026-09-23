import sys
import argparse
import csv
import json
from pprint import pprint

# Ensure UTF-8 output on Windows consoles
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')
if hasattr(sys.stderr, 'reconfigure'):
    sys.stderr.reconfigure(encoding='utf-8')

from core.ai_engine import ai_engine
from core.code_generator import code_generator
from core.deduplicator import deduplicator
from data.cpse_catalog import NATIONAL_MASTER_CATALOG, CPSE_RAW_MATERIALS

def cmd_match(args):
    """Match a free-text description against National Material Masters."""
    print(f"\n🔍 Searching National Master for: '{args.description}' (Threshold: {args.threshold}%)\n")
    attrs = ai_engine.extract_attributes(args.description)
    print("📋 Parsed Engineering Attributes:")
    for k, v in attrs.items():
        if k != "normalized_text" and v and v != "N/A":
            print(f"  • {k.replace('_', ' ').title()}: {v}")

    matches = ai_engine.match_against_national_masters(
        query_text=args.description,
        national_masters=NATIONAL_MASTER_CATALOG,
        threshold=args.threshold
    )

    if not matches:
        print("\n❌ No National Masters found above threshold.")
        proposed_code = code_generator.generate_cnmc(attrs)
        print(f"💡 Recommended New Common National Material Code: {proposed_code}\n")
        return

    print(f"\n✅ Found {len(matches)} Matching National Material Master(s):")
    for i, m in enumerate(matches, 1):
        master = m["national_master"]
        print(f"\n[{i}] {master['cnmc']} | Score: {m['confidence_pct']}% | Type: {m['match_type']}")
        print(f"    Short Desc: {master['standard_short_desc']}")
        print(f"    Breakdown : Attr: {m['score_breakdown']['attribute_compatibility']}% | Cosine: {m['score_breakdown']['semantic_cosine']}% | Fuzzy: {m['score_breakdown']['string_fuzzy']}%")
        print(f"    Action    : {m['recommendation']}")
    print()

def cmd_standardize(args):
    """Parse text and generate standardized descriptions and Common National Code."""
    print(f"\n⚙️  Standardizing description: '{args.text}'\n")
    attrs = ai_engine.extract_attributes(args.text)
    descs = ai_engine.build_standardized_descriptions(attrs)
    cnmc = code_generator.generate_cnmc(attrs)
    valid, msg = code_generator.validate_cnmc(cnmc)

    print("🏷️  Common National Material Code (CNMC):", cnmc)
    print("🛡️  Validation Status:", "VALID" if valid else f"INVALID ({msg})")
    print("\n📝 Formatted Master Description:")
    print("   ", descs["standard_master"])
    print("\n🏢 SAP 40-Character Short Description (MARA-MAKTX):")
    print(f"    '{descs['sap_short_desc']}' ({len(descs['sap_short_desc'])} chars)")
    print("\n🌐 GeM e-Procurement Long Description:")
    print("   ", descs["gem_long_desc"])
    print()

def cmd_stats(args):
    """Display National Unified Material Master metrics & savings."""
    metrics = deduplicator.get_summary_metrics()
    print("\n🇮🇳  NATIONAL UNIFIED MATERIAL MASTER (NUMM) - EXECUTIVE SUMMARY")
    print("=" * 65)
    print(f"Total CPSE Raw Catalog Records Ingested : {metrics['total_raw_materials_ingested']}")
    print(f"Unified National Master Items Created   : {metrics['total_national_master_codes']}")
    print(f"Redundant / Duplicate Codes Eliminated  : {metrics['redundant_codes_eliminated']}")
    print(f"Catalog Sprawl Rationalization Rate     : {metrics['rationalization_rate_pct']}%")
    print(f"Strategic Sourcing Savings Potential    : ₹ {metrics['total_procurement_savings_crores']} Crores")
    print(f"Inter-CPSE Visible Surplus Inventory    : {metrics['total_surplus_stock_visible']} Units")
    print("=" * 65)
    print("CPSE Material Share:")
    for cpse, cnt in metrics["cpse_item_counts"].items():
        print(f"  • {cpse:12}: {cnt} items")
    print("=" * 65 + "\n")

def cmd_harmonize(args):
    """Batch harmonize a CSV file of legacy materials."""
    input_file = args.input_file
    output_file = args.output or "harmonized_output.csv"
    print(f"\n📂 Reading legacy catalog from: {input_file}")

    with open(input_file, mode="r", encoding="utf-8-sig") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"⚙️  Processing {len(rows)} records using AI Engine...")

    results = []
    for r in rows:
        desc = r.get("description", "")
        attrs = ai_engine.extract_attributes(desc)
        descs = ai_engine.build_standardized_descriptions(attrs)
        matches = ai_engine.match_against_national_masters(desc, NATIONAL_MASTER_CATALOG, threshold=60.0)

        if matches and matches[0]["confidence_pct"] >= 90:
            cnmc = matches[0]["national_master"]["cnmc"]
            status = "MAPPED_EXISTING"
            score = matches[0]["confidence_pct"]
        else:
            cnmc = code_generator.generate_cnmc(attrs)
            status = "NEW_PROPOSAL"
            score = matches[0]["confidence_pct"] if matches else 100.0

        results.append({
            "Legacy_Code": r.get("legacy_code", ""),
            "CPSE": r.get("cpse_name", ""),
            "Original_Description": desc,
            "Standard_Short_Desc": descs["sap_short_desc"],
            "Common_National_Material_Code": cnmc,
            "Harmonization_Status": status,
            "Confidence_Score": f"{score}%"
        })

    with open(output_file, mode="w", newline="", encoding="utf-8-sig") as f:
        writer = csv.DictWriter(f, fieldnames=list(results[0].keys()))
        writer.writeheader()
        writer.writerows(results)

    print(f"✅ Successfully harmonized and saved to: {output_file}\n")

def main():
    parser = argparse.ArgumentParser(description="National Unified Material Master CLI ('One Nation – One Material Code')")
    subparsers = parser.add_subparsers(dest="command", help="Available subcommands")

    # Match subcommand
    p_match = subparsers.add_parser("match", help="Match material text against National Master")
    p_match.add_argument("description", type=str, help="Raw material description text")
    p_match.add_argument("--threshold", type=float, default=60.0, help="Minimum similarity threshold")
    p_match.set_defaults(func=cmd_match)

    # Standardize subcommand
    p_std = subparsers.add_parser("standardize", help="Standardize description & generate National Code")
    p_std.add_argument("text", type=str, help="Raw material description text")
    p_std.set_defaults(func=cmd_standardize)

    # Stats subcommand
    p_stats = subparsers.add_parser("stats", help="Show executive metrics & rationalization rate")
    p_stats.set_defaults(func=cmd_stats)

    # Harmonize subcommand
    p_harm = subparsers.add_parser("harmonize", help="Batch harmonize legacy CSV file")
    p_harm.add_argument("input_file", type=str, help="Path to input CSV file")
    p_harm.add_argument("--output", type=str, default="harmonized_output.csv", help="Path to output CSV")
    p_harm.set_defaults(func=cmd_harmonize)

    args = parser.parse_args()
    if hasattr(args, "func"):
        args.func(args)
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
