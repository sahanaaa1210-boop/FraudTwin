import streamlit as st
import pandas as pd
import altair as alt

from .config import RISK_COLORS

THEMES = {
    "Dark": {
        "bg": "#0B0A0F",
        "sidebar": "#111018",
        "surface": "#171522",
        "surface_elevated": "#211A2B",
        "text": "#F5F3F7",
        "muted": "#AAA3B5",
        "border": "#30283A",
        "canvas": "#0B0A0F",
        "white": "#171522",
        "surface_rgb": "23,21,34",
        "elevated_rgb": "33,26,43",
        "bg_rgb": "11,10,15",
        "border_rgb": "48,40,58",
        "input_bg": "#111018",
        "shadow": "rgba(0,0,0,0.20)",
        "shadow_strong": "rgba(0,0,0,0.28)",
    },
    "Light": {
        "bg": "#F7F5FB",
        "sidebar": "#FFFFFF",
        "surface": "#FFFFFF",
        "surface_elevated": "#F3EFFA",
        "text": "#1A1625",
        "muted": "#6B6478",
        "border": "#E1DBEC",
        "canvas": "#F7F5FB",
        "white": "#FFFFFF",
        "surface_rgb": "255,255,255",
        "elevated_rgb": "243,239,250",
        "bg_rgb": "247,245,251",
        "border_rgb": "225,219,236",
        "input_bg": "#FFFFFF",
        "shadow": "rgba(80,60,120,0.08)",
        "shadow_strong": "rgba(80,60,120,0.12)",
    },
}

# Brand/accent colors stay constant across both themes.
ACCENT = {
    "bronze": "#542B72",
    "accent": "#9B4DFF",
    "gold": "#D8B5FF",
    "magenta": "#D946EF",
    "success": "#45A56A",
    "error": "#E05260",
    "accent_light": "#C4B5FD",
    "live_good": "#6EE7A8",
    "live_alert": "#F3C86B",
    "ai_text": "#E8E3EE",
}


