from datetime import datetime, timedelta
from pathlib import Path

from itsm_kpi.cli import main
from itsm_kpi.metrics import Incident, load, summarize, to_markdown

AS_OF = datetime(2026, 11, 20)
DATA = Path(__file__).resolve().parents[1] / "data" / "sample_incidents.csv"


def inc(n, pr, opened, hours=None, state="6", reassign=0, group="SD"):
    o = datetime(2026, 11, opened)
    return Incident(n, pr, state, o, o + timedelta(hours=hours) if hours is not None else None, group, reassign)


def test_mttr_breach_and_fcr():
    s = summarize([inc("a", "1", 1, 2), inc("b", "1", 1, 6, reassign=1), inc("c", "3", 2, 10)], AS_OF)
    assert s["mttr_hours"] == 6.0
    assert s["by_priority"]["1"]["breach_pct"] == 50.0
    assert s["sla_breach_pct"] == 33.3
    assert s["no_reassignment_pct"] == 66.7


def test_backlog_aging_buckets():
    s = summarize([inc("a", "3", 19, state="2"), inc("b", "3", 15, state="2"), inc("c", "3", 1, state="2")], AS_OF)
    assert s["open"] == 3
    assert s["backlog_aging"] == {"0-2d": 1, "3-7d": 1, "8-30d": 1, ">30d": 0}


def test_empty_input_is_safe():
    s = summarize([], AS_OF)
    assert s["mttr_hours"] == 0.0 and s["sla_breach_pct"] == 0.0


def test_sample_file_and_markdown():
    s = summarize(load(DATA), AS_OF)
    assert s["total"] == 600
    md = to_markdown(s)
    assert "SLA breach rate" in md and "| P1 |" in md


def test_malformed_rows_skipped(tmp_path):
    f = tmp_path / "x.csv"
    f.write_text("number,priority,state,opened_at,resolved_at\nINC1,3,6,bad-date,\nINC2,3,2,2026-11-01 10:00:00,\n")
    assert len(load(f)) == 1


def test_cli(tmp_path):
    out = tmp_path / "r.md"
    assert main([str(DATA), "--as-of", "2026-11-20", "--out", str(out)]) == 0
    assert out.read_text().startswith("# ITSM KPI Report")
    assert main(["missing.csv"]) == 2
