"""
charts.py
=========
Every Plotly chart function lives here.  app.py knows nothing about Pandas or
Plotly — it simply calls these functions and forwards their JSON to the client.

Design rules:
  - Each function returns a JSON-serialisable dict (Plotly figure).
  - If the required DataFrame is empty, return {} — never raise.
  - Helper `_base_layout()` keeps all shared dark-theme settings DRY.

Author: (your name)
"""

import json
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from plotly.utils import PlotlyJSONEncoder

from data_loader import DATA


# ── Shared layout helper ──────────────────────────────────────────────────────

def _base_layout(extra: dict | None = None) -> dict:
    """
    Return a dict of Plotly layout keys shared by every chart.
    Callers may pass `extra` to override or extend specific keys.
    """
    base = {
        "paper_bgcolor": "rgba(0,0,0,0)",
        "plot_bgcolor":  "rgba(0,0,0,0)",
        "font":          {"color": "#ccd6f6", "family": "Inter, sans-serif"},
        "title_font":    {"size": 15},
        "margin":        {"t": 50, "b": 40, "l": 20, "r": 20},
        "legend":        {"bgcolor": "rgba(0,0,0,0)"},
    }
    if extra:
        base.update(extra)
    return base


def _to_json(fig: go.Figure) -> dict:
    """Convert a Plotly figure to a plain dict via JSON round-trip."""
    return json.loads(json.dumps(fig, cls=PlotlyJSONEncoder))


# ─────────────────────────────────────────────────────────────────────────────
# TAB: TRENDS
# ─────────────────────────────────────────────────────────────────────────────

def chart_medal_trends_over_time() -> dict:
    """
    Line chart — total medals distributed per Olympic year across all nations.
    Shows the growth trend from 1992 to the latest Games.
    """
    df = DATA["medals"]
    if df.empty:
        return {}

    yearly = df.groupby("year")["total_medals"].sum().reset_index()

    fig = px.line(
        yearly,
        x="year", y="total_medals",
        markers=True,
        labels={"year": "Olympic Year", "total_medals": "Total Medals Awarded"},
        template="plotly_dark",
        color_discrete_sequence=["#f4c300"],
    )
    fig.update_traces(line_width=2.5, marker_size=9,
                      hovertemplate="<b>%{x}</b><br>Medals: %{y}<extra></extra>")
    fig.update_layout(**_base_layout())
    return _to_json(fig)


def chart_host_advantage() -> dict:
    """
    Grouped bar — for each Games, compare the host country's medal total
    in the hosting year against their all-other-years average.

    Logic: look up the host in medal_results.csv; separate hosting-year row
    from all other rows; compute mean of the rest.
    """
    medals = DATA["medals"]
    games  = DATA["games"]
    if medals.empty or games.empty:
        return {}

    records = []
    for _, row in games.iterrows():
        host = row["host_country"]
        year = row["year"]
        host_data = medals[medals["country"] == host]
        if host_data.empty:
            continue

        host_year_medals = host_data.loc[host_data["year"] == year, "total_medals"].sum()
        other_years_mean = host_data.loc[host_data["year"] != year, "total_medals"].mean()

        if pd.notna(other_years_mean) and host_year_medals > 0:
            records.append({
                "label":    f"{year} · {host}",
                "as_host":  int(host_year_medals),
                "avg_other": round(float(other_years_mean), 1),
                "advantage": round(float(host_year_medals - other_years_mean), 1),
            })

    if not records:
        return {}

    result = pd.DataFrame(records)
    fig = go.Figure([
        go.Bar(
            name="As Host",
            x=result["label"],
            y=result["as_host"],
            marker_color="#f4c300",
            hovertemplate="<b>%{x}</b><br>As Host: %{y} medals<extra></extra>",
        ),
        go.Bar(
            name="Avg (Other Years)",
            x=result["label"],
            y=result["avg_other"],
            marker_color="#1a5276",
            hovertemplate="<b>%{x}</b><br>Avg Other: %{y} medals<extra></extra>",
        ),
    ])
    fig.update_layout(
        barmode="group",
        xaxis_title="Olympic Games — Host Country",
        yaxis_title="Total Medals",
        xaxis_tickangle=-30,
        template="plotly_dark",
        **_base_layout(),
    )
    return _to_json(fig)


def chart_gender_split() -> dict:
    """
    Donut chart — male vs female athlete count across all Games in the dataset.
    """
    df = DATA["athletes"]
    if df.empty or "Sex" not in df.columns:
        return {}

    counts = df["Sex"].value_counts().reset_index()
    counts.columns = ["gender", "count"]
    counts["gender"] = counts["gender"].map({"M": "Male", "F": "Female"}).fillna("Other")

    fig = px.pie(
        counts,
        names="gender", values="count",
        hole=0.48,
        template="plotly_dark",
        color_discrete_map={"Male": "#2196F3", "Female": "#E91E63", "Other": "#888"},
    )
    fig.update_traces(
        textinfo="percent+label",
        hovertemplate="<b>%{label}</b><br>Count: %{value}<br>%{percent}<extra></extra>",
    )
    fig.update_layout(**_base_layout())
    return _to_json(fig)


