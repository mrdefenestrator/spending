"""E2E tests for the Monthly tab."""

import pytest

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Structure and navigation (empty database)
# ---------------------------------------------------------------------------


def test_monthly_table_has_expected_columns(page, flask_server):
    """Monthly table renders all five header columns."""
    page.goto(f"{flask_server}/monthly")
    header = page.locator("table thead tr")
    assert header.locator("th", has_text="Category").is_visible()
    assert header.locator("th", has_text="Count").is_visible()
    assert header.locator("th", has_text="Total").is_visible()
    assert header.locator("th", has_text="3-Mo Avg").is_visible()
    assert header.locator("th", has_text="vs Avg").is_visible()


def test_monthly_shows_grand_total_footer(page, flask_server):
    """Monthly table always has a grand total row in tfoot."""
    page.goto(f"{flask_server}/monthly")
    assert page.locator("table tfoot").get_by_text("Total").is_visible()


def test_monthly_shows_current_month_label(page, flask_server):
    """Month/year label is rendered in the heading area (MM/YYYY format)."""
    page.goto(f"{flask_server}/monthly")
    # Matches e.g. "04/2026"
    assert page.locator("text=/\\d{2}\\/\\d{4}/").first.is_visible()


def test_monthly_prev_arrow_navigates_to_prior_month(page, flask_server):
    """Clicking ← decrements the month and updates the URL."""
    page.goto(f"{flask_server}/monthly?year=2026&month=4")
    page.click("a:has-text('←')")
    page.wait_for_url("**/monthly**month=3**")


def test_monthly_next_arrow_navigates_to_next_month(page, flask_server):
    """Clicking → increments the month and updates the URL."""
    page.goto(f"{flask_server}/monthly?year=2026&month=4")
    page.click("a:has-text('→')")
    page.wait_for_url("**/monthly**month=5**")


def test_monthly_prev_arrow_wraps_year_boundary(page, flask_server):
    """Clicking ← on January navigates to December of the prior year."""
    page.goto(f"{flask_server}/monthly?year=2026&month=1")
    page.click("a:has-text('←')")
    page.wait_for_url("**/monthly**year=2025**month=12**")


# ---------------------------------------------------------------------------
# Data display (confirmed_server has 4 transactions in 04/2026)
# ---------------------------------------------------------------------------


def test_monthly_shows_category_rows_with_data(page, confirmed_server):
    """After import is confirmed, at least one category row is visible."""
    page.goto(f"{confirmed_server}/monthly?year=2026&month=4")
    # Transactions are Uncategorized because the classification API is disabled
    assert page.locator("tbody tr td", has_text="Uncategorized").first.is_visible()


def test_monthly_category_row_shows_correct_count(page, confirmed_server):
    """The transaction count cell reflects all 4 seeded transactions."""
    page.goto(f"{confirmed_server}/monthly?year=2026&month=4")
    # Find the Uncategorized row and check its Count cell
    row = page.locator("tbody tr", has=page.locator("td", has_text="Uncategorized")).first
    count_cell = row.locator("td").nth(1)
    assert count_cell.inner_text().strip() == "4"


def test_monthly_grand_total_reflects_seeded_data(page, confirmed_server):
    """Grand total in tfoot shows the sum of all seeded transactions ($132.24)."""
    page.goto(f"{confirmed_server}/monthly?year=2026&month=4")
    tfoot = page.locator("table tfoot")
    assert "132.24" in tfoot.inner_text()


def test_monthly_drilldown_expands_on_click(page, confirmed_server):
    """Clicking a category row expands a nested transaction table via HTMX."""
    page.goto(f"{confirmed_server}/monthly?year=2026&month=4")
    row = page.locator("tbody tr", has=page.locator("td", has_text="Uncategorized")).first
    with page.expect_response(lambda r: "drilldown" in r.url):
        row.click()
    # A nested table should now be visible inside the drilldown row
    page.wait_for_selector("tbody tr + tr table")


def test_monthly_drilldown_contains_transaction_rows(page, confirmed_server):
    """The drilldown table shows individual transaction rows."""
    page.goto(f"{confirmed_server}/monthly?year=2026&month=4")
    row = page.locator("tbody tr", has=page.locator("td", has_text="Uncategorized")).first
    with page.expect_response(lambda r: "drilldown" in r.url):
        row.click()
    nested = page.locator("tbody tr + tr table tbody tr")
    assert nested.count() == 4


def test_monthly_drilldown_shows_merchant_names(page, confirmed_server):
    """Drilldown rows include merchant names from the imported transactions."""
    page.goto(f"{confirmed_server}/monthly?year=2026&month=4")
    row = page.locator("tbody tr", has=page.locator("td", has_text="Uncategorized")).first
    with page.expect_response(lambda r: "drilldown" in r.url):
        row.click()
    page.wait_for_selector("tbody tr + tr table")
    nested_text = page.locator("tbody tr + tr table").inner_text()
    assert "WHOLE FOODS" in nested_text or "CHIPOTLE" in nested_text


def test_monthly_empty_month_shows_zero_total(page, confirmed_server):
    """A month with no transactions shows $0.00 as the grand total."""
    page.goto(f"{confirmed_server}/monthly?year=2026&month=1")
    tfoot = page.locator("table tfoot")
    assert "0.00" in tfoot.inner_text()
