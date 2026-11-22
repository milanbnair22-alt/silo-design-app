"""
RC coal silo design dashboard (Janssen's theory).

Run:  streamlit run app.py

All engineering calculations live in silo_calc.py (formulas copied from
silo_design.py). This file only collects inputs, calls those functions and
draws the results.
"""
import numpy as np
import pandas as pd
import plotly.graph_objects as go
import streamlit as st
from plotly.subplots import make_subplots

import silo_calc as sc

st.set_page_config(page_title="RC Coal Silo Design", page_icon="🏗", layout="wide")

# ------------------------------------------------------------
# STYLE
# ------------------------------------------------------------
C_PH, C_PV, C_FR, C_STEEL, C_BLUE = "#c0503f", "#2f6f9f", "#3d8b5e", "#d38b0b", "#2f6f9f"
FONT = "Segoe UI, Helvetica Neue, Arial, sans-serif"

st.markdown(
    """
<style>
.stApp {background:#f2f4f6;}
[data-testid="stHeader"] {background:transparent;}
.block-container {padding-top:1.5rem; max-width:1500px;}
html, body, .stApp {font-family:"Segoe UI","Helvetica Neue",Arial,sans-serif;}

/* dark sidebar */
section[data-testid="stSidebar"] {background:#16222e;}
section[data-testid="stSidebar"] * {color:#d7e0e8;}
section[data-testid="stSidebar"] [data-baseweb="input"],
section[data-testid="stSidebar"] [data-baseweb="base-input"],
section[data-testid="stSidebar"] [data-testid="stNumberInputContainer"],
section[data-testid="stSidebar"] [data-testid="stNumberInputContainer"] > div,
section[data-testid="stSidebar"] input {background:#1d2e3d !important; border-color:#34495c !important;}
section[data-testid="stSidebar"] input {color:#f1f5f8 !important; -webkit-text-fill-color:#f1f5f8 !important;}
section[data-testid="stSidebar"] [data-testid="stNumberInputStepDown"],
section[data-testid="stSidebar"] [data-testid="stNumberInputStepUp"] {background:#25384a !important;}
section[data-testid="stSidebar"] [data-testid="stForm"] {border:none; padding:0;}
section[data-testid="stSidebar"] [data-testid="stFormSubmitButton"] button {
    background:#e3a52f; border:none; font-weight:650; padding:.6rem 0;}
section[data-testid="stSidebar"] [data-testid="stFormSubmitButton"] button * {color:#15202b !important;}
section[data-testid="stSidebar"] [data-testid="stFormSubmitButton"] button:hover {background:#f0b948;}
.side-title {font-size:1.25rem; font-weight:650; color:#ffffff; margin:.2rem 0 0;}
.side-sub {font-size:.8rem; color:#8fa5b8; margin-bottom:.6rem;}
.side-h {font-size:.84rem; font-weight:650; color:#8fb4d3; border-bottom:1px solid #2a3e50;
    margin:.9rem 0 .35rem; padding-bottom:.2rem;}

/* header */
.hero {border-bottom:2px solid #1f3548; padding-bottom:.55rem; margin-bottom:.9rem;}
.hero h1 {font-size:1.9rem; font-weight:700; color:#15222e; margin:0; padding:0;}
.hero p {color:#546674; margin:.2rem 0 0; font-size:.95rem;}

/* result cards */
.kpi {background:#fff; border:1px solid #dbe2e8; border-left:5px solid var(--c); border-radius:6px;
    padding:.7rem .95rem; margin-bottom:.8rem;}
.kpi.blue {--c:#2f6f9f;} .kpi.red {--c:#c0503f;} .kpi.amber {--c:#d38b0b;} .kpi.green {--c:#3d8b5e;}
.kpi-label {font-size:.82rem; color:#586a78;}
.kpi-value {font-size:1.6rem; font-weight:650; color:#15222e; line-height:1.3; font-variant-numeric:tabular-nums;}
.kpi-value.sm {font-size:1.2rem; padding:.2rem 0;}
.kpi-unit {font-size:.85rem; font-weight:500; color:#586a78; margin-left:.3rem;}
.kpi-note {font-size:.78rem; color:#6b7b88; min-height:1.1em;}

/* tables */
.panel-title {font-size:1.02rem; font-weight:650; color:#15222e; margin:.2rem 0 .45rem;}
.rt {width:100%; border-collapse:collapse; background:#fff; border:1px solid #dbe2e8; margin-bottom:.8rem;}
.rt th {background:#e7edf2; color:#2b3d4c; font-size:.82rem; text-align:left; padding:.45rem .7rem;}
.rt td {padding:.42rem .7rem; border-top:1px solid #edf1f4; font-size:.9rem; color:#1c2b37;}
.rt td.v {text-align:right; font-weight:600; font-variant-numeric:tabular-nums;}
.rt td.u {color:#6b7b88; width:5.5rem;}
.rt tr.hl td {background:#fdf4e1;}

[data-testid="stPlotlyChart"] {background:#fff; border:1px solid #dbe2e8; border-radius:6px; padding:.25rem;}
button[data-baseweb="tab"] {font-weight:600;}
</style>
""",
    unsafe_allow_html=True,
)


