from flask import Blueprint, current_app, render_template, request
from sqlalchemy.exc import IntegrityError

from spending.repository.accounts import add_account, edit_account, list_accounts

VALID_ACCOUNT_TYPES = {"checking", "savings", "credit_card", "other"}

bp = Blueprint("accounts", __name__)


@bp.route("/accounts")
def index():
    engine = current_app.config["engine"]
    with engine.connect() as conn:
        accts = list_accounts(conn)
    template = (
        "partials/accounts_content.html"
        if request.headers.get("HX-Request")
        else "accounts.html"
    )
    return render_template(template, active_tab="accounts", accounts=accts)


@bp.route("/accounts/<int:account_id>/edit")
def edit_form(account_id):
    engine = current_app.config["engine"]
    with engine.connect() as conn:
        accts = list_accounts(conn)
    acct = next((a for a in accts if a["id"] == account_id), None)
    return render_template("partials/account_edit_row.html", account=acct)


@bp.route("/accounts/<int:account_id>", methods=["POST"])
def update(account_id):
    name = request.form.get("name", "").strip()
    institution = request.form.get("institution", "").strip()
    account_type = request.form.get("account_type", "other")
    if account_type not in VALID_ACCOUNT_TYPES:
        account_type = "other"

    engine = current_app.config["engine"]
    with engine.connect() as conn:
        if name and institution:
            edit_account(conn, account_id, name=name, institution=institution, account_type=account_type)
        accts = list_accounts(conn)
    return render_template("partials/accounts_content.html", active_tab="accounts", accounts=accts)


@bp.route("/accounts", methods=["POST"])
def create():
    name = request.form.get("acct_name", "").strip()
    institution = request.form.get("acct_institution", "").strip()
    account_type = request.form.get("acct_type", "checking")
    if account_type not in VALID_ACCOUNT_TYPES:
        account_type = "other"

    engine = current_app.config["engine"]

    with engine.connect() as conn:
        if not name or not institution:
            accounts = list_accounts(conn)
            return render_template(
                "partials/account_panel.html",
                accounts=accounts,
                meta=None,
                selected_account_id=None,
                show_create=True,
                error="Name and institution are required.",
            )

        try:
            new_id = add_account(
                conn, name=name, institution=institution, account_type=account_type
            )
        except IntegrityError:
            accounts = list_accounts(conn)
            return render_template(
                "partials/account_panel.html",
                accounts=accounts,
                meta=None,
                selected_account_id=None,
                show_create=True,
                error=f'Account "{name}" already exists.',
            )

        accounts = list_accounts(conn)
        return render_template(
            "partials/account_panel.html",
            accounts=accounts,
            meta=None,
            selected_account_id=new_id,
            show_create=False,
            error=None,
        )
