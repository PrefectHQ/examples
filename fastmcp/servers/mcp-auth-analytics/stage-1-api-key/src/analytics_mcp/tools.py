"""The eight tools. No auth logic in here, on purpose.

This file is identical in every stage. Who may call what is decided in
``server.py`` and ``auth.py``, so ``git diff stage-1-api-key stage-3-authz``
shows only the security change.
"""

import calendar
from datetime import date
from typing import Literal

from fastmcp.exceptions import ToolError
from fastmcp.server.dependencies import get_access_token

from . import db

MAX_DAYS = 366
MAX_EXPORT_ROWS = 500


def _range(start: str, end: str) -> tuple[date, date]:
    try:
        s, e = date.fromisoformat(start), date.fromisoformat(end)
    except ValueError as exc:
        raise ToolError(f"Dates must be YYYY-MM-DD: {exc}") from exc
    if e < s:
        raise ToolError("end must not be before start")
    if (e - s).days > MAX_DAYS:
        raise ToolError(f"Date range is capped at {MAX_DAYS} days")
    return s, e


def _rows(sql: str, params: list) -> list[dict]:
    with db.read_connection() as con:
        cur = con.execute(sql, params)
        cols = [d[0] for d in cur.description]
        return [dict(zip(cols, r)) for r in cur.fetchall()]


METRICS = {
    "dau": "Daily active users: distinct users with any event on a day",
    "signups": "New users created per day",
    "retention": "Share of users active 7 days after creation, by signup day",
}


def list_metrics() -> list[dict]:
    """List the metric definitions this server knows."""
    return [{"metric": k, "definition": v} for k, v in METRICS.items()]


def get_metric(
    metric: Literal["dau", "signups", "retention"],
    start: str,
    end: str,
    region: Literal["NA", "EU", "APAC"] | None = None,
) -> list[dict]:
    """Daily aggregate for a metric over a date range, optionally for one region."""
    s, e = _range(start, end)
    region_sql = "AND a.region = ?" if region else ""
    extra = [region] if region else []
    if metric == "dau":
        sql = f"""SELECT CAST(ev.occurred_at AS DATE) AS day, count(DISTINCT ev.user_id) AS value
                  FROM events ev JOIN users u USING (user_id) JOIN accounts a USING (account_id)
                  WHERE CAST(ev.occurred_at AS DATE) BETWEEN ? AND ? {region_sql}
                  GROUP BY 1 ORDER BY 1"""
    elif metric == "signups":
        sql = f"""SELECT CAST(u.created_at AS DATE) AS day, count(*) AS value
                  FROM users u JOIN accounts a USING (account_id)
                  WHERE CAST(u.created_at AS DATE) BETWEEN ? AND ? {region_sql}
                  GROUP BY 1 ORDER BY 1"""
    else:
        sql = f"""SELECT CAST(u.created_at AS DATE) AS day,
                         round(avg(CASE WHEN EXISTS (
                             SELECT 1 FROM events ev WHERE ev.user_id = u.user_id
                               AND CAST(ev.occurred_at AS DATE) = CAST(u.created_at AS DATE) + 7
                         ) THEN 1.0 ELSE 0.0 END), 3) AS value
                  FROM users u JOIN accounts a USING (account_id)
                  WHERE CAST(u.created_at AS DATE) BETWEEN ? AND ? {region_sql}
                  GROUP BY 1 ORDER BY 1"""
    return _rows(sql, [s, e, *extra])


def top_events(start: str, end: str, limit: int = 10) -> list[dict]:
    """Top events by count for a date range."""
    s, e = _range(start, end)
    limit = max(1, min(limit, 50))
    return _rows(
        """SELECT event_name, count(*) AS events FROM events
           WHERE CAST(occurred_at AS DATE) BETWEEN ? AND ?
           GROUP BY 1 ORDER BY 2 DESC LIMIT ?""",
        [s, e, limit],
    )


def _month(value: str, end: bool) -> str:
    """Turn YYYY-MM into the first (or last) day of that month; leave dates alone."""
    if len(value) == 7 and value[4] == "-":
        try:
            y, m = int(value[:4]), int(value[5:])
            return date(y, m, calendar.monthrange(y, m)[1] if end else 1).isoformat()
        except ValueError:
            pass  # _range reports the bad value
    return value


def get_revenue(start_month: str, end_month: str) -> list[dict]:
    """Paid revenue by plan and month. MRR is the paid amount in that month.

    Months are YYYY-MM (2025-01) and both ends are inclusive; full YYYY-MM-DD dates also work.
    """
    s, e = _range(_month(start_month, end=False), _month(end_month, end=True))
    return _rows(
        """SELECT strftime(date_trunc('month', i.issued_at), '%Y-%m') AS month, a.plan,
                  CAST(sum(i.amount_usd) AS DOUBLE) AS revenue_usd, count(*) AS invoices
           FROM invoices i JOIN accounts a USING (account_id)
           WHERE i.status = 'paid' AND i.issued_at BETWEEN ? AND ?
           GROUP BY 1, 2 ORDER BY 1, 2""",
        [s, e],
    )


def lookup_account(account_id: int) -> dict:
    """Account details plus its users with emails (PII)."""
    acct = _rows("SELECT * FROM accounts WHERE account_id = ?", [account_id])
    if not acct:
        raise ToolError(f"No account {account_id}")
    users = _rows(
        "SELECT user_id, email, full_name FROM users WHERE account_id = ? ORDER BY user_id",
        [account_id],
    )
    return {"account": acct[0], "users": users}


def export_user_events(user_id: int) -> list[dict]:
    """Raw events for one user, newest first, capped at 500 rows."""
    return _rows(
        "SELECT event_id, event_name, occurred_at, properties FROM events "
        "WHERE user_id = ? ORDER BY occurred_at DESC LIMIT ?",
        [user_id, MAX_EXPORT_ROWS],
    )


def delete_user(user_id: int) -> dict:
    """Delete a user and their events (a GDPR-style request). The only write."""
    with db.write_connection() as con:
        events = con.execute(
            "DELETE FROM events WHERE user_id = ? RETURNING 1", [user_id]
        ).fetchall()
        users = con.execute(
            "DELETE FROM users WHERE user_id = ? RETURNING 1", [user_id]
        ).fetchall()
    return {
        "user_id": user_id,
        "users_deleted": len(users),
        "events_deleted": len(events),
    }


def whoami() -> dict:
    """Who the server thinks is calling: identity, scopes and roles as it sees them."""
    token = get_access_token()
    if token is None:
        return {"authenticated": False}
    claims = token.claims or {}
    return {
        "authenticated": True,
        "client_id": token.client_id,
        "sub": claims.get("sub"),
        "username": claims.get("preferred_username"),
        "scopes": list(token.scopes or []),
        "roles": (claims.get("realm_access") or {}).get("roles", []),
    }