# ─────────────────────────────────────────────────────────────────────────────
# TAB: PERFORMANCE
# ─────────────────────────────────────────────────────────────────────────────

def chart_top_countries() -> dict:
    """
    Horizontal bar — top 15 nations by all-time total medals (from investment CSV).
    """
    df = DATA["investment"]
    if df.empty:
        return {}

    top15 = df.nlargest(15, "alltime_total_medals").sort_values("alltime_total_medals")

    fig = px.bar(
        top15,
        x="alltime_total_medals", y="country",
        orientation="h",
        color="alltime_total_medals",
        color_continuous_scale=["#0d2137", "#f4c300"],
        labels={"alltime_total_medals": "All-Time Medals", "country": ""},
        template="plotly_dark",
        hover_data={"region": True, "alltime_total_medals": True},
    )
    fig.update_layout(coloraxis_showscale=False, **_base_layout())
    return _to_json(fig)


def chart_region_treemap() -> dict:
    """
    Treemap — total all-time medals broken down by continental region.
    Area of each tile is proportional to medal count.
    """
    df = DATA["investment"]
    if df.empty:
        return {}

    region_totals = df.groupby("region")["alltime_total_medals"].sum().reset_index()

    fig = px.treemap(
        region_totals,
        path=["region"],
        values="alltime_total_medals",
        color="alltime_total_medals",
        color_continuous_scale=["#0d2137", "#f4c300"],
        template="plotly_dark",
    )
    fig.update_traces(
        hovertemplate="<b>%{label}</b><br>Medals: %{value}<extra></extra>",
    )
    fig.update_layout(**_base_layout())
    return _to_json(fig)


# ─────────────────────────────────────────────────────────────────────────────
# TAB: EFFICIENCY
# ─────────────────────────────────────────────────────────────────────────────

def chart_investment_vs_efficiency() -> dict:
    """
    Bubble scatter — sports investment (x) vs medal efficiency % (y).
    Bubble size = all-time total medals.  Colour = region.
    Reveals whether spending more money always translates to better efficiency.
    """
    df = DATA["investment"]
    if df.empty:
        return {}

    fig = px.scatter(
        df,
        x="sports_investment",
        y="avg_efficiency_pct",
        size="alltime_total_medals",
        color="region",
        hover_name="country",
        size_max=52,
        labels={
            "sports_investment":  "Sports Investment (Million USD)",
            "avg_efficiency_pct": "Avg Medal Efficiency (%)",
            "alltime_total_medals": "All-Time Medals",
        },
        template="plotly_dark",
    )
    fig.update_layout(**_base_layout())
    return _to_json(fig)


def chart_efficiency_ranking() -> dict:
    """
    Horizontal bar — top 20 nations by average medal efficiency %.
    Green gradient highlights the most efficient performers.
    """
    df = DATA["investment"]
    if df.empty:
        return {}

    top20 = df.nlargest(20, "avg_efficiency_pct").sort_values("avg_efficiency_pct")

    fig = px.bar(
        top20,
        x="avg_efficiency_pct", y="country",
        orientation="h",
        color="avg_efficiency_pct",
        color_continuous_scale=["#1a5276", "#00c853"],
        labels={"avg_efficiency_pct": "Medal Efficiency (%)", "country": ""},
        template="plotly_dark",
    )
    fig.update_layout(coloraxis_showscale=False, **_base_layout())
    return _to_json(fig)


# ─────────────────────────────────────────────────────────────────────────────
# TAB: SPORTS
# ─────────────────────────────────────────────────────────────────────────────

def chart_top_sports() -> dict:
    """
    Horizontal bar — top 12 sport categories ranked by total medals produced.
    Uses a red gradient to contrast with the green efficiency chart.
    """
    df = DATA["athletes"]
    if df.empty or "sport_category" not in df.columns:
        return {}

    sport_totals = (
        df.groupby("sport_category")["sport_medals"]
        .sum()
        .reset_index()
        .nlargest(12, "sport_medals")
        .sort_values("sport_medals")
    )

    fig = px.bar(
        sport_totals,
        x="sport_medals", y="sport_category",
        orientation="h",
        color="sport_medals",
        color_continuous_scale=["#1a3a5c", "#df3e41"],
        labels={"sport_medals": "Total Medals", "sport_category": ""},
        template="plotly_dark",
    )
    fig.update_layout(coloraxis_showscale=False, **_base_layout())
    return _to_json(fig)


