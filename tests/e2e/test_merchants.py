"""E2E tests for the Merchants tab."""

import pytest

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# Filter controls and table structure (empty database)
# ---------------------------------------------------------------------------


def test_merchants_search_input_present(page, flask_server):
    """Merchant search input is rendered."""
    page.goto(f"{flask_server}/merchants")
    assert page.locator("input[name='search']").is_visible()


def test_merchants_category_filter_present(page, flask_server):
    """Category dropdown filter is rendered."""
    page.goto(f"{flask_server}/merchants")
    assert page.locator("select[name='category']").is_visible()


def test_merchants_source_filter_present(page, flask_server):
    """Source dropdown filter (API / Manual) is rendered."""
    page.goto(f"{flask_server}/merchants")
    source_select = page.locator("select[name='source']")
    assert source_select.is_visible()
    options = source_select.locator("option").all_inner_texts()
    assert "API" in options
    assert "Manual" in options


def test_merchants_table_has_expected_columns(page, flask_server):
    """Merchants table renders all expected header columns."""
    page.goto(f"{flask_server}/merchants")
    header = page.locator("table thead tr")
    for col in ("Merchant", "Category", "Source", "Transactions", "Last Seen"):
        assert header.locator("th", has_text=col).is_visible(), f"Missing column: {col}"


def test_merchants_empty_db_has_no_data_rows(page, flask_server):
    """With no merchant cache entries the table body is empty."""
    page.goto(f"{flask_server}/merchants")
    assert page.locator("table tbody tr").count() == 0


# ---------------------------------------------------------------------------
# Data display and inline editing (confirmed_server)
#
# The classification API is disabled, so the merchant_cache starts empty
# even after import.  We exercise the full correction flow:
#   Transactions tab → click category → select + apply-to-merchant →
#   save → Merchants tab shows the new entry.
# ---------------------------------------------------------------------------


def test_merchants_empty_after_import_before_categorization(page, confirmed_server):
    """Merchants table is empty immediately after a confirmed import because
    the classification API is disabled and no corrections have been made yet."""
    page.goto(f"{confirmed_server}/merchants")
    assert page.locator("table tbody tr").count() == 0


def test_merchants_appear_after_transaction_correction(page, confirmed_server):
    """Correcting a transaction with 'apply to merchant' populates the Merchants tab.

    Flow:
      1. Go to Transactions (April 2026).
      2. Click the first 'Uncategorized' category cell.
      3. Select 'Groceries', check 'Apply to all from this merchant'.
      4. Save → HTMX redirects back to /transactions.
      5. Navigate to /merchants → the merchant now appears.
    """
    # Step 1: open Transactions for April 2026
    page.goto(f"{confirmed_server}/transactions?year=2026&month=4")
    page.wait_for_selector("table tbody tr")

    # Step 2: click the first category cell to open the inline edit form
    cat_cell = page.locator("table tbody tr td.text-blue-600").first
    with page.expect_response(lambda r: "edit-category" in r.url):
        cat_cell.click()
    page.wait_for_selector('tr[id^="edit-"]')

    # Step 3: select a category and check the apply-to-merchant checkbox
    edit_row = page.locator('tr[id^="edit-"]').first
    edit_row.locator("select[name='category']").select_option("Groceries")
    edit_row.locator("input[name='apply_to_merchant']").check()

    # Step 4: save and wait for the page to reload via HX-Redirect
    with page.expect_response(lambda r: r.status == 204):
        edit_row.locator("button[type='submit']").click()
    page.wait_for_url("**/transactions**")

    # Step 5: merchants tab now has one entry
    page.goto(f"{confirmed_server}/merchants")
    rows = page.locator("table tbody tr")
    assert rows.count() >= 1
    row_text = rows.first.inner_text()
    assert "Groceries" in row_text
    assert "manual" in row_text.lower()


def test_merchants_inline_edit_form_appears_on_category_click(page, confirmed_server):
    """Clicking a category cell in the Merchants table opens an inline edit form.

    Prerequisite: at least one merchant must be present.  We re-use whatever
    was created by earlier tests in this module (confirmed_server is shared).
    If none exist yet, the test navigates to create one first.
    """
    page.goto(f"{confirmed_server}/merchants")

    # Ensure there is at least one merchant row to click.
    if page.locator("table tbody tr").count() == 0:
        # Create one via the transaction correction flow
        page.goto(f"{confirmed_server}/transactions?year=2026&month=4")
        cat_cell = page.locator("table tbody tr td.text-blue-600").first
        with page.expect_response(lambda r: "edit-category" in r.url):
            cat_cell.click()
        page.wait_for_selector('tr[id^="edit-"]')
        edit_row = page.locator('tr[id^="edit-"]').first
        edit_row.locator("select[name='category']").select_option("Dining")
        edit_row.locator("input[name='apply_to_merchant']").check()
        with page.expect_response(lambda r: r.status == 204):
            edit_row.locator("button[type='submit']").click()
        page.wait_for_url("**/transactions**")
        page.goto(f"{confirmed_server}/merchants")

    # Click the category cell of the first merchant row
    cat_cell = page.locator("table tbody tr td.text-blue-600").first
    with page.expect_response(lambda r: "/edit" in r.url and "merchant" in r.url):
        cat_cell.click()
    # An inline edit row with a category select should appear
    page.wait_for_selector("table tbody tr.bg-blue-50")
    edit_row = page.locator("table tbody tr.bg-blue-50")
    assert edit_row.locator("select[name='category']").is_visible()
    assert edit_row.locator("button", has_text="Save").is_visible()
    assert edit_row.locator("button", has_text="Cancel").is_visible()


def test_merchants_search_filters_results(page, confirmed_server):
    """Typing in the search box filters merchants by name."""
    page.goto(f"{confirmed_server}/merchants")
    # If the table is empty, first ensure at least one merchant exists
    if page.locator("table tbody tr").count() == 0:
        pytest.skip(
            "No merchants present — run after test_merchants_appear_after_transaction_correction"
        )

    total_before = page.locator("table tbody tr").count()

    # Search for a string that matches nothing → table should be empty
    search = page.locator("input[name='search']")
    search.fill("XYZZY_NO_MATCH_9999")
    page.wait_for_response(lambda r: "/merchants" in r.url and r.status == 200)
    assert page.locator("table tbody tr").count() == 0

    # Clear the search → all rows return
    search.fill("")
    page.wait_for_response(lambda r: "/merchants" in r.url and r.status == 200)
    assert page.locator("table tbody tr").count() == total_before
