"""Reproducible companion analysis for the Inc. 5000 (2014) Tableau dashboard.

Growth on the Inc. list is 3-year revenue growth (2010 -> 2013) and is extremely
skewed (Fuhu: +158,957%). Averages are therefore dominated by a few companies;
this script reports MEDIANS alongside means and regenerates the KPI numbers
shown on the dashboard so they can be checked.

Run: python insights.py   (needs pandas, matplotlib)
"""
from pathlib import Path
import json
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

ROOT = Path(__file__).resolve().parent
DARK, ACCENT, GREY = "#264653", "#e76f51", "#8d99ae"
plt.rcParams.update({"figure.dpi": 150, "axes.spines.top": False, "axes.spines.right": False,
                     "axes.titlelocation": "left", "axes.titleweight": "bold", "font.size": 10,
                     "text.parse_math": False})

df = pd.read_csv(ROOT / "Data Set- Inc5000 Company List_2014.csv")
df = df.drop(columns=[c for c in df.columns if c.startswith("_")])   # scraper metadata

kpi = {
    "companies": int(len(df)),
    "total_revenue_2013_usd": int(df.revenue.sum()),
    "growth_mean_pct": round(float(df.growth.mean()), 1),
    "growth_median_pct": round(float(df.growth.median()), 1),
    "growth_mean_excl_fuhu_pct": round(float(df[df.company != "Fuhu"].growth.mean()), 1),
    "workers_mean": round(float(df.workers.mean()), 1),
    "workers_median": float(df.workers.median()),
    "revenue_median_usd": int(df.revenue.median()),
    "min_growth_to_qualify_pct": round(float(df.growth.min()), 1),
    "companies_with_0_workers": int((df.workers == 0).sum()),
    "states_incl_dc_pr": int(df.state_s.nunique()),
}

ind = df.groupby("industry").agg(companies=("company", "size"), revenue_2013=("revenue", "sum"),
                                 growth_mean=("growth", "mean"), growth_median=("growth", "median"),
                                 workers=("workers", "sum"))
ind["mean_to_median"] = ind.growth_mean / ind.growth_median
ind.round(1).sort_values("growth_median", ascending=False).to_csv(ROOT / "industry_summary.csv")
by_state = df.groupby("state_s").agg(companies=("company", "size"), revenue=("revenue", "sum")) \
             .sort_values("companies", ascending=False)
by_state.to_csv(ROOT / "state_summary.csv")

# ---- Chart 1: mean vs median growth by industry ------------------------------------
p = ind.sort_values("growth_median")
fig, ax = plt.subplots(figsize=(9.5, 7))
y = range(len(p))
ax.scatter(p.growth_mean, y, color=GREY, s=22, label="Mean (what the dashboard shows)", zorder=3)
ax.scatter(p.growth_median, y, color=DARK, s=30, label="Median (typical company)", zorder=3)
for i, (a, b) in enumerate(zip(p.growth_median, p.growth_mean)):
    ax.plot([a, b], [i, i], color=GREY, lw=0.8, zorder=1)
ax.set_yticks(list(y), [f"{n} ({c})" for n, c in zip(p.index, p.companies)])
ax.set_xlabel("3-year revenue growth, 2010-2013 (%)   |   (n) = companies")
ax.legend(frameon=False, loc="lower right")
cps = ind.loc["Consumer Products & Services"]
ax.set_title(f"Industry 'average growth' is driven by outliers: Consumer Products\n"
             f"averages {cps.growth_mean:,.0f}% but its typical company grew {cps.growth_median:,.0f}%")
fig.tight_layout()
fig.savefig(ROOT / "industry_growth_mean_vs_median.png")
plt.close(fig)

# ---- Chart 2: top 10 by growth, with values -------------------------------------
top = df.nsmallest(10, "rank").iloc[::-1]
fig, ax = plt.subplots(figsize=(9.5, 4.8))
ax.barh([f"#{r} {c}" for r, c in zip(top["rank"], top.company)], top.growth / 1e3,
        color=[ACCENT if c == "Fuhu" else DARK for c in top.company])
for i, (g, rev, ind_) in enumerate(zip(top.growth, top.revenue, top.industry)):
    ax.text(g / 1e3 + 1.5, i, f"{g:,.0f}%  |  ${rev / 1e6:,.1f}M  |  {ind_}", va="center", fontsize=7.5)
ax.set_xlim(0, top.growth.max() / 1e3 * 1.75)
ax.set_xlabel("3-year revenue growth (thousands of %)")
ax.set_title("Top 10 by growth: Fuhu grew 158,957%, nearly 3x the No. 2")
fig.tight_layout()
fig.savefig(ROOT / "top10_growth.png")
plt.close(fig)

# ---- Chart 3: companies by state (top 15) -----------------------------------------
s = by_state.head(15).iloc[::-1]
fig, ax = plt.subplots(figsize=(9, 4.8))
ax.barh(s.index, s.companies, color=DARK)
for i, c in enumerate(s.companies):
    ax.text(c + 5, i, f"{c} ({c / len(df) * 100:.1f}%)", va="center", fontsize=8)
ax.set_xlabel("Companies on the 2014 list")
ax.set_title(f"California ({by_state.companies.iloc[0]}) and Texas ({by_state.companies.iloc[1]}) "
             f"hold {by_state.companies.iloc[:2].sum() / len(df) * 100:.0f}% of the list")
fig.tight_layout()
fig.savefig(ROOT / "companies_by_state.png")
plt.close(fig)

(ROOT / "kpi.json").write_text(json.dumps(kpi, indent=2))
print(json.dumps(kpi, indent=2))
print(ind.sort_values("growth_median", ascending=False).round(0).to_string())