# ─────────────────────────────────────────────────────────────────────────────
# NEW FEATURE 1 — Medal Heatmap (Country × Year)
# ─────────────────────────────────────────────────────────────────────────────

def chart_medal_heatmap(top_n: int = 20) -> dict:
    """
    Heatmap — medal totals for the top N countries across every Olympic year.

    This is an entirely new chart type not present in the reference project.
    It uses go.Heatmap instead of px wrappers, giving finer control over
    cell colour, hover text, and axis ordering.

    Parameters
    ----------
    top_n : int
        Number of countries to include (ranked by all-time medals).
    """
    medals_df  = DATA["medals"]
    invest_df  = DATA["investment"]
    if medals_df.empty or invest_df.empty:
        return {}

    # Select top N countries by all-time medals
    top_countries = (
        invest_df.nlargest(top_n, "alltime_total_medals")["country"].tolist()
    )

    # Pivot: rows = country, cols = year
    filtered = medals_df[medals_df["country"].isin(top_countries)]
    pivot = (
        filtered.pivot_table(
            index="country", columns="year",
            values="total_medals", aggfunc="sum"
        )
        .fillna(0)
        .astype(int)
    )
    # Sort rows by total descending for visual clarity
    pivot = pivot.loc[pivot.sum(axis=1).sort_values(ascending=True).index]

    years     = [str(y) for y in pivot.columns.tolist()]
    countries = pivot.index.tolist()
    z_values  = pivot.values.tolist()

    fig = go.Figure(go.Heatmap(
        z=z_values,
        x=years,
        y=countries,
        colorscale=[
            [0.0,  "#0d2137"],
            [0.4,  "#1a5276"],
            [0.7,  "#c9a000"],
            [1.0,  "#f4c300"],
        ],
        hovertemplate="<b>%{y}</b><br>Year: %{x}<br>Medals: %{z}<extra></extra>",
        showscale=True,
        colorbar={"title": "Medals", "thickness": 14, "len": 0.8},
    ))
    fig.update_layout(
        xaxis_title="Olympic Year",
        yaxis_title="",
        template="plotly_dark",
        **_base_layout({"margin": {"t": 50, "b": 60, "l": 130, "r": 20}}),
    )
    return _to_json(fig)


# ─────────────────────────────────────────────────────────────────────────────
# NEW FEATURE 2 — Year Comparison (side-by-side top countries)
# ─────────────────────────────────────────────────────────────────────────────