def inject_css(theme="Dark"):
    t = THEMES.get(theme, THEMES["Dark"])
    a = ACCENT

    st.markdown(f"""
    <style>
    :root {{
        --ft-bg: {t["bg"]};
        --ft-sidebar: {t["sidebar"]};
        --ft-surface: {t["surface"]};
        --ft-surface-elevated: {t["surface_elevated"]};
        --ft-bronze: {a["bronze"]};
        --ft-accent: {a["accent"]};
        --ft-gold: {a["gold"]};
        --ft-magenta: {a["magenta"]};
        --ft-text: {t["text"]};
        --ft-muted: {t["muted"]};
        --ft-border: {t["border"]};
        --ft-success: {a["success"]};
        --ft-error: {a["error"]};
        --ft-brand: {t["text"]};
        --ft-canvas: {t["canvas"]};
        --ft-body: {t["text"]};
        --ft-white: {t["white"]};
    }}

    html, body, [data-testid="stAppViewContainer"], .stApp {{
        overflow-x: hidden !important;
        background: {t["bg"]} !important;
    }}

    /* Rich pictorial background: abstract AI-fintech command center */
    [data-testid="stAppViewContainer"]::before {{
        content: "";
        position: fixed;
        inset: 0;
        pointer-events: none;
        z-index: 0;
        opacity: 1;
        background:
            radial-gradient(ellipse 520px 330px at 86% 18%, rgba(155,77,255,0.20), transparent 68%),
            radial-gradient(ellipse 430px 300px at 72% 72%, rgba(217,70,239,0.13), transparent 70%),
            radial-gradient(ellipse 360px 260px at 12% 44%, rgba(84,43,114,0.16), transparent 72%),
            linear-gradient(rgba(196,181,253,0.035) 1px, transparent 1px),
            linear-gradient(90deg, rgba(196,181,253,0.035) 1px, transparent 1px);
        background-size: auto, auto, auto, 48px 48px, 48px 48px;
    }}
    .main > div {{ position: relative; z-index: 1; }}

    /* Decorative fintech network: charts, nodes, radar and data columns */
    .ft-background-art {{
        position: fixed; right: -2vw; top: 7vh; width: 64vw; height: 68vh;
        pointer-events: none; z-index: 0; opacity: .62;
        transform: translateY(0);
    }}
    .ft-background-art svg {{ width: 100%; height: 100%; overflow: visible; }}
    .ft-art-grid {{ stroke: {t["border"]}; stroke-width: 1; opacity: .65; }}
    .ft-art-axis {{ stroke: {t["muted"]}; stroke-width: 1; opacity: .18; }}
    .ft-art-line {{ fill: none; stroke: url(#ftLine); stroke-width: 3; opacity: .72; }}
    .ft-art-line-soft {{ fill: none; stroke: {a["bronze"]}; stroke-width: 2; opacity: .48; }}
    .ft-art-ring {{ fill: none; stroke: {a["accent"]}; stroke-width: 1.5; opacity: .24; }}
    .ft-art-bar {{ fill: {a["bronze"]}; opacity: .42; }}
    .ft-art-bar-bright {{ fill: {a["accent"]}; opacity: .62; }}
    .ft-art-label {{ fill: {t["muted"]}; font-family: sans-serif; font-size: 10px; letter-spacing: 2px; opacity: .34; }}
    .ft-art-panel {{ fill: {t["surface"]}; stroke: {t["border"]}; stroke-width: 1; opacity: .36; }}
    .main > div {{ position: relative; z-index: 1; }}
    [data-testid="stHeader"] {{
        background: {t["bg"]} !important;
    }}
    [data-testid="stSidebar"] {{
        background: {t["sidebar"]} !important;
        border-right: 1px solid {t["border"]} !important;
    }}
    [data-testid="stSidebar"] > div:first-child {{
        background: {t["sidebar"]} !important;
    }}
    [data-testid="stSidebar"] * {{
        color: {t["text"]} !important;
    }}
    /* TRUE FULL-WIDTH WORKSPACE
       Streamlit versions use different wrappers for the main block.
       Target every known wrapper so collapsing the sidebar never leaves a
       centered 1200/1400px column surrounded by empty space. */
    [data-testid="stAppViewContainer"] .main,
    [data-testid="stAppViewContainer"] .main > div,
    [data-testid="stMain"],
    [data-testid="stMain"] > div,
    [data-testid="stMainBlockContainer"],
    [data-testid="stMain"] .block-container,
    .stMainBlockContainer,
    .block-container {{
        width: 100% !important;
        max-width: none !important;
        min-width: 0 !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        box-sizing: border-box !important;
    }}

    [data-testid="stMainBlockContainer"],
    [data-testid="stMain"] .block-container,
    .stMainBlockContainer,
    .block-container {{
        padding-top: 2rem !important;
        padding-bottom: 3rem !important;
        padding-left: clamp(18px, 2vw, 36px) !important;
        padding-right: clamp(18px, 2vw, 36px) !important;
    }}

    /* When the sidebar is collapsed, force the main content to occupy the
       entire viewport rather than retaining Streamlit's centered max width. */
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"],
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] > div,
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] .block-container {{
        width: 100vw !important;
        max-width: 100vw !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
    }}

    .ft-live-panel {{
        background: linear-gradient(135deg, rgba({t["surface_rgb"]},.96), rgba({t["elevated_rgb"]},.92));
        border: 1px solid rgba(155,77,255,.42); border-radius: 16px; padding: 20px 22px;
        box-shadow: 0 12px 35px {t["shadow"]}, inset 0 1px 0 rgba(196,181,253,.06);
        position: relative; overflow: hidden;
    }}
    .ft-live-panel::after {{
        content:""; position:absolute; right:-80px; top:-120px; width:300px; height:300px;
        border-radius:50%; background:radial-gradient(circle, rgba(155,77,255,.14), transparent 68%); pointer-events:none;
    }}
    .ft-live-header {{ display:flex; justify-content:space-between; align-items:flex-start; gap:20px; }}
    .ft-live-title {{ font-size:20px; font-weight:800; color:{t["text"]}; }}
    .ft-live-sub {{ margin-top:3px; font-size:12.5px; color:{t["muted"]}; }}
    .ft-live-status {{ white-space:nowrap; color:#6EE7A8; font-size:11px; font-weight:800; letter-spacing:.5px;
        border:1px solid rgba(110,231,168,.25); background:rgba(69,165,106,.10); padding:7px 10px; border-radius:999px; }}
    .ft-live-dot {{ display:inline-block; width:7px; height:7px; border-radius:50%; background:#6EE7A8; margin-right:6px; box-shadow:0 0 10px rgba(110,231,168,.7); }}
    .ft-live-grid {{ display:grid; grid-template-columns:repeat(4,1fr); gap:10px; margin-top:17px; }}
    .ft-live-metric {{ background:rgba({t["bg_rgb"]},.36); border:1px solid {t["border"]}; border-radius:10px; padding:12px 14px; }}
    .ft-live-metric span {{ display:block; color:{t["muted"]}; font-size:11px; margin-bottom:4px; }}
    .ft-live-metric strong {{ color:{t["text"]}; font-size:22px; }}
    .ft-live-latest {{ margin-top:12px; border-top:1px solid {t["border"]}; padding-top:13px; }}
    .ft-live-latest-label {{ color:{t["muted"]}; font-size:10px; font-weight:800; letter-spacing:1.2px; }}
    .ft-live-latest-main {{ margin-top:5px; color:{t["text"]}; font-size:15px; font-weight:700; }}
    .ft-live-latest-sub {{ margin-top:5px; color:{t["muted"]}; font-size:12px; }}
    .live-good {{ color:#6EE7A8; }} .live-alert {{ color:#F3C86B; }}
    @media (max-width: 900px) {{
        .ft-live-grid {{ grid-template-columns:repeat(2,1fr); }}
        .ft-live-header {{ flex-direction:column; }}
    }}

    h1, h2, h3, h4 {{ color: {t["text"]} !important; font-weight: 700 !important; }}
    p, li, span, label {{ color: {t["text"]}; }}
    [data-testid="stMarkdownContainer"] p, [data-testid="stMarkdownContainer"] li {{ color: {t["text"]} !important; }}
    [data-testid="stMarkdownContainer"] h1, [data-testid="stMarkdownContainer"] h2, [data-testid="stMarkdownContainer"] h3 {{ color: {t["text"]} !important; }}
    small, .stCaption, [data-testid="stCaptionContainer"] {{ color: {t["muted"]} !important; }}

    .ft-hero {{
        position: relative;
        overflow: hidden;
        background: linear-gradient(135deg, {t["surface"]} 0%, {t["surface_elevated"]} 62%, {t["sidebar"]} 100%);
        border: 1px solid {t["border"]};
        border-radius: 18px;
        padding: 30px 32px;
        margin-bottom: 20px;
        box-shadow: 0 12px 35px {t["shadow_strong"]}, inset 0 1px 0 rgba(196,181,253,0.08);
    }}
    .ft-hero::after {{
        content: ""; position: absolute; width: 280px; height: 280px;
        right: -100px; top: -120px; border-radius: 50%;
        background: radial-gradient(circle, rgba(155,77,255,0.18), transparent 68%);
        pointer-events: none;
    }}
    .ft-eyebrow {{
        display: inline-block; font-size: 11px; letter-spacing: 1.5px;
        text-transform: uppercase; color: #C4B5FD; font-weight: 800;
        background: rgba(155,77,255,0.14); border: 1px solid rgba(155,77,255,0.24);
        padding: 6px 12px; border-radius: 999px; margin-bottom: 12px;
    }}
    .ft-hero-title {{ font-size: 34px; font-weight: 800; color: {t["text"]}; margin: 0 0 8px 0; letter-spacing: -0.6px; }}
    .ft-hero-sub {{ font-size: 15px; color: {t["muted"]}; max-width: 760px; line-height: 1.55; margin: 0; }}

    .ft-home-kicker {{ color:{t["muted"]}; font-size:12px; text-transform:uppercase; letter-spacing:1.3px; font-weight:800; margin:0 0 7px 0; }}
    .ft-home-section {{ margin-top: 28px; }}
    .ft-home-cap-card {{
        background: rgba({t["surface_rgb"]},0.94); border:1px solid {t["border"]}; border-radius:14px;
        padding:18px 19px; min-height:156px; transition:all .15s ease;
    }}
    .ft-home-cap-card:hover {{ border-color:rgba(155,77,255,.55); transform:translateY(-2px); box-shadow:0 12px 28px {t["shadow"]}; }}
    .ft-home-cap-icon {{
        display:inline-flex; align-items:center; justify-content:center;
        width:34px; height:34px; margin-bottom:10px;
        border-radius:9px; background:rgba(155,77,255,0.12);
        border:1px solid rgba(155,77,255,0.32);
        color:#C4B5FD; font-size:11px; font-weight:800;
        letter-spacing:.6px;
    }}
    .ft-home-cap-title {{ font-size:15px; font-weight:800; color:{t["text"]}; margin-bottom:6px; }}
    .ft-home-cap-text {{ font-size:12.8px; color:{t["muted"]}; line-height:1.5; }}
    .ft-home-flow {{
        display:flex; align-items:center; gap:8px; flex-wrap:wrap; padding:17px 18px;
        background:rgba({t["surface_rgb"]},.82); border:1px solid {t["border"]}; border-radius:14px;
    }}
    .ft-home-step {{
        display:inline-flex; align-items:center; gap:7px; padding:8px 11px;
        border:1px solid rgba(196,181,253,.16); background:rgba({t["elevated_rgb"]},.72);
        border-radius:999px; color:{t["text"]}; font-size:12px; font-weight:700;
    }}
    .ft-home-arrow {{ color:{t["muted"]}; font-size:15px; }}
    .ft-home-note {{ color:{t["muted"]}; font-size:12px; margin-top:9px; }}

    .ft-card {{
        background: {t["surface"]};
        border: 1px solid {t["border"]};
        border-radius: 14px;
        padding: 22px 22px;
        height: 100%;
        transition: border-color 0.15s ease, transform 0.15s ease;
        box-shadow: 0 2px 10px {t["shadow"]};
    }}
    .ft-card:hover {{ border-color: {a["bronze"]}; transform: translateY(-2px); box-shadow: 0 10px 28px {t["shadow_strong"]}, 0 0 0 1px rgba(201,154,74,0.08); }}
    .ft-card-icon {{ font-size: 26px; margin-bottom: 10px; }}
    .ft-card-title {{ font-size: 16px; font-weight: 700; color: {t["text"]}; margin-bottom: 6px; }}
    .ft-card-text {{ font-size: 13.5px; color: {t["muted"]}; line-height: 1.55; }}

    .ft-section-title {{ font-size: 22px; font-weight: 700; color: {t["text"]}; margin-bottom: 2px; }}
    .ft-section-sub {{ font-size: 14px; color: {t["muted"]}; margin-bottom: 18px; }}

    .ft-badge {{
        display: inline-flex; align-items: center; gap: 8px;
        padding: 6px 16px; border-radius: 999px; font-weight: 700; font-size: 14px;
        border: 1px solid {t["border"]};
    }}
    .ft-score-wrap {{
        display: flex; align-items: center; gap: 28px; flex-wrap: wrap;
        background: {t["surface"]}; border: 1px solid {t["border"]};
        border-radius: 16px; padding: 26px 28px; margin-bottom: 18px;
        box-shadow: 0 2px 10px {t["shadow"]};
    }}
    .ft-score-number {{ font-size: 54px; font-weight: 800; line-height: 1; color: {t["text"]}; }}
    .ft-score-label {{ font-size: 13px; color: {t["muted"]}; text-transform: uppercase; letter-spacing: 1px; }}

    .ft-status-marker {{
        display:inline-flex; align-items:center; justify-content:center;
        min-width:42px; padding:3px 7px; border-radius:6px;
        background:rgba(155,77,255,.12); border:1px solid rgba(155,77,255,.25);
        color:#C4B5FD; font-size:9px; font-weight:800; letter-spacing:.7px;
    }}

    .ft-indicator {{
        display: flex; align-items: center; gap: 10px;
        background: {t["surface"]}; border: 1px solid {t["border"]};
        border-radius: 10px; padding: 10px 14px; margin-bottom: 8px; font-size: 14px;
        color: {t["text"]};
    }}
    .ft-stat-card {{
        background: {t["surface"]}; border: 1px solid {t["border"]};
        border-radius: 14px; padding: 18px 20px;
        box-shadow: 0 2px 10px {t["shadow"]};
    }}
    .ft-stat-value {{ font-size: 30px; font-weight: 800; color: {t["text"]}; }}
    .ft-stat-label {{ font-size: 13px; color: {t["muted"]}; margin-top: 2px; }}

    .ft-divider {{ height: 1px; background: {t["border"]}; margin: 28px 0; border: none; }}

    /* Sidebar navigation */
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] *,
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] .block-container {{
        box-sizing: border-box !important;
    }}

    [data-testid="stSidebar"][aria-expanded="true"] {{
        min-width: 255px !important;
        max-width: 255px !important;
        width: 255px !important;
    }}
    [data-testid="stSidebar"][aria-expanded="false"] {{
        min-width: 0 !important;
        max-width: 0 !important;
        width: 0 !important;
        flex: 0 0 0 !important;
    }}
    [data-testid="stSidebar"] .block-container {{ padding: 1.8rem 1.15rem 1.5rem 1.15rem !important; }}
    .ft-side-brand {{ font-size: 20px; font-weight: 800; color: {t["text"]} !important; margin-bottom: 2px; }}
    .ft-side-sub {{ color: {t["muted"]} !important; font-size: 12.5px; line-height: 1.45; margin-bottom: 26px; }}
    .ft-side-label {{ color: #9B4DFF !important; font-size: 11px; font-weight: 800; letter-spacing: 1.2px; text-transform: uppercase; margin: 0 0 8px 2px; }}
    [data-testid="stSidebar"] div.stButton > button {{
        width: 100% !important; min-height: 42px !important; margin: 0 0 7px 0 !important;
        padding: 8px 12px !important; text-align: left !important; justify-content: flex-start !important;
        border-radius: 9px !important; background: transparent !important; border: 1px solid transparent !important;
        color: {t["text"]} !important; box-shadow: none !important; font-size: 14px !important;
    }}
    [data-testid="stSidebar"] div.stButton > button:hover {{ background: rgba(155,77,255,0.14) !important; border-color: rgba(155,77,255,0.35) !important; color: {t["text"]} !important; }}
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] {{ background: #9B4DFF !important; border-color: #C4B5FD !important; color: #0B0A0F !important; font-weight: 800 !important; box-shadow: 0 5px 18px rgba(155,77,255,0.22) !important; }}
    [data-testid="stSidebar"] div.stButton > button[kind="primary"]:hover {{ background: #C4B5FD !important; color: #0B0A0F !important; }}
    .ft-side-divider {{ height: 1px; background: rgba({t["border_rgb"]},0.9); margin: 18px 0; }}
    .ft-side-current {{ background: {t["surface"]} !important; border: 1px solid {t["border"]} !important; border-radius: 12px; padding: 13px; margin-top: 2px; }}
    .ft-side-current-label {{ color: {a["bronze"]} !important; font-size: 11px; font-weight: 800; letter-spacing: .8px; margin-bottom: 7px; }}
    .ft-side-current-value {{ color: #C4B5FD !important; font-weight: 800; font-size: 16px; margin-top: 10px; }}

    /* ============================================================
       REPORTS — BLEND NATIVE DOWNLOAD / DATA CONTROLS INTO CANVAS
       ============================================================ */

    [data-testid="stDownloadButton"] {{
        width: 100% !important;
    }}

    [data-testid="stDownloadButton"] > button,
    [data-testid="stDownloadButton"] button {{
        width: 100% !important;
        min-height: 48px !important;
        border-radius: 12px !important;
        background: rgba({t["surface_rgb"]},0.94) !important;
        color: {t["text"]} !important;
        border: 1px solid {t["border"]} !important;
        box-shadow: 0 8px 24px {t["shadow"]} !important;
        opacity: 1 !important;
    }}

    [data-testid="stDownloadButton"] button:hover {{
        background: {t["surface_elevated"]} !important;
        border-color: #9B4DFF !important;
        color: {t["text"]} !important;
    }}

    [data-testid="stDownloadButton"] button p,
    [data-testid="stDownloadButton"] button span {{
        color: {t["text"]} !important;
        opacity: 1 !important;
    }}

    /* Keep wide report tables inside the FraudTwin canvas. */
    [data-testid="stDataFrame"] {{
        width: 100% !important;
        max-width: 100% !important;
        border: 1px solid {t["border"]} !important;
        border-radius: 12px !important;
        overflow: hidden !important;
        background: rgba({t["surface_rgb"]},0.78) !important;
    }}

    /* The report page should never create a white native surface. */
    [data-testid="stDataFrame"] iframe,
    [data-testid="stDataFrame"] > div {{
        background: transparent !important;
    }}

    /* Native Streamlit controls */
    [data-baseweb="input"], [data-baseweb="select"], [data-baseweb="textarea"],
    [data-testid="stNumberInput"], [data-testid="stSelectbox"] {{
        background: {t["surface"]} !important;
        color: {t["text"]} !important;
    }}
    [data-baseweb="input"] > div, [data-baseweb="select"] > div,
    [data-baseweb="textarea"] > div {{
        background: {t["surface"]} !important;
        border-color: {t["border"]} !important;
    }}
    input, textarea {{
        background: {t["input_bg"]} !important; color: {t["text"]} !important;
        -webkit-text-fill-color: {t["text"]} !important;
        border-color: {t["border"]} !important;
    }}
    [data-baseweb="select"] *, [data-baseweb="input"] *, [data-baseweb="textarea"] * {{
        color: {t["text"]} !important;
    }}
    [role="listbox"], [role="option"] {{
        background: {t["input_bg"]} !important; color: {t["text"]} !important;
    }}
    [role="option"]:hover {{ background: {t["surface_elevated"]} !important; }}

    div.stButton > button {{
        border-radius: 10px !important; font-weight: 600 !important;
        border: 1px solid {t["border"]} !important;
        background: {t["surface"]} !important; color: {t["text"]} !important;
    }}
    div.stButton > button:hover {{
        border-color: #9B4DFF !important; color: {t["text"]} !important;
        background: {t["surface_elevated"]} !important;
    }}
    div.stButton > button[kind="primary"] {{
        background: #9B4DFF !important; color: #0B0A0F !important; border: none !important;
        box-shadow: 0 5px 18px rgba(155,77,255,0.18) !important;
    }}
    div.stButton > button[kind="primary"] p {{ color: #0B0A0F !important; }}

    [data-testid="stAlert"] {{
        background: {t["surface_elevated"]} !important; border-color: {a["bronze"]} !important;
        color: {t["text"]} !important;
    }}
    [data-testid="stExpander"] {{
        background: {t["surface"]} !important; border: 1px solid {t["border"]} !important;
    }}
    [data-testid="stDataFrame"] {{
        background: {t["surface"]} !important;
        border: 1px solid {t["border"]} !important;
    }}
    [data-testid="stProgressBar"] > div > div {{ background: #9B4DFF !important; }}

    /* Sidebar navigation states */
    [data-testid="stSidebar"] div.stButton > button {{
        background: transparent !important;
        color: {t["text"]} !important;
        border-color: transparent !important;
        text-align: left !important;
    }}
    [data-testid="stSidebar"] div.stButton > button:hover {{
        background: rgba(155,77,255,0.12) !important;
        border-color: rgba(155,77,255,0.35) !important;
        color: #9B4DFF !important;
    }}
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] {{
        background: #9B4DFF !important;
        color: #0B0A0F !important;
    }}
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] p {{
        color: #0B0A0F !important;
    }}

    /* Canvas finish */
    [data-testid="stAppViewContainer"] .main {{
        background: radial-gradient(circle at 78% 0%, rgba(84,43,114,0.12), transparent 34%), {t["bg"]} !important;
    }}
    [data-testid="stSidebar"], [data-testid="stSidebar"] > div:first-child {{
        background: {t["sidebar"]} !important;
    }}
    [data-testid="stSidebar"] {{ border-right: 1px solid {t["border"]} !important; }}
    [data-testid="stSidebar"] div.stButton > button[kind="primary"] {{
        background: #9B4DFF !important;
        color: #0B0A0F !important;
        box-shadow: 0 5px 18px rgba(155,77,255,0.20) !important;
    }}
    .ft-side-current {{
        background: {t["surface"]} !important; border-color: {t["border"]} !important;
    }}
    .ft-side-current-value {{ color: #C4B5FD !important; }}

    /* Final presentation polish: keep charts inside the FraudTwin canvas. */
    [data-testid="stVegaLiteChart"] {{
        background: transparent !important;
        border: 1px solid {t["border"]} !important;
        border-radius: 12px !important;
        padding: 8px !important;
        overflow: hidden !important;
    }}
    .ft-ai-result, .ft-ai-result * {{ color: {t["text"]} !important; }}
    .ft-ai-result h1, .ft-ai-result h2, .ft-ai-result h3 {{ color: {t["text"]} !important; }}
    .ft-ai-result li, .ft-ai-result p {{ color: #E8E3EE !important; }}
    @media (max-width: 900px) {{
        .block-container {{ padding-left: 1rem !important; padding-right: 1rem !important; }}
        .ft-score-wrap {{ padding: 20px !important; gap: 18px !important; }}
        .ft-score-number {{ font-size: 46px !important; }}
    }}
    /* FINAL SIDEBAR-COLLAPSE ALIGNMENT */
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] {{
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        left: 0 !important;
        right: 0 !important;
        transform: none !important;
    }}

    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] > div,
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] [data-testid="stMainBlockContainer"],
    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] .block-container {{
        width: 100% !important;
        max-width: none !important;
        min-width: 0 !important;
        margin-left: 0 !important;
        margin-right: 0 !important;
        box-sizing: border-box !important;
        overflow-x: hidden !important;
    }}

    /* Analyze form: never let Streamlit columns become wider than the visible canvas. */
    [data-testid="stMain"] [data-testid="stHorizontalBlock"] {{
        width: 100% !important;
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }}
    [data-testid="stMain"] [data-testid="stColumn"] {{
        min-width: 0 !important;
        max-width: 100% !important;
        box-sizing: border-box !important;
    }}
    [data-testid="stMain"] [data-testid="stColumn"] > div {{
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }}

    /* Prevent long selectbox labels and native controls from creating horizontal overflow. */
    [data-testid="stMain"] [data-baseweb="select"],
    [data-testid="stMain"] [data-baseweb="input"],
    [data-testid="stMain"] [data-testid="stNumberInput"],
    [data-testid="stMain"] [data-testid="stSelectbox"] {{
        max-width: 100% !important;
        min-width: 0 !important;
        box-sizing: border-box !important;
    }}

    @media (max-width: 900px) {{
        [data-testid="stMain"] [data-testid="stHorizontalBlock"] {{
            flex-wrap: wrap !important;
        }}
        [data-testid="stMain"] [data-testid="stColumn"] {{
            min-width: 100% !important;
            flex: 1 1 100% !important;
        }}
    }}

    [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] [data-testid="stHorizontalBlock"] {{
        width: 100% !important;
        max-width: none !important;
    }}

    @media (max-width: 900px) {{
        [data-testid="stSidebar"][aria-expanded="false"] ~ [data-testid="stMain"] .block-container {{
            max-width: 100% !important;
        }}
    }}

    </style>
    <div class="ft-background-art" aria-hidden="true">
        <svg viewBox="0 0 1100 720" preserveAspectRatio="none">
            <defs>
                <linearGradient id="ftLine" x1="0" x2="1">
                    <stop offset="0" stop-color="#542B72" stop-opacity="0"/>
                    <stop offset="0.42" stop-color="#9B4DFF" stop-opacity="0.78"/>
                    <stop offset="0.82" stop-color="#D946EF" stop-opacity="0.58"/>
                    <stop offset="1" stop-color="#C4B5FD" stop-opacity="0.10"/>
                </linearGradient>
            </defs>
            <rect x="80" y="70" width="910" height="590" rx="28" class="ft-art-panel"/>
            <g>
                <line x1="130" y1="150" x2="950" y2="150" class="ft-art-grid"/>
                <line x1="130" y1="250" x2="950" y2="250" class="ft-art-grid"/>
                <line x1="130" y1="350" x2="950" y2="350" class="ft-art-grid"/>
                <line x1="130" y1="450" x2="950" y2="450" class="ft-art-grid"/>
                <line x1="130" y1="550" x2="950" y2="550" class="ft-art-grid"/>
                <line x1="130" y1="120" x2="130" y2="585" class="ft-art-axis"/>
                <line x1="130" y1="585" x2="950" y2="585" class="ft-art-axis"/>
            </g>
            <path d="M130 500 L220 445 L285 470 L365 390 L440 420 L520 315 L600 355 L680 245 L760 285 L850 175 L950 215" class="ft-art-line"/>
            <path d="M130 525 L220 485 L285 505 L365 435 L440 460 L520 360 L600 395 L680 300 L760 325 L850 220 L950 255" class="ft-art-line-soft"/>
            <circle cx="680" cy="245" r="45" class="ft-art-ring"/>
            <circle cx="680" cy="245" r="68" class="ft-art-ring"/>
            <g opacity=".85">
                <rect x="165" y="555" width="26" height="30" class="ft-art-bar"/>
                <rect x="205" y="525" width="26" height="60" class="ft-art-bar"/>
                <rect x="245" y="545" width="26" height="40" class="ft-art-bar-bright"/>
                <rect x="285" y="495" width="26" height="90" class="ft-art-bar"/>
                <rect x="325" y="515" width="26" height="70" class="ft-art-bar-bright"/>
                <rect x="365" y="465" width="26" height="120" class="ft-art-bar"/>
                <rect x="405" y="485" width="26" height="100" class="ft-art-bar-bright"/>
            </g>
            <g opacity=".72">
                <rect x="760" y="105" width="150" height="95" rx="12" class="ft-art-panel"/>
                <circle cx="795" cy="140" r="18" class="ft-art-ring"/>
                <circle cx="795" cy="140" r="5" class="ft-art-node-pink"/>
                <line x1="825" y1="130" x2="880" y2="130" class="ft-art-grid"/>
                <line x1="825" y1="150" x2="895" y2="150" class="ft-art-grid"/>
                <line x1="825" y1="170" x2="865" y2="170" class="ft-art-grid"/>
            </g>
            <text x="145" y="105" class="ft-art-label">RISK INTELLIGENCE / LIVE SIGNALS</text>
            <text x="735" y="635" class="ft-art-label">FRAUDTWIN • AI ANALYTICS</text>
        </svg>
    </div>
    """, unsafe_allow_html=True)