def fmt(x, n=2):
    return f"{float(x):,.{n}f}"


def card(label, value, unit="", note="", tone="blue"):
    return (f'<div class="kpi {tone}"><div class="kpi-label">{label}</div>'
            f'<div class="kpi-value{" sm" if len(str(value)) > 9 else ""}">{value}<span class="kpi-unit">{unit}</span></div>'
            f'<div class="kpi-note">{note}</div></div>')


def cards(items):
    cols = st.columns(len(items))
    for col, item in zip(cols, items):
        col.markdown(card(*item), unsafe_allow_html=True)


def table(rows, header=("Quantity", "Value", "Unit"), highlight=()):
    html = "<table class='rt'><tr>" + "".join(f"<th>{h}</th>" for h in header) + "</tr>"
    for i, (name, val, unit) in enumerate(rows):
        cls = " class='hl'" if i in highlight else ""
        html += f"<tr{cls}><td>{name}</td><td class='v'>{val}</td><td class='u'>{unit}</td></tr>"
    st.markdown(html + "</table>", unsafe_allow_html=True)


def bars_text(dia, spacing):
    return f"{dia:.0f} mm @ {spacing:.0f} mm c/c" if spacing > 0 else "no valid spacing"


def style(fig, height=420, **kw):
    fig.update_layout(
        template="plotly_white", height=height, margin=dict(l=55, r=25, t=55, b=45),
        paper_bgcolor="#ffffff", plot_bgcolor="#ffffff",
        font=dict(family=FONT, size=12, color="#1c2833"),
        legend=dict(orientation="h", yanchor="bottom", y=1.0, xanchor="right", x=1.0), **kw)
    fig.update_xaxes(gridcolor="#e8edf1", zeroline=False)
    fig.update_yaxes(gridcolor="#e8edf1", zeroline=False)
    return fig


def title(fig, text):
    fig.update_layout(title=dict(text=text, x=0.01, font=dict(size=15)))


def show(fig):
    st.plotly_chart(fig, width="stretch", theme=None)


def ring_levels(length_m, spacing_mm, cap=400):
    """Bar positions used by the original figures: start at s/2, step s."""
    if spacing_mm <= 0:
        return np.array([])
    return np.arange(spacing_mm / 2000, length_m, spacing_mm / 1000)[:cap]


# ------------------------------------------------------------
# SIDEBAR : INPUTS (applied when "Calculate Design" is pressed)
# ------------------------------------------------------------
Dft = sc.DEFAULTS
with st.sidebar:
    st.markdown('<div class="side-title">Silo design inputs</div>'
                '<div class="side-sub">Edit the values, then press Calculate Design.</div>',
                unsafe_allow_html=True)
    with st.form("inputs"):
        st.markdown('<div class="side-h">Geometry</div>', unsafe_allow_html=True)
        D = st.number_input("Silo diameter D (m)", 1.0, 30.0, Dft["D"], 0.1, format="%.2f", key="D")
        h = st.number_input("Cylindrical height h (m)", 0.5, 60.0, Dft["h"], 0.1, format="%.2f", key="h")
        t = st.number_input("Wall thickness t (m)", 0.05, 1.5, Dft["t"], 0.01, format="%.3f", key="t")
        hh = st.number_input("Hopper height hh (m)", 0.2, 30.0, Dft["hh"], 0.05, format="%.2f", key="hh")
        d2 = st.number_input("Outlet diameter d2 (m)", 0.1, 10.0, Dft["d2"], 0.05, format="%.2f", key="d2")

        st.markdown('<div class="side-h">Stored material</div>', unsafe_allow_html=True)
        w = st.number_input("Coal density w (kN/m³)", 1.0, 30.0, Dft["w"], 0.1, format="%.2f", key="w")
        phi = st.number_input("Angle of repose φ (deg)", 10.0, 60.0, Dft["phi"], 1.0, format="%.1f", key="phi")
        mu = st.number_input("Wall friction coefficient μ'", 0.05, 1.5, Dft["mu"], 0.05, format="%.2f", key="mu")
        K = st.number_input("Lateral pressure coefficient K", 0.05, 1.0, Dft["K"], 0.01, format="%.3f", key="K")
        use_k_phi = st.checkbox("Use K = (1 − sin φ)/(1 + sin φ) instead", value=False, key="use_k_phi",
                                help="Ticked: K is computed from φ when you press Calculate Design "
                                     "and the K value above is ignored.")

        st.markdown('<div class="side-h">Materials and loading</div>', unsafe_allow_html=True)
        gc = st.number_input("Unit weight of concrete γc (kN/m³)", 15.0, 30.0, Dft["gc"], 0.5, format="%.1f", key="gc")
        gf = st.number_input("Load factor γf", 1.0, 3.0, Dft["gf"], 0.05, format="%.2f", key="gf")
        fy = st.number_input("Steel yield strength fy (MPa)", 250.0, 700.0, Dft["fy"], 5.0, format="%.0f", key="fy")
        fck = st.number_input("Concrete strength fck (MPa)", 10.0, 80.0, Dft["fck"], 1.0, format="%.0f", key="fck",
                              help="Kept as an input as in the original script, but none of its formulas use fck.")
        bar = st.number_input("Wall bar diameter (mm)", 6.0, 32.0, Dft["bar"], 1.0, format="%.0f", key="bar")

        st.form_submit_button("Calculate Design", type="primary", width="stretch")

