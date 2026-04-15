import tempfile
from pathlib import Path

from flask import Blueprint, current_app, render_template, request

from spending.classifier import classify_merchants
from spending.importer import run_import
from spending.repository.accounts import list_accounts
from spending.repository.categories import get_category_names
from spending.repository.imports import (
    confirm_import,
    get_staging_imports,
    reject_import,
)
from spending.repository.merchants import get_uncached_merchants, set_merchant_category
from spending.repository.transactions import get_transactions

bp = Blueprint("imports", __name__)


@bp.route("/import")
def index():
    engine = current_app.config["engine"]
    with engine.connect() as conn:
        staging = get_staging_imports(conn)
        accounts = list_accounts(conn)

    template = (
        "partials/import_content.html"
        if request.headers.get("HX-Request")
        else "import.html"
    )
    return render_template(
        template,
        active_tab="import",
        staging=staging,
        accounts=accounts,
    )


@bp.route("/import/upload", methods=["POST"])
def upload():
    files = request.files.getlist("files")
    account_id = request.form.get("account_id", type=int)

    if not files or not account_id:
        return "<p class='text-red-500'>Please select files and an account.</p>", 400

    engine = current_app.config["engine"]
    results = []

    with engine.connect() as conn:
        all_new_merchants = set()

        for f in files:
            if not f.filename:
                continue
            # Save to temp file
            suffix = Path(f.filename).suffix
            with tempfile.NamedTemporaryFile(delete=False, suffix=suffix) as tmp:
                f.save(tmp.name)
                result = run_import(conn, tmp.name, account_id)
                result["filename"] = f.filename
                results.append(result)
                if not result.get("error"):
                    all_new_merchants.update(result.get("new_merchants", []))

        # Classify new merchants
        if all_new_merchants:
            uncached = get_uncached_merchants(conn, list(all_new_merchants))
            if uncached:
                category_names = get_category_names(conn)
                classifications = classify_merchants(uncached, category_names)
                for name, category in classifications.items():
                    set_merchant_category(conn, name, category, source="api")

        # Re-fetch staging imports
        staging = get_staging_imports(conn)
        accounts = list_accounts(conn)

    template = (
        "partials/import_content.html"
        if request.headers.get("HX-Request")
        else "import.html"
    )
    return render_template(
        template,
        active_tab="import",
        staging=staging,
        accounts=accounts,
        results=results,
    )


@bp.route("/import/<int:import_id>/review")
def review(import_id):
    engine = current_app.config["engine"]
    with engine.connect() as conn:
        txns = get_transactions(conn, import_id=import_id)
    return render_template(
        "partials/import_batch.html", transactions=txns, import_id=import_id
    )


@bp.route("/import/<int:import_id>/confirm", methods=["POST"])
def confirm(import_id):
    engine = current_app.config["engine"]
    with engine.connect() as conn:
        confirm_import(conn, import_id)
        staging = get_staging_imports(conn)
        accounts = list_accounts(conn)
    return render_template(
        "partials/import_content.html",
        active_tab="import",
        staging=staging,
        accounts=accounts,
    )


@bp.route("/import/<int:import_id>/reject", methods=["POST"])
def do_reject(import_id):
    engine = current_app.config["engine"]
    with engine.connect() as conn:
        reject_import(conn, import_id)
        staging = get_staging_imports(conn)
        accounts = list_accounts(conn)
    return render_template(
        "partials/import_content.html",
        active_tab="import",
        staging=staging,
        accounts=accounts,
    )