def chart_year_comparison(year1: int, year2: int, top_n: int = 10) -> dict:
    """
    Grouped bar — compare the top N medal-winning countries in two selected years.

    This feature does not exist in the reference project.

    Parameters
    ----------
    year1, year2 : int   — The two Olympic years to compare.
    top_n        : int   — How many countries to include per year.
    """
    df = DATA["medals"]
    if df.empty:
        return {}

    def top_for_year(yr: int) -> pd.DataFrame:
        sub = df[df["year"] == yr][["country", "total_medals"]]
        return sub.nlargest(top_n, "total_medals")

    df1 = top_for_year(year1)
    df2 = top_for_year(year2)

    # Union of countries that appear in either year's top-N
    all_countries = sorted(set(df1["country"]) | set(df2["country"]))

    def medals_for(yr_df: pd.DataFrame, country: str) -> int:
        row = yr_df[yr_df["country"] == country]
        return int(row["total_medals"].values[0]) if not row.empty else 0

    fig = go.Figure([
        go.Bar(
            name=str(year1),
            x=all_countries,
            y=[medals_for(df1, c) for c in all_countries],
            marker_color="#f4c300",
            hovertemplate="<b>%{x}</b><br>" + str(year1) + ": %{y} medals<extra></extra>",
        ),
        go.Bar(
            name=str(year2),
            x=all_countries,
            y=[medals_for(df2, c) for c in all_countries],
            marker_color="#2196F3",
            hovertemplate="<b>%{x}</b><br>" + str(year2) + ": %{y} medals<extra></extra>",
        ),
    ])
    fig.update_layout(
        barmode="group",
        xaxis_title="Country",
        yaxis_title="Total Medals",
        xaxis_tickangle=-35,
        template="plotly_dark",
        **_base_layout(),
    )
    return _to_json(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Country deep-dive (on-demand)
# ─────────────────────────────────────────────────────────────────────────────

def chart_country_medal_history(country: str) -> dict:
    """
    Stacked bar — gold / silver / bronze per Olympic year for a specific country.
    Called on-demand when the user selects a country in the UI.
    """
    df = DATA["medals"]
    if df.empty:
        return {}

    country_df = df[df["country"] == country]
    if country_df.empty:
        return {}

    yearly = country_df.groupby("year")[["gold", "silver", "bronze"]].sum().reset_index()

    fig = go.Figure()
    medal_colours = {"gold": "#FFD700", "silver": "#C0C0C0", "bronze": "#CD7F32"}
    for medal_type in ["gold", "silver", "bronze"]:
        fig.add_trace(go.Bar(
            name=medal_type.capitalize(),
            x=yearly["year"],
            y=yearly[medal_type],
            marker_color=medal_colours[medal_type],
            hovertemplate=f"<b>%{{x}}</b><br>{medal_type.capitalize()}: %{{y}}<extra></extra>",
        ))

    fig.update_layout(
        barmode="stack",
        xaxis_title="Olympic Year",
        yaxis_title="Medals",
        template="plotly_dark",
        **_base_layout(),
    )
    return _to_json(fig)


# ─────────────────────────────────────────────────────────────────────────────
# Data-driven Insights  (NEW — replaces hard-coded HTML text)
# ─────────────────────────────────────────────────────────────────────────────

def compute_insights() -> list[dict]:
    """
    Derive 6 factual insight strings from the actual DataFrames.
    Returns a list of dicts with 'icon', 'title', 'body' keys.
    These replace the hard-coded insight cards in the original project.
    """
    medals_df  = DATA["medals"]
    invest_df  = DATA["investment"]
    athletes_df = DATA["athletes"]

    insights = []

    # 1. Top 3 nations by all-time medals
    if not invest_df.empty:
        top3 = invest_df.nlargest(3, "alltime_total_medals")["country"].tolist()
        total_pct = (
            invest_df.nlargest(3, "alltime_total_medals")["alltime_total_medals"].sum()
            / invest_df["alltime_total_medals"].sum() * 100
        )
        insights.append({
            "icon": "🏆",
            "title": "Dominant Nations",
            "body": (
                f"{', '.join(top3)} lead the all-time standings, together accounting for "
                f"{total_pct:.1f}% of all medals in the dataset."
            ),
        })

    # 2. Most efficient small nation
    if not invest_df.empty:
        most_eff = invest_df.loc[invest_df["avg_efficiency_pct"].idxmax()]
        insights.append({
            "icon": "⚡",
            "title": "Most Efficient Nation",
            "body": (
                f"{most_eff['country']} achieves the highest medal efficiency at "
                f"{most_eff['avg_efficiency_pct']:.1f}% — winning the most medals "
                f"relative to athletes sent."
            ),
        })

    # 3. Host advantage: average advantage score
    if not medals_df.empty and not DATA["games"].empty:
        games = DATA["games"]
        advantages = []
        for _, row in games.iterrows():
            host, yr = row["host_country"], row["year"]
            hd = medals_df[medals_df["country"] == host]
            if hd.empty:
                continue
            hosting = hd.loc[hd["year"] == yr, "total_medals"].sum()
            others  = hd.loc[hd["year"] != yr, "total_medals"].mean()
            if pd.notna(others) and hosting > 0:
                advantages.append(hosting - others)
        if advantages:
            avg_adv = sum(advantages) / len(advantages)
            insights.append({
                "icon": "🏠",
                "title": "Host Nation Advantage",
                "body": (
                    f"On average, host nations win {avg_adv:.1f} more medals in their "
                    f"hosting year compared to their performance in other Games."
                ),
            })

    # 4. Gender trend
    if not athletes_df.empty and "Sex" in athletes_df.columns:
        female_pct = (athletes_df["Sex"] == "F").mean() * 100
        insights.append({
            "icon": "♀️",
            "title": "Gender Representation",
            "body": (
                f"Female athletes make up {female_pct:.1f}% of all athlete records "
                f"across the analysed Games — reflecting growing gender parity in Olympic sport."
            ),
        })

    # 5. Top sport by medals
    if not athletes_df.empty and "sport_category" in athletes_df.columns:
        top_sport = (
            athletes_df.groupby("sport_category")["sport_medals"]
            .sum()
            .idxmax()
        )
        insights.append({
            "icon": "🏅",
            "title": "Highest-Medal Sport",
            "body": (
                f"{top_sport} produces the most medals of any sport category "
                f"in the dataset, reflecting the volume of events and disciplines offered."
            ),
        })

    # 6. Investment note
    if not invest_df.empty:
        corr = invest_df[["sports_investment", "alltime_total_medals"]].corr().iloc[0, 1]
        insights.append({
            "icon": "💰",
            "title": "Investment vs Returns",
            "body": (
                f"Sports investment and total medals show a Pearson correlation of "
                f"{corr:.2f} — a positive but imperfect relationship, suggesting "
                f"factors beyond spending (talent pipelines, culture) matter."
            ),
        })

    return insights
