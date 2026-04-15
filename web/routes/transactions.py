from datetime import date

from flask import Blueprint, current_app, render_template, request

from spending.repository.accounts import list_accounts
from spending.repository.categories import get_category_names
from spending.repository.corrections import apply_transaction_correction
from spending.repository.merchants import set_merchant_category
from spending.repository.transactions import get_transactions

bp = Blueprint("transactions", __name__)


@bp.route("/transactions")
def index():
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)
    category = request.args.get("category")
    account_id = request.args.get("account_id", type=int)
    search = request.args.get("search")
    status = request.args.get("status")

    engine = current_app.config["engine"]
    with engine.connect() as conn:
        txns = get_transactions(
            conn,
            year=year,
            month=month,
            category=category,
            account_id=account_id,
            search=search,
            status=status,
        )
        accounts = list_accounts(conn)
        categories = get_category_names(conn)

    prev_month = month - 1 if month > 1 else 12
    prev_year = year if month > 1 else year - 1
    next_month = month + 1 if month < 12 else 1
    next_year = year if month < 12 else year + 1

    template = (
        "partials/transactions_content.html"
        if request.headers.get("HX-Request")
        else "transactions.html"
    )
    return render_template(
        template,
        active_tab="transactions",
        transactions=txns,
        accounts=accounts,
        categories=categories,
        year=year,
        month=month,
        prev_year=prev_year,
        prev_month=prev_month,
        next_year=next_year,
        next_month=next_month,
        selected_category=category,
        selected_account=account_id,
        search=search or "",
        selected_status=status,
    )


@bp.route("/transactions/<int:txn_id>/edit-category", methods=["GET"])
def edit_category_form(txn_id):
    engine = current_app.config["engine"]
    with engine.connect() as conn:
        categories = get_category_names(conn)
    return render_template(
        "partials/transaction_edit.html",
        txn_id=txn_id,
        categories=categories,
        field="category",
    )


@bp.route("/transactions/<int:txn_id>/category", methods=["POST"])
def update_category(txn_id):
    category = request.form["category"]
    apply_to_merchant = request.form.get("apply_to_merchant") == "on"

    engine = current_app.config["engine"]
    with engine.connect() as conn:
        if apply_to_merchant:
            from spending.models import transactions as txn_table
            from sqlalchemy import select

            row = conn.execute(
                select(txn_table.c.normalized_merchant).where(txn_table.c.id == txn_id)
            ).fetchone()
            if row:
                set_merchant_category(conn, row[0], category, source="manual")
        else:
            apply_transaction_correction(conn, txn_id, category=category)

    current_url = request.headers.get("HX-Current-URL", "/transactions")
    return "", 204, {"HX-Redirect": current_url}


@bp.route("/transactions/bulk-categorize", methods=["POST"])
def bulk_categorize():
    txn_ids = request.form.getlist("txn_ids", type=int)
    category = request.form["category"]

    engine = current_app.config["engine"]
    with engine.connect() as conn:
        for txn_id in txn_ids:
            apply_transaction_correction(conn, txn_id, category=category)

    return "", 200, {"HX-Trigger": "refreshTransactions"}