K_used = float(sc.k_from_phi(phi)) if use_k_phi else K

# ------------------------------------------------------------
# CALCULATE (calls the real functions in silo_calc.py)
# ------------------------------------------------------------
st.markdown('<div class="hero"><h1>RC coal silo design</h1>'
            "<p>Janssen pressure analysis, cylindrical wall and hopper reinforcement</p></div>",
            unsafe_allow_html=True)

if d2 >= D:
    st.error("Outlet diameter d2 must be smaller than the silo diameter D. Reduce d2 or increase D.")
    st.stop()

with np.errstate(all="ignore"):
    res = sc.design(D=D, h=h, t=t, hh=hh, d2=d2, w=w, phi=phi, mu=mu, gc=gc, gf=gf,
                    fy=fy, fck=fck, bar=bar, K=K_used)

W, A, B, HP = res["wall"], res["A"], res["B"], res["hopper"]
Ht = res["Ht"]
P = dict(D=D, w=w, mu=mu, K=K_used)

# warnings that depend on the current inputs
if not use_k_phi and abs(K - float(sc.k_from_phi(phi))) > 0.02:
    st.info(f"K = {K:.3f} differs from (1 − sin φ)/(1 + sin φ) = {float(sc.k_from_phi(phi)):.3f} "
            f"for φ = {phi:.0f}°. The calculation uses the K you entered.")
if W["spacing"] <= 0:
    st.error("Wall hoop steel: the required area cannot be provided with this bar diameter at 10 mm "
             "spacing or more. Increase the bar diameter or the wall thickness.")
if A["spacing"] <= 0:
    st.error("Hopper Method A: no valid bar spacing with this bar diameter. Increase the bar diameter.")
if B["spacing"] <= 0:
    st.error("Hopper Method B: no valid bar spacing even with 16 mm bars. Increase the wall thickness.")
elif not B["spacing_ok"]:
    st.warning("Hopper Method B: even 16 mm bars give less than 100 mm spacing. "
               "Consider a thicker hopper wall.")

tab_over, tab_press, tab_wall, tab_hop, tab_par, tab_3d = st.tabs(
    ["Overview", "Janssen pressure", "Cylindrical wall", "Hopper design", "Parametric study", "3D silo"])

