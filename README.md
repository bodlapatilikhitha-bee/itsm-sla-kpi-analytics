# ITSM SLA & KPI Analytics

Turns a ServiceNow incident export into the service desk KPIs that managers ask for: MTTR, SLA breach rate by priority, resolution without reassignment, repeat reassignment, backlog aging and MTTR by assignment group. Outputs a Markdown report or JSON.

> **Portfolio project.** Written from scratch for this repository. The 600 sample incidents are synthetic (`data/generate_sample.py`); SLA targets are illustrative. No employer or client data is included.

## Why

ServiceNow reports and Performance Analytics answer these questions inside the platform. This tool is for the cases where you need the same numbers outside it: checking a data extract, comparing periods, or validating that a dashboard is calculating correctly.

## Quick start

```bash
pip install -r requirements-dev.txt   # pytest only; the tool uses the standard library
python -m itsm_kpi.cli data/sample_incidents.csv --as-of 2026-11-20 --out report.md
python -m itsm_kpi.cli data/sample_incidents.csv --as-of 2026-11-20 --json
```

Excerpt from `sample_report.md` (synthetic data):

| Metric | Value |
|---|---|
| Incidents | 600 |
| MTTR (mean) | 28.0 h |
| Time to resolve (median) | 18.7 h |
| SLA breach rate | 23.2% |
| Resolved without reassignment | 59.4% |
| Reassigned 2+ times | 17.2% |

## Input format

Export `incident.list` as CSV with these columns (use `sys_choice` values for priority and state):

`number, priority, state, opened_at, resolved_at, assignment_group, reassignment_count`

Dates use `YYYY-MM-DD HH:MM:SS`. States 6 (Resolved) and 7 (Closed) count as resolved. Malformed rows are skipped with a warning.

## KPI definitions

| KPI | Definition |
|---|---|
| MTTR | Mean hours from `opened_at` to `resolved_at` for resolved incidents |
| SLA breach rate | Resolved incidents whose time to resolve exceeds the priority target (P1 4h, P2 8h, P3 24h, P4 72h, P5 120h) |
| Resolved without reassignment | Resolved incidents with `reassignment_count = 0` |
| Reassigned 2+ times | Share of all incidents bounced between groups two or more times |
| Backlog aging | Open incidents bucketed by age at the `--as-of` date |

Note: this uses simple calendar-hour targets. ServiceNow Task SLAs use schedules and pause conditions, so results will differ from `task_sla` data.

## Tests

```bash
python -m pytest -q
```

## Limitations and next steps

- Calendar hours only; no business-hours schedules.
- Next: read `task_sla` records for exact breach data, and add trend charts by week.

## License

MIT — see `LICENSE`.
