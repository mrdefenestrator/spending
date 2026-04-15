from datetime import date

from flask import Blueprint, current_app, render_template, request

from spending.repository.aggregations import (
    get_monthly_category_totals,
    get_rolling_average,
)
from spending.repository.transactions import get_transactions

bp = Blueprint("monthly", __name__)


@bp.route("/")
@bp.route("/monthly")
def index():
    today = date.today()
    year = request.args.get("year", today.year, type=int)
    month = request.args.get("month", today.month, type=int)

    engine = current_app.config["engine"]
    with engine.connect() as conn:
        totals = get_monthly_category_totals(conn, year=year, month=month)
        averages = get_rolling_average(conn, year=year, month=month, months_back=3)

    # Merge averages into totals
    for row in totals:
        row["average"] = averages.get(row["category"])

    excluded = {"Transfer", "Income"}
    grand_total = sum(row["total"] for row in totals if row["category"] not in excluded)

    template = (
        "partials/monthly_table.html"
        if request.headers.get("HX-Request")
        else "monthly.html"
    )
    return render_template(
        template,
        active_tab="monthly",
        totals=totals,
        grand_total=grand_total,
        year=year,
        month=month,
    )


@bp.route("/monthly/drilldown/<category>")
def drilldown(category):
    year = request.args.get("year", date.today().year, type=int)
    month = request.args.get("month", date.today().month, type=int)

    engine = current_app.config["engine"]
    with engine.connect() as conn:
        txns = get_transactions(conn, year=year, month=month, category=category)

    return render_template(
        "partials/monthly_drilldown.html",
        transactions=txns,
        category=category,
    )