# ------------------------------------------------------------
# 1. OVERVIEW
# ------------------------------------------------------------
with tab_over:
    cards([("Silo diameter D", fmt(D), "m", f"Wall thickness t = {t * 1000:.0f} mm", "blue"),
           ("Cylindrical height h", fmt(h), "m", "", "blue"),
           ("Hopper height hh", fmt(hh), "m", f"Outlet d2 = {d2:.2f} m", "blue"),
           ("Total height", fmt(Ht), "m", "h + hh", "blue")])
    cards([("Horizontal pressure ph", fmt(res["ph_base"]), "kN/m²", f"at depth h = {h:.2f} m", "red"),
           ("Vertical pressure pv", fmt(res["pv_base"]), "kN/m²", f"pv = ph / K, K = {K_used:.3f}", "red"),
           ("Wall friction μ·ph", fmt(res["fric_base"]), "kN/m²", "at the base of the cylinder", "red"),
           ("Ultimate hoop tension Tu", fmt(W["Tu"]), "kN/m", f"T = {W['T']:.2f} kN/m, γf = {gf:.2f}", "amber")])
    cards([("Wall hoop steel required", fmt(W["Ast"], 1), "mm²/m", f"Minimum 0.12 %: {W['Amin']:.0f} mm²/m", "amber"),
           ("Wall hoop steel provided", bars_text(bar, W["spacing"]), "", f"{fmt(W['provided'], 0)} mm²/m", "green"),
           ("Hopper, Method A", bars_text(A["dia"], A["spacing"]), "", f"Ast required {A['Ast']:.1f} mm²/m", "green"),
           ("Hopper, Method B", bars_text(B["dia"], B["spacing"]), "", f"Ast required {B['Ast']:.0f} mm²/m", "green")])

    left, right = st.columns([1.15, 1])
    with left:
        a_, b_ = D / 2, d2 / 2
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=[-a_, a_, a_, b_, -b_, -a_], y=[0, 0, -h, -Ht, -Ht, -h], mode="none",
                                 fill="toself", fillcolor="rgba(60,60,60,0.7)", name="Coal", hoverinfo="skip"))
        for xs, ys in (([-a_, -a_, -b_], [0, -h, -Ht]), ([a_, a_, b_], [0, -h, -Ht]), ([-b_, b_], [-Ht, -Ht])):
            fig.add_trace(go.Scatter(x=xs, y=ys, mode="lines", line=dict(color="#56626e", width=7),
                                     showlegend=False, hoverinfo="skip"))
        lv = ring_levels(h, W["spacing"])
        if len(lv):
            fig.add_trace(go.Scatter(x=np.r_[-np.full(len(lv), a_), np.full(len(lv), a_)], y=-np.r_[lv, lv],
                                     mode="markers", marker=dict(color=C_PH, size=5),
                                     name=f"Hoop bars {bars_text(bar, W['spacing'])}"))
        zz = np.linspace(0, h, 40)
        fig.add_trace(go.Scatter(x=a_ + 0.2 + sc.ph(zz, **P) / res["ph_base"] * 1.2, y=-zz, mode="lines",
                                 line=dict(color=C_PH, width=2.5), name="ph on wall"))
        fig.add_trace(go.Scatter(x=[a_ + 0.2, a_ + 0.2], y=[0, -h], mode="lines", line=dict(color=C_PH, width=1),
                                 showlegend=False, hoverinfo="skip"))
        for x_, y_, txt in ((0, 0.35, f"D = {D:.2f} m"), (-a_ - 0.6, -h / 2, f"h = {h:.2f} m"),
                            (-a_ - 0.6, -h - hh / 2, f"hh = {hh:.2f} m"), (0, -Ht - 0.35, f"d2 = {d2:.2f} m")):
            fig.add_annotation(x=x_, y=y_, text=txt, showarrow=False, font=dict(size=12))
        style(fig, 470)
        title(fig, "Section and wall pressure")
        fig.update_xaxes(visible=False, range=[-a_ - 1.1, a_ + 1.9])
        fig.update_yaxes(visible=False, scaleanchor="x", scaleratio=1)
        show(fig)
    with right:
        st.markdown('<div class="panel-title">Reinforcement schedule</div>', unsafe_allow_html=True)
        st.markdown(
            "<table class='rt'><tr><th>Element</th><th>Required (mm²/m)</th><th>Provided</th></tr>"
            f"<tr><td>Wall, hoop</td><td class='v'>{W['Ast']:.1f}</td><td class='v'>{bars_text(bar, W['spacing'])}</td></tr>"
            "<tr><td>Wall, vertical</td><td class='v'>-</td><td class='v'>8 mm @ 300 mm c/c</td></tr>"
            f"<tr><td>Hopper, Method A</td><td class='v'>{A['Ast']:.1f}</td><td class='v'>{bars_text(A['dia'], A['spacing'])}</td></tr>"
            f"<tr><td>Hopper, Method B</td><td class='v'>{B['Ast']:.0f}</td><td class='v'>{bars_text(B['dia'], B['spacing'])}</td></tr>"
            "</table>", unsafe_allow_html=True)
        st.markdown('<div class="panel-title">Input summary</div>', unsafe_allow_html=True)
        table([("Angle of repose φ", fmt(phi, 1), "deg"), ("Wall friction μ'", fmt(mu), ""),
               ("Lateral pressure coefficient K", fmt(K_used, 3), ""), ("Coal density w", fmt(w), "kN/m³"),
               ("Concrete unit weight γc", fmt(gc, 1), "kN/m³"), ("Steel yield strength fy", fmt(fy, 0), "MPa"),
               ("Concrete strength fck", fmt(fck, 0), "MPa")])

