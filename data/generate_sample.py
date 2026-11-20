"""Generates a synthetic incident export (no real data)."""
import csv
import random
from datetime import datetime, timedelta
from pathlib import Path

random.seed(7)
groups = ["Service Desk", "Network Ops", "Database Admin", "App Support", "End User Computing"]
start = datetime(2026, 9, 1)
rows = []
for n in range(1, 601):
    pr = random.choices(["1", "2", "3", "4"], weights=[3, 12, 55, 30])[0]
    opened = start + timedelta(minutes=random.randint(0, 80 * 24 * 60))
    target = {"1": 4, "2": 8, "3": 24, "4": 72}[pr]
    hours = random.lognormvariate(0, 0.7) * target * 0.6
    resolved = opened + timedelta(hours=hours)
    is_open = resolved > datetime(2026, 11, 20) or random.random() < 0.05
    rows.append({"number": f"INC{n:07d}", "priority": pr, "state": "2" if is_open else random.choice(["6", "7"]),
                 "opened_at": opened.strftime("%Y-%m-%d %H:%M:%S"),
                 "resolved_at": "" if is_open else resolved.strftime("%Y-%m-%d %H:%M:%S"),
                 "assignment_group": random.choice(groups),
                 "reassignment_count": random.choices([0, 1, 2, 3], weights=[60, 25, 10, 5])[0]})
with open(Path(__file__).parent / "sample_incidents.csv", "w", newline="", encoding="utf-8") as fh:
    w = csv.DictWriter(fh, fieldnames=list(rows[0]))
    w.writeheader()
    w.writerows(rows)
print(f"wrote {len(rows)} incidents")
