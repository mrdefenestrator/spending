from flask import Blueprint, current_app, render_template, request
from sqlalchemy.exc import IntegrityError

from spending.repository.accounts import add_account, edit_account, list_accounts

VALID_ACCOUNT_TYPES = {"checking", "savings", "credit_card", "other"}

_ACCOUNT_SORT_KEYS = {
    "name": lambda a: (a["name"] or "").lower(),
    "institution": lambda a: (a["institution"] or "").lower(),
    "type": lambda a: (a["account_type"] or "").lower(),
    "created": lambda a: str(a["created_at"] or ""),
}

bp = Blueprint("accounts", __name__)


def _sort_accounts(accts: list, sort: str, sort_dir: str) -> list:
    if sort in _ACCOUNT_SORT_KEYS:
        return sorted(accts, key=_ACCOUNT_SORT_KEYS[sort], reverse=(sort_dir == "desc"))
    return sorted(accts, key=lambda a: (a["name"] or "").lower())


@bp.route("/accounts")
def index():
    sort = request.args.get("sort", "")
    sort_dir = request.args.get("dir", "")
    engine = current_app.config["engine"]
    with engine.connect() as conn:
        accts = list_accounts(conn)
    accts = _sort_accounts(accts, sort, sort_dir)
    template = (
        "partials/accounts_content.html"
        if request.headers.get("HX-Request")
        else "accounts.html"
    )
    return render_template(
        template, active_tab="accounts", accounts=accts, sort=sort, dir=sort_dir
    )


@bp.route("/accounts/<int:account_id>/edit")
def edit_form(account_id):
    engine = current_app.config["engine"]
    with engine.connect() as conn:
        accts = list_accounts(conn)
    acct = next((a for a in accts if a["id"] == account_id), None)
    return render_template("partials/account_edit_row.html", account=acct)


@bp.route("/accounts/<int:account_id>/row")
def row(account_id):
    engine = current_app.config["engine"]
    with engine.connect() as conn:
        accts = list_accounts(conn)
    acct = next((a for a in accts if a["id"] == account_id), None)
    if not acct:
        return "", 404
    return render_template("partials/account_row.html", a=acct)


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
            edit_account(
                conn,
                account_id,
                name=name,
                institution=institution,
                account_type=account_type,
            )
        accts = list_accounts(conn)
    acct = next((a for a in accts if a["id"] == account_id), None)
    if not acct:
        return "", 404
    return render_template("partials/account_row.html", a=acct)


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