# ------------------------------------------------------------
# 2. JANSSEN PRESSURE
# ------------------------------------------------------------
with tab_press:
    cards([("Horizontal pressure ph", fmt(res["ph_base"]), "kN/m²", f"at z = h = {h:.2f} m", "red"),
           ("Vertical pressure pv", fmt(res["pv_base"]), "kN/m²", "at z = h", "blue"),
           ("Wall friction μ·ph", fmt(res["fric_base"]), "kN/m²", "at z = h", "green"),
           ("Hydraulic radius R = D/4", fmt(res["R"]), "m", "", "amber")])

    rng = st.radio("Depth range for the graph", ["Cylinder and hopper (as in the original figure)", "Cylinder only"],
                   horizontal=True, key="press_range")
    zmax = Ht if rng.startswith("Cylinder and") else h
    z_all = np.linspace(0, zmax, 100)
    ph_c, pv_c, fr_c = sc.pressure_profile(z_all, **P)
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=ph_c, y=z_all, name="ph (horizontal)", line=dict(color=C_PH, width=3)))
    fig.add_trace(go.Scatter(x=pv_c, y=z_all, name="pv (vertical)", line=dict(color=C_PV, width=3)))
    fig.add_trace(go.Scatter(x=fr_c, y=z_all, name="Wall friction μ·ph", line=dict(color=C_FR, width=3)))
    if zmax > h:
        fig.add_hline(y=h, line_dash="dash", line_color="#8996a1",
                      annotation_text="cylinder / hopper", annotation_position="bottom right")
    style(fig, 470)
    title(fig, "Janssen pressure against depth")
    fig.update_xaxes(title="Pressure (kN/m²)")
    fig.update_yaxes(title="Depth z (m)", autorange="reversed")
    show(fig)

    c1, c2 = st.columns([1.4, 1])
    with c1:
        st.markdown('<div class="panel-title">Pressures at selected depths</div>', unsafe_allow_html=True)
        n_st = st.slider("Number of depth stations", 3, 25, 5, key="n_stations")
        tab_rng = st.radio("Table range", ["Cylinder (0 to h)", "Full height (0 to h + hh)"], horizontal=True,
                           key="table_range")
        zt = np.linspace(0, h if tab_rng.startswith("Cylinder") else Ht, n_st)
        a1, a2, a3 = sc.pressure_profile(zt, **P)
        df = pd.DataFrame({"Depth z (m)": zt, "ph (kN/m²)": a1, "pv (kN/m²)": a2, "μ·ph (kN/m²)": a3})
        st.dataframe(df.style.format("{:.2f}"), hide_index=True, width="stretch")
    with c2:
        st.markdown('<div class="panel-title">Pressure at one depth</div>', unsafe_allow_html=True)
        zq = st.number_input("Depth z (m)", 0.0, float(Ht), float(h), 0.1, format="%.2f", key="zq")
        q1, q2, q3 = sc.pressure_profile(zq, **P)
        table([("Horizontal pressure ph", fmt(q1), "kN/m²"), ("Vertical pressure pv", fmt(q2), "kN/m²"),
               ("Wall friction μ·ph", fmt(q3), "kN/m²")])

# ------------------------------------------------------------
# 3. CYLINDRICAL WALL
# ------------------------------------------------------------
with tab_wall:
    cards([("Hoop tension T", fmt(W["T"]), "kN/m", "T = ph × D / 2", "blue"),
           ("Ultimate tension Tu", fmt(W["Tu"]), "kN/m", f"Tu = {gf:.2f} × T", "red"),
           ("Steel required", fmt(W["Ast"], 1), "mm²/m", "Tu / (0.87 fy)", "amber"),
           ("Minimum steel (0.12 %)", fmt(W["Amin"], 0), "mm²/m", "0.0012 × 1000 × t", "amber")])
    cards([("Provided hoop steel", bars_text(bar, W["spacing"]), "", f"Ast provided = {fmt(W['provided'], 0)} mm²/m", "green"),
           ("Vertical reinforcement", "8 mm @ 300 mm c/c", "", "fixed value, as in the original script", "green"),
           ("Governing steel", "Minimum" if W["Amin"] >= W["Ast"] else "Calculated", "",
            "larger of required and minimum", "blue"),
           ("Utilisation of provided steel", fmt(100 * max(W["Ast"], W["Amin"]) / W["provided"], 0)
            if W["spacing"] > 0 else "-", "%", "governing / provided", "blue")])

    z_w = np.linspace(0, h, 100)
    T_w, Tu_w, Ast_w = sc.wall_profile(z_w, gf=gf, fy=fy, **P)
    fig = make_subplots(rows=1, cols=2, shared_yaxes=True, horizontal_spacing=0.06,
                        subplot_titles=("Hoop tension in wall", "Hoop steel"))
    fig.add_trace(go.Scatter(x=T_w, y=z_w, name="T", line=dict(color=C_PV, width=3)), row=1, col=1)
    fig.add_trace(go.Scatter(x=Tu_w, y=z_w, name=f"Tu = {gf:g} T", line=dict(color=C_PH, width=3)), row=1, col=1)
    fig.add_trace(go.Scatter(x=Ast_w, y=z_w, name="Ast required", line=dict(color=C_PV, width=3)), row=1, col=2)
    fig.add_vline(x=W["Amin"], line_dash="dash", line_color="#2b3d4c", row=1, col=2,
                  annotation_text="Minimum 0.12 %", annotation_position="top left")
    if W["spacing"] > 0:
        fig.add_vline(x=W["provided"], line_color=C_FR, line_width=3, row=1, col=2,
                      annotation_text=f"Provided {bars_text(bar, W['spacing'])}", annotation_position="bottom right")
    style(fig, 470)
    fig.update_xaxes(title_text="Hoop tension (kN/m)", row=1, col=1)
    fig.update_xaxes(title_text="Steel (mm²/m)", row=1, col=2)
    fig.update_yaxes(title_text="Depth z (m)", autorange="reversed", row=1, col=1)
    fig.update_yaxes(autorange="reversed", row=1, col=2)
    show(fig)

