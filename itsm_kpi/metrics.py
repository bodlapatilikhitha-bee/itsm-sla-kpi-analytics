"""Calculates service desk KPIs from a ServiceNow incident CSV export.

KPIs: volume, MTTR (mean time to resolve), SLA breach rate by priority,
resolution without reassignment, repeat reassignment, and backlog aging. Written for
this portfolio on synthetic data.
"""
from __future__ import annotations

import csv
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime
from statistics import mean, median

FMT = "%Y-%m-%d %H:%M:%S"
# Resolution targets in hours, by priority (illustrative values).
SLA_HOURS = {"1": 4, "2": 8, "3": 24, "4": 72, "5": 120}
RESOLVED_STATES = {"6", "7"}  # Resolved, Closed


@dataclass
class Incident:
    number: str
    priority: str
    state: str
    opened_at: datetime
    resolved_at: datetime | None
    assignment_group: str
    reassignment_count: int

    @property
    def hours_to_resolve(self) -> float | None:
        if not self.resolved_at:
            return None
        return (self.resolved_at - self.opened_at).total_seconds() / 3600


def _dt(value: str) -> datetime | None:
    value = (value or "").strip()
    return datetime.strptime(value, FMT) if value else None


def load(path) -> list[Incident]:
    rows, bad = [], 0
    with open(path, newline="", encoding="utf-8") as fh:
        for r in csv.DictReader(fh):
            try:
                rows.append(Incident(r["number"], r["priority"], r["state"], _dt(r["opened_at"]),
                                     _dt(r.get("resolved_at", "")), r.get("assignment_group", ""),
                                     int(r.get("reassignment_count") or 0)))
            except (KeyError, ValueError, TypeError):
                bad += 1
    if bad:
        print(f"warning: skipped {bad} malformed rows")
    return rows


def summarize(incidents: list[Incident], as_of: datetime) -> dict:
    resolved = [i for i in incidents if i.state in RESOLVED_STATES and i.resolved_at]
    open_ = [i for i in incidents if i.state not in RESOLVED_STATES]
    hours = [i.hours_to_resolve for i in resolved]

    by_p = defaultdict(lambda: {"resolved": 0, "breached": 0, "hours": []})
    for i in resolved:
        p = by_p[i.priority]
        p["resolved"] += 1
        p["hours"].append(i.hours_to_resolve)
        if i.hours_to_resolve > SLA_HOURS.get(i.priority, 120):
            p["breached"] += 1

    aging = Counter()
    for i in open_:
        days = (as_of - i.opened_at).days
        aging["0-2d" if days <= 2 else "3-7d" if days <= 7 else "8-30d" if days <= 30 else ">30d"] += 1

    group_mttr = defaultdict(list)
    for i in resolved:
        group_mttr[i.assignment_group].append(i.hours_to_resolve)

    def pct(a, b):
        return round(100 * a / b, 1) if b else 0.0

    return {
        "total": len(incidents),
        "resolved": len(resolved),
        "open": len(open_),
        "mttr_hours": round(mean(hours), 1) if hours else 0.0,
        "median_ttr_hours": round(median(hours), 1) if hours else 0.0,
        "sla_breach_pct": pct(sum(p["breached"] for p in by_p.values()), len(resolved)),
        "no_reassignment_pct": pct(sum(1 for i in resolved if i.reassignment_count == 0), len(resolved)),
        "reassigned_2plus_pct": pct(sum(1 for i in incidents if i.reassignment_count >= 2), len(incidents)),
        "by_priority": {k: {"resolved": v["resolved"], "breach_pct": pct(v["breached"], v["resolved"]),
                            "mttr_hours": round(mean(v["hours"]), 1)} for k, v in sorted(by_p.items())},
        "backlog_aging": {k: aging.get(k, 0) for k in ("0-2d", "3-7d", "8-30d", ">30d")},
        "mttr_by_group": {g: round(mean(h), 1) for g, h in sorted(group_mttr.items())},
    }


def to_markdown(s: dict, title: str = "ITSM KPI Report") -> str:
    lines = [f"# {title}", "",
             f"| Metric | Value |", "|---|---|",
             f"| Incidents | {s['total']} |", f"| Resolved | {s['resolved']} |", f"| Open backlog | {s['open']} |",
             f"| MTTR (mean) | {s['mttr_hours']} h |", f"| Time to resolve (median) | {s['median_ttr_hours']} h |",
             f"| SLA breach rate | {s['sla_breach_pct']}% |",
             f"| Resolved without reassignment | {s['no_reassignment_pct']}% |",
             f"| Reassigned 2+ times | {s['reassigned_2plus_pct']}% |", "",
             "## By priority", "", "| Priority | Resolved | Breach % | MTTR (h) |", "|---|---|---|---|"]
    lines += [f"| P{p} | {v['resolved']} | {v['breach_pct']}% | {v['mttr_hours']} |" for p, v in s["by_priority"].items()]
    lines += ["", "## Backlog aging", "", "| Age | Open incidents |", "|---|---|"]
    lines += [f"| {k} | {v} |" for k, v in s["backlog_aging"].items()]
    lines += ["", "## MTTR by assignment group", "", "| Group | MTTR (h) |", "|---|---|"]
    lines += [f"| {g} | {h} |" for g, h in s["mttr_by_group"].items()]
    return "\n".join(lines) + "\n"
