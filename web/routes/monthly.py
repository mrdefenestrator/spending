from flask import Blueprint, render_template

bp = Blueprint("monthly", __name__)


@bp.route("/")
@bp.route("/monthly")
def index():
    return render_template("monthly.html", active_tab="monthly")
