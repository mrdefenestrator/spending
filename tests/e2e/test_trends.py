"""E2E tests for the Trends tab."""

import pytest

pytestmark = pytest.mark.e2e

_PERIODS = [
    ("quarterly", "Quarterly"),
    ("ytd", "Year to Date"),
    ("trailing12", "Trailing 12 Mo"),
    ("annual", "Last Year"),
]


# ---------------------------------------------------------------------------
# Period selector (empty database)
# ---------------------------------------------------------------------------


def test_trends_all_period_buttons_visible(page, flask_server):
    """All four preset period buttons are rendered."""
    page.goto(f"{flask_server}/trends")
    for _, label in _PERIODS:
        assert page.locator(f"a:has-text('{label}')").is_visible(), f"Missing: {label}"


def test_trends_ytd_is_active_by_default(page, flask_server):
    """'Year to Date' button has active (blue) styling on initial load."""
    page.goto(f"{flask_server}/trends")
    ytd_btn = page.locator("a:has-text('Year to Date')")
    classes = ytd_btn.get_attribute("class")
    assert "bg-blue-500" in classes


def test_trends_inactive_period_buttons_not_highlighted(page, flask_server):
    """Non-active period buttons do not carry the blue active class."""
    page.goto(f"{flask_server}/trends")
    for period, label in _PERIODS:
        if period == "ytd":
            continue
        btn = page.locator(f"a:has-text('{label}')")
        classes = btn.get_attribute("class") or ""
        assert "bg-blue-500" not in classes, f"Button '{label}' should not be active"


def test_trends_click_quarterly_updates_active_button(page, flask_server):
    """Clicking 'Quarterly' makes it the active button and updates the URL."""
    page.goto(f"{flask_server}/trends")
    page.click("a:has-text('Quarterly')")
    page.wait_for_url("**/trends**period=quarterly**")
    quarterly_btn = page.locator("a:has-text('Quarterly')")
    assert "bg-blue-500" in (quarterly_btn.get_attribute("class") or "")


def test_trends_click_trailing12_updates_url(page, flask_server):
    """Clicking 'Trailing 12 Mo' updates the URL to period=trailing12."""
    page.goto(f"{flask_server}/trends")
    page.click("a:has-text('Trailing 12 Mo')")
    page.wait_for_url("**/trends**period=trailing12**")


def test_trends_click_annual_updates_url(page, flask_server):
    """Clicking 'Last Year' updates the URL to period=annual."""
    page.goto(f"{flask_server}/trends")
    page.click("a:has-text('Last Year')")
    page.wait_for_url("**/trends**period=annual**")


# ---------------------------------------------------------------------------
# Table structure (empty database)
# ---------------------------------------------------------------------------


def test_trends_table_has_expected_columns(page, flask_server):
    """Trends table renders Category, Total, Monthly Avg, and Trend columns."""
    page.goto(f"{flask_server}/trends")
    header = page.locator("table thead tr")
    for col in ("Category", "Total", "Monthly Avg", "Trend"):
        assert header.locator("th", has_text=col).is_visible(), f"Missing column: {col}"


def test_trends_table_has_grand_total_footer(page, flask_server):
    """Trends table always has a Total row in tfoot."""
    page.goto(f"{flask_server}/trends")
    assert page.locator("table tfoot").get_by_text("Total").is_visible()


# ---------------------------------------------------------------------------
# Data display (confirmed_server has 4 transactions in 04/2026)
# ---------------------------------------------------------------------------


def test_trends_ytd_shows_data_rows(page, confirmed_server):
    """YTD view shows at least one category row when data exists."""
    page.goto(f"{confirmed_server}/trends?period=ytd")
    rows = page.locator("table tbody tr")
    assert rows.count() >= 1


def test_trends_ytd_grand_total_matches_seeded_data(page, confirmed_server):
    """YTD grand total reflects the $132.24 seeded in 04/2026."""
    page.goto(f"{confirmed_server}/trends?period=ytd")
    tfoot = page.locator("table tfoot")
    assert "132.24" in tfoot.inner_text()


def test_trends_quarterly_shows_data_rows(page, confirmed_server):
    """Quarterly view shows data rows when transactions exist in the quarter."""
    page.goto(f"{confirmed_server}/trends?period=quarterly")
    rows = page.locator("table tbody tr")
    assert rows.count() >= 1


def test_trends_row_has_sparkline_svg(page, confirmed_server):
    """Each data row in the trends table contains an inline SVG sparkline."""
    page.goto(f"{confirmed_server}/trends?period=ytd")
    first_row = page.locator("table tbody tr").first
    assert first_row.locator("svg").is_visible()
