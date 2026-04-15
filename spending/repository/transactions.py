from calendar import monthrange
from datetime import date

from sqlalchemy import Connection, select

from spending.repository.aggregations import _base_query


def get_transactions(
    conn: Connection,
    *,
    year: int | None = None,
    month: int | None = None,
    category: str | None = None,
    account_id: int | None = None,
    search: str | None = None,
    status: str | None = None,
    import_id: int | None = None,
) -> list[dict]:
    """Get transactions with resolved category and merchant.

    Filters are optional and combine with AND.
    """
    from spending.models import transactions

    subq = _base_query()

    if year and month:
        start = date(year, month, 1)
        _, last_day = monthrange(year, month)
        end = date(year, month, last_day)
        subq = subq.where(
            transactions.c.date >= start,
            transactions.c.date <= end,
        )

    if account_id:
        subq = subq.where(transactions.c.account_id == account_id)

    if import_id:
        subq = subq.where(transactions.c.import_id == import_id)

    subq = subq.order_by(transactions.c.date.desc()).subquery()

    # Wrap in outer query to filter on resolved columns
    stmt = select(subq)

    if category:
        stmt = stmt.where(subq.c.category == category)

    if search:
        pattern = f"%{search}%"
        stmt = stmt.where(
            subq.c.raw_description.ilike(pattern) | subq.c.merchant.ilike(pattern)
        )

    if status == "corrected":
        stmt = stmt.where(subq.c.correction_id.isnot(None))
    elif status == "uncategorized":
        stmt = stmt.where(subq.c.category == "Uncategorized")
    elif status == "categorized":
        stmt = stmt.where(
            subq.c.category != "Uncategorized",
            subq.c.correction_id.is_(None),
        )

    rows = conn.execute(stmt).fetchall()
    return [dict(row._mapping) for row in rows]