# ------------------------------------------------------------
# 4. HOPPER
# ------------------------------------------------------------
with tab_hop:
    cards([("Hopper angle", fmt(HP["theta_deg"]), "deg", "slope to the horizontal", "blue"),
           ("Slant length", fmt(HP["slant"]), "m", "", "blue"),
           ("Mean diameter", fmt(HP["dm"]), "m", "(D + d2) / 2", "blue")])
    col_a, col_b = st.columns(2)
    with col_a:
        st.markdown('<div class="panel-title">Method A (class notes)</div>', unsafe_allow_html=True)
        table([("Self-weight of hopper", fmt(A["self_w"], 3), "kN"),
               ("Surcharge", fmt(A["surcharge"]), "kN/m²"),
               ("Coal weight", "not included", ""),
               ("Ultimate load", fmt(A["Wu"]), ""),
               ("Tension T", fmt(A["T"]), "kN/m"),
               ("Steel required", fmt(A["Ast"], 2), "mm²/m"),
               ("Minimum steel (0.12 %)", fmt(A["Amin"], 0), "mm²/m"),
               ("Provided bars", bars_text(A["dia"], A["spacing"]), ""),
               ("Steel provided", fmt(A["provided"], 0) if A["spacing"] > 0 else "-", "mm²/m")], highlight=(7,))
    with col_b:
        st.markdown('<div class="panel-title">Method B (corrected)</div>', unsafe_allow_html=True)
        table([("Self-weight of hopper", fmt(B["self_w"], 1), "kN"),
               ("Surcharge pv × plan area", fmt(B["surcharge"], 1), "kN"),
               ("Coal inside hopper", fmt(B["coal"], 1), "kN"),
               ("Ultimate load", fmt(B["Wu"], 1), "kN"),
               ("Tension T", fmt(B["T"], 1), "kN/m"),
               ("Steel required", fmt(B["Ast"], 0), "mm²/m"),
               ("Minimum steel (0.12 %)", fmt(B["Amin"], 0), "mm²/m"),
               ("Provided bars", bars_text(B["dia"], B["spacing"]), ""),
               ("Steel provided", fmt(B["provided"], 0) if B["spacing"] > 0 else "-", "mm²/m")], highlight=(7,))
    st.caption("Method A is calculated exactly as in the class-notes section of the script. Method B tries 8, 10, 12 "
               "and 16 mm bars and stops at the first one giving at least 100 mm spacing.")

    fig = make_subplots(rows=1, cols=3, horizontal_spacing=0.08,
                        subplot_titles=("Ultimate load (kN)", "Tension in slab (kN/m)", "Ast required (mm²/m)"))
    for i, (va, vb) in enumerate(((A["Wu"], B["Wu"]), (A["T"], B["T"]), (A["Ast"], B["Ast"])), start=1):
        fig.add_trace(go.Bar(x=["Method A", "Method B"], y=[float(va), float(vb)], marker_color=["#8d98a3", C_PH],
                             text=[f"{float(va):.1f}", f"{float(vb):.1f}"], textposition="outside",
                             showlegend=False, cliponaxis=False), row=1, col=i)
    style(fig, 400)
    fig.update_layout(margin=dict(l=55, r=25, t=70, b=40))
    show(fig)

