from flask import Blueprint, current_app, render_template, request

from spending.repository.categories import get_category_names
from spending.repository.merchants import (
    list_merchants_with_stats,
    set_merchant_category,
)

bp = Blueprint("merchants", __name__)


@bp.route("/merchants")
def index():
    search = request.args.get("search", "")
    filter_category = request.args.get("category", "")
    filter_source = request.args.get("source", "")

    engine = current_app.config["engine"]
    with engine.connect() as conn:
        merchants = list_merchants_with_stats(conn)
        categories = get_category_names(conn)

    if search:
        merchants = [
            m for m in merchants if search.upper() in m["merchant_name"].upper()
        ]
    if filter_category:
        merchants = [m for m in merchants if m["category"] == filter_category]
    if filter_source:
        merchants = [m for m in merchants if m["source"] == filter_source]

    template = (
        "partials/merchant_rows.html"
        if request.headers.get("HX-Request")
        else "merchants.html"
    )
    return render_template(
        template,
        active_tab="merchants",
        merchants=merchants,
        categories=categories,
        search=search,
        selected_category=filter_category,
        selected_source=filter_source,
    )


@bp.route("/merchants/<int:merchant_id>/edit", methods=["GET"])
def edit_form(merchant_id):
    engine = current_app.config["engine"]
    with engine.connect() as conn:
        categories = get_category_names(conn)
    return render_template(
        "partials/merchant_edit.html", merchant_id=merchant_id, categories=categories
    )


@bp.route("/merchants/<int:merchant_id>/category", methods=["POST"])
def update_category(merchant_id):
    category = request.form["category"]
    merchant_name = request.form["merchant_name"]

    engine = current_app.config["engine"]
    with engine.connect() as conn:
        set_merchant_category(conn, merchant_name, category, source="manual")

    return "", 200, {"HX-Trigger": "refreshMerchants"}
