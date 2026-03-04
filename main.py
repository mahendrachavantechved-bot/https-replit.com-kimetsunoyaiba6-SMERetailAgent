# main.py — Enterprise Loan Intelligence Dashboard
# Replit-compatible: matplotlib charts, flet 0.24.1, Sarvam STT + Translate

import flet as ft
import json, os, random, time, threading, base64, io
from data_generator import generate_retail_samples, generate_sme_samples
from pipelines import RetailPipeline, SMEPipeline
from sarvam_utils import stt_from_file, translate_to_hindi

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import numpy as np
import pandas as pd

# ── Load or generate data ────────────────────────────────────────────────────
def load_data():
    try:
        with open("retail_applicants.json") as f: retail = json.load(f)
        with open("sme_applicants.json")   as f: sme    = json.load(f)
    except FileNotFoundError:
        retail = generate_retail_samples()
        sme    = generate_sme_samples()
    return retail, sme

retail_all, sme_all = load_data()

# ── Chart helpers ────────────────────────────────────────────────────────────
PALETTE = ["#6C5CE7","#00CEC9","#FD79A8","#FDCB6E","#55EFC4","#E17055","#74B9FF","#A29BFE"]

def _b64(fig, dpi=100):
    buf = io.BytesIO()
    fig.savefig(buf, format="png", bbox_inches="tight", dpi=dpi,
                facecolor=fig.get_facecolor())
    buf.seek(0)
    b64 = base64.b64encode(buf.read()).decode()
    plt.close(fig)
    return b64

def _img(b64, h=280):
    return ft.Image(src_base64=b64, height=h, fit=ft.ImageFit.CONTAIN, expand=True)

def _dark_fig(w=8, h=3.5):
    fig, ax = plt.subplots(figsize=(w,h))
    fig.patch.set_facecolor("#1E1E2E")
    ax.set_facecolor("#2A2A3E")
    for spine in ax.spines.values(): spine.set_color("#444466")
    ax.tick_params(colors="#AAAACC", labelsize=9)
    ax.xaxis.label.set_color("#AAAACC")
    ax.yaxis.label.set_color("#AAAACC")
    ax.title.set_color("#FFFFFF")
    return fig, ax

def chart_pipeline_flow(is_retail=True):
    stages = ["Intake","KYC","Bureau","Underwriting","Decision","Sanction","Disbursed"]
    vals   = [1200,1050,920,850,700,640,580] if is_retail else [800,720,650,580,510,460,400]
    colors = PALETTE[:7]
    fig, ax = _dark_fig(9, 3.2)
    bars = ax.barh(stages, vals, color=colors, edgecolor="#1E1E2E", height=0.65)
    for bar, v in zip(bars, vals):
        ax.text(bar.get_width()+12, bar.get_y()+bar.get_height()/2,
                f"{v:,}", va="center", color="#FFFFFF", fontsize=9, fontweight="bold")
    ax.set_title(f"{'Retail' if is_retail else 'SME'} Pipeline Flow", fontsize=13, fontweight="bold")
    ax.invert_yaxis(); ax.set_xlabel("Applications", color="#AAAACC")
    ax.set_xlim(0, max(vals)*1.15)
    for bar in bars:
        bar.set_alpha(0.88)
    fig.tight_layout()
    return _img(_b64(fig), 280)

def chart_gauge(value, title, max_val=100, good_max=40, warn_max=60):
    fig, ax = plt.subplots(figsize=(4,2.8), subplot_kw={"projection":"polar"})
    fig.patch.set_facecolor("#1E1E2E"); ax.set_facecolor("#1E1E2E")
    theta = np.linspace(np.pi, 0, 300)
    for lo, hi, col in [(0,good_max,"#55EFC4"),(good_max,warn_max,"#FDCB6E"),(warn_max,max_val,"#E17055")]:
        mask = (theta >= np.pi*(1-hi/max_val)) & (theta <= np.pi*(1-lo/max_val))
        ax.fill_between(theta[mask], 0.55, 1.0, color=col, alpha=0.85)
    angle = np.pi*(1-min(value,max_val)/max_val)
    ax.annotate("", xy=(angle,0.82), xytext=(np.pi/2,0.02),
                arrowprops=dict(arrowstyle="->",color="white",lw=2.5))
    ax.set_yticks([]); ax.set_xticks([])
    ax.spines["polar"].set_visible(False)
    ax.set_title(f"{title}\n{value:.1f}", color="white", fontsize=12, fontweight="bold", pad=10)
    fig.tight_layout()
    return _img(_b64(fig), 220)

