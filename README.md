# Olympic Analytics Dashboard

A full-stack data analytics web application built with **Python 3, Flask, Pandas, and Plotly**
analysing 35+ years of Olympic Games history (1992–2026).

> **Academic Note:** This is an independently implemented version.  The four cleaned CSV datasets
> and the project concept are derived from a reference project.  All code — architecture, chart
> logic, frontend JS, and new features — is written independently.  Please credit the original
> data source (Kaggle / IOC public dataset) if required by your college.

---

## Features

| Feature | Description |
|---------|-------------|
| 10 interactive charts | Generated server-side with Pandas + Plotly, rendered with Plotly.js |
| **NEW** Medal Heatmap | Country × Year grid using `go.Heatmap` — not in the reference project |
| **NEW** Year Comparison Tool | Compare top medal winners between any two Olympic years |
| **NEW** CSV Export | Download the leaderboard as a CSV file (client-side Blob API) |
| **NEW** Data-driven Insights | 6 insight cards computed from actual DataFrames, not hard-coded text |
| **NEW** Medal Momentum KPI | Year-on-year % change in medals distributed |
| Per-tab lazy loading | Charts only load when the user opens that tab |
| Leaderboard sorting & filter | Click column headers to sort; filter by region |
| Country Deep-Dive | On-demand chart for any of 60 countries |
| Skeleton shimmer loaders | Smooth loading UX replacing plain spinners |
| 35 automated tests | unittest — data, charts, KPIs, all routes, new endpoints |

## Tech Stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3, Flask |
| Data | Pandas, NumPy |
| Charts | Plotly Python (server) + Plotly.js (browser) |
| Frontend | Bootstrap 5, custom CSS, vanilla JS |
| Tests | Python `unittest` |

## Project Structure

```
olympic-analytics/
├── app.py              # HTTP routes only (~230 lines)
├── charts.py           # All 12 chart/insight functions (~590 lines)
├── data_loader.py      # Data loading + KPI computation (~120 lines)
├── requirements.txt    # Python dependencies
├── test_app.py         # 35 automated tests (~320 lines)
├── templates/
│   └── index.html      # Single-page frontend (~620 lines)
└── DataSets - Global Olympic Sports Performance Analysis/
    └── Cleaned Datasets/
        ├── medal_results.csv       # 910 rows — per-country per-Games medals
        ├── athletes_cleaned.csv    # 1,548 rows — athlete & sport data
        ├── games_summary.csv       # 18 rows — host country / year
        └── alltime_investment.csv  # 60 rows — investment & efficiency
```

## Quick Start (Windows)

```bat
cd C:\Users\aa\Downloads\olympic-analytics

:: Create a virtual environment
python -m venv venv
venv\Scripts\activate.bat

:: Install dependencies
pip install -r requirements.txt

:: Run the app
python app.py

:: Open in your browser
:: http://127.0.0.1:5000
```

## Run Tests

```bat
python test_app.py
:: Expected: Ran 35 tests in ~1.5s   OK
```

## API Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /` | Dashboard (server-rendered HTML) |
| `GET /api/charts/trends` | Trends tab charts (medal trends, host advantage, gender) |
| `GET /api/charts/performance` | Performance tab charts (top countries, treemap) |
| `GET /api/charts/efficiency` | Efficiency tab charts (scatter, ranking) |
| `GET /api/charts/sports` | Sports tab charts (top sports, **heatmap**) |
| `GET /api/charts/country?name=X` | Medal history for country X |
| `GET /api/charts/compare?y1=X&y2=Y` | **NEW** Year comparison chart |
| `GET /api/leaderboard[?region=X]` | Top 20 nations table (filterable) |
| `GET /api/search?q=X` | Country name search |
| `GET /api/insights` | **NEW** Data-driven insight strings |
| `GET /api/export/leaderboard` | **NEW** Download leaderboard as CSV |

## Key Changes vs Reference Project

1. **Modular architecture** — `app.py` / `charts.py` / `data_loader.py` instead of one 460-line file
2. **Per-tab lazy loading** — 4 tab-specific endpoints replace one huge `/api/charts/overview` call
3. **Medal Heatmap** — new `go.Heatmap` chart showing Country × Year medal matrix
4. **Year Comparison** — grouped bar comparing any two Olympic years
5. **Data-driven insights** — computed from DataFrames, not hard-coded text strings
6. **Medal Momentum KPI** — new metric showing YoY medal change %
7. **Skeleton shimmer loaders** — replace plain spinners for better UX
8. **Leaderboard sorting + region filter** — click headers to sort; pills to filter
9. **CSV export** — client-side Blob download on leaderboard
10. **Fixed dead Jinja loop** — hero stat pills now render correctly
11. **Fixed test typo** — `chart_gold_silva_bronze_breakdown` corrected
12. **35 tests** — up from 29; covers all new endpoints

## License

Academic project — for educational purposes.
Original data sourced from cleaned Olympic datasets.