def ft_line_chart(series, y_title):
    chart_df = pd.DataFrame({"Scenario": series.index.astype(str), "Risk Score": pd.to_numeric(series.values)})
    chart = (
        alt.Chart(chart_df)
        .mark_line(point=True, strokeWidth=2.5)
        .encode(
            x=alt.X("Scenario:N", title=None, axis=alt.Axis(labelColor="#AAA3B5", labelAngle=-45, grid=False)),
            y=alt.Y("Risk Score:Q", title=y_title, axis=alt.Axis(labelColor="#AAA3B5", titleColor="#AAA3B5", gridColor="#30283A")),
            tooltip=[alt.Tooltip("Scenario:N", title="Transaction"), alt.Tooltip("Risk Score:Q", format=".2f")]
        )
        .properties(background="transparent", height=330)
        .configure_view(strokeOpacity=0)
    )
    st.altair_chart(chart, use_container_width=True)


def ft_bar_chart(df, value_column, y_title):
    chart_df = df.reset_index()
    category_column = chart_df.columns[0]
    chart = (
        alt.Chart(chart_df)
        .mark_bar(cornerRadiusTopLeft=5, cornerRadiusTopRight=5)
        .encode(
            x=alt.X(f"{category_column}:N", title=None, axis=alt.Axis(labelColor="#AAA3B5", labelAngle=-35, grid=False)),
            y=alt.Y(f"{value_column}:Q", title=y_title, axis=alt.Axis(labelColor="#AAA3B5", titleColor="#AAA3B5", gridColor="#30283A")),
            tooltip=[alt.Tooltip(f"{category_column}:N", title="Category"), alt.Tooltip(f"{value_column}:Q", title="Score", format=".2f")]
        )
        .properties(background="transparent", height=330)
        .configure_view(strokeOpacity=0)
    )
    st.altair_chart(chart, use_container_width=True)