def chart_radar(result, is_retail=True):
    if is_retail:
        labels = ["CIBIL","FOIR\n(inv)","LTV\n(inv)","Lead\nScore","Decision"]
        vals   = [
            (result.get("cibil_score",700)-300)/5,
            100-result.get("foir_post_loan",40),
            100-result.get("ltv_ratio",70),
            result.get("lead_score",70),
            {"LOW":90,"MEDIUM":60,"HIGH":25}.get(result.get("risk","MEDIUM"),60)
        ]
    else:
        labels = ["CIBIL","DSCR","Vintage","Health","Decision"]
        vals   = [
            (result.get("cibil_score",700)-300)/5,
            result.get("dscr",1.5)*25,
            min(100,result.get("vintage_years",5)*5),
            result.get("financial_health_score",70),
            {"LOW":90,"MEDIUM":60,"HIGH":25}.get(result.get("risk","MEDIUM"),60)
        ]
    N = len(labels)
    angles = [n/N*2*np.pi for n in range(N)]+[0]
    vals   = vals+[vals[0]]
    fig, ax = plt.subplots(figsize=(4.5,4.5), subplot_kw={"polar":True})
    fig.patch.set_facecolor("#1E1E2E"); ax.set_facecolor("#2A2A3E")
    ax.plot(angles, vals, "o-", lw=2, color="#6C5CE7")
    ax.fill(angles, vals, alpha=0.3, color="#6C5CE7")
    ax.set_xticks(angles[:-1]); ax.set_xticklabels(labels, color="white", size=9)
    ax.set_ylim(0,100); ax.tick_params(colors="#555577")
    ax.set_title("Risk Scorecard", color="white", fontsize=12, fontweight="bold", pad=15)
    ax.spines["polar"].set_color("#444466")
    fig.tight_layout()
    return _img(_b64(fig), 300)

def chart_dpd():
    months = ["Jan","Feb","Mar","Apr","May","Jun"]
    d = {"0–30 DPD":[620,580,550,520,490,460],
         "31–60 DPD":[140,130,120,110,100,90],
         "61–90 DPD":[60,55,50,45,40,35],
         "90+ DPD":[30,28,25,22,20,18]}
    fig, ax = _dark_fig(7,3.2)
    for (label,vals),col in zip(d.items(), ["#55EFC4","#FDCB6E","#E17055","#FD79A8"]):
        ax.plot(months, vals, "o-", label=label, color=col, lw=2.2, markersize=5)
    ax.set_title("DPD Bucket Trend", fontsize=13, fontweight="bold")
    ax.legend(fontsize=8, labelcolor="white", facecolor="#2A2A3E", edgecolor="#444466")
    fig.tight_layout()
    return _img(_b64(fig), 260)

def chart_portfolio(by="city"):
    if by == "city":
        labels = ["Bengaluru","Mumbai","Delhi","Hyderabad","Chennai"]
        vals   = [145,122,98,76,59]
        title  = "Portfolio by City (₹ Cr)"
    else:
        labels = ["IT","Manufacturing","Retail","Healthcare","Logistics"]
        vals   = [180,140,105,88,67]
        title  = "Portfolio by Industry (₹ Cr)"
    fig, ax = _dark_fig(7,3.2)
    colors = PALETTE[:len(labels)]
    wedges, texts, autotexts = ax.pie(vals, labels=labels, colors=colors,
                                       autopct="%1.0f%%", startangle=140,
                                       textprops={"color":"white","fontsize":9},
                                       pctdistance=0.75,
                                       wedgeprops={"edgecolor":"#1E1E2E","linewidth":2})
    for at in autotexts: at.set_color("white"); at.set_fontsize(8)
    ax.set_title(title, fontsize=13, fontweight="bold", color="white")
    fig.tight_layout()
    return _img(_b64(fig), 270)

