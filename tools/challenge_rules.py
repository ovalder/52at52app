"""Challenge scoring only. Never substitute credited km for physical distance."""
from decimal import Decimal

GOAL_KM = 52
RULE_VERSION = "run-1-ride-half-v1"


def credited_distance(activity):
    kind = activity["type"].lower()
    if kind not in ("run", "ride"):
        raise ValueError("Activity type must be 'run' or 'ride'.")
    distance = Decimal(str(activity["distance_km"]))
    if not distance.is_finite() or distance < 0:
        raise ValueError("Distance must be a finite non-negative number.")
    return distance / (2 if kind == "ride" else 1)


def score(activities):
    credits = [credited_distance(a) for a in activities]
    credited = sum(credits, Decimal(0))
    return {
        "credited_km": float(credited),
        "credited_km_by_type": {
            kind: float(sum((c for a, c in zip(activities, credits)
                             if a["type"].lower() == kind), Decimal(0)))
            for kind in ("run", "ride")
        },
        "goal_km": GOAL_KM,
        "goal_met": credited >= GOAL_KM,
        "scoring_rule": RULE_VERSION,
    }


def week_score(week, activities):
    rows = [a for a in activities if a["week"] == week["week"]]
    if not rows:
        rows = [{"type": kind, "distance_km": km}
                for kind, km in week.get("km_by_type", {}).items()]
    return score(rows)
