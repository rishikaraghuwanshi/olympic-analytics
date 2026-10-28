"""
test_app.py
===========
Extended automated tests for the Olympic Analytics Dashboard.

Run from the project root:
    python test_app.py

Test coverage:
  - Data loading (all 4 CSVs, column schema)
  - KPI computation (types, keys, new momentum metric)
  - Every chart function (valid Plotly figure dict)
  - All Flask routes (status codes, content types)
  - Country API (valid, invalid, missing param)
  - Year Comparison API (valid, invalid years)
  - Leaderboard API (structure, region filter)
  - Search API
  - Insights API (data-driven content)
  - Export endpoint (CSV download)

Fixed from reference: typo 'chart_gold_silva_bronze_breakdown' -> correct import name.
"""

import sys
import os
import json
import unittest

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import app
from data_loader import DATA, compute_kpis, get_country_list, get_olympic_years
import charts


# ── 1. Data Loading ──────────────────────────────────────────────────────────

class TestDataLoading(unittest.TestCase):
    """All four datasets must load and have their required columns."""

    def test_medals_not_empty(self):
        self.assertFalse(DATA["medals"].empty, "medal_results.csv is empty or missing")

    def test_athletes_not_empty(self):
        self.assertFalse(DATA["athletes"].empty, "athletes_cleaned.csv is empty or missing")

    def test_games_not_empty(self):
        self.assertFalse(DATA["games"].empty, "games_summary.csv is empty or missing")

    def test_investment_not_empty(self):
        self.assertFalse(DATA["investment"].empty, "alltime_investment.csv is empty or missing")

    def test_medals_required_columns(self):
        required = {"year", "country", "gold", "silver", "bronze", "total_medals"}
        self.assertTrue(required.issubset(set(DATA["medals"].columns)),
                        f"Missing cols: {required - set(DATA['medals'].columns)}")

    def test_investment_required_columns(self):
        required = {"country", "region", "alltime_total_medals", "avg_efficiency_pct", "sports_investment"}
        self.assertTrue(required.issubset(set(DATA["investment"].columns)))

    def test_athletes_required_columns(self):
        required = {"Name", "Sex", "year", "country", "sport_category"}
        self.assertTrue(required.issubset(set(DATA["athletes"].columns)))

    def test_games_required_columns(self):
        required = {"year", "host_country"}
        self.assertTrue(required.issubset(set(DATA["games"].columns)))


# ── 2. KPI Computation ───────────────────────────────────────────────────────

class TestKPIs(unittest.TestCase):
    """KPI function must return correct structure and types, including momentum."""

    def setUp(self):
        self.kpis = compute_kpis()

    def test_all_keys_present(self):
        expected_keys = [
            "total_countries", "total_games", "total_athletes", "total_sports",
            "top_country", "top_country_medals", "most_efficient", "most_efficient_pct",
            "momentum_pct", "momentum_year",  # new keys
        ]
        for k in expected_keys:
            self.assertIn(k, self.kpis, f"Missing KPI key: {k}")

    def test_counts_are_positive(self):
        self.assertGreater(self.kpis["total_countries"], 0)
        self.assertGreater(self.kpis["total_games"],     0)
        self.assertGreater(self.kpis["total_athletes"],  0)

    def test_top_country_is_string(self):
        self.assertIsInstance(self.kpis["top_country"], str)
        self.assertGreater(len(self.kpis["top_country"]), 0)

    def test_efficiency_is_float(self):
        self.assertIsInstance(self.kpis["most_efficient_pct"], float)

    def test_momentum_is_float(self):
        self.assertIsInstance(self.kpis["momentum_pct"], float)

    def test_country_list_sorted(self):
        lst = get_country_list()
        self.assertEqual(lst, sorted(lst))

    def test_olympic_years_sorted(self):
        yrs = get_olympic_years()
        self.assertEqual(yrs, sorted(yrs))


# ── 3. Chart Functions ───────────────────────────────────────────────────────

class TestChartFunctions(unittest.TestCase):
    """Each chart function must return a valid Plotly figure dict."""

    def _check(self, fig, name):
        self.assertIsInstance(fig, dict, f"{name} must return dict")
        self.assertIn("data", fig, f"{name}: missing 'data' key")
        self.assertGreater(len(fig["data"]), 0, f"{name}: 'data' is empty")

    def test_medal_trends(self):
        self._check(charts.chart_medal_trends_over_time(), "medal_trends")

    def test_host_advantage(self):
        self._check(charts.chart_host_advantage(), "host_advantage")

    def test_gender_split(self):
        self._check(charts.chart_gender_split(), "gender_split")

    def test_top_countries(self):
        self._check(charts.chart_top_countries(), "top_countries")

    def test_region_treemap(self):
        self._check(charts.chart_region_treemap(), "region_treemap")

    def test_investment_scatter(self):
        self._check(charts.chart_investment_vs_efficiency(), "investment_scatter")

    def test_efficiency_ranking(self):
        self._check(charts.chart_efficiency_ranking(), "efficiency_ranking")

    def test_top_sports(self):
        self._check(charts.chart_top_sports(), "top_sports")

    def test_medal_heatmap(self):
        """NEW: Heatmap chart must return a valid go.Heatmap figure."""
        self._check(charts.chart_medal_heatmap(), "medal_heatmap")

    def test_year_comparison_valid(self):
        """NEW: Year comparison for two valid years."""
        years = get_olympic_years()
        if len(years) >= 2:
            self._check(charts.chart_year_comparison(years[0], years[-1]), "year_comparison")

    def test_country_medal_history_valid(self):
        """Country history for first country in investment dataset."""
        countries = get_country_list()
        if countries:
            country = countries[0]
            df = DATA["medals"]
            if not df.empty and country in df["country"].values:
                self._check(charts.chart_country_medal_history(country), f"history:{country}")

    def test_country_medal_history_invalid(self):
        """Invalid country must return empty dict (not raise)."""
        result = charts.chart_country_medal_history("ZZZFakeCountry999")
        self.assertEqual(result, {})

    def test_insights_structure(self):
        """compute_insights must return a non-empty list of dicts with required keys."""
        items = charts.compute_insights()
        self.assertIsInstance(items, list)
        self.assertGreater(len(items), 0)
        for item in items:
            self.assertIn("icon",  item)
            self.assertIn("title", item)
            self.assertIn("body",  item)
            self.assertIsInstance(item["body"], str)
            self.assertGreater(len(item["body"]), 20)  # must not be trivially short


