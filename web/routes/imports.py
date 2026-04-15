from flask import Blueprint, render_template

bp = Blueprint("imports", __name__)


@bp.route("/import")
def index():
    return render_template("import.html", active_tab="import")
