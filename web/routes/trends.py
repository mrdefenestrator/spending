from datetime import date
from collections import defaultdict

from flask import Blueprint, current_app, render_template, request

from spending.repository.aggregations import get_monthly_totals_range

bp = Blueprint("trends", __name__)


def _period_range(period: str, today: date) -> tuple[date, date]:
    if period == "quarterly":
        quarter_start_month = ((today.month - 1) // 3) * 3 + 1
        return date(today.year, quarter_start_month, 1), today
    elif period == "ytd":
        return date(today.year, 1, 1), today
    elif period == "trailing12":
        start_year = today.year - 1
        start_month = today.month + 1
        if start_month > 12:
            start_month -= 12
            start_year += 1
        return date(start_year, start_month, 1), today
    elif period == "annual":
        return date(today.year - 1, 1, 1), date(today.year - 1, 12, 31)
    else:
        return date(today.year, 1, 1), today


@bp.route("/trends")
def index():
    today = date.today()
    period = request.args.get("period", "ytd")
    start, end = _period_range(period, today)

    engine = current_app.config["engine"]
    with engine.connect() as conn:
        monthly_data = get_monthly_totals_range(conn, start_date=start, end_date=end)

    # Group by category, build per-month values for sparklines
    by_category = defaultdict(lambda: {"total": 0, "months": defaultdict(float)})
    all_months = set()
    for row in monthly_data:
        key = (row["year"], row["month"])
        all_months.add(key)
        by_category[row["category"]]["total"] += float(row["total"])
        by_category[row["category"]]["months"][key] = float(row["total"])

    sorted_months = sorted(all_months)
    num_months = max(len(sorted_months), 1)

    trends = []
    for cat, data in sorted(by_category.items(), key=lambda x: x[1]["total"]):
        sparkline_values = [abs(data["months"].get(m, 0)) for m in sorted_months]
        trends.append(
            {
                "category": cat,
                "total": data["total"],
                "monthly_avg": data["total"] / num_months,
                "sparkline_values": sparkline_values,
            }
        )

    grand_total = sum(t["total"] for t in trends)

    template = (
        "partials/trends_table.html"
        if request.headers.get("HX-Request")
        else "trends.html"
    )
    return render_template(
        template,
        active_tab="trends",
        trends=trends,
        grand_total=grand_total,
        period=period,
    )
