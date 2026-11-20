"""python -m itsm_kpi.cli data/sample_incidents.csv --as-of 2026-11-20 --out report.md"""
from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime

from .metrics import load, summarize, to_markdown


def main(argv=None) -> int:
    p = argparse.ArgumentParser(description="ITSM KPIs from a ServiceNow incident export")
    p.add_argument("csv")
    p.add_argument("--as-of", help="YYYY-MM-DD used for backlog aging (default: now)")
    p.add_argument("--out", help="write a Markdown report here")
    p.add_argument("--json", action="store_true", help="print JSON instead of Markdown")
    a = p.parse_args(argv)
    try:
        incidents = load(a.csv)
    except OSError as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    as_of = datetime.strptime(a.as_of, "%Y-%m-%d") if a.as_of else datetime.now()
    s = summarize(incidents, as_of)
    text = json.dumps(s, indent=2) if a.json else to_markdown(s)
    if a.out:
        with open(a.out, "w", encoding="utf-8") as fh:
            fh.write(text)
    print(text)
    return 0


if __name__ == "__main__":
    sys.exit(main())
