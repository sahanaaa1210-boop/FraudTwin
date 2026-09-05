import streamlit as st
import pandas as pd
import numpy as np
from datetime import datetime, timedelta


# ============================================================
# AUTH INITIALIZATION
# ============================================================

def initialize_auth():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False

    if "username" not in st.session_state:
        st.session_state.username = ""

    if "account_created" not in st.session_state:
        st.session_state.account_created = False

    if "confirm_logout" not in st.session_state:
        st.session_state.confirm_logout = False

    if "page" not in st.session_state:
        st.session_state.page = "landing"


# Initialize immediately
initialize_auth()


# ============================================================
# GLOBAL STYLES (shared across auth + app shell)
# ============================================================

def inject_global_styles():
    st.markdown(
        """
        <style>

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        /* ---------- App background ---------- */
        .stApp {
            background:
                radial-gradient(circle at 15% 20%, rgba(168, 85, 247, 0.18), transparent 40%),
                radial-gradient(circle at 85% 80%, rgba(99, 102, 241, 0.15), transparent 45%),
                radial-gradient(circle at 50% 50%, rgba(236, 72, 153, 0.06), transparent 60%),
                linear-gradient(135deg, #0b0912, #151020, #0b0912);
            background-attachment: fixed;
        }

        #MainMenu, header, footer {visibility: hidden;}

        /* ---------- Brand ---------- */
        .auth-brand {
            display: inline-block;
            color: #c084fc;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 3px;
            margin-bottom: 22px;
            padding: 6px 14px;
            border: 1px solid rgba(168, 85, 247, 0.35);
            border-radius: 999px;
            background: rgba(168, 85, 247, 0.08);
        }

        /* ---------- Hero text ---------- */
        .auth-title {
            font-size: 42px;
            font-weight: 800;
            line-height: 1.2;
            margin-bottom: 16px;
            color: #f5f3ff;
            letter-spacing: -0.5px;
        }

        .auth-subtitle {
            color: #a8a2ba;
            font-size: 15.5px;
            line-height: 1.6;
            margin-bottom: 30px;
            max-width: 460px;
        }

        /* ---------- Feature list ---------- */
        .feature-row {
            display: flex;
            align-items: center;
            gap: 12px;
            padding: 10px 14px;
            margin-bottom: 10px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.06);
            max-width: 420px;
            transition: all 0.2s ease;
        }

        .feature-row:hover {
            background: rgba(168, 85, 247, 0.08);
            border-color: rgba(168, 85, 247, 0.25);
            transform: translateX(4px);
        }

        .feature-num {
            font-size: 12px;
            font-weight: 700;
            color: #a855f7;
            background: rgba(168, 85, 247, 0.15);
            border-radius: 6px;
            padding: 4px 8px;
            min-width: 26px;
            text-align: center;
        }

        .feature-label {
            color: #e5e1f0;
            font-size: 14.5px;
            font-weight: 500;
        }

        /* ---------- Auth card (right panel) ---------- */
        .auth-card-wrapper {
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(255, 255, 255, 0.09);
            border-radius: 18px;
            padding: 30px 28px 10px 28px;
            backdrop-filter: blur(14px);
            box-shadow: 0 8px 32px rgba(0, 0, 0, 0.35);
            position: relative;
            overflow: hidden;
        }

        .auth-card-wrapper::before {
            content: "";
            position: absolute;
            top: -60%;
            right: -30%;
            width: 220px;
            height: 220px;
            background: radial-gradient(circle, rgba(168, 85, 247, 0.25), transparent 70%);
            pointer-events: none;
        }

        .auth-card-title {
            font-size: 22px;
            font-weight: 700;
            color: #f5f3ff;
            margin-bottom: 4px;
        }

        .auth-card-caption {
            color: #948da3;
            font-size: 13.5px;
            margin-bottom: 22px;
        }

        /* ---------- Tabs ---------- */
        .stTabs [data-baseweb="tab-list"] {
            gap: 4px;
            background: rgba(255, 255, 255, 0.04);
            padding: 4px;
            border-radius: 10px;
        }

        .stTabs [data-baseweb="tab"] {
            border-radius: 8px;
            color: #a8a2ba;
            font-weight: 600;
            font-size: 14px;
        }

        .stTabs [aria-selected="true"] {
            background: linear-gradient(135deg, #a855f7, #7c3aed);
            color: #ffffff !important;
        }

        /* ---------- Text inputs ---------- */
        .stTextInput input {
            background: rgba(255, 255, 255, 0.05) !important;
            border: 1px solid rgba(255, 255, 255, 0.12) !important;
            border-radius: 10px !important;
            color: #f5f3ff !important;
            padding: 10px 14px !important;
        }

        .stTextInput input:focus {
            border-color: #a855f7 !important;
            box-shadow: 0 0 0 1px #a855f7 !important;
        }

        .stTextInput label {
            color: #c9c3d6 !important;
            font-size: 13.5px !important;
            font-weight: 600 !important;
        }

        /* ---------- Buttons (primary / gradient) ---------- */
        .stButton button {
            background: linear-gradient(135deg, #a855f7, #7c3aed);
            color: #ffffff;
            border: none;
            border-radius: 10px;
            padding: 10px 0;
            font-weight: 700;
            font-size: 14.5px;
            letter-spacing: 0.3px;
            margin-top: 6px;
            transition: all 0.2s ease;
            box-shadow: 0 4px 14px rgba(168, 85, 247, 0.35);
        }

        .stButton button:hover {
            filter: brightness(1.1);
            box-shadow: 0 6px 20px rgba(168, 85, 247, 0.5);
            transform: translateY(-1px);
        }

        /* Secondary / outline-style buttons via data-testid on the container */
        div[data-testid="stHorizontalBlock"] .stButton button {
            box-shadow: none;
        }

        /* ---------- Alerts ---------- */
        .stAlert {
            border-radius: 10px;
        }

        /* ---------- Dashboard ---------- */
        .dash-section-title {
            color: #f0ecfa;
            font-size: 15.5px;
            font-weight: 700;
            margin: 26px 0 14px 0;
            letter-spacing: 0.2px;
        }

        .kpi-card {
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(255, 255, 255, 0.08);
            border-radius: 14px;
            padding: 18px 20px;
            height: 100%;
        }

        .kpi-label {
            color: #948da3;
            font-size: 12.5px;
            font-weight: 600;
            letter-spacing: 0.3px;
            text-transform: uppercase;
            margin-bottom: 8px;
        }

        .kpi-value {
            color: #f5f3ff;
            font-size: 27px;
            font-weight: 800;
            letter-spacing: -0.5px;
        }

        .kpi-delta {
            font-size: 12.5px;
            font-weight: 600;
            margin-top: 6px;
        }

        .kpi-delta.up { color: #4ade80; }
        .kpi-delta.down { color: #f87171; }
        .kpi-delta.flat { color: #948da3; }

        .chart-card {
            background: rgba(255, 255, 255, 0.03);
            border: 1px solid rgba(255, 255, 255, 0.07);
            border-radius: 14px;
            padding: 16px 18px 6px 18px;
        }

        .chart-card-title {
            color: #d9d3e8;
            font-size: 13.5px;
            font-weight: 700;
            margin-bottom: 8px;
        }

        .alert-item {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 12px 16px;
            border-radius: 10px;
            background: rgba(255, 255, 255, 0.025);
            border: 1px solid rgba(255, 255, 255, 0.06);
            margin-bottom: 8px;
        }

        .alert-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .alert-dot {
            width: 8px;
            height: 8px;
            border-radius: 50%;
            flex-shrink: 0;
        }

        .alert-dot.high { background: #f87171; box-shadow: 0 0 8px rgba(248,113,113,0.6); }
        .alert-dot.medium { background: #fbbf24; box-shadow: 0 0 8px rgba(251,191,36,0.5); }
        .alert-dot.low { background: #4ade80; box-shadow: 0 0 8px rgba(74,222,128,0.5); }

        .alert-text {
            color: #e5e1f0;
            font-size: 13.5px;
            font-weight: 500;
        }

        .alert-sub {
            color: #7a7288;
            font-size: 12px;
            margin-top: 2px;
        }

        .alert-badge {
            font-size: 11px;
            font-weight: 700;
            padding: 3px 10px;
            border-radius: 999px;
            letter-spacing: 0.3px;
        }

        .alert-badge.high { background: rgba(248,113,113,0.15); color: #fca5a5; }
        .alert-badge.medium { background: rgba(251,191,36,0.15); color: #fcd34d; }
        .alert-badge.low { background: rgba(74,222,128,0.15); color: #86efac; }

        /* ---------- App shell (post-login) ---------- */
        .topbar {
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 14px 22px;
            border-radius: 14px;
            background: rgba(255, 255, 255, 0.035);
            border: 1px solid rgba(255, 255, 255, 0.09);
            backdrop-filter: blur(14px);
            margin-bottom: 26px;
        }

        .topbar-left {
            display: flex;
            align-items: center;
            gap: 12px;
        }

        .avatar-badge {
            width: 38px;
            height: 38px;
            border-radius: 50%;
            background: linear-gradient(135deg, #a855f7, #7c3aed);
            display: flex;
            align-items: center;
            justify-content: center;
            font-weight: 700;
            color: #fff;
            font-size: 15px;
        }

        .topbar-username {
            color: #f5f3ff;
            font-weight: 700;
            font-size: 15px;
        }

        .topbar-role {
            color: #948da3;
            font-size: 12px;
        }

        .logout-warning-card {
            background: rgba(239, 68, 68, 0.08);
            border: 1px solid rgba(239, 68, 68, 0.3);
            border-radius: 14px;
            padding: 20px 22px;
            margin-bottom: 16px;
        }

        .logout-warning-title {
            color: #fca5a5;
            font-weight: 700;
            font-size: 15.5px;
            margin-bottom: 4px;
        }

        .logout-warning-text {
            color: #d8b4b4;
            font-size: 13.5px;
        }

        </style>
        """,
        unsafe_allow_html=True,
    )


