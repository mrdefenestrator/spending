from sqlalchemy import Connection, delete, insert, select

from spending.models import accounts


def add_account(
    conn: Connection, *, name: str, institution: str, account_type: str
) -> int:
    result = conn.execute(
        insert(accounts).values(
            name=name, institution=institution, account_type=account_type
        )
    )
    conn.commit()
    return result.inserted_primary_key[0]


def list_accounts(conn: Connection) -> list[dict]:
    rows = conn.execute(select(accounts).order_by(accounts.c.name)).fetchall()
    return [dict(row._mapping) for row in rows]


def get_account_by_name(conn: Connection, name: str) -> dict | None:
    row = conn.execute(select(accounts).where(accounts.c.name == name)).fetchone()
    return dict(row._mapping) if row else None


def get_account_by_id(conn: Connection, account_id: int) -> dict | None:
    row = conn.execute(select(accounts).where(accounts.c.id == account_id)).fetchone()
    return dict(row._mapping) if row else None


def edit_account(
    conn: Connection,
    account_id: int,
    *,
    name: str | None = None,
    institution: str | None = None,
    account_type: str | None = None,
) -> None:
    values = {}
    if name is not None:
        values["name"] = name
    if institution is not None:
        values["institution"] = institution
    if account_type is not None:
        values["account_type"] = account_type
    if values:
        conn.execute(
            accounts.update().where(accounts.c.id == account_id).values(**values)
        )
        conn.commit()


def delete_account(conn: Connection, account_id: int) -> None:
    conn.execute(delete(accounts).where(accounts.c.id == account_id))
    conn.commit()
