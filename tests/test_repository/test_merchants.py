from spending.repository.merchants import (
    get_cached_category,
    get_uncached_merchants,
    list_merchants,
    set_merchant_category,
)


def test_set_and_get_cached_category(conn):
    set_merchant_category(conn, "WHOLE FOODS", "Groceries", source="api")
    assert get_cached_category(conn, "WHOLE FOODS") == "Groceries"


def test_get_cached_category_miss(conn):
    assert get_cached_category(conn, "UNKNOWN") is None


def test_get_uncached_merchants(conn):
    set_merchant_category(conn, "WHOLE FOODS", "Groceries", source="api")
    uncached = get_uncached_merchants(conn, ["WHOLE FOODS", "NETFLIX", "TARGET"])
    assert set(uncached) == {"NETFLIX", "TARGET"}


def test_set_merchant_category_updates_existing(conn):
    set_merchant_category(conn, "WHOLE FOODS", "Groceries", source="api")
    set_merchant_category(conn, "WHOLE FOODS", "Shopping", source="manual")
    assert get_cached_category(conn, "WHOLE FOODS") == "Shopping"


def test_list_merchants(conn):
    set_merchant_category(conn, "WHOLE FOODS", "Groceries", source="api")
    set_merchant_category(conn, "NETFLIX", "Subscriptions", source="manual")
    merchants = list_merchants(conn)
    assert len(merchants) == 2
    names = {m["merchant_name"] for m in merchants}
    assert names == {"WHOLE FOODS", "NETFLIX"}
