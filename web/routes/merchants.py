from flask import Blueprint, render_template

bp = Blueprint("merchants", __name__)


@bp.route("/merchants")
def index():
    return render_template("merchants.html", active_tab="merchants")