def chart_rejection():
    reasons = ["Low CIBIL","High FOIR","High LTV","Low Vintage","Fraud Flag","Doc Missing"]
    counts  = [320,185,140,90,65,45]
    fig, ax = _dark_fig(7,3)
    colors  = ["#E17055","#FDCB6E","#FD79A8","#A29BFE","#6C5CE7","#74B9FF"]
    bars = ax.bar(reasons, counts, color=colors, edgecolor="#1E1E2E", width=0.65)
    for bar,v in zip(bars,counts):
        ax.text(bar.get_x()+bar.get_width()/2, bar.get_height()+5,
                str(v), ha="center", color="white", fontsize=9, fontweight="bold")
    ax.set_title("Rejection Reasons", fontsize=13, fontweight="bold")
    ax.set_ylim(0, max(counts)*1.18)
    fig.tight_layout()
    return _img(_b64(fig), 260)

def chart_network(applicant):
    import networkx as nx
    G  = nx.complete_graph(6)
    pos= nx.spring_layout(G, seed=42)
    node_labels = {0:applicant.get("name","Applicant")[:10],
                   1:"Director A",2:"Director B",
                   3:"Bank X",4:"Supplier",5:"GST Portal"}
    node_colors = ["#E17055","#6C5CE7","#6C5CE7","#00CEC9","#55EFC4","#FDCB6E"]
    fig, ax = plt.subplots(figsize=(6,4))
    fig.patch.set_facecolor("#1E1E2E"); ax.set_facecolor("#1E1E2E")
    nx.draw_networkx(G, pos, ax=ax, labels=node_labels,
                     node_color=node_colors, node_size=1400,
                     font_size=7, font_color="white",
                     edge_color="#555577", width=1.2, alpha=0.9)
    ax.set_title("Entity Network", color="white", fontsize=12, fontweight="bold")
    ax.axis("off"); fig.tight_layout()
    return _img(_b64(fig), 300)

# ════════════════════════════════════════════════════════════════════════════
# FLET APP
# ════════════════════════════════════════════════════════════════════════════
BG      = "#13131F"
CARD_BG = "#1E1E2E"
ACCENT  = "#6C5CE7"
ACCENT2 = "#00CEC9"
TEXT    = "#E8E8FF"
SUBTEXT = "#9090BB"

def card(content, padding=14, bgcolor=CARD_BG, radius=14, expand=False):
    return ft.Container(content=content, bgcolor=bgcolor, border_radius=radius,
                        padding=padding, expand=expand,
                        shadow=ft.BoxShadow(blur_radius=12, color="#00000055",
                                            offset=ft.Offset(0,4)))

def label(text, size=12, color=SUBTEXT, bold=False):
    return ft.Text(text, size=size, color=color,
                   weight=ft.FontWeight.BOLD if bold else ft.FontWeight.NORMAL)

def heading(text, size=16):
    return ft.Text(text, size=size, color=TEXT, weight=ft.FontWeight.BOLD)

def kv_row(k, v, accent=False):
    return ft.Row([
        ft.Text(k, size=12, color=SUBTEXT, expand=2),
        ft.Text(str(v), size=12, color=ACCENT2 if accent else TEXT,
                weight=ft.FontWeight.W_500, expand=3),
    ])

def chip(text, color):
    return ft.Container(ft.Text(text, size=11, color="white", weight=ft.FontWeight.BOLD),
                        bgcolor=color, border_radius=20, padding=ft.padding.symmetric(4,10))

