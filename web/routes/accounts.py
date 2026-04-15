from flask import Blueprint, current_app, render_template, request
from sqlalchemy.exc import IntegrityError

from spending.repository.accounts import add_account, list_accounts

bp = Blueprint("accounts", __name__)


@bp.route("/accounts", methods=["POST"])
def create():
    name = request.form.get("acct_name", "").strip()
    institution = request.form.get("acct_institution", "").strip()
    account_type = request.form.get("acct_type", "checking")

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