# ------------------------------------------------------------
# 5. PARAMETRIC STUDY
# ------------------------------------------------------------
with tab_par:
    st.caption("Ranges below are used for the three graphs. All other values come from the sidebar design.")
    c1, c2, c3 = st.columns(3)
    with c1:
        st.markdown('<div class="panel-title">Coal density</div>', unsafe_allow_html=True)
        d_lo = st.number_input("From (kN/m³)", 0.5, 50.0, 6.0, 0.5, key="d_lo")
        d_hi = st.number_input("To (kN/m³)", 0.5, 50.0, 12.0, 0.5, key="d_hi")
        d_n = st.slider("Points", 5, 100, 25, key="d_n")
    with c2:
        st.markdown('<div class="panel-title">Wall friction</div>', unsafe_allow_html=True)
        m_lo = st.number_input("From μ'", 0.05, 1.5, 0.3, 0.05, key="m_lo")
        m_hi = st.number_input("To μ'", 0.05, 1.5, 0.8, 0.05, key="m_hi")
        m_n = st.slider("Points", 5, 100, 25, key="m_n")
        angles = st.multiselect("Angles of repose φ (deg), K from each φ", list(range(15, 51)),
                                default=[25, 30, 35], key="angles")
    with c3:
        st.markdown('<div class="panel-title">Silo diameter</div>', unsafe_allow_html=True)
        s_lo = st.number_input("From D (m)", 0.5, 40.0, 3.0, 0.5, key="s_lo")
        s_hi = st.number_input("To D (m)", 0.5, 40.0, 8.0, 0.5, key="s_hi")
        s_n = st.slider("Points", 5, 100, 26, key="s_n")

    g1, g2, g3 = st.columns(3)
    with g1:
        if d_lo < d_hi:
            dens = np.linspace(d_lo, d_hi, d_n)
            fig = go.Figure(go.Scatter(x=dens, y=sc.tu_vs_density(dens, D, h, mu, K_used, gf),
                                       line=dict(color=C_PH, width=3), name="Tu"))
            fig.add_trace(go.Scatter(x=[w], y=[W["Tu"]], mode="markers", name="Current design",
                                     marker=dict(color="#15222e", size=11, symbol="diamond")))
            style(fig, 400)
            title(fig, "Tu against coal density")
            fig.update_xaxes(title="Density of coal (kN/m³)")
            fig.update_yaxes(title="Tu (kN/m)")
            show(fig)
        else:
            st.warning("Density: 'From' must be smaller than 'To'.")
    with g2:
        if m_lo < m_hi and angles:
            fr = np.linspace(m_lo, m_hi, m_n)
            palette = ["#2f6f9f", "#d38b0b", "#3d8b5e", "#8a5fb0", "#c0503f", "#4a5b69"]
            fig = go.Figure()
            for i, ang in enumerate(sorted(angles)):
                fig.add_trace(go.Scatter(x=fr, y=sc.tu_vs_friction(fr, ang, D, h, w, gf), name=f"φ = {ang}",
                                         line=dict(color=palette[i % len(palette)], width=3)))
            fig.add_vline(x=mu, line_dash="dash", line_color="#15222e",
                          annotation_text="current μ'", annotation_position="top")
            style(fig, 400)
            title(fig, "Tu against wall friction")
            fig.update_xaxes(title="Wall friction μ'")
            fig.update_yaxes(title="Tu (kN/m)")
            show(fig)
        else:
            st.warning("Friction: 'From' must be smaller than 'To' and at least one angle must be selected.")
    with g3:
        if s_lo < s_hi:
            dias = np.linspace(s_lo, s_hi, s_n)
            fig = go.Figure(go.Scatter(x=dias, y=sc.tu_vs_diameter(dias, h, w, mu, K_used, gf),
                                       line=dict(color=C_FR, width=3), name="Tu"))
            fig.add_trace(go.Scatter(x=[D], y=[W["Tu"]], mode="markers", name="Current design",
                                     marker=dict(color="#15222e", size=11, symbol="diamond")))
            style(fig, 400)
            title(fig, "Tu against silo diameter")
            fig.update_xaxes(title="Diameter (m)")
            fig.update_yaxes(title="Tu (kN/m)")
            show(fig)
        else:
            st.warning("Diameter: 'From' must be smaller than 'To'.")

