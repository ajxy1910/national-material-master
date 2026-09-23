"""
Duplicate, Near-Duplicate, and Functional Equivalency Clustering Engine.
Calculates catalog rationalization rate, cross-CPSE procurement price variance, and demand aggregation savings.
"""

from typing import List, Dict, Any
from core.ai_engine import ai_engine
from core.code_generator import code_generator
from data.cpse_catalog import CPSE_RAW_MATERIALS, NATIONAL_MASTER_CATALOG

class Deduplicator:
    def __init__(self):
        self.raw_materials = list(CPSE_RAW_MATERIALS)
        self.national_masters = list(NATIONAL_MASTER_CATALOG)
        # Fit AI engine on descriptions
        ai_engine.fit_corpus(self.raw_materials + [
            {"id": m["cnmc"], "description": m["standard_long_desc"]}
            for m in self.national_masters
        ])

    def build_clusters(self) -> List[Dict[str, Any]]:
        """
        Groups CPSE raw materials around National Master codes,
        detecting exact duplicates, near-duplicates, and functional equivalents.
        """
        clusters = []

        for master in self.national_masters:
            cluster_items = []
            mapped_ids = set(master.get("mapped_cpse_items", []))

            # Fetch matching raw materials
            for item in self.raw_materials:
                if item["id"] in mapped_ids:
                    sim = ai_engine.calculate_similarity(item["description"], master)
                    cluster_items.append({
                        **item,
                        "similarity_score": sim["confidence_pct"],
                        "match_type": sim["match_type"],
                        "score_breakdown": sim["score_breakdown"],
                        "recommendation": sim["recommendation"]
                    })

            prices = [item["unit_price_inr"] for item in cluster_items]
            min_price = min(prices) if prices else master["benchmark_price_inr"]
            max_price = max(prices) if prices else master["benchmark_price_inr"]
            avg_price = sum(prices) / len(prices) if prices else master["benchmark_price_inr"]
            variance_pct = round(((max_price - min_price) / min_price * 100), 1) if min_price > 0 else 0

            total_qty = sum(item["annual_procurement_qty"] for item in cluster_items)
            total_spend_current = sum(item["unit_price_inr"] * item["annual_procurement_qty"] for item in cluster_items)
            
            negotiated_bulk_price = round(min_price * 0.92, 0)
            total_spend_aggregated = negotiated_bulk_price * total_qty
            potential_savings_inr = max(0, total_spend_current - total_spend_aggregated)
            potential_savings_crores = round(potential_savings_inr / 10_000_000, 2)

            total_stock_on_hand = sum(item["stock_on_hand"] for item in cluster_items)

            clusters.append({
                "cnmc": master["cnmc"],
                "category": master["category"],
                "standard_short_desc": master["standard_short_desc"],
                "standard_long_desc": master["standard_long_desc"],
                "standard_uom": master["standard_uom"],
                "harmonization_status": master["harmonization_status"],
                "items_count": len(cluster_items),
                "items": cluster_items,
                "price_stats": {
                    "min_price_inr": min_price,
                    "max_price_inr": max_price,
                    "avg_price_inr": round(avg_price, 0),
                    "variance_pct": variance_pct,
                    "benchmark_price_inr": master["benchmark_price_inr"],
                    "negotiated_bulk_price": negotiated_bulk_price
                },
                "procurement_analytics": {
                    "total_annual_demand_qty": total_qty,
                    "total_stock_on_hand": total_stock_on_hand,
                    "current_annual_spend_inr": total_spend_current,
                    "aggregated_annual_spend_inr": total_spend_aggregated,
                    "potential_savings_crores": potential_savings_crores
                }
            })

        return clusters

    def get_summary_metrics(self) -> Dict[str, Any]:
        """Calculates executive dashboard KPIs."""
        total_raw_codes = len(self.raw_materials)
        total_national_codes = len(self.national_masters)
        clusters = self.build_clusters()

        total_savings_crores = round(sum(
            c["procurement_analytics"]["potential_savings_crores"] for c in clusters
        ), 2)

        rationalization_rate = round(((total_raw_codes - total_national_codes) / total_raw_codes) * 100, 1)

        cpse_counts = {}
        for item in self.raw_materials:
            cpse = item["cpse"]
            cpse_counts[cpse] = cpse_counts.get(cpse, 0) + 1

        exact_count = 0
        near_count = 0
        equiv_count = 0
        for cluster in clusters:
            for itm in cluster["items"]:
                if itm["match_type"] == "EXACT_DUPLICATE":
                    exact_count += 1
                elif itm["match_type"] == "NEAR_DUPLICATE":
                    near_count += 1
                else:
                    equiv_count += 1

        return {
            "total_raw_materials_ingested": total_raw_codes,
            "total_national_master_codes": total_national_codes,
            "redundant_codes_eliminated": total_raw_codes - total_national_codes,
            "rationalization_rate_pct": rationalization_rate,
            "total_procurement_savings_crores": total_savings_crores,
            "total_surplus_stock_visible": sum(c["procurement_analytics"]["total_stock_on_hand"] for c in clusters),
            "cpse_item_counts": cpse_counts,
            "match_distribution": {
                "exact_duplicates": exact_count,
                "near_duplicates": near_count,
                "functional_equivalents": equiv_count
            }
        }

deduplicator = Deduplicator()
