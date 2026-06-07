import asyncio, sys, os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))
from data_processor.fetch_data_commons import fetch_place_statistics

def build_profiles(stats: dict) -> list[dict]:
    return [
        {
            "persona_type": "investor",
            "region": "us",
            "focus_area": "finance",
            "group_label": "Data-Driven Financial Decision Maker",
            "demographic_data": {"income_index": stats.get("finance_income_median"), "education": stats.get("marketing_educated")},
            "behavioral_profile": {"skepticism_level": 4, "decision_driver": "roi_evidence", "communication": "direct_metrics"},
            "group_size_estimate": int(stats.get("finance_employed") or 0)
        },
        {
            "persona_type": "customer",
            "region": "us",
            "focus_area": "marketing",
            "group_label": "Urban Professional Consumer",
            "demographic_data": {"youth_concentration": stats.get("marketing_young_professional"), "education": stats.get("marketing_educated")},
            "behavioral_profile": {"skepticism_level": 2, "decision_driver": "social_proof", "communication": "visual_narrative"},
            "group_size_estimate": int(stats.get("marketing_young_professional") or 0)
        },
        {
            "persona_type": "executive",
            "region": "us",
            "focus_area": "business",
            "group_label": "Strategic Business Operator",
            "demographic_data": {"self_employment": stats.get("business_self_employed")},
            "behavioral_profile": {"skepticism_level": 3, "decision_driver": "strategic_fit", "communication": "executive_summary"},
            "group_size_estimate": int(stats.get("business_self_employed") or 0)
        },
    ]

async def run():
    stats = await fetch_place_statistics()
    profiles = build_profiles(stats)
    for p in profiles:
        print(f"[{p['focus_area'].upper()}] {p['group_label']} — {p['group_size_estimate']:,}")
    return profiles

if __name__ == "__main__":
    asyncio.run(run())