def risk_badge_html(level, icon=None):
    color = RISK_COLORS.get(level, "#AAA3B5")  # badge color stays semantic, not theme-driven
    return (
        f'<span class="ft-badge" style="background:{color}22; color:{color}; '
        f'border-color:{color}55;">{level}</span>'
    )


def indicator_row(text, positive=False):
    icon = "PASS" if positive else "FLAG"
    st.markdown(f'<div class="ft-indicator"><span class="ft-status-marker">{icon}</span><span>{text}</span></div>', unsafe_allow_html=True)


def stat_card(value, label):
    st.markdown(
        f'<div class="ft-stat-card"><div class="ft-stat-value">{value}</div>'
        f'<div class="ft-stat-label">{label}</div></div>',
        unsafe_allow_html=True
    )


def section_title(title, subtitle=None):
    st.markdown(f'<div class="ft-section-title">{title}</div>', unsafe_allow_html=True)
    if subtitle:
        st.markdown(f'<div class="ft-section-sub">{subtitle}</div>', unsafe_allow_html=True)


def score_hero(score, level, icon, decision):
    color = RISK_COLORS.get(level, "#AAA3B5")
    st.markdown(
        f"""
        <div class="ft-score-wrap">
            <div>
                <div class="ft-score-label">Risk Intelligence Score</div>
                <div class="ft-score-number" style="color:{color};">{score:.0f}<span style="font-size:22px;color:#AAA3B5;">/100</span></div>
            </div>
            <div style="flex:1; min-width:220px;">
                {risk_badge_html(level, icon)}
                <div style="margin-top:10px; color:#AAA3B5; font-size:14px;">
                    Recommended action: <strong style="color:#F5F3F7;">{decision}</strong>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True
    )
    st.progress(min(max(int(score), 0), 100))