# ------------------------------------------------------------
# 6. 3D MODEL
# ------------------------------------------------------------
with tab_3d:
    o1, o2, o3, o4 = st.columns(4)
    show_concrete = o1.checkbox("Concrete shell", True, key="v_conc")
    show_coal = o1.checkbox("Coal", True, key="v_coal")
    show_hoop = o2.checkbox("Hoop bars", True, key="v_hoop")
    show_vert = o2.checkbox("Vertical bars", True, key="v_vert")
    conc_op = o3.slider("Concrete opacity", 0.05, 0.8, 0.25, 0.05, key="v_op")
    hop_method = o4.radio("Hopper bars shown for", ["Method A", "Method B"], horizontal=True, key="v_meth",
                          help="The original 3D figure draws the hopper rings at the Method A spacing.")
    hop = A if hop_method == "Method A" else B

    a_, b_ = D / 2, d2 / 2
    th = np.linspace(0, 2 * np.pi, 73)
    flat = lambda c: [[0, c], [1, c]]
    fig = go.Figure()

    def surf(rad, z, color, opacity):
        rad, z = np.asarray(rad), np.asarray(z)
        fig.add_trace(go.Surface(x=np.outer(rad, np.cos(th)), y=np.outer(rad, np.sin(th)),
                                 z=np.outer(z, np.ones_like(th)), colorscale=flat(color), showscale=False,
                                 opacity=opacity, hoverinfo="skip", lighting=dict(ambient=0.8)))

    zh = np.linspace(-h, -Ht, 10)
    if show_concrete:
        surf([a_, a_], [0, -h], "#b9c2ca", conc_op)
        surf(a_ + (zh + h) / (-hh) * (b_ - a_), zh, "#b9c2ca", conc_op)
    if show_coal:
        ai, bi = a_ - t, max(b_ - t, 0.02)
        surf([ai, ai], [0, -h], "#2b2b2b", 0.55)
        surf(ai + (zh + h) / (-hh) * (bi - ai), zh, "#2b2b2b", 0.55)
        surf([0, ai], [0, 0], "#111111", 0.95)   # coal top surface

    rm = a_ - t / 2
    if show_hoop:
        xs, ys, zs = [], [], []
        for lv in ring_levels(h, W["spacing"]):
            xs += [*(rm * np.cos(th)), np.nan]; ys += [*(rm * np.sin(th)), np.nan]; zs += [*np.full(len(th), -lv), np.nan]
        if xs:
            fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", line=dict(color="#e2552f", width=3),
                                       name=f"Wall hoop bars {bars_text(bar, W['spacing'])}", hoverinfo="skip"))
        xs, ys, zs = [], [], []
        if hop["spacing"] > 0:
            n_rings = int(min(np.ceil(HP["slant"] / (hop["spacing"] / 1000)), 40))
            for i in range(1, n_rings + 1):
                u = i / (n_rings + 1)
                r_i = rm - u * (D - d2) / 2
                xs += [*(r_i * np.cos(th)), np.nan]; ys += [*(r_i * np.sin(th)), np.nan]
                zs += [*np.full(len(th), -h - u * hh), np.nan]
        if xs:
            fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", line=dict(color="#d9a21b", width=3),
                                       name=f"Hopper hoop bars {bars_text(hop['dia'], hop['spacing'])}",
                                       hoverinfo="skip"))
    if show_vert:
        count = int(min(np.floor(np.pi * D / 0.3), 60))
        xs, ys, zs = [], [], []
        for i in range(count):
            ang = 2 * np.pi * i / count
            xs += [rm * np.cos(ang)] * 2 + [np.nan]; ys += [rm * np.sin(ang)] * 2 + [np.nan]; zs += [0, -h, np.nan]
        fig.add_trace(go.Scatter3d(x=xs, y=ys, z=zs, mode="lines", line=dict(color="#3b7bb5", width=2),
                                   name="Vertical bars 8 mm @ 300 mm c/c", hoverinfo="skip"))
    # outlet ring and dimension labels
    fig.add_trace(go.Scatter3d(x=b_ * np.cos(th), y=b_ * np.sin(th), z=np.full(len(th), -Ht), mode="lines",
                               line=dict(color="#15222e", width=7), name="Outlet", hoverinfo="skip"))
    fig.add_trace(go.Scatter3d(x=[0, a_ * 1.5, a_ * 1.1, 0], y=[0, 0, 0, 0],
                               z=[0.3, -h / 2, -h - hh / 2, -Ht - 0.35], mode="text", showlegend=False,
                               text=[f"D = {D:.2f} m", f"h = {h:.2f} m", f"hh = {hh:.2f} m", f"d2 = {d2:.2f} m"],
                               textfont=dict(size=13, color="#15222e"), hoverinfo="skip"))
    fig.update_layout(
        height=680, margin=dict(l=0, r=0, t=10, b=0), paper_bgcolor="#ffffff", font=dict(family=FONT),
        legend=dict(orientation="h", y=0.02, x=0.01),
        scene=dict(aspectmode="data", xaxis_title="x (m)", yaxis_title="y (m)", zaxis_title="height (m)",
                   camera=dict(eye=dict(x=0.95, y=-1.4, z=0.95))))
    show(fig)
    st.caption("Drag to rotate, scroll to zoom, double-click to reset the view. Dimensions follow the sidebar inputs.")

st.markdown("<div style='color:#7a8a97;font-size:.8rem;margin-top:1rem'>Formulas: silo_calc.py "
            "(copied from silo_design.py). Check results against your class notes and the applicable code "
            "before using them for any real design.</div>", unsafe_allow_html=True)