# ============================================================
# LANDING PAGE (cinematic, page 1)
# ============================================================

def inject_landing_styles():
    st.markdown(
        """
        <style>

        @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800;900&display=swap');

        html, body, [class*="css"] {
            font-family: 'Inter', sans-serif;
        }

        #MainMenu, header, footer {visibility: hidden;}

        html, body {
            overflow-x: hidden;
        }

        /* ---------- Cinematic background ---------- */
        .stApp {
            background: #06050a;
            overflow-x: hidden;
        }

        .film-grain {
            position: fixed;
            inset: 0;
            pointer-events: none;
            z-index: 5;
            opacity: 0.035;
            background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='120' height='120'%3E%3Cfilter id='n'%3E%3CfeTurbulence type='fractalNoise' baseFrequency='0.9' numOctaves='2' stitchTiles='stitch'/%3E%3C/filter%3E%3Crect width='100%25' height='100%25' filter='url(%23n)'/%3E%3C/svg%3E");
        }

        .letterbox-top, .letterbox-bottom {
            position: fixed;
            left: 0;
            right: 0;
            height: 46px;
            background: #000;
            z-index: 6;
        }
        .letterbox-top { top: 0; }
        .letterbox-bottom { bottom: 0; }

        .cinema-orb {
            position: fixed;
            border-radius: 50%;
            filter: blur(70px);
            z-index: 0;
            animation: drift 22s ease-in-out infinite;
        }

        .orb-a {
            width: 480px;
            height: 480px;
            top: -120px;
            left: -100px;
            background: radial-gradient(circle, rgba(168, 85, 247, 0.35), transparent 70%);
            animation-delay: 0s;
        }

        .orb-b {
            width: 420px;
            height: 420px;
            bottom: -140px;
            right: -80px;
            background: radial-gradient(circle, rgba(59, 130, 246, 0.28), transparent 70%);
            animation-delay: -8s;
        }

        .orb-c {
            width: 300px;
            height: 300px;
            top: 40%;
            left: 55%;
            background: radial-gradient(circle, rgba(236, 72, 153, 0.16), transparent 70%);
            animation-delay: -14s;
        }

        @keyframes drift {
            0%   { transform: translate(0px, 0px) scale(1); }
            33%  { transform: translate(30px, -25px) scale(1.06); }
            66%  { transform: translate(-25px, 20px) scale(0.97); }
            100% { transform: translate(0px, 0px) scale(1); }
        }

        /* ---------- Content ---------- */
        .landing-wrap {
            position: relative;
            z-index: 2;
            display: flex;
            flex-direction: column;
            align-items: flex-start;
            justify-content: center;
            text-align: left;
            padding-top: 7vh;
            max-width: 640px;
            margin: 0;
            width: 100%;
            box-sizing: border-box;
            padding-left: 56px;
            padding-right: 20px;
        }

        .landing-kicker {
            opacity: 0;
            color: #9d8bb0;
            font-size: 12.5px;
            letter-spacing: 4px;
            font-weight: 600;
            margin-bottom: 20px;
            animation: reveal 0.9s ease forwards;
            animation-delay: 0.15s;
        }

        .landing-title {
            opacity: 0;
            font-size: clamp(28px, 4.6vw, 54px);
            font-weight: 800;
            line-height: 1.18;
            color: #f6f4fb;
            letter-spacing: -1px;
            margin-bottom: 18px;
            overflow-wrap: break-word;
            animation: reveal 1s ease forwards;
            animation-delay: 0.4s;
        }

        .landing-title .accent {
            background: linear-gradient(120deg, #c084fc, #818cf8, #c084fc);
            background-size: 200% auto;
            -webkit-background-clip: text;
            background-clip: text;
            color: transparent;
            animation: shimmer 6s linear infinite;
        }

        .landing-sub {
            opacity: 0;
            max-width: 560px;
            color: #a49bb8;
            font-size: 16.5px;
            line-height: 1.65;
            margin-bottom: 46px;
            animation: reveal 1s ease forwards;
            animation-delay: 0.75s;
        }

        .landing-sub b { color: #d9cef0; font-weight: 600; }

        @keyframes reveal {
            from { opacity: 0; transform: translateY(16px); }
            to   { opacity: 1; transform: translateY(0); }
        }

        @keyframes shimmer {
            to { background-position: 200% center; }
        }

        /* ---------- CTA ---------- */
        .landing-cta-zone {
            opacity: 0;
            width: 100%;
            animation: reveal 1s ease forwards;
            animation-delay: 1.05s;
        }

        .stButton button {
            background: linear-gradient(135deg, #a855f7, #6d28d9);
            color: #fff;
            border: none;
            border-radius: 999px;
            padding: 14px 20px;
            font-weight: 700;
            font-size: 15.5px;
            letter-spacing: 0.2px;
            box-shadow: 0 0 0 1px rgba(255,255,255,0.06), 0 10px 30px rgba(168, 85, 247, 0.4);
            transition: all 0.25s ease;
        }

        .stButton button:hover {
            transform: translateY(-2px);
            box-shadow: 0 0 0 1px rgba(255,255,255,0.1), 0 16px 40px rgba(168, 85, 247, 0.55);
        }

        .landing-footnote {
            opacity: 0;
            margin-top: 18px;
            color: #665d78;
            font-size: 12.5px;
            animation: reveal 1s ease forwards;
            animation-delay: 1.3s;
        }

        /* ---------- Hero visual (cinematic product preview, top-right) ---------- */
        .cinema-visual-wrap {
            position: fixed;
            top: 12%;
            right: 6%;
            width: 440px;
            max-width: 40vw;
            z-index: 2;
            opacity: 0;
            animation: reveal-visual 1.3s ease forwards;
            animation-delay: 0.5s;
        }

        @keyframes reveal-visual {
            from { opacity: 0; transform: translateY(24px) scale(0.94); }
            to   { opacity: 1; transform: translateY(0) scale(1); }
        }

        @media (max-width: 1000px) {
            .cinema-visual-wrap {
                position: static;
                margin: 34px auto 10px auto;
                right: auto;
                top: auto;
                width: 92%;
                max-width: 420px;
            }
        }

        .radar-ring {
            position: absolute;
            top: 50%;
            left: 50%;
            width: 380px;
            height: 380px;
            transform: translate(-50%, -50%);
            border-radius: 50%;
            border: 1px solid rgba(168, 85, 247, 0.14);
            z-index: 0;
            pointer-events: none;
        }

        .radar-ring::before {
            content: "";
            position: absolute;
            inset: 46px;
            border-radius: 50%;
            border: 1px solid rgba(168, 85, 247, 0.12);
        }

        .radar-ring::after {
            content: "";
            position: absolute;
            inset: 0;
            border-radius: 50%;
            background: conic-gradient(from 0deg, rgba(168, 85, 247, 0.4), transparent 28%, transparent 100%);
            filter: blur(3px);
            animation: radar-spin 7s linear infinite;
        }

        @keyframes radar-spin {
            to { transform: rotate(360deg); }
        }

        .signal-node {
            position: absolute;
            width: 7px;
            height: 7px;
            border-radius: 50%;
            background: #c084fc;
            box-shadow: 0 0 10px rgba(192, 132, 252, 0.8);
            z-index: 1;
            animation: node-pulse 2.6s ease-in-out infinite;
        }

        @keyframes node-pulse {
            0%, 100% { opacity: 0.35; transform: scale(1); }
            50%      { opacity: 1; transform: scale(1.7); }
        }

        .hero-card {
            position: relative;
            z-index: 2;
            background: linear-gradient(160deg, rgba(255,255,255,0.055), rgba(255,255,255,0.02));
            border: 1px solid rgba(255,255,255,0.10);
            border-radius: 18px;
            padding: 22px 24px 20px 24px;
            backdrop-filter: blur(16px);
            box-shadow:
                0 30px 60px rgba(0,0,0,0.55),
                0 0 60px rgba(168, 85, 247, 0.16),
                inset 0 1px 0 rgba(255,255,255,0.08);
            text-align: left;
            transform: rotateX(6deg) rotateY(-4deg);
            animation: float-card 6s ease-in-out infinite;
        }

        @keyframes float-card {
            0%, 100% { transform: rotateX(6deg) rotateY(-4deg) translateY(0px); }
            50%      { transform: rotateX(4deg) rotateY(-2deg) translateY(-10px); }
        }

        .hero-card-glow {
            position: absolute;
            inset: -1px;
            border-radius: 18px;
            padding: 1px;
            background: linear-gradient(120deg, rgba(168,85,247,0.5), transparent 40%, transparent 60%, rgba(59,130,246,0.4));
            -webkit-mask: linear-gradient(#000 0 0) content-box, linear-gradient(#000 0 0);
            -webkit-mask-composite: xor;
            mask-composite: exclude;
            pointer-events: none;
        }

        .hero-card-header {
            display: flex;
            align-items: center;
            justify-content: space-between;
            margin-bottom: 16px;
        }

        .hero-card-label {
            color: #cabdea;
            font-size: 12px;
            font-weight: 700;
            letter-spacing: 1px;
        }

        .hero-live-pill {
            display: flex;
            align-items: center;
            gap: 6px;
            background: rgba(74, 222, 128, 0.12);
            border: 1px solid rgba(74, 222, 128, 0.3);
            border-radius: 999px;
            padding: 3px 10px;
            font-size: 10.5px;
            font-weight: 700;
            color: #86efac;
            letter-spacing: 0.5px;
        }

        .hero-live-dot {
            width: 6px;
            height: 6px;
            border-radius: 50%;
            background: #4ade80;
            animation: pulse-dot 1.6s ease-in-out infinite;
        }

        @keyframes pulse-dot {
            0%, 100% { opacity: 1; box-shadow: 0 0 0 0 rgba(74,222,128,0.5); }
            50%      { opacity: 0.5; box-shadow: 0 0 0 4px rgba(74,222,128,0); }
        }

        .hero-score-row {
            display: flex;
            align-items: baseline;
            gap: 10px;
            margin-bottom: 18px;
        }

        .hero-score-value {
            font-size: 34px;
            font-weight: 800;
            color: #f5f3ff;
            letter-spacing: -0.5px;
        }

        .hero-score-trend {
            font-size: 12.5px;
            font-weight: 700;
            color: #4ade80;
        }

        .hero-bars {
            display: flex;
            align-items: flex-end;
            gap: 6px;
            height: 64px;
            margin-bottom: 14px;
        }

        .hero-bar {
            flex: 1;
            border-radius: 5px 5px 2px 2px;
            background: linear-gradient(180deg, #c084fc, #7c3aed);
            opacity: 0.85;
            animation: bar-breathe 3.2s ease-in-out infinite;
        }

        @keyframes bar-breathe {
            0%, 100% { transform: scaleY(1); }
            50%      { transform: scaleY(0.85); }
        }

        .hero-card-footer {
            display: flex;
            align-items: center;
            justify-content: space-between;
            border-top: 1px solid rgba(255,255,255,0.08);
            padding-top: 12px;
        }

        .hero-footer-item {
            color: #8a8298;
            font-size: 11.5px;
        }

        .hero-footer-item b {
            color: #d9d3e8;
            font-weight: 700;
        }

        </style>

        <div class="film-grain"></div>
        <div class="letterbox-top"></div>
        <div class="letterbox-bottom"></div>
        <div class="cinema-orb orb-a"></div>
        <div class="cinema-orb orb-b"></div>
        <div class="cinema-orb orb-c"></div>
        """,
        unsafe_allow_html=True,
    )