def main(page: ft.Page):
    page.title       = "Enterprise Loan Intelligence"
    page.theme_mode  = ft.ThemeMode.DARK
    page.bgcolor     = BG
    page.padding     = 0
    page.fonts       = {}
    page.window_width  = 1440
    page.window_height = 900

    # ── Shared state ─────────────────────────────────────────────────────────
    sel = {"data": None, "is_retail": True}
    picked_wav = [None]

    # ── Live ticker ───────────────────────────────────────────────────────────
    live_val  = ft.Text("Risk Index: —", size=12, color=ACCENT2, weight=ft.FontWeight.BOLD)
    live_time = ft.Text("", size=11, color=SUBTEXT)
    def _ticker():
        while True:
            live_val.value  = f"🔴 Live Risk Index: {random.randint(480,820)}"
            live_time.value = time.strftime("Updated %H:%M:%S")
            try: page.update()
            except: pass
            time.sleep(3)
    threading.Thread(target=_ticker, daemon=True).start()

    # ── File picker ───────────────────────────────────────────────────────────
    def on_file_picked(e):
        if e.files:
            picked_wav[0] = e.files[0].path
            voice_status.value = f"📎 Loaded: {e.files[0].name}"
            page.update()
    file_picker = ft.FilePicker(on_result=on_file_picked)
    page.overlay.append(file_picker)

    # ── Detail panel ─────────────────────────────────────────────────────────
    detail_col     = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=6, expand=True)
    dashboard_col  = ft.Column(scroll=ft.ScrollMode.AUTO, spacing=16, expand=True)
    translate_out  = ft.Text("", size=13, color="#FDCB6E", italic=True)
    voice_status   = ft.Text("", size=11, color=SUBTEXT)
    stt_out        = ft.TextField(label="STT Output", multiline=True, min_lines=2,
                                  read_only=True, bgcolor="#2A2A3E",
                                  border_color=ACCENT, color=TEXT, label_style=ft.TextStyle(color=SUBTEXT))

    def show_detail(app, is_retail=True):
        sel["data"] = app; sel["is_retail"] = is_retail
        risk_color  = {"LOW":"#55EFC4","MEDIUM":"#FDCB6E","HIGH":"#E17055"}.get(app.get("risk",""),"#888")
        decision    = app.get("decision","")
        dec_color   = {"APPROVED":"#55EFC4","REVIEW":"#FDCB6E","REJECTED":"#E17055"}.get(decision,"#888")

        rows  = []
        skip  = {"id","risk","decision","lead_score","financial_health_score","recommended_rate"}
        for k,v in app.items():
            if k in skip: continue
            rows.append(kv_row(k.replace("_"," ").title(), v,
                               accent=k in ("pan","gstin","cibil_score","loan_amt")))

        detail_col.controls.clear()
        detail_col.controls.extend([
            ft.Row([
                ft.Text(app["name"], size=15, color=TEXT, weight=ft.FontWeight.BOLD, expand=True),
                chip(app["id"], ACCENT),
            ]),
            ft.Divider(color="#333355", height=1),
            *rows,
            ft.Divider(color="#333355", height=1),
        ])
        if app.get("risk"):
            detail_col.controls.append(
                ft.Row([chip(f"Risk: {app['risk']}", risk_color),
                        chip(f"Decision: {decision}", dec_color)], spacing=8))
        if app.get("recommended_rate"):
            detail_col.controls.append(kv_row("Recommended Rate", f"{app['recommended_rate']}%", accent=True))
        detail_col.controls.append(translate_out)
        page.update()

    def process_and_show(e):
        app = sel.get("data")
        if not app:
            page.snack_bar = ft.SnackBar(ft.Text("⚠️ Select an applicant first!",color="#FDCB6E"),
                                          bgcolor=CARD_BG); page.snack_bar.open=True; page.update(); return
        is_retail = sel["is_retail"]
        result = (RetailPipeline() if is_retail else SMEPipeline()).run(app)
        sel["data"] = result
        show_detail(result, is_retail)

        risk   = result.get("risk","MEDIUM")
        r_col  = {"LOW":"#55EFC4","MEDIUM":"#FDCB6E","HIGH":"#E17055"}.get(risk,"#888")
        dec    = result.get("decision","—")
        d_col  = {"APPROVED":"#55EFC4","REVIEW":"#FDCB6E","REJECTED":"#E17055"}.get(dec,"#888")

        dashboard_col.controls.clear()
        dashboard_col.controls.append(
            ft.Row([
                card(ft.Column([label("DECISION",10), ft.Text(dec,size=22,color=d_col,weight=ft.FontWeight.BOLD)]),
                     bgcolor=CARD_BG),
                card(ft.Column([label("RISK LEVEL",10), ft.Text(risk,size=22,color=r_col,weight=ft.FontWeight.BOLD)]),
                     bgcolor=CARD_BG),
                card(ft.Column([label("RATE",10), ft.Text(f"{result.get('recommended_rate','—')}%",size=22,color=ACCENT2,weight=ft.FontWeight.BOLD)]),
                     bgcolor=CARD_BG),
                card(ft.Column([label("SCORE",10),
                                ft.Text(str(result.get("lead_score",result.get("financial_health_score","—"))),
                                        size=22,color=ACCENT,weight=ft.FontWeight.BOLD)]),
                     bgcolor=CARD_BG),
            ], spacing=12, wrap=True)
        )
        # Charts
        dashboard_col.controls.extend([
            heading("Pipeline Flow"),
            card(chart_pipeline_flow(is_retail), padding=8),
            ft.Row([
                ft.Column([heading("FOIR Gauge"), card(chart_gauge(result.get("foir_post_loan",38),"FOIR %"), padding=8)], expand=1),
                ft.Column([heading("LTV Gauge"),  card(chart_gauge(result.get("ltv_ratio",68),"LTV %",good_max=60,warn_max=75), padding=8)], expand=1),
            ], spacing=12),
            ft.Row([
                ft.Column([heading("Risk Scorecard"), card(chart_radar(result, is_retail), padding=8)], expand=1),
                ft.Column([heading("Entity Network"),  card(chart_network(result), padding=8)], expand=1),
            ], spacing=12),
            heading("DPD Trend"),
            card(chart_dpd(), padding=8),
            ft.Row([
                ft.Column([heading("Portfolio by City"),     card(chart_portfolio("city"),     padding=8)], expand=1),
                ft.Column([heading("Portfolio by Industry"), card(chart_portfolio("industry"), padding=8)], expand=1),
            ], spacing=12),
            heading("Rejection Analysis"),
            card(chart_rejection(), padding=8),
        ])
        page.tabs.selected_index = 2
        page.update()

    def do_translate(e):
        app = sel.get("data")
        if not app: return
        snippet = (f"Applicant {app.get('name')} from {app.get('city','')}, "
                   f"loan ₹{app.get('loan_amt',''):,}, CIBIL {app.get('cibil_score','')}, "
                   f"risk {app.get('risk','')}, decision {app.get('decision','')}")
        translate_out.value = "⏳ Translating to Hindi..."
        page.update()
        hindi = translate_to_hindi(snippet)
        translate_out.value = f"🇮🇳 {hindi}"
        page.update()

    def do_stt(e):
        if not picked_wav[0]:
            voice_status.value = "❌ Pick a WAV file first"
            page.update(); return
        voice_status.value = "⏳ Transcribing..."
        page.update()
        result = stt_from_file(picked_wav[0])
        stt_out.value  = result
        voice_status.value = "✅ Done"
        page.update()

    # ════════════════════════════════════════════════════════════════════════
    # SEARCHABLE APPLICANT LIST
    # ════════════════════════════════════════════════════════════════════════
    def build_tab(all_data, is_retail, filter_key):
        search = ft.TextField(hint_text=f"Search name / {filter_key} / city…",
                              prefix_icon=ft.icons.SEARCH,
                              bgcolor="#2A2A3E", border_color=ACCENT,
                              color=TEXT, hint_style=ft.TextStyle(color=SUBTEXT),
                              height=44, expand=True,
                              border_radius=10)
        list_v = ft.ListView(expand=True, spacing=6, padding=ft.padding.only(top=6))

        def render(data):
            list_v.controls.clear()
            for app in data[:120]:
                fk_val = app.get(filter_key,"")
                def _click(e, a=app):
                    show_detail(a, is_retail)
                list_v.controls.append(
                    ft.Container(
                        content=ft.Column([
                            ft.Row([
                                ft.Text(app["name"], size=13, color=TEXT,
                                        weight=ft.FontWeight.W_600, expand=True),
                                chip(app["id"], ACCENT),
                            ]),
                            ft.Row([
                                label(f"₹{app['loan_amt']:,}", 11, ACCENT2),
                                label("·", 11), label(f"CIBIL {app['cibil_score']}", 11, "#A29BFE"),
                                label("·", 11), label(str(fk_val), 11, SUBTEXT),
                            ], spacing=4),
                        ], spacing=3),
                        bgcolor=CARD_BG, border_radius=10, padding=10,
                        on_click=_click,
                        ink=True,
                        border=ft.border.all(1,"#2E2E4A"),
                    )
                )
            page.update()

        def on_search(e):
            q = search.value.strip().lower()
            f = [a for a in all_data if
                 q in a["name"].lower() or q in a.get(filter_key,"").lower()
                 or q in a.get("city","").lower()] if q else all_data
            render(f)

        search.on_change = on_search
        render(all_data)

        voice_row = ft.Column([
            ft.Row([
                ft.ElevatedButton("📎 Pick WAV",
                    on_click=lambda _: file_picker.pick_files(allowed_extensions=["wav"]),
                    bgcolor="#2A2A3E", color=TEXT),
                ft.ElevatedButton("🎙 Transcribe",
                    on_click=do_stt, bgcolor=ACCENT, color="white"),
            ], spacing=8),
            voice_status, stt_out,
        ], spacing=6)

        return ft.Row([
            # LEFT: search + list
            ft.Container(
                ft.Column([search,
                           ft.Container(list_v, expand=True)],
                          expand=True, spacing=8),
                width=380, padding=10,
                bgcolor=CARD_BG, border_radius=14,
            ),
            # RIGHT: detail + controls
            ft.Container(
                ft.Column([
                    ft.Row([
                        ft.ElevatedButton("⚙ Process",
                            on_click=process_and_show, bgcolor=ACCENT, color="white", height=40),
                        ft.ElevatedButton("🇮🇳 Translate",
                            on_click=do_translate, bgcolor="#8E44AD", color="white", height=40),
                    ], spacing=10),
                    ft.Divider(color="#333355"),
                    ft.Container(detail_col, expand=True,
                                 bgcolor=CARD_BG, border_radius=12, padding=12),
                    voice_row,
                ], expand=True, spacing=10),
                expand=True, padding=10,
            ),
        ], expand=True, vertical_alignment=ft.CrossAxisAlignment.START, spacing=12)

    retail_tab_content = build_tab(retail_all, True,  "city")
    sme_tab_content    = build_tab(sme_all,    False, "industry")

    # ════════════════════════════════════════════════════════════════════════
    # DASHBOARD TAB
    # ════════════════════════════════════════════════════════════════════════
    dashboard_tab = ft.Container(
        ft.Column([
            ft.Text("Process an applicant from Retail or SME tab to see the full dashboard.",
                    size=15, color=SUBTEXT, italic=True),
            ft.Container(dashboard_col, expand=True, padding=4),
        ], scroll=ft.ScrollMode.AUTO, expand=True),
        expand=True, padding=12,
    )

    # ════════════════════════════════════════════════════════════════════════
    # PAGE LAYOUT
    # ════════════════════════════════════════════════════════════════════════
    tabs = ft.Tabs(
        selected_index=0, animation_duration=250, expand=True,
        label_color=ACCENT2, unselected_label_color=SUBTEXT,
        indicator_color=ACCENT,
        tabs=[
            ft.Tab(text="🏦  Retail Loans",
                   content=ft.Container(retail_tab_content, padding=ft.padding.symmetric(12,8), expand=True)),
            ft.Tab(text="🏢  SME Loans",
                   content=ft.Container(sme_tab_content,   padding=ft.padding.symmetric(12,8), expand=True)),
            ft.Tab(text="📊  Dashboard",
                   content=dashboard_tab),
        ],
    )
    page.tabs = tabs

    header = ft.Container(
        ft.Row([
            ft.Container(width=6, height=36, bgcolor=ACCENT, border_radius=3),
            ft.Column([
                ft.Text("Enterprise Loan Intelligence", size=19, color=TEXT, weight=ft.FontWeight.BOLD),
                ft.Text("Retail & SME Loan Processing Dashboard", size=11, color=SUBTEXT),
            ], spacing=1),
            ft.Container(expand=True),
            ft.Column([live_val, live_time], spacing=2, horizontal_alignment=ft.CrossAxisAlignment.END),
        ], spacing=12, vertical_alignment=ft.CrossAxisAlignment.CENTER),
        bgcolor=CARD_BG, padding=ft.padding.symmetric(14,20),
        shadow=ft.BoxShadow(blur_radius=10, color="#00000044", offset=ft.Offset(0,3)),
    )

    page.add(ft.Column([header, ft.Container(tabs, expand=True, padding=ft.padding.symmetric(0,8))],
                       spacing=0, expand=True))

if __name__ == "__main__":
    ft.app(target=main, port=8000, view=ft.WEB_BROWSER)
