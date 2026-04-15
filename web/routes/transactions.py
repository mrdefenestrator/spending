from flask import Blueprint, render_template

bp = Blueprint("transactions", __name__)


@bp.route("/transactions")
def index():
    return render_template("transactions.html", active_tab="transactions")
