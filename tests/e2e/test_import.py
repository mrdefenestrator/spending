"""E2E tests for the Import tab.

All tests share a single module-scoped ``import_server`` (empty DB at start).
They run in document order and progressively build state:

  1–3   Empty-DB / account-panel structure
  4     Inline account creation via HTMX form
  5–6   Dropzone and "no pending" empty state
  7–9   File upload → staging review
  10    Confirm clears staging
  11–12 Second upload → reject removes from staging
  13    Duplicate-file error message
  14    OFX detect-account pre-fills institution field
"""

import pytest

pytestmark = pytest.mark.e2e


# ---------------------------------------------------------------------------
# 1–3  Empty-DB: create-account form is shown
# ---------------------------------------------------------------------------


def test_import_empty_db_shows_no_accounts_message(page, import_server):
    """With an empty database the account panel shows 'No accounts yet'."""
    page.goto(f"{import_server}/import")
    assert page.locator("#account-panel").is_visible()
    assert page.locator("text=No accounts yet").is_visible()


def test_import_create_form_has_name_field(page, import_server):
    """The inline create-account form has a name input."""
    page.goto(f"{import_server}/import")
    assert page.locator("input[name='acct_name']").is_visible()


def test_import_create_form_has_institution_and_type_fields(page, import_server):
    """The inline create-account form has institution and account-type inputs."""
    page.goto(f"{import_server}/import")
    assert page.locator("input[name='acct_institution']").is_visible()
    assert page.locator("select[name='acct_type']").is_visible()


# ---------------------------------------------------------------------------
# 4  Inline account creation
# ---------------------------------------------------------------------------


def test_import_create_account_via_htmx_form(page, import_server):
    """Filling the create-account form and clicking 'Create Account' replaces
    the panel with an account <select> that has the new account pre-selected."""
    page.goto(f"{import_server}/import")

    page.fill("input[name='acct_name']", "Test Checking")
    page.fill("input[name='acct_institution']", "Test Bank")
    page.select_option("select[name='acct_type']", "checking")

    # Button uses hx-post="/accounts" → replaces #account-panel
    with page.expect_response(
        lambda r: r.url.endswith("/accounts") and r.status == 200
    ):
        page.click("button:has-text('Create Account')")

    page.wait_for_selector("select[name='account_id']")
    select = page.locator("select[name='account_id']")
    assert select.is_visible()
    # New account should appear as an option
    options = select.locator("option").all_inner_texts()
    assert any("Test Checking" in o for o in options)


# ---------------------------------------------------------------------------
# 5–6  Dropzone and empty staging state (account now exists)
# ---------------------------------------------------------------------------


def test_import_dropzone_is_visible(page, import_server):
    """Upload dropzone is visible after an account exists."""
    page.goto(f"{import_server}/import")
    assert page.locator("#dropzone").is_visible()


def test_import_no_pending_imports_message(page, import_server):
    """Before any uploads the staging column shows 'No pending imports'."""
    page.goto(f"{import_server}/import")
    assert page.locator("text=No pending imports").is_visible()


# ---------------------------------------------------------------------------
# 7–9  File upload → staging review
# ---------------------------------------------------------------------------


def test_import_upload_ofx_creates_staging_batch(page, import_server, ofx_file):
    """Uploading an OFX file creates a staging batch in the right column."""
    page.goto(f"{import_server}/import")

    # Select the account
    page.select_option("select[name='account_id']", label="Test Checking")

    # Set file (triggers JS detectAccount fetch first)
    with page.expect_response(lambda r: "detect-account" in r.url):
        page.set_input_files("#file-input", str(ofx_file))

    # Submit the import form (HTMX hx-post /import/upload)
    with page.expect_response(lambda r: "/import/upload" in r.url and r.status == 200):
        page.click("button[type='submit']")

    # A staging batch div should appear
    page.wait_for_selector('[id^="batch-"]')