def show_landing_page():
    """The very first screen a visitor sees, before they pick login or sign up."""

    inject_landing_styles()

    # ---- Cinematic visual, pinned top-right (radar rings + floating card) ----
    bar_heights = [38, 56, 44, 64, 50, 60, 46]
    bars_html = "".join(
        f'<div class="hero-bar" style="height:{h}%; animation-delay:{i * 0.15}s;"></div>'
        for i, h in enumerate(bar_heights)
    )

    node_positions = [
        (6, 18), (88, 10), (94, 55), (78, 92), (12, 82), (2, 46),
    ]
    nodes_html = "".join(
        f'<div class="signal-node" style="top:{top}%; left:{left}%; '
        f'animation-delay:{i * 0.35}s;"></div>'
        for i, (top, left) in enumerate(node_positions)
    )

    st.markdown(
        f"""
        <div class="cinema-visual-wrap">
            <div class="radar-ring"></div>
            {nodes_html}
            <div class="hero-card">
                <div class="hero-card-glow"></div>
                <div class="hero-card-header">
                    <div class="hero-card-label">MERCHANT #4471</div>
                    <div class="hero-live-pill">
                        <div class="hero-live-dot"></div>LIVE
                    </div>
                </div>
                <div class="hero-score-row">
                    <div class="hero-score-value">94.6</div>
                    <div class="hero-score-trend">avg. confidence, last hour</div>
                </div>
                <div class="hero-bars">{bars_html}</div>
                <div class="hero-card-footer">
                    <div class="hero-footer-item"><b>2,481</b> checked / min</div>
                    <div class="hero-footer-item"><b>0.6%</b> sent to a human</div>
                </div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    # ---- Left-aligned text column ----
    st.markdown('<div class="landing-wrap">', unsafe_allow_html=True)

    st.markdown(
        '<div class="landing-kicker">A QUIET TOOL FOR A LOUD PROBLEM</div>',
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="landing-title">
            Most fraud doesn't<br>
            look like fraud.<br>
            <span class="accent">Not until you know what you're looking for.</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown(
        """
        <div class="landing-sub">
            We built FraudTwin after one too many meetings where someone
            asked <b>"why did the model flag this?"</b> and nobody in the
            room had a real answer. So every score here comes with a reason
            attached — something you can actually put in front of a customer,
            an auditor, or your own boss.
        </div>
        """,
        unsafe_allow_html=True,
    )

    st.markdown('<div class="landing-cta-zone">', unsafe_allow_html=True)

    left_col, _ = st.columns([1, 2])
    with left_col:
        if st.button("Take me in →", key="landing_enter_button", use_container_width=True):
            st.session_state.page = "auth"
            st.rerun()

    st.markdown(
        '<div class="landing-footnote">No credit card. No demo call. '
        'Just log in and poke around.</div>',
        unsafe_allow_html=True,
    )

    st.markdown('</div></div>', unsafe_allow_html=True)


# ============================================================
# LOGOUT (with confirmation)
# ============================================================

def request_logout():
    """Trigger the confirmation prompt instead of logging out immediately."""
    st.session_state.confirm_logout = True
    st.rerun()


def cancel_logout():
    st.session_state.confirm_logout = False
    st.rerun()


def perform_logout():
    st.session_state.authenticated = False
    st.session_state.username = ""
    st.session_state.confirm_logout = False
    st.session_state.page = "landing"
    st.rerun()


def request_login(username, password):
    """Sign in immediately — no confirmation step."""
    st.session_state.authenticated = True
    st.session_state.username = username
    st.rerun()


def request_signup(username, password):
    """Create the account and sign in immediately — no confirmation step."""
    st.session_state.account_created = True
    st.session_state.authenticated = True
    st.session_state.username = username
    st.rerun()


def render_logout_confirmation():
    """Styled confirmation card, shown in place of the normal app content."""

    st.markdown(
        """
        <div class="logout-warning-card">
            <div class="logout-warning-title">Sign out?</div>
            <div class="logout-warning-text">
                Anything you were mid-way through on this page — notes,
                a case you had open — won't be saved.
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

    col1, col2, col3 = st.columns([1, 1, 2])

    with col1:
        if st.button("Yes, sign out", key="confirm_logout_yes", use_container_width=True):
            perform_logout()

    with col2:
        if st.button("Cancel", key="confirm_logout_no", use_container_width=True):
            cancel_logout()


# ============================================================
# APP SHELL (shown after successful authentication)
# ============================================================

def render_topbar():
    initial = (st.session_state.username or "?")[0].upper()

    left, right = st.columns([4, 1])

    with left:
        st.markdown(
            f"""
            <div class="topbar">
                <div class="topbar-left">
                    <div class="avatar-badge">{initial}</div>
                    <div>
                        <div class="topbar-username">{st.session_state.username}</div>
                        <div class="topbar-role">FraudTwin</div>
                    </div>
                </div>
            </div>
            """,
            unsafe_allow_html=True,
        )

    with right:
        st.write("")  # vertical align spacer
        if st.button("Log out", key="topbar_logout_button", use_container_width=True):
            request_logout()


def generate_dashboard_data():
    """Deterministic sample data so the dashboard looks the same on every run."""

    rng = np.random.default_rng(seed=42)

    dates = [datetime.today() - timedelta(days=i) for i in range(29, -1, -1)]
    risk_scores = np.clip(
        58 + np.cumsum(rng.normal(0, 3, size=30)).round(1), 20, 95
    )
    trend_df = pd.DataFrame(
        {"Avg. Risk Score": risk_scores},
        index=[d.strftime("%b %d") for d in dates],
    )

    categories = ["Card Testing", "Account Takeover", "Refund Abuse", "Bot Traffic", "Mule Accounts"]
    flagged_counts = [142, 98, 76, 61, 34]
    category_df = pd.DataFrame({"Flagged": flagged_counts}, index=categories)

    alerts = [
        ("high", "Card testing burst on merchant #4471", "2 minutes ago"),
        ("high", "New device + new billing address, high-value order", "18 minutes ago"),
        ("medium", "Login from unusual location for user jdoe_82", "41 minutes ago"),
        ("medium", "Refund requested within 3 minutes of delivery scan", "1 hour ago"),
        ("low", "Velocity check passed after manual review", "2 hours ago"),
    ]

    return trend_df, category_df, alerts


def render_kpi_row():
    kpis = [
        ("Transactions today", "18,432", "+6.2% vs yesterday", "up"),
        ("Flagged for review", "217", "-3.1% vs yesterday", "down"),
        ("Fraud prevented", "$94,850", "+11.4% vs yesterday", "up"),
        ("False positive rate", "4.8%", "steady", "flat"),
    ]

    cols = st.columns(4)
    for col, (label, value, delta, direction) in zip(cols, kpis):
        with col:
            st.markdown(
                f"""
                <div class="kpi-card">
                    <div class="kpi-label">{label}</div>
                    <div class="kpi-value">{value}</div>
                    <div class="kpi-delta {direction}">{delta}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_charts_row(trend_df, category_df):
    left, right = st.columns([1.4, 1])

    with left:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="chart-card-title">Average risk score — last 30 days</div>',
            unsafe_allow_html=True,
        )
        st.line_chart(trend_df, height=240)
        st.markdown('</div>', unsafe_allow_html=True)

    with right:
        st.markdown('<div class="chart-card">', unsafe_allow_html=True)
        st.markdown(
            '<div class="chart-card-title">Flagged transactions by pattern</div>',
            unsafe_allow_html=True,
        )
        st.bar_chart(category_df, height=240)
        st.markdown('</div>', unsafe_allow_html=True)


def render_alerts_feed(alerts):
    st.markdown('<div class="dash-section-title">Recent alerts</div>', unsafe_allow_html=True)

    for severity, text, when in alerts:
        st.markdown(
            f"""
            <div class="alert-item">
                <div class="alert-left">
                    <div class="alert-dot {severity}"></div>
                    <div>
                        <div class="alert-text">{text}</div>
                        <div class="alert-sub">{when}</div>
                    </div>
                </div>
                <div class="alert-badge {severity}">{severity.upper()}</div>
            </div>
            """,
            unsafe_allow_html=True,
        )


def render_dashboard():
    trend_df, category_df, alerts = generate_dashboard_data()

    st.markdown(
        f"<div style='color:#f5f3ff; font-size:22px; font-weight:800; "
        f"margin-top:4px; margin-bottom:2px;'>Welcome back, {st.session_state.username} 👋</div>",
        unsafe_allow_html=True,
    )
    st.markdown(
        "<div style='color:#948da3; font-size:13.5px; margin-bottom:8px;'>"
        "Here's what's going on across your transactions right now.</div>",
        unsafe_allow_html=True,
    )

    st.markdown('<div class="dash-section-title">Overview</div>', unsafe_allow_html=True)
    render_kpi_row()

    st.markdown('<div class="dash-section-title">Signal</div>', unsafe_allow_html=True)
    render_charts_row(trend_df, category_df)

    render_alerts_feed(alerts)


def show_app_shell():
    """Authenticated area: topbar + real dashboard."""

    inject_global_styles()
    render_topbar()

    if st.session_state.confirm_logout:
        render_logout_confirmation()
    else:
        render_dashboard()


# ============================================================
# AUTH PAGE
# ============================================================

def show_auth_page():

    initialize_auth()
    inject_global_styles()

    left, right = st.columns([1.3, 1], gap="large")

    # ========================================================
    # LEFT SIDE
    # ========================================================

    with left:

        st.markdown(
            '<div class="auth-brand">BUILT FOR FRAUD &amp; RISK TEAMS</div>',
            unsafe_allow_html=True,
        )

        st.markdown(
            """
            <div class="auth-title">
                Understand risk<br>
                before it becomes<br>
                <span style="background: linear-gradient(135deg, #c084fc, #a855f7);
                             -webkit-background-clip: text;
                             background-clip: text;
                             color: transparent;">fraud.</span>
            </div>
            """,
            unsafe_allow_html=True,
        )

        st.markdown(
            '<div class="auth-subtitle">'
            'FraudTwin puts your model scores, the context behind them, and a '
            'proper place to investigate a case all in one screen — so a flag '
            'never just sits there unexplained.'
            '</div>',
            unsafe_allow_html=True,
        )

        features = [
            ("01", "See why something got flagged, not just that it was"),
            ("02", "Look at the account, not just the one transaction"),
            ("03", "Try a rule out before you turn it on"),
            ("04", "A trail for every call you make"),
        ]

        feature_html = ""
        for num, label in features:
            feature_html += (
                f'<div class="feature-row">'
                f'<div class="feature-num">{num}</div>'
                f'<div class="feature-label">{label}</div>'
                f'</div>'
            )

        st.markdown(feature_html, unsafe_allow_html=True)

    # ========================================================
    # RIGHT SIDE
    # ========================================================

    with right:

        st.markdown('<div class="auth-card-wrapper">', unsafe_allow_html=True)

        st.markdown(
            '<div class="auth-card-title">Welcome to FraudTwin</div>'
            '<div class="auth-card-caption">Sign in, or set up an account '
            'if you\'re new here.</div>',
            unsafe_allow_html=True,
        )

        login_tab, create_tab = st.tabs(
            ["Login", "Create Account"]
        )

        # ====================================================
        # LOGIN
        # ====================================================

        with login_tab:

            username = st.text_input(
                "Username",
                placeholder="Enter your username",
                key="login_username",
            )

            password = st.text_input(
                "Password",
                type="password",
                placeholder="Enter your password",
                key="login_password",
            )

            if st.button(
                "Sign In",
                use_container_width=True,
                key="sign_in_button",
            ):

                if not username or not password:
                    st.error(
                        "Please enter your username and password."
                    )
                else:
                    request_login(username, password)

        # ====================================================
        # CREATE ACCOUNT
        # ====================================================

        with create_tab:

            new_username = st.text_input(
                "Username",
                placeholder="Choose a username",
                key="create_username",
            )

            new_password = st.text_input(
                "Password",
                type="password",
                placeholder="Create a password",
                key="create_password",
            )

            confirm_password = st.text_input(
                "Confirm Password",
                type="password",
                placeholder="Confirm your password",
                key="confirm_password",
            )

            if st.button(
                "Create Account",
                use_container_width=True,
                key="create_account_button",
            ):

                if (
                    not new_username
                    or not new_password
                    or not confirm_password
                ):
                    st.error(
                        "Please fill in all fields."
                    )

                elif new_password != confirm_password:
                    st.error(
                        "Passwords do not match."
                    )

                else:
                    request_signup(new_username, new_password)

        st.markdown('</div>', unsafe_allow_html=True)


# ============================================================
# ENTRY POINT
# ============================================================

def main():
    st.set_page_config(page_title="FraudTwin", layout="wide")

    if st.session_state.authenticated:
        show_app_shell()
    elif st.session_state.page == "landing":
        show_landing_page()
    else:
        show_auth_page()


if __name__ == "__main__":
    main()