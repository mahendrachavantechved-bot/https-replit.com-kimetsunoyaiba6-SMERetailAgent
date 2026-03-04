import matplotlib
matplotlib.use("Agg")  # headless, no display needed
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import io, base64, random
import flet as ft

def _fig_to_b64(fig):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=100)
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode("ascii")
    plt.close(fig)
    return b64

def _chart_image(b64, height=300):
    return ft.Image(src_base64=b64, height=height, fit=ft.ImageFit.CONTAIN, expand=True)

# ── 1. Sankey-style pipeline bar chart ──────────────────────────────────────
def sankey_pipeline_diagram():
    stages = ["Intake", "KYC", "Underwriting", "Decision", "Disbursement"]
    values = [1000, 850, 700, 650, 610]
    colors = ["#4C72B0","#55A868","#C44E52","#8172B2","#CCB974"]
    fig, ax = plt.subplots(figsize=(9, 3))
    bars = ax.barh(stages, values, color=colors, edgecolor="white", height=0.6)
    for bar, val in zip(bars, values):
        ax.text(bar.get_width() + 10, bar.get_y() + bar.get_height()/2,
                str(val), va="center", fontsize=10)
    ax.set_title("Loan Pipeline Flow", fontweight="bold")
    ax.set_xlabel("Applications")
    ax.invert_yaxis()
    ax.spines[["top","right"]].set_visible(False)
    fig.tight_layout()
    return _chart_image(_fig_to_b64(fig), height=280)

# ── 2. FOIR / LTV Gauge (speedometer) ───────────────────────────────────────
def gauge_chart(value, title, low=40, high=60):
    fig, ax = plt.subplots(figsize=(4, 2.5), subplot_kw={"projection": "polar"})
    theta = np.linspace(np.pi, 0, 300)
    # background arcs
    for (lo, hi, col) in [(0,40,"#2ecc71"),(40,60,"#f39c12"),(60,100,"#e74c3c")]:
        mask = (theta >= np.pi*(1 - hi/100)) & (theta <= np.pi*(1 - lo/100))
        ax.fill_between(theta[mask], 0.6, 1.0, color=col, alpha=0.7)
    # needle
    angle = np.pi * (1 - value / 100)
    ax.annotate("", xy=(angle, 0.85), xytext=(np.pi/2, 0),
                arrowprops=dict(arrowstyle="->", color="black", lw=2))
    ax.set_yticks([])
    ax.set_xticks([])
    ax.set_title(f"{title}: {value:.1f}", fontweight="bold", pad=12)
    ax.spines["polar"].set_visible(False)
    fig.tight_layout()
    return _chart_image(_fig_to_b64(fig), height=220)

def foir_dscr_gauge(value, title="FOIR (%)"):
    return gauge_chart(value, title)

def ltv_gauge(value):
    return gauge_chart(value, "LTV (%)")

# ── 3. Radar scorecard ───────────────────────────────────────────────────────
def radar_scorecard(result):
    labels = ["CIBIL", "FOIR", "LTV", "Lead\nScore", "Risk\nScore"]
    cibil_n = (result.get("cibil_score", 700) - 300) / 500 * 100
    foir_n  = 100 - result.get("foir_post_loan", 40)
    ltv_n   = 100 - result.get("ltv_ratio", 70)
    lead    = result.get("lead_score", result.get("financial_health_score", 70))
    risk_map = {"LOW": 90, "MEDIUM": 55, "HIGH": 20}
    risk_n  = risk_map.get(result.get("risk", "MEDIUM"), 55)
    values  = [cibil_n, foir_n, ltv_n, lead, risk_n]

    N = len(labels)
    angles = [n / float(N) * 2 * np.pi for n in range(N)]
    angles += angles[:1]
    values += values[:1]

    fig, ax = plt.subplots(figsize=(4, 4), subplot_kw={"polar": True})
    ax.plot(angles, values, "o-", linewidth=2, color="#4C72B0")
    ax.fill(angles, values, alpha=0.25, color="#4C72B0")
    ax.set_xticks(angles[:-1])
    ax.set_xticklabels(labels, size=9)
    ax.set_ylim(0, 100)
    ax.set_title("Risk Scorecard", fontweight="bold", pad=15)
    fig.tight_layout()
    return _chart_image(_fig_to_b64(fig), height=280)

# ── 4. DPD trend ─────────────────────────────────────────────────────────────
def dpd_trend_chart():
    months = ["Jan", "Feb", "Mar", "Apr", "May", "Jun"]
    d0  = [600, 580, 550, 520, 500, 470]
    d30 = [200, 210, 195, 185, 180, 170]
    d60 = [80,  75,  70,  65,  60,  55]
    fig, ax = plt.subplots(figsize=(7, 3))
    ax.plot(months, d0,  "o-", label="0-30 DPD",  color="#2ecc71")
    ax.plot(months, d30, "s-", label="31-60 DPD", color="#f39c12")
    ax.plot(months, d60, "^-", label="61-90 DPD", color="#e74c3c")
    ax.set_title("DPD Bucket Trend", fontweight="bold")
    ax.legend(fontsize=8)
    ax.spines[["top","right"]].set_visible(False)
    fig.tight_layout()
    return _chart_image(_fig_to_b64(fig), height=240)

# ── 5. Portfolio treemap (via nested bar) ────────────────────────────────────
def portfolio_treemap():
    cities  = ["Bengaluru", "Mumbai", "Delhi", "Hyderabad", "Chennai"]
    amounts = [150, 120, 100, 80, 60]
    colors  = ["#4C72B0","#55A868","#C44E52","#8172B2","#CCB974"]
    fig, ax = plt.subplots(figsize=(7, 3))
    bars = ax.bar(cities, amounts, color=colors, edgecolor="white", width=0.6)
    for bar, amt in zip(bars, amounts):
        ax.text(bar.get_x() + bar.get_width()/2, bar.get_height() + 2,
                f"₹{amt}Cr", ha="center", fontsize=9, fontweight="bold")
    ax.set_title("Portfolio by City (₹ Crore)", fontweight="bold")
    ax.spines[["top","right"]].set_visible(False)
    ax.set_ylim(0, max(amounts) * 1.2)
    fig.tight_layout()
    return _chart_image(_fig_to_b64(fig), height=240)

# ── 6. Network graph ─────────────────────────────────────────────────────────
def cambridge_network(applicant):
    import networkx as nx
    G = nx.complete_graph(6)
    pos = nx.spring_layout(G, seed=42)
    labels = {0: applicant.get("name", "Applicant")[:12],
              1: "Director 1", 2: "Director 2",
              3: "Supplier A", 4: "Bank X", 5: "GST Portal"}
    colors_map = ["#e74c3c"] + ["#4C72B0"]*2 + ["#55A868"]*2 + ["#f39c12"]
    fig, ax = plt.subplots(figsize=(6, 4))
    nx.draw_networkx(G, pos, ax=ax, labels=labels,
                     node_color=colors_map, node_size=1200,
                     font_size=7, font_color="white",
                     edge_color="#aaaaaa", width=0.8)
    ax.set_title("Entity Relationship Network", fontweight="bold")
    ax.axis("off")
    fig.tight_layout()
    return _chart_image(_fig_to_b64(fig), height=300)
