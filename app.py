"""
app.py — Routes only.
=====================
This module handles HTTP routing exclusively.  All data logic lives in
data_loader.py; all chart logic lives in charts.py.  This separation follows
the Single Responsibility Principle and makes each file easy to test in isolation.

Author: (your name)
"""

from flask import Flask, render_template, jsonify, request

from data_loader import DATA, compute_kpis, get_country_list, get_olympic_years
import charts

# ── App Setup ─────────────────────────────────────────────────────────────────
app = Flask(__name__)


# ── Main Page ─────────────────────────────────────────────────────────────────

@app.route("/")
def index():
    """
    Render the single-page dashboard.
    KPI values and country list are server-rendered via Jinja2;
    all charts are loaded asynchronously by the frontend JavaScript.
    """
    return render_template(
        "index.html",
        kpis=compute_kpis(),
        countries=get_country_list(),
        years=get_olympic_years(),
    )


# ── Chart API — per-tab, lazily loaded ────────────────────────────────────────

@app.route("/api/charts/trends")
def api_trends():
    """Charts for the Trends tab (loaded when that tab is first opened)."""
    return jsonify({
        "medal_trends":   charts.chart_medal_trends_over_time(),
        "host_advantage": charts.chart_host_advantage(),
        "gender_split":   charts.chart_gender_split(),
    })


@app.route("/api/charts/performance")
def api_performance():
    """Charts for the Performance tab."""
    return jsonify({
        "top_countries": charts.chart_top_countries(),
        "region_treemap": charts.chart_region_treemap(),
    })


@app.route("/api/charts/efficiency")
def api_efficiency():
    """Charts for the Efficiency tab."""
    return jsonify({
        "investment_scatter":  charts.chart_investment_vs_efficiency(),
        "efficiency_ranking":  charts.chart_efficiency_ranking(),
    })


@app.route("/api/charts/sports")
def api_sports():
    """Charts for the Sports tab."""
    return jsonify({
        "top_sports":     charts.chart_top_sports(),
        "medal_heatmap":  charts.chart_medal_heatmap(),
    })


# ── Country Deep-Dive ─────────────────────────────────────────────────────────

@app.route("/api/charts/country")
def api_country():
    """
    Return the medal history chart for a specific country.

    Query params:
        name (str) — country name (must match a value in medal_results.csv)
    """
    country = request.args.get("name", "").strip()
    if not country:
        return jsonify({"error": "Query parameter 'name' is required."}), 400

    df = DATA["medals"]
    if df.empty or country not in df["country"].values:
        return jsonify({"error": f"No data found for country: '{country}'"}), 404

    fig = charts.chart_country_medal_history(country)
    if not fig:
        return jsonify({"error": f"Could not generate chart for: '{country}'"}), 404

    return jsonify(fig)


# ── NEW: Year Comparison ──────────────────────────────────────────────────────

@app.route("/api/charts/compare")
def api_compare():
    """
    Compare medal counts for two Olympic years.

    Query params:
        y1 (int) — first year
        y2 (int) — second year
    """
    try:
        y1 = int(request.args.get("y1", 0))
        y2 = int(request.args.get("y2", 0))
    except (ValueError, TypeError):
        return jsonify({"error": "y1 and y2 must be integers."}), 400

    if y1 == 0 or y2 == 0:
        return jsonify({"error": "Both y1 and y2 are required."}), 400

    valid_years = get_olympic_years()
    for yr in (y1, y2):
        if yr not in valid_years:
            return jsonify({"error": f"Year {yr} is not in the dataset."}), 404

    fig = charts.chart_year_comparison(y1, y2)
    return jsonify(fig)


# ── Leaderboard ───────────────────────────────────────────────────────────────

@app.route("/api/leaderboard")
def api_leaderboard():
    """
    Return the top 20 nations as a JSON list for the leaderboard table.
    Also supports filtering by region via ?region=X query param.
    """
    df = DATA["investment"]
    if df.empty:
        return jsonify([])

    region_filter = request.args.get("region", "").strip()
    if region_filter:
        df = df[df["region"].str.lower() == region_filter.lower()]

    top = (
        df.nlargest(20, "alltime_total_medals")
        [["country", "region", "alltime_total_medals", "avg_efficiency_pct", "sports_investment"]]
        .round(2)
        .rename(columns={
            "alltime_total_medals": "Total Medals",
            "avg_efficiency_pct":   "Efficiency (%)",
            "sports_investment":    "Investment (M$)",
        })
    )
    return jsonify(top.to_dict(orient="records"))


# ── Country Search ────────────────────────────────────────────────────────────

@app.route("/api/search")
def api_search():
    """
    Full-text search across country names.
    Returns matching rows with country, noc_code, region, and all-time medals.

    Query params:
        q (str) — search query
    """
    query = request.args.get("q", "").strip().lower()
    df = DATA["investment"]
    if df.empty or not query:
        return jsonify([])

    matches = df[df["country"].str.lower().str.contains(query, na=False)]
    return jsonify(
        matches[["country", "noc_code", "region", "alltime_total_medals"]]
        .to_dict(orient="records")
    )


# ── Data-driven Insights (NEW) ────────────────────────────────────────────────

@app.route("/api/insights")
def api_insights():
    """
    Return 6 data-driven insight strings computed from the actual DataFrames.
    Replaces the hard-coded insight cards in the original project.
    """
    return jsonify(charts.compute_insights())


# ── NEW: CSV Export endpoint ──────────────────────────────────────────────────

@app.route("/api/export/leaderboard")
def api_export_leaderboard():
    """
    Return the full leaderboard as a downloadable CSV file.
    The Content-Disposition header triggers a browser download.
    """
    import io
    df = DATA["investment"]
    if df.empty:
        return "No data", 404

    top = (
        df.nlargest(20, "alltime_total_medals")
        [["country", "region", "alltime_total_medals", "avg_efficiency_pct", "sports_investment"]]
        .round(2)
    )
    csv_string = top.to_csv(index=False)
    return app.response_class(
        response=csv_string,
        status=200,
        mimetype="text/csv",
        headers={"Content-Disposition": "attachment; filename=olympic_leaderboard.csv"},
    )


# ── Entry Point ───────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Olympic Analytics — My Independent Version")
    print("  http://127.0.0.1:5000")
    print("=" * 60)
    app.run(debug=True, port=5000)
