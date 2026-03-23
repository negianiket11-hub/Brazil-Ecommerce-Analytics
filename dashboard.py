import warnings
warnings.filterwarnings("ignore")

import pandas as pd
import numpy as np
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import streamlit as st
import requests

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(
    page_title="Brazil E-Commerce Dashboard",
    page_icon="🇧🇷",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ── Theme ──────────────────────────────────────────────────────────────────────
CYAN   = "#00D4FF"
GREEN  = "#10B981"
AMBER  = "#F59E0B"
PURPLE = "#7C3AED"
RED    = "#EF4444"
PINK   = "#EC4899"
BG     = "#0A0E1A"
CARD   = "#0F1629"

TEMPLATE = "plotly_dark"
LAYOUT   = dict(template=TEMPLATE, paper_bgcolor=BG, plot_bgcolor=CARD,
                font=dict(family="Inter, system-ui, sans-serif", color="#E2E8F0"),
                margin=dict(l=40, r=40, t=60, b=40))

def insight(title, color, points, takeaway=None):
    glow = color + "22"
    pts_html = "".join(f'<div class="insight-point">{p}</div>' for p in points)
    ta_html  = (f'<div class="insight-takeaway" style="--accent:{color};--accent-glow:{glow};">'
                f'💡 <strong>Key Takeaway:</strong> {takeaway}</div>') if takeaway else ""
    st.markdown(
        f'<div class="insight-box" style="--accent:{color};--accent-glow:{glow};">'
        f'<div class="insight-title">📊 {title}</div>'
        f'<div class="insight-grid">{pts_html}</div>'
        f'{ta_html}</div>',
        unsafe_allow_html=True)

def apply_layout(fig, height=420, extra=None):
    cfg = {**LAYOUT, "height": height}
    if extra:
        cfg.update(extra)
    fig.update_layout(**cfg)
    return fig

def section(title):
    st.markdown(f'<div class="section-title">{title}</div>', unsafe_allow_html=True)

# ── CSS ────────────────────────────────────────────────────────────────────────
st.markdown("""
<style>
  html, body, [data-testid="stAppViewContainer"],
  [data-testid="stHeader"], .main { background: #0A0E1A !important; color: #E2E8F0; }
  [data-testid="block-container"] { padding-top: 1rem; }
  /* fixed sidebar — always visible, no toggle button */
  [data-testid="stSidebar"] {
    background: #0F1629 !important;
    border-right: 1px solid #1E2A45 !important;
    min-width: 280px !important;
    max-width: 280px !important;
    transform: none !important;
    visibility: visible !important;
  }
  [data-testid="stSidebar"] * { color: #E2E8F0 !important; }
  /* hide all collapse/expand toggle buttons */
  [data-testid="collapsedControl"],
  [data-testid="stSidebarCollapseButton"],
  button[aria-label="Close sidebar"],
  button[aria-label="Open sidebar"] { display: none !important; }

  .kpi-card {
    background: #0F1629; border: 1px solid #1E2A45; border-radius: 14px;
    padding: 20px 16px; text-align: center; box-shadow: 0 0 18px var(--glow);
    transition: transform .2s, box-shadow .2s;
  }
  .kpi-card:hover { transform: translateY(-3px); box-shadow: 0 0 32px var(--glow); }
  .kpi-value { font-size: 1.7rem; font-weight: 800; color: var(--glow); }
  .kpi-label { font-size: .78rem; color: #94A3B8; margin-top: 4px;
               text-transform: uppercase; letter-spacing: .06em; }

  .section-title {
    font-size: 1rem; font-weight: 700; color: #94A3B8;
    text-transform: uppercase; letter-spacing: .1em;
    border-left: 3px solid #00D4FF; padding-left: 10px; margin: 28px 0 10px;
  }
  .filter-badge {
    display:inline-block; background:#1E2A45; color:#00D4FF;
    border-radius:20px; padding:3px 12px; font-size:.75rem;
    margin:2px; border:1px solid #00D4FF33;
  }
  #MainMenu, footer { visibility: hidden; }
  [data-testid="stToolbar"] { display: none; }

  /* Insight cards */
  .insight-box {
    background: #0F1629;
    border-left: 4px solid var(--accent);
    border-radius: 0 12px 12px 0;
    padding: 16px 20px;
    margin: 14px 0 6px;
    box-shadow: -2px 0 18px var(--accent-glow);
  }
  .insight-title {
    font-size: .85rem; font-weight: 800; letter-spacing: .08em;
    text-transform: uppercase; color: var(--accent); margin-bottom: 10px;
  }
  .insight-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(260px, 1fr)); gap: 10px; }
  .insight-point {
    background: #151f38; border-radius: 8px; padding: 10px 14px;
    font-size: .82rem; line-height: 1.55; color: #CBD5E1;
    border: 1px solid #1E2A4520;
  }
  .insight-point strong { color: #E2E8F0; }
  .insight-takeaway {
    margin-top: 12px; padding: 10px 16px;
    background: linear-gradient(90deg, var(--accent-glow), transparent);
    border-radius: 8px; font-size: .82rem; color: #E2E8F0;
    border-left: 3px solid var(--accent);
  }
</style>
""", unsafe_allow_html=True)

# ── Load raw data (cached) ────────────────────────────────────────────────────
@st.cache_data
def load_raw():
    DATE_COLS = [
        "order_purchase_timestamp","order_approved_at",
        "order_delivered_carrier_date","order_delivered_customer_date",
        "order_estimated_delivery_date","shipping_limit_date",
        "review_creation_date","review_answer_timestamp",
    ]
    df = pd.read_csv("main_dataset_clean.csv", parse_dates=DATE_COLS)
    df["freight_pct"] = (df["freight_value"] /
                         (df["price"] + df["freight_value"]).replace(0, np.nan) * 100)
    df["month"]       = df["order_purchase_timestamp"].dt.to_period("M")
    df["year"]        = df["order_purchase_timestamp"].dt.year
    df["month_num"]   = df["order_purchase_timestamp"].dt.month
    return df

@st.cache_data
def load_geojson():
    url = ("https://raw.githubusercontent.com/codeforamerica/click_that_hood"
           "/master/public/data/brazil-states.geojson")
    try:
        return requests.get(url, timeout=20).json()
    except Exception:
        return None

df_raw   = load_raw()
geojson  = load_geojson()

# ════════════════════════════════════════════════════════════════════════════════
# SIDEBAR — FILTERS
# ════════════════════════════════════════════════════════════════════════════════
with st.sidebar:
    st.markdown("""
    <div style="text-align:center; padding:10px 0 20px;">
      <div style="font-size:1.6rem;">🇧🇷</div>
      <div style="font-weight:800; font-size:1rem; color:#00D4FF;">Dashboard Filters</div>
      <div style="font-size:.75rem; color:#475569; margin-top:4px;">All charts update live</div>
    </div>""", unsafe_allow_html=True)

    st.markdown("---")

    # 1. Date range
    st.markdown("**📅 Date Range**")
    min_date = df_raw["order_purchase_timestamp"].min().to_pydatetime()
    max_date = df_raw["order_purchase_timestamp"].max().to_pydatetime()
    date_range = st.date_input(
        "Select date range",
        value=(min_date, max_date),
        min_value=min_date, max_value=max_date,
        label_visibility="collapsed",
    )

    st.markdown("---")

    # 2. Order Status
    st.markdown("**📦 Order Status**")
    all_statuses = sorted(df_raw["order_status"].dropna().unique().tolist())
    sel_status = st.multiselect("Status", all_statuses, default=all_statuses,
                                 label_visibility="collapsed")

    st.markdown("---")

    # 3. Customer State
    st.markdown("**📍 Customer State**")
    all_states = sorted(df_raw["customer_state"].dropna().unique().tolist())
    sel_states = st.multiselect("States", all_states, default=all_states,
                                 label_visibility="collapsed")

    st.markdown("---")

    # 4. Product Category
    st.markdown("**🏷️ Product Category**")
    all_cats = sorted(df_raw["product_category_name_english"].dropna().unique().tolist())
    sel_cats = st.multiselect("Categories", all_cats, default=all_cats,
                               label_visibility="collapsed",
                               placeholder="All categories")

    st.markdown("---")

    # 5. Payment Type
    st.markdown("**💳 Payment Type**")
    all_pay = sorted(df_raw["payment_type"].dropna().unique().tolist())
    sel_pay = st.multiselect("Payment", all_pay, default=all_pay,
                              label_visibility="collapsed")

    st.markdown("---")

    # 6. Price range
    st.markdown("**💵 Price Range (R$)**")
    p_min = float(df_raw["price"].min())
    p_max = float(df_raw["price"].max())
    price_range = st.slider("Price range", p_min, p_max,
                             (p_min, p_max), step=10.0,
                             label_visibility="collapsed")

    st.markdown("---")

    # Reset button
    if st.button("🔄 Reset All Filters", use_container_width=True):
        st.rerun()

# ── Apply filters ──────────────────────────────────────────────────────────────
start_dt = pd.Timestamp(date_range[0]) if len(date_range) == 2 else pd.Timestamp(min_date)
end_dt   = pd.Timestamp(date_range[1]) if len(date_range) == 2 else pd.Timestamp(max_date)

df = df_raw.copy()
df = df[df["order_purchase_timestamp"].between(start_dt, end_dt)]
if sel_status:
    df = df[df["order_status"].isin(sel_status)]
if sel_states:
    df = df[df["customer_state"].isin(sel_states)]
if sel_cats:
    df = df[df["product_category_name_english"].isin(sel_cats)]
if sel_pay:
    df = df[df["payment_type"].isin(sel_pay)]
df = df[df["price"].between(price_range[0], price_range[1])]

# delivered subset from filtered df
delivered = (
    df[df["order_status"] == "delivered"]
    .drop_duplicates("order_id").copy()
    .pipe(lambda d: d.dropna(subset=[
        "order_delivered_customer_date",
        "order_purchase_timestamp",
        "order_estimated_delivery_date"]))
)
if len(delivered) > 0:
    delivered["actual_days"]    = (delivered["order_delivered_customer_date"] - delivered["order_purchase_timestamp"]).dt.days
    delivered["estimated_days"] = (delivered["order_estimated_delivery_date"]  - delivered["order_purchase_timestamp"]).dt.days
    delivered["on_time"]        = (delivered["estimated_days"] - delivered["actual_days"]) >= 0

# ── Header ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:24px 0 8px;">
  <h1 style="font-size:2.2rem; font-weight:800;
             background:linear-gradient(135deg,#00D4FF,#7C3AED,#EC4899);
             -webkit-background-clip:text; -webkit-text-fill-color:transparent;
             background-clip:text; margin-bottom:6px;">
    🇧🇷 Brazil E-Commerce Intelligence Dashboard
  </h1>
  <p style="color:#94A3B8; font-size:.85rem; letter-spacing:.08em; text-transform:uppercase;">
    Olist Dataset &nbsp;·&nbsp; 2016–2018 &nbsp;·&nbsp; Interactive Analysis
  </p>
</div>""", unsafe_allow_html=True)

# Active filter badges
active = []
if start_dt != pd.Timestamp(min_date) or end_dt != pd.Timestamp(max_date):
    active.append(f"📅 {start_dt.date()} → {end_dt.date()}")
if len(sel_status) < len(all_statuses):
    active.append(f"📦 {len(sel_status)} statuses")
if len(sel_states) < len(all_states):
    active.append(f"📍 {', '.join(sel_states[:3])}{'…' if len(sel_states)>3 else ''}")
if len(sel_cats) < len(all_cats):
    active.append(f"🏷️ {len(sel_cats)} categories")
if len(sel_pay) < len(all_pay):
    active.append(f"💳 {', '.join(sel_pay)}")
if price_range != (p_min, p_max):
    active.append(f"💵 R${price_range[0]:.0f}–R${price_range[1]:.0f}")

if active:
    badges = " ".join([f'<span class="filter-badge">{a}</span>' for a in active])
    total_pct = len(df) / len(df_raw) * 100
    st.markdown(
        f'<div style="text-align:center; margin-bottom:8px;">'
        f'{badges}'
        f'<span class="filter-badge" style="border-color:#10B98133; color:#10B981;">'
        f'📊 {len(df):,} rows ({total_pct:.1f}%)</span></div>',
        unsafe_allow_html=True)

# ── Guard: no data ─────────────────────────────────────────────────────────────
if len(df) == 0:
    st.error("No data matches the current filters. Please adjust the sidebar filters.")
    st.stop()

# ════════════════════════════════════════════════════════════════════════════════
# KPI CARDS
# ════════════════════════════════════════════════════════════════════════════════
kpi_orders    = df["order_id"].nunique()
kpi_revenue   = df["price"].sum()
kpi_review    = df["review_score"].mean()
kpi_on_time   = delivered["on_time"].mean() * 100 if len(delivered) > 0 else 0
kpi_customers = df["customer_unique_id"].nunique()
kpi_sellers   = df["seller_id"].nunique()

kpis = [
    ("📦 Total Orders",     f"{kpi_orders:,}",         CYAN),
    ("💰 Total Revenue",    f"R$ {kpi_revenue/1_000_000:.2f}M",  GREEN),
    ("⭐ Avg Review",       f"{kpi_review:.2f} / 5",   AMBER),
    ("🚚 On-Time Delivery", f"{kpi_on_time:.1f}%",     "#22D3EE"),
    ("👥 Customers",        f"{kpi_customers:,}",      PURPLE),
    ("🏪 Sellers",          f"{kpi_sellers:,}",        PINK),
]
cols = st.columns(6)
for col, (label, value, color) in zip(cols, kpis):
    col.markdown(f"""
    <div class="kpi-card" style="--glow:{color}">
      <div class="kpi-value">{value}</div>
      <div class="kpi-label">{label}</div>
    </div>""", unsafe_allow_html=True)

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 1 — Monthly Trends
# ════════════════════════════════════════════════════════════════════════════════
section("📈 Monthly Business Trends")

monthly_orders  = df.drop_duplicates("order_id").groupby("month").size()
monthly_revenue = df.groupby("month")["price"].sum()
monthly_items   = df.groupby("month").size()
x = [str(p) for p in monthly_orders.index]

fig_trends = make_subplots(rows=3, cols=1, shared_xaxes=True,
    subplot_titles=["Monthly Unique Orders","Monthly Revenue (R$)","Monthly Items Sold"],
    vertical_spacing=0.07)

for row, (y_vals, color, fill, name, hover) in enumerate([
    (monthly_orders.values,  CYAN,  "rgba(0,212,255,0.08)",  "Orders",  "Orders: %{y:,}"),
    (monthly_revenue.values, GREEN, "rgba(16,185,129,0.08)", "Revenue", "Revenue: R$%{y:,.0f}"),
    (monthly_items.values,   AMBER, "rgba(245,158,11,0.08)", "Items",   "Items: %{y:,}"),
], 1):
    fig_trends.add_trace(go.Scatter(
        x=x, y=y_vals, name=name,
        line=dict(color=color, width=2.5), mode="lines+markers",
        marker=dict(size=4), fill="tozeroy", fillcolor=fill,
        hovertemplate=f"<b>%{{x}}</b><br>{hover}<extra></extra>",
    ), row=row, col=1)

for date, label, color in [
    ("2017-11", "Black Friday Spike",          PINK),
    ("2018-06", "FIFA World Cup + Truckers Strike", PURPLE),
    ("2018-09", "Dataset Ends",                RED),
]:
    if date in x:
        for r in [1,2,3]:
            fig_trends.add_vline(x=date, line_dash="dash",
                                 line_color=color, line_width=1.5, row=r, col=1)

apply_layout(fig_trends, height=600,
             extra={"showlegend": True, "legend": dict(orientation="h", y=1.04)})
st.plotly_chart(fig_trends, use_container_width=True)

insight("Monthly Trends — Key Events", CYAN, [
    "📉 <strong>Apr 2017 dip (−9%):</strong> Easter & Holy Week (Apr 16). Brazil is 65% Catholic — nationwide travel & offline activity replaces online shopping.",
    "🚀 <strong>Nov 2017 spike (+32%):</strong> Black Friday. Brazil adopted Black Friday from US culture — it is now the biggest e-commerce event of the year.",
    "📉 <strong>Dec 2017 dip (−24%):</strong> Post-Black Friday correction. Consumers already bought in November — December demand was pulled forward and exhausted.",
    "📉 <strong>Jun–Aug 2018 sustained dip (−11%):</strong> FIFA World Cup (Jun 14 – Jul 15) + Truckers' Strike (May 21–30). World Cup paralysed online activity; strike collapsed logistics nationwide.",
    "⚠️ <strong>Sep 2018 near-zero:</strong> Not a real dip — the dataset was frozen in early September capturing only 1–2 days. Exclude from trend analysis.",
], takeaway="Black Friday is the single biggest revenue opportunity. Jun–Aug is structurally weak every World Cup year — plan inventory and logistics accordingly.")

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 2 — Order Timing
# ════════════════════════════════════════════════════════════════════════════════
section("🕐 Order Timing Patterns")
col1, col2 = st.columns(2)

dow_order  = ["Monday","Tuesday","Wednesday","Thursday","Friday","Saturday","Sunday"]
dow_counts = df["order_purchase_timestamp"].dt.day_name().value_counts().reindex(dow_order)
hour_counts= df["order_purchase_timestamp"].dt.hour.value_counts().sort_index()

fig_dow = go.Figure(go.Bar(
    x=dow_counts.index, y=dow_counts.values,
    marker=dict(color=dow_counts.values, colorscale="Blues", showscale=False),
    text=dow_counts.values, texttemplate="%{text:,}", textposition="outside",
    hovertemplate="<b>%{x}</b><br>%{y:,} items<extra></extra>",
))
fig_dow.update_layout(title=dict(text="Orders by Day of Week", font=dict(size=14,color=CYAN)),
                       xaxis_title="Day", yaxis_title="Items")
apply_layout(fig_dow, height=360)
col1.plotly_chart(fig_dow, use_container_width=True)

fig_hr = go.Figure(go.Bar(
    x=hour_counts.index, y=hour_counts.values,
    marker=dict(color=hour_counts.values, colorscale="Oranges", showscale=False),
    hovertemplate="<b>%{x}:00</b><br>%{y:,} items<extra></extra>",
))
fig_hr.update_layout(title=dict(text="Orders by Hour of Day", font=dict(size=14,color=AMBER)),
                      xaxis=dict(title="Hour (24h)", dtick=2), yaxis_title="Items")
apply_layout(fig_hr, height=360)
col2.plotly_chart(fig_hr, use_container_width=True)

insight("Order Timing Patterns", AMBER, [
    "😴 <strong>1AM–8AM is dead time:</strong> Core sleeping hours in Brazil (UTC-3). Virtually zero shopping intent — never schedule campaigns in this window.",
    "💼 <strong>8AM–9AM surge:</strong> Workers arrive at desks and browse personal tasks first — this is the highest-ROI email/push notification send time.",
    "🍽️ <strong>10AM–2PM peak:</strong> Brazilian lunch breaks are long (1–1.5 hrs). Mobile shopping spikes dramatically during this window.",
    "🌙 <strong>6PM–9PM second peak:</strong> Post-work leisure browsing at home on phones and tablets.",
    "📅 <strong>Weekdays dominate:</strong> Monday–Thursday consistently outperform weekends — Brazilians shop from work devices during business hours.",
], takeaway="Schedule all marketing campaigns to fire at 9AM BRT. Avoid 1AM–7AM completely. Lunch (12–2PM) and evening (7–9PM) are secondary high-value windows.")

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 3 — Order Status & Payment
# ════════════════════════════════════════════════════════════════════════════════
section("🧾 Order Status & Payment Distribution")
col1, col2 = st.columns(2)

status_counts = df.drop_duplicates("order_id")["order_status"].value_counts()
fig_status = go.Figure(go.Pie(
    labels=status_counts.index, values=status_counts.values, hole=0.6,
    marker=dict(colors=[CYAN,GREEN,RED,AMBER,PURPLE,PINK,"#64748B"],
                line=dict(color=BG, width=2)),
    textinfo="percent+label",
    hovertemplate="<b>%{label}</b><br>%{value:,} orders (%{percent})<extra></extra>",
))
fig_status.update_layout(
    title=dict(text="Order Status", font=dict(size=15,color=CYAN)),
    annotations=[dict(text=f"<b>{status_counts.sum():,}</b><br>Orders",
                      x=0.5,y=0.5,font_size=13,showarrow=False)])
apply_layout(fig_status, height=380)
col1.plotly_chart(fig_status, use_container_width=True)

pay_counts = df.drop_duplicates("order_id")["payment_type"].value_counts(dropna=False)
pay_counts = pay_counts[pay_counts.index.notna()]
fig_pay = go.Figure(go.Pie(
    labels=pay_counts.index, values=pay_counts.values, hole=0.6,
    marker=dict(colors=[GREEN,CYAN,AMBER,PURPLE,PINK],
                line=dict(color=BG, width=2)),
    textinfo="percent+label",
    hovertemplate="<b>%{label}</b><br>%{value:,} orders (%{percent})<extra></extra>",
))
fig_pay.update_layout(
    title=dict(text="Payment Type", font=dict(size=15,color=GREEN)),
    annotations=[dict(text=f"<b>{pay_counts.sum():,}</b><br>Payments",
                      x=0.5,y=0.5,font_size=13,showarrow=False)])
apply_layout(fig_pay, height=380)
col2.plotly_chart(fig_pay, use_container_width=True)

insight("Payment Distribution", GREEN, [
    "💳 <strong>Credit card at 74%:</strong> Brazilians use credit cards specifically to split purchases into interest-free installments — it is a budgeting tool, not a debt tool.",
    "📄 <strong>Boleto at 20%:</strong> A uniquely Brazilian payment slip payable at any bank or lottery house. Used by unbanked consumers and B2B — never remove this option.",
    "💵 <strong>Credit card AOV is highest:</strong> Installment availability removes the psychological price barrier — a R$500 item becomes R$50/month for 10 months.",
    "📉 <strong>Boleto AOV is lowest:</strong> Boleto users pay the full amount upfront — naturally limits spend to immediately available cash.",
    "🔑 <strong>Debit card at 2%:</strong> Almost nobody uses debit online — no installment option, no rewards. Credit card is always preferred.",
])

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 4 — Payment Installments
# ════════════════════════════════════════════════════════════════════════════════
section("💳 Payment Installments Distribution")

inst = (df.drop_duplicates("order_id")["payment_installments"]
          .value_counts().sort_index().head(15))
fig_inst = go.Figure(go.Bar(
    x=inst.index.astype(str), y=inst.values,
    marker=dict(color=inst.values, colorscale="Blues", showscale=True,
                colorbar=dict(title="Count", tickfont=dict(color="#E2E8F0"),
                              title_font=dict(color="#E2E8F0"))),
    text=inst.values, texttemplate="%{text:,}", textposition="outside",
    hovertemplate="<b>%{x} installments</b><br>%{y:,} orders<extra></extra>",
))
fig_inst.update_layout(title=dict(text="Installments Distribution (Top 15)",
                                   font=dict(size=15,color=AMBER)),
                        xaxis_title="Installments", yaxis_title="Orders")
apply_layout(fig_inst, height=380)
st.plotly_chart(fig_inst, use_container_width=True)

insight("Installment Culture (Parcelamento)", AMBER, [
    "1️⃣ <strong>Massive 1-installment spike:</strong> Represents boleto payments + small impulse purchases paid in full. Low-friction checkout is critical for this segment.",
    "🔢 <strong>2–6 installments — core Brazilian behaviour:</strong> For R$150–R$600 items, splitting is automatic. Retailers advertise '6x de R$49' not 'R$294 total'.",
    "📅 <strong>7–12 installments for high-value items:</strong> Electronics, furniture, appliances. '10x sem juros' (10x interest-free) is a standard closing tactic in Brazil.",
    "🚫 <strong>Beyond 12x drops to near zero:</strong> Most credit agreements cap interest-free installments at 12. Beyond this, interest applies and conversion collapses.",
], takeaway="Sellers who offer more installment options sell more expensive products. Enabling 10–12x installments is the single most effective lever for increasing basket size in Brazil.")

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 5 — Categories
# ════════════════════════════════════════════════════════════════════════════════
section("📦 Top Product Categories")

# top N slider
top_n = st.slider("Number of categories to show", 5, 30, 15, key="cat_n")
col1, col2 = st.columns(2)

cat_col = "product_category_name_english"
cat_rev = df.groupby(cat_col)["price"].sum().sort_values().tail(top_n)
cat_vol = df.groupby(cat_col).size().sort_values().tail(top_n)

for col, series, color, title, xlabel in [
    (col1, cat_rev, "Greens", f"Top {top_n} by Revenue (R$)",  "Revenue (R$)"),
    (col2, cat_vol, "Blues",  f"Top {top_n} by Volume (Items)", "Items Sold"),
]:
    fig = go.Figure(go.Bar(
        x=series.values, y=series.index, orientation="h",
        marker=dict(color=series.values, colorscale=color, showscale=False),
        hovertemplate="<b>%{y}</b><br>" + xlabel + ": %{x:,}<extra></extra>",
        text=[f"{int(v):,}" for v in series.values], textposition="outside",
    ))
    fig.update_layout(title=dict(text=title,
                                  font=dict(size=14,color=GREEN if color=="Greens" else CYAN)),
                       xaxis_title=xlabel)
    apply_layout(fig, height=max(380, top_n * 26))
    col.plotly_chart(fig, use_container_width=True)

insight("Category Performance", GREEN, [
    "🏆 <strong>Health & Beauty leads revenue (R$1.18M):</strong> High purchase frequency, strong repeat buying, and affordable price points with manageable freight.",
    "⌚ <strong>Watches & Gifts at #2 (R$1.15M):</strong> High average order value — gifting occasions drive premium purchases year-round.",
    "🏠 <strong>Bed/Bath/Table at #3:</strong> High volume + mid-range pricing = consistent revenue. Sweet spot of weight-to-value ratio for freight.",
    "🖥️ <strong>Electronics (computers_accessories):</strong> Low volume but very high AOV. Every lost sale is costly — review score and delivery speed are critical here.",
    "⚖️ <strong>Volume ≠ Revenue:</strong> Some categories rank top 5 by items but not by revenue (cheap fashion) — and vice versa (luxury items).",
])

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 6 — Geographic Maps
# ════════════════════════════════════════════════════════════════════════════════
section("🗺️ Geographic Distribution")

map_metric = st.selectbox(
    "Select map metric",
    ["Orders", "Revenue (R$)", "Avg Review Score", "On-Time Delivery (%)"],
    key="map_metric"
)

if geojson:
    state_orders = df.drop_duplicates("order_id").groupby("customer_state").size().reset_index(name="orders")
    state_rev    = df.groupby("customer_state")["price"].sum().reset_index(name="revenue")
    state_review = df.drop_duplicates("order_id").groupby("customer_state")["review_score"].mean().reset_index(name="avg_review")
    state_ontime = (delivered.groupby("customer_state")["on_time"].mean().mul(100).reset_index(name="on_time_pct")
                    if len(delivered) > 0 else pd.DataFrame(columns=["customer_state","on_time_pct"]))

    geo_df = (state_orders
              .merge(state_rev,    on="customer_state", how="left")
              .merge(state_review, on="customer_state", how="left")
              .merge(state_ontime, on="customer_state", how="left"))

    metric_map = {
        "Orders":               ("orders",     "Blues",  "Orders"),
        "Revenue (R$)":         ("revenue",    "Greens", "Revenue R$"),
        "Avg Review Score":     ("avg_review", "RdYlGn", "Avg Review"),
        "On-Time Delivery (%)": ("on_time_pct","RdYlGn", "On-Time %"),
    }
    col_name, scale, label = metric_map[map_metric]

    fig_geo = go.Figure(go.Choropleth(
        geojson=geojson, locations=geo_df["customer_state"],
        z=geo_df[col_name], featureidkey="properties.sigla",
        colorscale=scale, marker_line_color=BG, marker_line_width=0.6,
        colorbar=dict(title=label, thickness=14,
                      tickfont=dict(color="#E2E8F0"),
                      title_font=dict(color="#E2E8F0")),
        hovertemplate=f"<b>%{{location}}</b><br>{label}: %{{z:,.1f}}<extra></extra>",
    ))
    fig_geo.update_geos(visible=False, fitbounds="locations",
                         bgcolor=BG, landcolor=CARD, oceancolor=BG,
                         showcoastlines=True, coastlinecolor="#1E2A45")
    fig_geo.update_layout(title=dict(text=f"Brazil States — {map_metric}",
                                      font=dict(size=15,color=CYAN), x=0.5))
    apply_layout(fig_geo, height=560, extra={"margin": dict(l=10,r=10,t=60,b=10)})
    st.plotly_chart(fig_geo, use_container_width=True)
else:
    st.warning("Could not load GeoJSON — geographic map unavailable.")

insight("Geographic Distribution", CYAN, [
    "🏙️ <strong>São Paulo dominates everything:</strong> SP alone generates ~35–40% of all orders and an even higher share of revenue. Any fulfilment centre must be in SP first.",
    "🗺️ <strong>Southeast = 55–60% of total revenue:</strong> SP + RJ + MG together. Marketing budget should weight heavily toward this region.",
    "⚡ <strong>Seller concentration creates a logistics mismatch:</strong> 80%+ of sellers are in SP/MG/PR but customers are spread across all 27 states — this drives long delivery times in the North/Northeast.",
    "💰 <strong>Remote states have HIGHER avg item prices:</strong> In Amazonas, Roraima, Acre — customers only order online when shipping cost is worth it. Cheap items are not worth the freight — only high-value purchases survive.",
    "🏛️ <strong>Brasília (DF) punches above its weight:</strong> Federal government employees have stable high incomes — DF revenue per order is among the highest in Brazil.",
    "🌱 <strong>North/Northeast = growth opportunity:</strong> Near-zero sellers in these regions means long delivery times. The company that builds regional fulfilment here will unlock the next wave of Brazilian e-commerce growth.",
], takeaway="Brazilian e-commerce is a São Paulo-centric business. The further from SP a customer lives, the worse their experience. Solving last-mile logistics for the North/Northeast is the single biggest untapped opportunity.")

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 7 — Delivery Performance
# ════════════════════════════════════════════════════════════════════════════════
section("🚚 Delivery Performance")

if len(delivered) == 0:
    st.info("No delivered orders in the current filter selection.")
else:
    col1, col2, col3 = st.columns(3)

    fig_dh = go.Figure(go.Histogram(
        x=delivered["actual_days"].clip(upper=delivered["actual_days"].quantile(0.99)),
        nbinsx=50, marker=dict(color=CYAN, opacity=0.85, line=dict(color=BG, width=0.5)),
        hovertemplate="Days: %{x}<br>Count: %{y:,}<extra></extra>",
    ))
    fig_dh.add_vline(x=delivered["actual_days"].mean(), line_dash="dash",
                      line_color=AMBER, line_width=2,
                      annotation_text=f"Mean {delivered['actual_days'].mean():.1f}d",
                      annotation_font_color=AMBER)
    fig_dh.update_layout(title=dict(text="Actual Delivery Days",
                                     font=dict(size=14,color=CYAN)),
                          xaxis_title="Days", yaxis_title="Orders")
    apply_layout(fig_dh, height=360)
    col1.plotly_chart(fig_dh, use_container_width=True)

    ot = delivered.groupby("customer_state")["on_time"].mean().mul(100).sort_values(ascending=False).head(15)
    fig_ot = go.Figure(go.Bar(
        x=ot.index, y=ot.values,
        marker=dict(color=[GREEN if v>=80 else (AMBER if v>=60 else RED) for v in ot.values]),
        text=[f"{v:.0f}%" for v in ot.values], textposition="outside",
        hovertemplate="<b>%{x}</b><br>On-Time: %{y:.1f}%<extra></extra>",
    ))
    fig_ot.update_layout(title=dict(text="On-Time Rate by State (Top 15)",
                                     font=dict(size=14,color=GREEN)),
                          xaxis_title="State",
                          yaxis=dict(title="On-Time %", range=[0,115]))
    apply_layout(fig_ot, height=360)
    col2.plotly_chart(fig_ot, use_container_width=True)

    avg_d = delivered.groupby("customer_state")["actual_days"].mean().sort_values().head(15)
    fig_ad = go.Figure(go.Bar(
        x=avg_d.index, y=avg_d.values,
        marker=dict(color=avg_d.values, colorscale="RdYlGn_r", showscale=False),
        text=[f"{v:.1f}d" for v in avg_d.values], textposition="outside",
        hovertemplate="<b>%{x}</b><br>Avg Days: %{y:.1f}<extra></extra>",
    ))
    fig_ad.update_layout(title=dict(text="Fastest States — Avg Delivery Days",
                                     font=dict(size=14,color=AMBER)),
                          xaxis_title="State", yaxis_title="Avg Days")
    apply_layout(fig_ad, height=360)
    col3.plotly_chart(fig_ad, use_container_width=True)

insight("Delivery Performance", "#22D3EE", [
    "✅ <strong>92.4% on-time rate overall:</strong> Strong national performance — but the average hides massive regional inequality.",
    "📦 <strong>Mean actual delivery: 12.1 days</strong> vs estimated 23.4 days — Olist significantly over-promises on delivery estimates (almost 2× the actual time).",
    "🟢 <strong>States near SP deliver fastest:</strong> SP, PR, MG customers receive orders in 7–10 days with 90%+ on-time rates.",
    "🔴 <strong>Northern states suffer most:</strong> AM, PA, RR customers wait 20–30+ days with on-time rates dropping below 75% — a direct result of seller concentration in the Southeast.",
    "⚠️ <strong>Over-estimation is a double-edged sword:</strong> Setting long estimated delivery dates protects the on-time metric but damages conversion — customers see '23 days' and abandon the cart.",
], takeaway="The 92.4% on-time rate is misleading at a national level. The North/Northeast experience is dramatically worse. Fixing this requires regional distribution centres, not just better carrier contracts.")

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 8 — Review Analysis
# ════════════════════════════════════════════════════════════════════════════════
section("⭐ Review Score Analysis")
col1, col2 = st.columns(2)

rev_counts = df.drop_duplicates("order_id")["review_score"].value_counts().sort_index().dropna()
fig_rev = go.Figure(go.Bar(
    x=rev_counts.index.astype(int), y=rev_counts.values,
    marker=dict(color=[RED,"#F97316",AMBER,"#84CC16",GREEN],
                line=dict(color=BG, width=1)),
    text=rev_counts.values, texttemplate="%{text:,}", textposition="outside",
    hovertemplate="<b>%{x} Stars</b><br>%{y:,} reviews<extra></extra>",
))
fig_rev.update_layout(title=dict(text="Review Score Distribution",
                                   font=dict(size=14,color=AMBER)),
                       xaxis=dict(title="Stars", tickvals=[1,2,3,4,5]),
                       yaxis_title="Count")
apply_layout(fig_rev, height=360)
col1.plotly_chart(fig_rev, use_container_width=True)

if len(delivered) > 0:
    bins   = [0,3,7,14,21,30,9999]
    labels = ["0-3d","4-7d","8-14d","15-21d","22-30d","30d+"]
    delivered["speed_bucket"] = pd.cut(delivered["actual_days"], bins=bins, labels=labels)
    speed_rev = delivered.groupby("speed_bucket", observed=True)["review_score"].mean()
    fig_sp = go.Figure(go.Bar(
        x=speed_rev.index.astype(str), y=speed_rev.values,
        marker=dict(color=speed_rev.values, colorscale="RdYlGn", cmin=1, cmax=5,
                    showscale=True, colorbar=dict(title="Score",
                                                   tickfont=dict(color="#E2E8F0"),
                                                   title_font=dict(color="#E2E8F0"))),
        text=[f"{v:.2f}" for v in speed_rev.values], textposition="outside",
        hovertemplate="<b>%{x}</b><br>Avg Score: %{y:.2f}<extra></extra>",
    ))
    fig_sp.update_layout(title=dict(text="Avg Review Score by Delivery Speed",
                                     font=dict(size=14,color=GREEN)),
                          xaxis_title="Delivery Bucket",
                          yaxis=dict(title="Avg Score", range=[0,5.5]))
    apply_layout(fig_sp, height=360)
    col2.plotly_chart(fig_sp, use_container_width=True)

insight("Review Score Analysis", AMBER, [
    "⭐ <strong>Overall avg 4.04/5:</strong> Healthy platform average — but 5-star reviews (63K) dwarf all others, suggesting a bimodal pattern of love-it or hate-it experiences.",
    "🚀 <strong>Faster delivery = higher scores:</strong> Orders delivered in 0–3 days score ~4.5+ stars. Orders taking 30+ days score below 3.5. Delivery speed is the #1 driver of customer satisfaction.",
    "📉 <strong>1-star reviews spike at slow delivery:</strong> The 14K one-star reviews are disproportionately from orders that arrived late or were canceled — not product quality issues.",
    "🏭 <strong>Category scores vary widely:</strong> Products requiring assembly or precise sizing (furniture, fashion) score lowest. Consumables (health/beauty, food) score highest.",
    "💬 <strong>Most reviews have no comment:</strong> 58% of review_comment_message is empty — customers rate quickly but rarely explain why. Negative reviews with comments are gold-standard feedback.",
], takeaway="Every day shaved off delivery time directly increases review scores, which directly drives repeat purchases. Speed is not a logistics metric — it is a revenue metric.")

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 9 — Price & Freight
# ════════════════════════════════════════════════════════════════════════════════
section("💵 Price & Freight Analysis")
col1, col2 = st.columns(2)

p99 = df["price"].quantile(0.99)
fig_ph = go.Figure(go.Histogram(
    x=df[df["price"] <= p99]["price"], nbinsx=60,
    marker=dict(color=PURPLE, opacity=0.85, line=dict(color=BG, width=0.5)),
    hovertemplate="Price: R$%{x:.0f}<br>Count: %{y:,}<extra></extra>",
))
for val, label, color in [
    (df["price"].mean(),   f"Mean R${df['price'].mean():.0f}",   RED),
    (df["price"].median(), f"Median R${df['price'].median():.0f}", AMBER),
]:
    fig_ph.add_vline(x=val, line_dash="dash", line_color=color, line_width=2,
                     annotation_text=label, annotation_font_color=color)
fig_ph.update_layout(title=dict(text="Price Distribution (up to 99th pct)",
                                  font=dict(size=14,color=PURPLE)),
                      xaxis_title="Price (R$)", yaxis_title="Count")
apply_layout(fig_ph, height=360)
col1.plotly_chart(fig_ph, use_container_width=True)

fq99 = df["freight_pct"].quantile(0.99)
fig_fh = go.Figure(go.Histogram(
    x=df[df["freight_pct"] <= fq99]["freight_pct"], nbinsx=60,
    marker=dict(color=PINK, opacity=0.85, line=dict(color=BG, width=0.5)),
    hovertemplate="Freight %%: %{x:.1f}%%<br>Count: %{y:,}<extra></extra>",
))
fig_fh.add_vline(x=df["freight_pct"].mean(), line_dash="dash", line_color=AMBER,
                  line_width=2, annotation_text=f"Mean {df['freight_pct'].mean():.1f}%",
                  annotation_font_color=AMBER)
fig_fh.update_layout(title=dict(text="Freight as % of Total Cost",
                                  font=dict(size=14,color=PINK)),
                      xaxis_title="Freight %", yaxis_title="Count")
apply_layout(fig_fh, height=360)
col2.plotly_chart(fig_fh, use_container_width=True)

insight("Price & Freight Analysis", PURPLE, [
    "📊 <strong>Median price R$74, mean R$120:</strong> The R$46 gap reveals a right-skewed market — a small number of high-value items (electronics, furniture) pull the mean up significantly.",
    "🚚 <strong>Freight averages 19–20% of total cost:</strong> For a R$30 item with R$15 shipping, the customer pays 50% extra — a major conversion killer for cheap goods.",
    "⚠️ <strong>Cheap items face a freight trap:</strong> Items under R$50 are nearly uncompetitive on e-commerce when shipping eats 30–50% of the total price. Bundles and minimum order values help.",
    "📦 <strong>Price and freight are weakly correlated:</strong> Product dimensions and weight matter far more than price when predicting freight cost. A R$500 piece of jewellery ships for R$12; a R$200 chair ships for R$80.",
    "🎯 <strong>Sweet spot: R$50–R$150 items:</strong> High enough value that freight is a small percentage, low enough to not require installments. This is where the majority of volume and conversions happen.",
], takeaway="Free shipping thresholds (e.g. 'Free shipping over R$99') are the most effective tool to increase basket size AND reduce freight's psychological impact on conversion.")

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 10 — Seller Analysis
# ════════════════════════════════════════════════════════════════════════════════
section("🏪 Seller Performance")

top_n_sellers = st.slider("Number of top sellers to show", 5, 30, 15, key="seller_n")
col1, col2 = st.columns(2)

seller_stats = (df.groupby("seller_id")
                  .agg(revenue=("price","sum"),
                       avg_score=("review_score","mean"),
                       order_count=("order_id","nunique"))
                  .reset_index())

sample_size = min(3000, len(seller_stats))
sample = seller_stats.sample(sample_size, random_state=42)
fig_sc = go.Figure(go.Scatter(
    x=sample["revenue"], y=sample["avg_score"], mode="markers",
    marker=dict(size=np.clip(np.log1p(sample["order_count"])*3, 3, 18),
                color=sample["avg_score"], colorscale="RdYlGn",
                cmin=1, cmax=5, showscale=True, opacity=0.7,
                line=dict(color=BG, width=0.4),
                colorbar=dict(title="Avg Score",
                              tickfont=dict(color="#E2E8F0"),
                              title_font=dict(color="#E2E8F0"))),
    hovertemplate="Revenue: R$%{x:,.0f}<br>Avg Score: %{y:.2f}<extra></extra>",
))
fig_sc.update_layout(title=dict(text=f"Seller Revenue vs Avg Review Score ({sample_size:,} sellers)",
                                  font=dict(size=14,color=PURPLE)),
                      xaxis=dict(title="Revenue (R$)", type="log"),
                      yaxis_title="Avg Review Score")
apply_layout(fig_sc, height=420)
col1.plotly_chart(fig_sc, use_container_width=True)

top_sellers = seller_stats.nlargest(top_n_sellers, "revenue").sort_values("revenue")
fig_ts = go.Figure(go.Bar(
    x=top_sellers["revenue"],
    y=[f"...{s[-6:]}" for s in top_sellers["seller_id"]],
    orientation="h",
    marker=dict(color=top_sellers["revenue"], colorscale="Purples", showscale=False),
    text=[f"R${v:,.0f}" for v in top_sellers["revenue"]], textposition="outside",
    hovertemplate="Revenue: R$%{x:,.0f}<extra></extra>",
))
fig_ts.update_layout(title=dict(text=f"Top {top_n_sellers} Sellers by Revenue",
                                  font=dict(size=14,color=PURPLE)),
                      xaxis_title="Revenue (R$)")
apply_layout(fig_ts, height=420)
col2.plotly_chart(fig_ts, use_container_width=True)

insight("Seller Performance", PINK, [
    "📊 <strong>Classic power law distribution:</strong> The vast majority of sellers have sold fewer than 50 items total. A tiny elite drives most revenue — this is the long tail of e-commerce.",
    "💰 <strong>Top 10% of sellers (306) = 67.5% of revenue:</strong> Losing even a handful of top sellers would devastate platform revenue. Retention > acquisition.",
    "⭐ <strong>Review sweet spot is 3.8–4.5 stars, not 5.0:</strong> ALL high-revenue sellers cluster in this range. Perfect 5.0 sellers tend to be small/niche. Chasing perfection at the expense of volume is the wrong strategy.",
    "🚫 <strong>Below 3.0 stars = revenue ceiling:</strong> No seller with consistently poor reviews achieves meaningful revenue. Bad reviews are a hard growth blocker.",
    "🏭 <strong>Two seller archetypes:</strong> Volume sellers (many cheap items, modest revenue — fashion, accessories) vs Value sellers (few expensive items, high revenue — electronics, furniture). Top sellers combine both.",
    "📈 <strong>Most sellers are dormant:</strong> The bottom 50% of sellers contribute negligible revenue but consume support and infrastructure costs. Activation programs for mid-tier sellers have high ROI.",
], takeaway="Olist's marketplace health depends on ~300 sellers. A VIP program with dedicated account managers for the top 10% is fully justified — and identifying sellers moving from mid-tier to top-tier is the highest-leverage growth activity.")

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 11 — Seller Churn Analysis
# ════════════════════════════════════════════════════════════════════════════════
section("📉 Seller Churn Analysis (2017 → 2018)")

df["year"] = df["order_purchase_timestamp"].dt.year
sellers_2017 = set(df[df["year"] == 2017]["seller_id"])
sellers_2018 = set(df[df["year"] == 2018]["seller_id"])

churned  = sellers_2017 - sellers_2018
retained = sellers_2017 & sellers_2018
new_2018 = sellers_2018 - sellers_2017
churn_rate = len(churned) / len(sellers_2017) * 100

sel_2017       = df[df["year"] == 2017].groupby("seller_id")["price"].sum()
rev_churned    = sel_2017[sel_2017.index.isin(churned)].sum()
rev_retained   = sel_2017[sel_2017.index.isin(retained)].sum()
rev_total_2017 = sel_2017.sum()
rev_risk_pct   = rev_churned / rev_total_2017 * 100

items_churned  = df[(df["year"]==2017) & (df["seller_id"].isin(churned))].groupby("seller_id").size()
items_retained = df[(df["year"]==2017) & (df["seller_id"].isin(retained))].groupby("seller_id").size()

# KPI strip
kc1, kc2, kc3, kc4 = st.columns(4)
kc1.metric("2017 Sellers", f"{len(sellers_2017):,}")
kc2.metric("Churned", f"{len(churned):,}", f"-{churn_rate:.1f}%", delta_color="inverse")
kc3.metric("Retained", f"{len(retained):,}", f"+{100-churn_rate:.1f}%")
kc4.metric("Revenue at Risk", f"R$ {rev_churned/1e3:.1f}K", f"{rev_risk_pct:.1f}% of 2017 rev", delta_color="inverse")

col1, col2 = st.columns(2)

# Donut — churn vs retention
fig_donut = go.Figure(go.Pie(
    labels=[f"Churned ({len(churned):,})", f"Retained ({len(retained):,})"],
    values=[len(churned), len(retained)],
    hole=0.55,
    marker=dict(colors=[RED, GREEN]),
    textinfo="label+percent",
    hovertemplate="%{label}<br>%{value:,} sellers<extra></extra>",
))
fig_donut.update_layout(title=dict(text="2017 Seller Churn vs Retention", font=dict(size=14, color=RED)))
apply_layout(fig_donut, height=380)
col1.plotly_chart(fig_donut, use_container_width=True)

# Bar — seller base waterfall
bar_labels = ["2017 Sellers", "Churned", "Retained", "New 2018", "2018 Total"]
bar_values = [len(sellers_2017), len(churned), len(retained), len(new_2018), len(sellers_2018)]
bar_colors = [CYAN, RED, GREEN, AMBER, PURPLE]
fig_wf = go.Figure(go.Bar(
    x=bar_labels, y=bar_values,
    marker=dict(color=bar_colors),
    text=[f"{v:,}" for v in bar_values], textposition="outside",
    hovertemplate="%{x}: %{y:,}<extra></extra>",
))
fig_wf.update_layout(title=dict(text="Seller Base: 2017 → 2018 Composition", font=dict(size=14, color=CYAN)))
apply_layout(fig_wf, height=380)
col2.plotly_chart(fig_wf, use_container_width=True)

col3, col4 = st.columns(2)

# Revenue — churned vs retained
fig_rev = go.Figure(go.Bar(
    x=["Churned Sellers\n2017 Revenue", "Retained Sellers\n2017 Revenue"],
    y=[rev_churned, rev_retained],
    marker=dict(color=[RED, GREEN]),
    text=[f"R$ {rev_churned:,.0f}", f"R$ {rev_retained:,.0f}"], textposition="outside",
    hovertemplate="%{x}: R$%{y:,.0f}<extra></extra>",
))
fig_rev.update_layout(title=dict(text=f"2017 Revenue — {rev_risk_pct:.1f}% at Risk from Churn", font=dict(size=14, color=RED)))
apply_layout(fig_rev, height=380)
col3.plotly_chart(fig_rev, use_container_width=True)

# Items sold histogram — churned vs retained
clip_val = float(max(items_churned.quantile(0.95), items_retained.quantile(0.95)))
hist_c, bins_c = np.histogram(items_churned.clip(upper=clip_val), bins=25, density=True)
hist_r, bins_r = np.histogram(items_retained.clip(upper=clip_val), bins=25, density=True)
fig_hist = go.Figure()
fig_hist.add_trace(go.Bar(
    x=bins_c[:-1], y=hist_c, name=f"Churned (median={items_churned.median():.0f})",
    marker_color=RED, opacity=0.65,
    hovertemplate="Items: %{x:.0f}<br>Density: %{y:.4f}<extra></extra>",
))
fig_hist.add_trace(go.Bar(
    x=bins_r[:-1], y=hist_r, name=f"Retained (median={items_retained.median():.0f})",
    marker_color=GREEN, opacity=0.65,
    hovertemplate="Items: %{x:.0f}<br>Density: %{y:.4f}<extra></extra>",
))
fig_hist.update_layout(
    title=dict(text="Items Sold in 2017: Churned vs Retained Sellers", font=dict(size=14, color=AMBER)),
    barmode="overlay", xaxis_title="Items Sold", yaxis_title="Density"
)
apply_layout(fig_hist, height=380)
col4.plotly_chart(fig_hist, use_container_width=True)

insight("Seller Churn Analysis", RED, [
    f"📉 <strong>{churn_rate:.1f}% churn rate (2017→2018):</strong> {len(churned):,} sellers who were active in 2017 placed zero orders in 2018. This is structurally high — B2B marketplace benchmarks target sub-20% annual churn.",
    f"💸 <strong>R$ {rev_churned:,.0f} revenue at risk ({rev_risk_pct:.1f}% of 2017 revenue):</strong> The churned cohort's 2017 contribution represents real lost GMV unless replaced by new or growing sellers.",
    f"📦 <strong>Churned sellers sold far fewer items:</strong> Median items sold by churned sellers ({items_churned.median():.0f}) vs retained ({items_retained.median():.0f}). Low engagement is the earliest leading indicator of churn.",
    f"🌱 <strong>{len(new_2018):,} new sellers joined in 2018:</strong> Gross acquisition partially offsets churn, but new sellers need 3–6 months to ramp. Net seller base change matters most for platform health.",
    "⚠️ <strong>Seller acquisition ≠ seller retention:</strong> Replacing churned sellers with new ones costs 5–7x more. Early intervention (seller coaching, category suggestions, demand signals) for low-volume sellers is the high-ROI play.",
    "🔍 <strong>Churn is concentrated in the long tail:</strong> The sellers who churned are predominantly those who never broke through single-digit item counts. This is a product-fit problem, not a pricing problem.",
], takeaway=f"With a {churn_rate:.1f}% churn rate, Olist loses over a third of its seller base yearly. A proactive churn-prevention program targeting sellers with <10 items in their first 3 months could rescue the majority of this cohort before they disappear.")

# ════════════════════════════════════════════════════════════════════════════════
# SECTION 12 — Correlation Heatmap
# ════════════════════════════════════════════════════════════════════════════════
section("🔗 Correlation Heatmap")


corr_cols = ["price","freight_value","payment_total_value","payment_installments",
             "review_score","product_weight_g","product_photos_qty"]
if len(delivered) > 0:
    ad = delivered[["order_id","actual_days"]].copy()
    df_corr = df.merge(ad, on="order_id", how="left")
    corr_cols.append("actual_days")
else:
    df_corr = df.copy()

avail  = [c for c in corr_cols if c in df_corr.columns]
matrix = df_corr[avail].corr()
mask   = np.triu(np.ones_like(matrix, dtype=bool), k=1)
masked = matrix.where(~mask)

fig_hm = go.Figure(go.Heatmap(
    z=masked.values, x=masked.columns.tolist(), y=masked.index.tolist(),
    colorscale="RdBu", zmid=0, zmin=-1, zmax=1,
    text=masked.round(2).values, texttemplate="%{text}",
    hovertemplate="<b>%{y} × %{x}</b><br>r = %{z:.3f}<extra></extra>",
    colorbar=dict(title="Pearson r",
                  tickfont=dict(color="#E2E8F0"),
                  title_font=dict(color="#E2E8F0")),
))
fig_hm.update_layout(title=dict(text="Correlation Heatmap (Lower Triangle)",
                                  font=dict(size=15,color=PINK)),
                      xaxis=dict(tickangle=-30))
apply_layout(fig_hm, height=500, extra={"margin": dict(l=160,r=40,t=80,b=120)})
st.plotly_chart(fig_hm, use_container_width=True)

insight("Correlation Heatmap — Key Findings", PINK, [
    "💰 <strong>Price ↔ Payment Total (strong positive):</strong> Higher-priced items drive higher payment totals. Payment value is determined by product price, not freight markups.",
    "📦 <strong>Price ↔ Product Weight (moderate positive):</strong> Heavier products cost more — consistent with furniture and appliances. Weight is a reliable proxy for product value tier.",
    "🚚 <strong>Freight ↔ Product Weight (moderate positive):</strong> The most logical relationship — heavier products cost more to ship. Sellers of bulky goods face a structural freight disadvantage vs lightweight competitors.",
    "💳 <strong>Price ↔ Installments (weak positive):</strong> More expensive items get split into more installments — confirms the Brazilian parcelamento reflex. High price triggers the installment decision automatically.",
    "⭐ <strong>Review Score ↔ Delivery Days (negative):</strong> The most actionable finding — longer delivery directly causes lower review scores. Every extra day in transit costs customer satisfaction.",
    "📸 <strong>Product Photos ↔ Price (weak positive):</strong> Higher-priced items have more photos — sellers invest more in presentation for premium goods. Low-photo listings for expensive items are a missed conversion opportunity.",
    "🔗 <strong>Freight ↔ Delivery Days (weak positive):</strong> Higher freight and longer delivery are both driven by geographic distance — remote customers pay more AND wait longer.",
    "📊 <strong>Most pairs are weakly correlated:</strong> No single variable predicts everything. Each metric adds independent information — multi-factor analysis is essential, not single-KPI thinking.",
], takeaway="The most critical correlation for revenue: Review Score ↔ Delivery Days. Cutting delivery time by 1–2 days measurably lifts review scores → drives repeat purchases → compounds platform revenue.")

# ── Footer ─────────────────────────────────────────────────────────────────────
st.markdown("""
<div style="text-align:center; padding:40px 0 20px; color:#475569; font-size:.8rem;">
  Brazil Olist E-Commerce Analysis &nbsp;·&nbsp; Built with Python, Plotly & Streamlit
</div>""", unsafe_allow_html=True)
