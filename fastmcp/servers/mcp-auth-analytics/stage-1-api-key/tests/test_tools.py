import pytest
from analytics_mcp import db, tools

from fastmcp.exceptions import ToolError


def test_row_counts(warehouse):
    with db.read_connection() as con:
        counts = {
            t: con.execute(f"SELECT count(*) FROM {t}").fetchone()[0]
            for t in ("accounts", "users", "events", "invoices")
        }
    assert counts == {
        "accounts": 500,
        "users": 5000,
        "events": 200000,
        "invoices": 6000,
    }


def test_metrics_are_aggregates(warehouse):
    rows = tools.get_metric("dau", "2025-03-01", "2025-03-07")
    assert rows and set(rows[0]) == {"day", "value"}
    assert tools.get_metric("signups", "2025-03-01", "2025-03-07", region="EU")


def test_date_range_cap(warehouse):
    with pytest.raises(ToolError, match="capped"):
        tools.top_events("2024-01-01", "2025-12-31")


def test_read_connection_rejects_writes(warehouse):
    with db.read_connection() as con, pytest.raises(Exception, match="read-only"):
        con.execute("DELETE FROM events")


def test_export_is_capped(warehouse):
    assert len(tools.export_user_events(1)) <= tools.MAX_EXPORT_ROWS


def test_delete_user_removes_user_and_events(warehouse):
    result = tools.delete_user(7)
    assert result["users_deleted"] == 1
    assert tools.export_user_events(7) == []


def test_parameterized_sql(warehouse):
    with pytest.raises(Exception):
        tools.lookup_account("1; DROP TABLE users")  # type: ignore[arg-type]


def test_revenue_accepts_months(warehouse):
    by_month = tools.get_revenue("2025-01", "2025-03")
    assert by_month == tools.get_revenue("2025-01-01", "2025-03-31")
    assert by_month and {r["month"] for r in by_month} <= {
        "2025-01",
        "2025-02",
        "2025-03",
    }
    with pytest.raises(ToolError, match="YYYY-MM-DD"):
        tools.get_revenue("2025-13", "2025-14")