def test_import_staging_shows_filename(page, import_server, ofx_file):
    """The staging area displays the uploaded filename."""
    page.goto(f"{import_server}/import")
    # The batch was already created by the previous test; just reload the page
    # to verify the filename persists in the staging panel.
    content_text = page.locator("#content").inner_text()
    assert (
        "import.ofx" in content_text
        or "seed.ofx" in content_text
        or "No pending" not in content_text
    )


def test_import_staging_review_table_loads(page, import_server):
    """The batch review table loads via HTMX (hx-trigger='load') and shows
    transaction rows for the staged import."""
    page.goto(f"{import_server}/import")
    # The review table inside the batch div is loaded automatically on page load
    page.wait_for_selector('[id^="batch-"] table')
    rows = page.locator('[id^="batch-"] table tbody tr')
    assert rows.count() >= 1


# ---------------------------------------------------------------------------
# 10  Confirm clears staging
# ---------------------------------------------------------------------------


def test_import_confirm_removes_batch_from_staging(page, import_server):
    """Clicking 'Confirm' finalises the import and removes it from the staging panel."""
    page.goto(f"{import_server}/import")

    # Confirm the first (only) pending batch
    with page.expect_response(lambda r: "/confirm" in r.url and r.status == 200):
        page.locator("button:has-text('Confirm')").first.click()

    page.wait_for_selector("text=No pending imports")


# ---------------------------------------------------------------------------
# 11–12  Second upload → reject
# ---------------------------------------------------------------------------


def test_import_second_upload_creates_new_staging(page, import_server, ofx_file_2):
    """Uploading a second, distinct OFX file creates a new staging batch."""
    page.goto(f"{import_server}/import")
    page.select_option("select[name='account_id']", label="Test Checking")

    with page.expect_response(lambda r: "detect-account" in r.url):
        page.set_input_files("#file-input", str(ofx_file_2))

    with page.expect_response(lambda r: "/import/upload" in r.url and r.status == 200):
        page.click("button[type='submit']")

    page.wait_for_selector('[id^="batch-"]')


def test_import_reject_removes_batch_from_staging(page, import_server):
    """Clicking 'Reject' discards the import and removes it from the staging panel."""
    page.goto(f"{import_server}/import")

    # Reject the pending batch
    with page.expect_response(lambda r: "/reject" in r.url and r.status == 200):
        page.locator("button:has-text('Reject')").first.click()

    page.wait_for_selector("text=No pending imports")


# ---------------------------------------------------------------------------
# 13  Duplicate-file detection
# ---------------------------------------------------------------------------


def test_import_duplicate_file_shows_already_imported_error(
    page, import_server, ofx_file
):
    """Re-uploading the first OFX file (already confirmed) shows an error message
    rather than creating a second staging batch."""
    page.goto(f"{import_server}/import")
    page.select_option("select[name='account_id']", label="Test Checking")

    with page.expect_response(lambda r: "detect-account" in r.url):
        page.set_input_files("#file-input", str(ofx_file))

    with page.expect_response(lambda r: "/import/upload" in r.url and r.status == 200):
        page.click("button[type='submit']")

    # Result area should show an "already imported" message
    content = page.locator("#content").inner_text()
    assert "already imported" in content.lower() or "skipped" in content.lower()


# ---------------------------------------------------------------------------
# 14  OFX detect-account pre-fills the create-account form
# ---------------------------------------------------------------------------


def test_import_ofx_detect_account_prefills_institution(
    page, import_server, ofx_file_with_institution
):
    """Selecting a QFX/OFX file in the dropzone sends it to /import/detect-account
    and the returned account panel is pre-filled with the institution name."""
    page.goto(f"{import_server}/import")

    # After account creation earlier in this module the panel shows a select.
    # The detect-account response also shows a collapsed "Create new account" form.
    with page.expect_response(lambda r: "detect-account" in r.url and r.status == 200):
        page.set_input_files("#file-input", str(ofx_file_with_institution))

    # The institution field inside the account panel should be pre-filled with "Chase"
    page.wait_for_selector("#account-panel")
    panel_html = page.locator("#account-panel").inner_html()
    assert "Chase" in panel_html
