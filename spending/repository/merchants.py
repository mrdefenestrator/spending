from datetime import datetime, timezone

from sqlalchemy import Connection, insert, select, update

from spending.models import merchant_cache


def get_cached_category(conn: Connection, merchant_name: str) -> str | None:
    row = conn.execute(
        select(merchant_cache.c.category).where(
            merchant_cache.c.merchant_name == merchant_name
        )
    ).fetchone()
    return row[0] if row else None


def set_merchant_category(
    conn: Connection, merchant_name: str, category: str, *, source: str
) -> None:
    existing = conn.execute(
        select(merchant_cache.c.id).where(
            merchant_cache.c.merchant_name == merchant_name
        )
    ).fetchone()

    if existing:
        conn.execute(
            update(merchant_cache)
            .where(merchant_cache.c.merchant_name == merchant_name)
            .values(
                category=category,
                source=source,
                updated_at=datetime.now(timezone.utc),
            )
        )
    else:
        conn.execute(
            insert(merchant_cache).values(
                merchant_name=merchant_name, category=category, source=source
            )
        )
    conn.commit()


def get_uncached_merchants(conn: Connection, merchant_names: list[str]) -> list[str]:
    if not merchant_names:
        return []
    cached = conn.execute(
        select(merchant_cache.c.merchant_name).where(
            merchant_cache.c.merchant_name.in_(merchant_names)
        )
    ).fetchall()
    cached_set = {row[0] for row in cached}
    return [name for name in merchant_names if name not in cached_set]


def list_merchants(conn: Connection) -> list[dict]:
    rows = conn.execute(
        select(merchant_cache).order_by(merchant_cache.c.merchant_name)
    ).fetchall()
    return [dict(row._mapping) for row in rows]
