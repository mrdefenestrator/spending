from flask import Blueprint, render_template

bp = Blueprint("trends", __name__)


@bp.route("/trends")
def index():
    return render_template("trends.html", active_tab="trends")