# ── 4. Flask Routes ──────────────────────────────────────────────────────────

class TestFlaskRoutes(unittest.TestCase):
    """Integration tests for all HTTP routes."""

    def setUp(self):
        app.config["TESTING"] = True
        self.client = app.test_client()

    # Homepage
    def test_homepage_200(self):
        resp = self.client.get("/")
        self.assertEqual(resp.status_code, 200)
        self.assertIn(b"Olympic", resp.data)

    # Tab chart endpoints
    def test_api_trends_200(self):
        resp = self.client.get("/api/charts/trends")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        for key in ("medal_trends", "host_advantage", "gender_split"):
            self.assertIn(key, data)

    def test_api_performance_200(self):
        resp = self.client.get("/api/charts/performance")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        for key in ("top_countries", "region_treemap"):
            self.assertIn(key, data)

    def test_api_efficiency_200(self):
        resp = self.client.get("/api/charts/efficiency")
        self.assertEqual(resp.status_code, 200)

    def test_api_sports_200(self):
        resp = self.client.get("/api/charts/sports")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIn("medal_heatmap", data)  # new chart

    # Country endpoint
    def test_country_valid(self):
        resp = self.client.get("/api/charts/country?name=United+States")
        self.assertEqual(resp.status_code, 200)

    def test_country_missing_param(self):
        resp = self.client.get("/api/charts/country")
        self.assertEqual(resp.status_code, 400)

    def test_country_invalid(self):
        resp = self.client.get("/api/charts/country?name=ZZZFakeCountry999")
        self.assertEqual(resp.status_code, 404)

    # Year comparison (NEW)
    def test_compare_valid(self):
        years = get_olympic_years()
        if len(years) >= 2:
            resp = self.client.get(f"/api/charts/compare?y1={years[0]}&y2={years[-1]}")
            self.assertEqual(resp.status_code, 200)

    def test_compare_missing_params(self):
        resp = self.client.get("/api/charts/compare")
        self.assertEqual(resp.status_code, 400)

    def test_compare_invalid_year(self):
        resp = self.client.get("/api/charts/compare?y1=1800&y2=1900")
        self.assertEqual(resp.status_code, 404)

    def test_compare_non_integer(self):
        resp = self.client.get("/api/charts/compare?y1=abc&y2=def")
        self.assertEqual(resp.status_code, 400)

    # Leaderboard
    def test_leaderboard_200(self):
        resp = self.client.get("/api/leaderboard")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    def test_leaderboard_fields(self):
        resp = self.client.get("/api/leaderboard")
        data = json.loads(resp.data)
        first = data[0]
        for field in ("country", "Total Medals", "Efficiency (%)", "Investment (M$)"):
            self.assertIn(field, first)

    def test_leaderboard_region_filter(self):
        """Region filter must narrow results."""
        resp_all    = self.client.get("/api/leaderboard")
        resp_europe = self.client.get("/api/leaderboard?region=Europe")
        all_data    = json.loads(resp_all.data)
        eur_data    = json.loads(resp_europe.data)
        if eur_data:
            self.assertLessEqual(len(eur_data), len(all_data))
            for row in eur_data:
                self.assertEqual(row["region"], "Europe")

    # Search
    def test_search_returns_list(self):
        resp = self.client.get("/api/search?q=aus")
        self.assertEqual(resp.status_code, 200)
        self.assertIsInstance(json.loads(resp.data), list)

    def test_search_empty_query(self):
        resp = self.client.get("/api/search?q=")
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(json.loads(resp.data), [])

    # Insights (NEW)
    def test_insights_200(self):
        resp = self.client.get("/api/insights")
        self.assertEqual(resp.status_code, 200)
        data = json.loads(resp.data)
        self.assertIsInstance(data, list)
        self.assertGreater(len(data), 0)

    # Export (NEW)
    def test_export_leaderboard_csv(self):
        resp = self.client.get("/api/export/leaderboard")
        self.assertEqual(resp.status_code, 200)
        self.assertIn("text/csv", resp.content_type)
        self.assertIn(b"country", resp.data)  # must have CSV header


# ── Runner ────────────────────────────────────────────────────────────────────

if __name__ == "__main__":
    print("=" * 60)
    print("  Olympic Analytics — Automated Tests (Extended)")
    print("=" * 60)
    loader = unittest.TestLoader()
    suite  = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
