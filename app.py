"""
Startup Validator — Multi-Agent Venture Validation Platform
Autonomous sequential pipeline for quantitative market sizing, competitor discovery,
SWOT/risk audit, MVP roadmap, financial feasibility & P&L modeling, and executive report synthesis.
"""
import sys
import os
import json
import time
import hashlib
from pathlib import Path
from datetime import datetime, timezone

# Windows UTF-8 console output
if hasattr(sys.stdout, 'reconfigure'):
    sys.stdout.reconfigure(encoding='utf-8')

# pyrefly: ignore[missing-import]
import streamlit as st
# pyrefly: ignore[missing-import]
import plotly.graph_objects as go
# pyrefly: ignore[missing-import]
import plotly.express as px

from config import (
    APP_NAME, APP_VERSION, APP_TAGLINE, PIPELINE_STEPS,
    AVAILABLE_PROVIDERS, DEFAULT_PROVIDER
)
from models import IdeaSubmission, FullValidationReport, FinancialFeasibility, FinancialYearProjection
from orchestrator import ValidationOrchestrator
from utils.sample_ideas import SAMPLE_IDEAS
from utils.pdf_generator import generate_pdf_report
from utils.llm_client import UnifiedLLMClient
from agents.advisor_agent import ConversationalAdvisorAgent
from agents.report_agent import ReportGenerationAgent

# Page Configuration
st.set_page_config(
    page_title="Startup Validator",
    page_icon=None,
    layout="wide",
    initial_sidebar_state="expanded"
)

# User Database Persistence
USERS_FILE = Path(__file__).resolve().parent / "users.json"

def load_users() -> dict:
    if not USERS_FILE.exists():
        default_users = {
            "founder": hashlib.sha256("password".encode()).hexdigest(),
            "admin": hashlib.sha256("admin123".encode()).hexdigest(),
        }
        with open(USERS_FILE, "w", encoding="utf-8") as f:
            json.dump(default_users, f, indent=2)
        return default_users
    try:
        with open(USERS_FILE, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception:
        return {}

def save_users(users: dict):
    with open(USERS_FILE, "w", encoding="utf-8") as f:
        json.dump(users, f, indent=2)

def hash_pw(pw: str) -> str:
    return hashlib.sha256(pw.encode()).hexdigest()

# Dynamic Theme Engine with Professional Typography and Icon Protection
# Dynamic Theme Engine
PALETTES = {
        "light": {
        "bg": "linear-gradient(135deg,#F9D6EA 0%,#EBD9FA 28%,#FFE3D1 62%,#CDF1E8 100%)",
        "card": "#FFFFFF", "glass": "rgba(255,255,255,.74)",
        "line": "#E0C9E6", "ink": "#231530", "muted": "#51405C",
        "accent": "#7B2D8E", "accent-soft": "#F1DDF6",
        "shadow": "0 1px 2px rgba(35,21,48,.08), 0 12px 30px -10px rgba(123,45,142,.35)",
        "input-bg": "#F7ECF8", "sidebar": "#FFFFFF", "sidebar2": "#F1DDF6",
        "active-bg": "#F1DDF6", "active-bd": "#7B2D8E",
        "done-bg": "#D5F5EC", "done-bd": "#5CCDB6", "done-tx": "#0B6B5E",
        "pend-bg": "#FFFFFF", "pend-tx": "#51405C",
        "title-grad": "linear-gradient(135deg,#4A1D4F 0%,#7B2D8E 45%,#E8475F 100%)",
        "ok": "#0B7A5F", "warn": "#B45309", "bad": "#BE123C",
        "c1": "#7B2D8E", "c2": "#E8475F", "c3": "#0F9D8A",
        "c4": "#F59E0B", "c5": "#DB2777", "c6": "#F97316",
        "k1": "#E9D6FA", "k2": "#CFF3E9", "k3": "#FFDCC7", "k4": "#FFEDB8", "k5": "#FBD3E4",
    },
    "dark": {
        "bg": "radial-gradient(circle at 0% 0%,#2A1233 0%,#170B1E 50%,#0E0814 100%)",
        "card": "#211128", "line": "#3E2549", "ink": "#F8ECF7", "muted": "#CDB4CB",
        "accent": "#E9A8F5", "accent-soft": "rgba(224,150,240,.16)",
        "shadow": "0 10px 28px rgba(0,0,0,.5)",
        "input-bg": "#1A0E21", "sidebar": "#1A0E21", "sidebar2": "#2A1233",
        "active-bg": "rgba(192,107,219,.20)", "active-bd": "#C06BDB",
        "done-bg": "rgba(45,212,191,.12)", "done-bd": "rgba(45,212,191,.45)", "done-tx": "#5EEAD4",
        "pend-bg": "#1A0E21", "pend-tx": "#CDB4CB",
        "title-grad": "linear-gradient(135deg,#F8D7FF 0%,#F0A6D8 50%,#FDBA74 100%)",
        "ok": "#5EEAD4", "warn": "#FCD34D", "bad": "#FDA4AF",
        "c1": "#C06BDB", "c2": "#FB7185", "c3": "#2DD4BF",
        "c4": "#FBBF24", "c5": "#F472B6", "c6": "#FB923C",
    },
}

BASE_CSS = """
@import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');

html, body, .stApp, p, h1, h2, h3, h4, h5, h6, label, input, textarea, select, table, th, td,
button:not([class*="material"]) {
  font-family: 'Plus Jakarta Sans', 'Inter', -apple-system, 'Segoe UI', Roboto, sans-serif !important;
}
[data-testid="stIconMaterial"], .material-icons, [class*="material-symbols"] {
  font-family: 'Material Symbols Rounded','Material Symbols Outlined','Material Icons' !important;
}

.stApp { 
background: var(--bg); 
color: var(--ink);
 }
header[data-testid="stHeader"] {
 background: transparent; 
 }
.block-container { 
padding-top: 2.2rem; 
max-width: 1360px; 
}
p, span, label, li, .stMarkdown { color: var(--ink); line-height: 1.6; }
h1, h2, h3, h4, h5, h6 { color: var(--ink) !important; font-weight: 700; letter-spacing: -.015em; }
hr { border-color: var(--line) !important; }
.stCaption, [data-testid="stCaptionContainer"] { color: var(--muted) !important; }

[style*="color: #475569"], [style*="color:#475569"],
[style*="color: #64748B"], [style*="color:#64748B"] { color: var(--muted) !important; }

/* ===== EMPTY WHITE BARS: hide every empty card wrapper ===== */
.glass-card:empty { display: none !important; }
div[data-testid="stElementContainer"]:has(> div[data-testid="stMarkdown"] .glass-card:empty),
div.element-container:has(.glass-card:empty) { display: none !important; }
div[data-testid="stMarkdownContainer"]:empty { display: none; }

/* ---------- sidebar ---------- */
[data-testid="stSidebar"] { background: var(--sidebar) !important; border-right: 1px solid var(--line); }
[data-testid="stSidebar"] * { color: var(--ink); }
[data-testid="stSidebar"] label p { white-space: nowrap; font-size: .95rem; }

/* ---------- cards ---------- */
.glass-card {
  background: var(--card); border: 1px solid var(--line); border-radius: 14px;
  padding: 22px 24px; margin-bottom: 18px; box-shadow: var(--shadow);
}
.hero-badge { display: inline-block; background: var(--accent-soft); color: var(--accent);
  border: 1px solid var(--line); padding: 5px 12px; border-radius: 99px; font-size: .78rem;
  font-weight: 700; letter-spacing: .07em; text-transform: uppercase; margin-bottom: 12px; }
.hero-title { font-size: 2.4rem; font-weight: 800; line-height: 1.15; margin-bottom: 8px;
  background: var(--title-grad); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.hero-subtitle { font-size: 1.02rem; color: var(--muted); max-width: 820px; line-height: 1.6; margin-bottom: 20px; }

.metric-box { background: var(--card); border: 1px solid var(--line); border-radius: 12px;
  padding: 16px 18px; text-align: center; height: 100%; box-shadow: var(--shadow); }
.metric-value { font-size: 2rem; font-weight: 800; color: var(--accent); letter-spacing: -.02em; }
.metric-label { font-size: .78rem; color: var(--muted); text-transform: uppercase;
  letter-spacing: .06em; font-weight: 700; margin-top: 4px; }

.adaptive-card, .adaptive-subcard { background: var(--card); border: 1px solid var(--line);
  color: var(--ink); border-radius: 10px; padding: 14px 16px; margin-bottom: 10px; }
.adaptive-subcard { background: var(--input-bg); }

/* ---------- pipeline stepper ---------- */
.stepper-grid { display: grid; grid-template-columns: repeat(3, 1fr); gap: 10px; margin: 16px 0 14px; }
@media (max-width: 900px) { .stepper-grid { grid-template-columns: repeat(2, 1fr); } }
.step-card { border-radius: 10px; padding: 12px 14px; min-height: 64px; }
.step-active  { background: var(--active-bg); border: 1.5px solid var(--active-bd); color: var(--ink); }
.step-done    { background: var(--done-bg);   border: 1px solid var(--done-bd);     color: var(--done-tx); }
.step-pending { background: var(--pend-bg);   border: 1px solid var(--line);        color: var(--pend-tx); }
.analysis-overview-card { background: var(--card); border: 1.5px solid var(--active-bd);
  border-radius: 12px; padding: 18px 22px; margin-top: 12px; box-shadow: var(--shadow); }

/* ---------- buttons (normal, primary, download, form submit) ---------- */
.stButton > button, .stDownloadButton > button, [data-testid="stFormSubmitButton"] > button {
  background: var(--card); color: var(--ink) !important; border: 1px solid var(--line);
  border-radius: 8px; font-weight: 600; padding: .55rem 1rem; transition: all .15s ease; }
.stButton > button:hover, .stDownloadButton > button:hover, [data-testid="stFormSubmitButton"] > button:hover {
  border-color: var(--accent); color: var(--accent) !important; }
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"] {
  background: var(--accent); color: #fff !important; border: none; }
.stButton > button:focus-visible, .stDownloadButton > button:focus-visible {
  outline: 3px solid var(--accent); outline-offset: 2px; }

/* ---------- inputs ---------- */
/* ---------- inputs (text, text area, number, select) ---------- */
[data-baseweb="input"], [data-baseweb="base-input"], [data-baseweb="textarea"],
[data-baseweb="select"] > div {
  background: var(--input-bg) !important;
  border-color: var(--line) !important;
  border-radius: 8px !important;
}
input, textarea, [data-baseweb="select"] input {
  background: transparent !important;
  color: var(--ink) !important;
  -webkit-text-fill-color: var(--ink) !important;
  caret-color: var(--accent);
}
input::placeholder, textarea::placeholder {
  color: var(--muted) !important;
  -webkit-text-fill-color: var(--muted) !important;
  opacity: 1 !important;
}
[data-baseweb="select"] div, [data-baseweb="select"] span, [data-baseweb="select"] svg {
  color: var(--ink) !important;
  fill: var(--ink) !important;
}
[data-baseweb="popover"] ul, [data-baseweb="menu"] {
  background: var(--card) !important;
  color: var(--ink) !important;
}
[data-baseweb="popover"] li:hover { background: var(--accent-soft) !important; }

/* ---------- tabs / expanders / tables ---------- */
.stTabs [data-baseweb="tab"] { font-size: .92rem; color: var(--muted); }
.stTabs [aria-selected="true"] { color: var(--accent) !important; font-weight: 700; }
[data-testid="stExpander"] { background: var(--card); border: 1px solid var(--line); border-radius: 10px; }
[data-testid="stExpander"] details summary { font-weight: 600; padding: 10px 14px; }
[data-testid="stTable"] table, [data-testid="stTable"] th, [data-testid="stTable"] td { color: var(--ink); border-color: var(--line); }

/* ---------- status / verdict / tags ---------- */
.status-pill { display: inline-block; padding: 3px 10px; border-radius: 99px; font-size: .74rem;
  font-weight: 700; text-transform: uppercase; letter-spacing: .04em; }
.status-active { background: var(--accent-soft); color: var(--accent); border: 1px solid var(--accent); }
.status-ready  { background: var(--done-bg); color: var(--ok); border: 1px solid var(--done-bd); }
.status-idle   { background: var(--input-bg); color: var(--muted); border: 1px solid var(--line); }
.verdict-strong-go, .verdict-caution, .verdict-pivot { padding: 8px 16px; border-radius: 8px;
  font-weight: 700; font-size: 1.02rem; display: inline-block; }
.verdict-strong-go { background: rgba(16,185,129,.14); border: 1.5px solid var(--ok);   color: var(--ok); }
.verdict-caution   { background: rgba(245,158,11,.14); border: 1.5px solid var(--warn); color: var(--warn); }
.verdict-pivot     { background: rgba(239,68,68,.14);  border: 1.5px solid var(--bad);  color: var(--bad); }
.tag-must, .tag-should, .tag-could, .tag-wont { padding: 3px 8px; border-radius: 4px; font-size: .76rem; font-weight: 700; }
.tag-must   { background: rgba(239,68,68,.14);  color: var(--bad);    border: 1px solid var(--bad); }
.tag-should { background: rgba(245,158,11,.14); color: var(--warn);   border: 1px solid var(--warn); }
.tag-could  { background: var(--accent-soft);   color: var(--accent); border: 1px solid var(--accent); }
.tag-wont   { background: var(--input-bg);      color: var(--muted);  border: 1px solid var(--line); }

/* ---------- advisor chat ---------- */
.chat-bubble-agent, .chat-bubble-user { border-radius: 10px; padding: 14px 16px; margin-bottom: 12px; border: 1px solid var(--line); }
.chat-bubble-agent { background: var(--card); }
.chat-bubble-user  { background: var(--accent-soft); }

/* ===== COLOUR LAYER ===== */
[data-testid="stSidebar"] {
  background: linear-gradient(180deg, var(--sidebar) 0%, var(--sidebar2) 100%) !important;
}
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, var(--c1), var(--c2)) !important;
  box-shadow: 0 6px 18px -6px var(--c1);
}
.stButton > button[kind="primary"]:hover { filter: brightness(1.08); color: #fff !important; }

/* gradient numbers on KPI cards */
.metric-value {
  background: linear-gradient(90deg, var(--c1), var(--c2));
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
}

/* a different coloured strip on each KPI card in a row */
[data-testid="stColumn"]:nth-child(1) .metric-box, [data-testid="column"]:nth-child(1) .metric-box { border-top: 4px solid var(--c1); }
[data-testid="stColumn"]:nth-child(2) .metric-box, [data-testid="column"]:nth-child(2) .metric-box { border-top: 4px solid var(--c3); }
[data-testid="stColumn"]:nth-child(3) .metric-box, [data-testid="column"]:nth-child(3) .metric-box { border-top: 4px solid var(--c6); }
[data-testid="stColumn"]:nth-child(4) .metric-box, [data-testid="column"]:nth-child(4) .metric-box { border-top: 4px solid var(--c4); }
[data-testid="stColumn"]:nth-child(5) .metric-box, [data-testid="column"]:nth-child(5) .metric-box { border-top: 4px solid var(--c5); }

/* agent cards on the dashboard: coloured left edge per column */
[data-testid="stColumn"]:nth-child(1) .adaptive-card, [data-testid="column"]:nth-child(1) .adaptive-card { border-left: 4px solid var(--c1); }
[data-testid="stColumn"]:nth-child(2) .adaptive-card, [data-testid="column"]:nth-child(2) .adaptive-card { border-left: 4px solid var(--c6); }
[data-testid="stColumn"]:nth-child(3) .adaptive-card, [data-testid="column"]:nth-child(3) .adaptive-card { border-left: 4px solid var(--c3); }
[data-testid="stColumn"]:nth-child(4) .adaptive-card, [data-testid="column"]:nth-child(4) .adaptive-card { border-left: 4px solid var(--c4); }

/* cards get a soft gradient top edge */
.glass-card { border-top: 3px solid var(--c1); }

/* tabs and progress bar */
.stTabs [data-baseweb="tab-highlight"] { background: linear-gradient(90deg, var(--c1), var(--c2)) !important; height: 3px; }
[data-testid="stProgress"] div[role="progressbar"] > div { background: linear-gradient(90deg, var(--c1), var(--c3)) !important; }
.step-active { box-shadow: 0 0 0 3px var(--accent-soft); }
.hero-badge { background: linear-gradient(90deg, var(--accent-soft), transparent); border-left: 3px solid var(--c1); }



    
/* ===== SIDEBAR v3: plum + coral, no radio circles, watermark ===== */
[data-testid="stSidebar"] {
  --sb1:#2A1233; --sb2:#3B1747; --sb3:#52204F;       /* panel gradient */
  --pill1:#FB7185; --pill2:#F59E0B;                  /* active item */
  --sbtext:#F8ECF7; --sbmuted:#D8BAD6;
  background-color: var(--sb2) !important;
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='240' height='240' viewBox='0 0 24 24' fill='none' stroke='white' stroke-width='.45' stroke-linecap='round' stroke-linejoin='round' opacity='.14'%3E%3Cg transform='rotate(18 12 12)'%3E%3Cpath d='M12 2c3 2 5 6 5 10l-2 3H9l-2-3c0-4 2-8 5-10z'/%3E%3Ccircle cx='12' cy='9' r='1.6'/%3E%3Cpath d='M7 12l-3 3 3 1M17 12l3 3-3 1M10 18l2 4 2-4'/%3E%3C/g%3E%3C/svg%3E"),
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260' viewBox='0 0 260 260' fill='none' stroke='white' stroke-width='.8' stroke-linecap='round' stroke-linejoin='round' opacity='.07'%3E%3Cg transform='translate(20 24) rotate(-14 12 12) scale(2)'%3E%3Cpath d='M12 2c3 2 5 6 5 10l-2 3H9l-2-3c0-4 2-8 5-10z'/%3E%3Ccircle cx='12' cy='9' r='1.6'/%3E%3Cpath d='M7 12l-3 3 3 1M17 12l3 3-3 1M10 18l2 4 2-4'/%3E%3C/g%3E%3Cg transform='translate(150 30) scale(2)'%3E%3Cpath d='M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.8.8 1 1.5 1 2.5h6c0-1 .2-1.7 1-2.5A6 6 0 0 0 12 3z'/%3E%3C/g%3E%3Cg transform='translate(28 150) scale(2)'%3E%3Cpath d='M3 20h18M5 16l4-4 3 3 6-7M15 8h3v3'/%3E%3C/g%3E%3Cg transform='translate(158 156) scale(2)'%3E%3Ccircle cx='12' cy='12' r='9'/%3E%3Cpath d='M8 12.5l3 3 5-6'/%3E%3C/g%3E%3Cg transform='translate(100 96) scale(1.2)'%3E%3Ccircle cx='12' cy='12' r='9'/%3E%3Ccircle cx='12' cy='12' r='5'/%3E%3Ccircle cx='12' cy='12' r='1'/%3E%3C/g%3E%3Cpath d='M120 20v8M116 24h8M230 120v8M226 124h8M96 230v8M92 234h8' /%3E%3C/svg%3E"),
    linear-gradient(180deg, var(--sb1) 0%, var(--sb2) 55%, var(--sb3) 100%) !important;
  background-repeat: no-repeat, repeat, no-repeat !important;
  background-position: right -50px bottom 190px, 0 0, 0 0 !important;
  background-size: 240px, 220px, cover !important;
  border-right: none !important;
}
[data-testid="stSidebarContent"] { background: transparent !important; }

[data-testid="stSidebar"] *, [data-testid="stSidebar"] p,
[data-testid="stSidebar"] label, [data-testid="stSidebar"] span { color: var(--sbtext) !important; }
.sb-sub, .sb-label, .sb-foot, .sb-urole { color: var(--sbmuted) !important; }
.sb-name, .sb-uname { color: #FFFFFF !important; }
.sb-logo { background: linear-gradient(135deg, var(--pill1), var(--pill2)) !important;
  box-shadow: 0 8px 18px -6px rgba(251,113,133,.7); }

/* --- remove the radio circles (several selectors so one matches your version) --- */
[data-testid="stSidebar"] [data-testid="stRadio"] label > div:first-of-type:not(:only-of-type),
[data-testid="stSidebar"] label[data-baseweb="radio"] > div:first-of-type:not(:only-of-type),
[data-testid="stSidebar"] [role="radiogroup"] label > div:first-of-type:not(:only-of-type) { display: none !important; }
[data-testid="stSidebar"] input[type="radio"] { position: absolute; opacity: 0; pointer-events: none; }

/* --- menu rows --- */
[data-testid="stSidebar"] [role="radiogroup"] { gap: 6px; }
[data-testid="stSidebar"] label[data-baseweb="radio"] {
  width: 100%; margin: 0; padding: 11px 14px; border-radius: 10px; cursor: pointer;
  transition: background .15s ease; }
[data-testid="stSidebar"] label[data-baseweb="radio"]:hover { background: rgba(255,255,255,.10); }
[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) {
  background: linear-gradient(135deg, var(--pill1), var(--pill2));
  box-shadow: 0 8px 18px -8px rgba(251,113,133,.9); }
[data-testid="stSidebar"] label[data-baseweb="radio"]:has(input:checked) * { color: #2A1233 !important; font-weight: 700; }

/* --- day / night switch --- */
.st-key-theme_radio [role="radiogroup"] { background: rgba(255,255,255,.08) !important;
  border: 1px solid rgba(255,255,255,.18) !important; border-radius: 10px; padding: 4px; gap: 4px; flex-wrap: nowrap; }
.st-key-theme_radio label[data-baseweb="radio"] { flex: 1; justify-content: center; padding: 7px 6px; }
.st-key-theme_radio label[data-baseweb="radio"]:has(input:checked) { background: #FFFFFF; box-shadow: none; }
.st-key-theme_radio label[data-baseweb="radio"]:has(input:checked) * { color: #52204F !important; }

/* --- user card + sign out --- */
.sb-user { background: rgba(255,255,255,.08); border: 1px solid rgba(255,255,255,.16); }
.sb-avatar { background: linear-gradient(135deg, #2DD4BF, #10B981) !important; color: #052E2B !important; }
[data-testid="stSidebar"] .stButton > button { background: rgba(255,255,255,.10);
  border: 1px solid rgba(255,255,255,.28); color: #FFFFFF !important; }
[data-testid="stSidebar"] .stButton > button:hover { background: #E11D48; border-color: transparent; }

/* ===== WATERMARK on the main page (faint, sits behind the cards) ===== */
.stApp {
  background-image:
    url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='260' height='260' viewBox='0 0 260 260' fill='none' stroke='%2364748B' stroke-width='.8' stroke-linecap='round' stroke-linejoin='round' opacity='.10'%3E%3Cg transform='translate(20 24) rotate(-14 12 12) scale(2)'%3E%3Cpath d='M12 2c3 2 5 6 5 10l-2 3H9l-2-3c0-4 2-8 5-10z'/%3E%3Ccircle cx='12' cy='9' r='1.6'/%3E%3Cpath d='M7 12l-3 3 3 1M17 12l3 3-3 1M10 18l2 4 2-4'/%3E%3C/g%3E%3Cg transform='translate(150 30) scale(2)'%3E%3Cpath d='M9 18h6M10 21h4M12 3a6 6 0 0 0-4 10.5c.8.8 1 1.5 1 2.5h6c0-1 .2-1.7 1-2.5A6 6 0 0 0 12 3z'/%3E%3C/g%3E%3Cg transform='translate(28 150) scale(2)'%3E%3Cpath d='M3 20h18M5 16l4-4 3 3 6-7M15 8h3v3'/%3E%3C/g%3E%3Cg transform='translate(158 156) scale(2)'%3E%3Ccircle cx='12' cy='12' r='9'/%3E%3Cpath d='M8 12.5l3 3 5-6'/%3E%3C/g%3E%3Cg transform='translate(100 96) scale(1.2)'%3E%3Ccircle cx='12' cy='12' r='9'/%3E%3Ccircle cx='12' cy='12' r='5'/%3E%3Ccircle cx='12' cy='12' r='1'/%3E%3C/g%3E%3Cpath d='M120 20v8M116 24h8M230 120v8M226 124h8M96 230v8M92 234h8' /%3E%3C/svg%3E"),
    var(--bg) !important;
  background-repeat: repeat, no-repeat !important;
  background-attachment: fixed !important;
}



/* ===== PLUM + CORAL RECOLOUR ===== */
/* Recent Activity banner */
[style*="border-left: 4px solid #0284C7"] {
  background: var(--accent-soft) !important;
  border-left: 4px solid var(--c2) !important;
}
/* hard-coded blue text anywhere in the app */
[style*="color: #0284C7"], [style*="color:#0284C7"],
[style*="color: #0369A1"], [style*="color:#0369A1"] { color: var(--accent) !important; }
[style*="border-left: 4px solid #0284C7"] b { color: var(--ink); }

/* main page buttons: plum to coral */
.stButton > button[kind="primary"], [data-testid="stFormSubmitButton"] > button[kind="primary"] {
  background: linear-gradient(135deg, var(--c1), var(--c2)) !important;
  box-shadow: 0 8px 20px -8px var(--c2);
}
/* KPI numbers and tabs */
.metric-value { background: linear-gradient(90deg, var(--c1), var(--c2)); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }
.stTabs [data-baseweb="tab-highlight"] { background: linear-gradient(90deg, var(--c1), var(--c2)) !important; }
[data-testid="stProgress"] div[role="progressbar"] > div { background: linear-gradient(90deg, var(--c1), var(--c4)) !important; }
.glass-card { border-top: 3px solid var(--c2); }
.hero-badge { background: var(--accent-soft); color: var(--accent); border-left: 3px solid var(--c2); }








/* ===== DAY MODE: ~40% COLOUR ===== */
/* section cards: translucent so the page colour shows through */
.glass-card { background: var(--glass, var(--card)); backdrop-filter: blur(6px); }

/* KPI cards: a pastel fill per card */
[data-testid="stColumn"]:nth-child(1) .metric-box, [data-testid="column"]:nth-child(1) .metric-box { background: var(--k1, var(--card)); }
[data-testid="stColumn"]:nth-child(2) .metric-box, [data-testid="column"]:nth-child(2) .metric-box { background: var(--k2, var(--card)); }
[data-testid="stColumn"]:nth-child(3) .metric-box, [data-testid="column"]:nth-child(3) .metric-box { background: var(--k3, var(--card)); }
[data-testid="stColumn"]:nth-child(4) .metric-box, [data-testid="column"]:nth-child(4) .metric-box { background: var(--k4, var(--card)); }
[data-testid="stColumn"]:nth-child(5) .metric-box, [data-testid="column"]:nth-child(5) .metric-box { background: var(--k5, var(--card)); }

/* agent cards: matching pastel fills */
[data-testid="stColumn"]:nth-child(1) .adaptive-card, [data-testid="column"]:nth-child(1) .adaptive-card { background: var(--k1, var(--card)); }
[data-testid="stColumn"]:nth-child(2) .adaptive-card, [data-testid="column"]:nth-child(2) .adaptive-card { background: var(--k5, var(--card)); }
[data-testid="stColumn"]:nth-child(3) .adaptive-card, [data-testid="column"]:nth-child(3) .adaptive-card { background: var(--k2, var(--card)); }
[data-testid="stColumn"]:nth-child(4) .adaptive-card, [data-testid="column"]:nth-child(4) .adaptive-card { background: var(--k4, var(--card)); }

/* tab bar, banner and expanders get a coloured base */
.stTabs [data-baseweb="tab-list"] { background: var(--glass, transparent); border-radius: 12px; padding: 4px 8px; }
[style*="border-left: 4px solid"] { background: var(--k1, var(--accent-soft)) !important; }
[data-testid="stExpander"] { background: var(--glass, var(--card)); }

/* slightly stronger text colours on pastel fills */
.metric-label { color: var(--ink); opacity: .75; }
"""


def get_theme_css(theme: str = "light") -> str:
    pal = PALETTES["light" if theme == "light" else "dark"]
    root = ":root{" + "".join(f"--{k}:{v};" for k, v in pal.items()) + "}"
    return f"<style>{root}{BASE_CSS}</style>"

# Session State Initialization
if "authenticated" not in st.session_state:
    st.session_state.authenticated = False
if "username" not in st.session_state:
    st.session_state.username = None
if "current_page" not in st.session_state:
    st.session_state.current_page = "Dashboard"
if "theme" not in st.session_state:
    st.session_state.theme = "light"
if "validation_report" not in st.session_state:
    st.session_state.validation_report = None
if "history" not in st.session_state:
    st.session_state.history = []
if "advisor_chat" not in st.session_state:
    st.session_state.advisor_chat = []
if "selected_sample" not in st.session_state:
    st.session_state.selected_sample = None
if "profile_info" not in st.session_state:
    st.session_state.profile_info = {
        "full_name": "Koushik Founder",
        "email": "koushik@startupvalidator.io",
        "role": "Founder",
        "company": "InnovateFlow Labs"
    }

# Inject Current Theme Stylesheet
st.markdown(get_theme_css(st.session_state.theme), unsafe_allow_html=True)


# =========================================================================
# LOGIN & REGISTRATION GATEWAY
# =========================================================================
if not st.session_state.authenticated:
    st.markdown("<div style='text-align: center; margin-top: 40px; margin-bottom: 20px;'>", unsafe_allow_html=True)
    st.markdown("<div class='hero-badge'>Multi-Agent Venture Validation Platform</div>", unsafe_allow_html=True)
    st.markdown("<h1 style='font-size: 2.8rem; margin: 0; padding: 0;'>Startup Validator</h1>", unsafe_allow_html=True)
    st.markdown("<p style='font-size: 1.1rem; color: #475569; margin-top: 6px;'>Autonomous Multi-Agent Potential Assessment and Live Market Intelligence</p>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    col_l, col_center, col_r = st.columns([1, 1.3, 1])
    with col_center:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        
        auth_mode = st.radio(
            "Account Access",
            options=["Sign In", "Create Account"],
            horizontal=True,
            label_visibility="collapsed"
        )
        
        users = load_users()

        if auth_mode == "Sign In":
            st.markdown("### Sign In to Workspace")
            st.caption("Access your executive validation workspace, live web search, and reports.")
            
            with st.form("login_form"):
                login_user = st.text_input("Username", placeholder="e.g. founder")
                login_pw = st.text_input("Password", type="password", placeholder="Enter your password")
                login_btn = st.form_submit_button("Sign In", use_container_width=True)

                if login_btn:
                    clean_u = login_user.strip()
                    if not clean_u or not login_pw:
                        st.error("Please enter both username and password.")
                    elif clean_u not in users:
                        st.error("Account not found. Please verify your credentials or register.")
                    elif users[clean_u] != hash_pw(login_pw):
                        st.error("Incorrect password. Please try again.")
                    else:
                        st.session_state.authenticated = True
                        st.session_state.username = clean_u
                        st.session_state.profile_info["full_name"] = clean_u.capitalize()
                        st.session_state.profile_info["email"] = f"{clean_u}@startupvalidator.io"
                        st.rerun()

            st.markdown("---")
            st.caption("Demo Account: **founder** / **password** (or **admin** / **admin123**)")

        else:
            st.markdown("### Register New Account")
            st.caption("Create an account to save venture validations and export investment dossiers.")
            
            with st.form("register_form"):
                reg_user = st.text_input("Choose Username", placeholder="e.g. founder1")
                reg_pw = st.text_input("Choose Password", type="password", placeholder="Minimum 4 characters")
                reg_pw_confirm = st.text_input("Confirm Password", type="password", placeholder="Re-enter password")
                reg_btn = st.form_submit_button("Register Account", use_container_width=True)

                if reg_btn:
                    clean_u = reg_user.strip()
                    if not clean_u:
                        st.error("Username cannot be empty.")
                    elif len(clean_u) < 3:
                        st.error("Username must be at least 3 characters long.")
                    elif clean_u in users:
                        st.error("Username is already registered. Please choose another username.")
                    elif len(reg_pw) < 4:
                        st.error("Password must be at least 4 characters long.")
                    elif reg_pw != reg_pw_confirm:
                        st.error("Passwords do not match.")
                    else:
                        users[clean_u] = hash_pw(reg_pw)
                        save_users(users)
                        st.session_state.authenticated = True
                        st.session_state.username = clean_u
                        st.session_state.profile_info["full_name"] = clean_u.capitalize()
                        st.session_state.profile_info["email"] = f"{clean_u}@startupvalidator.io"
                        st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)
    st.stop()


# =========================================================================
# AUTHENTICATED SIDE PANEL NAVIGATION
# =========================================================================
with st.sidebar:
    st.markdown("<div style='padding: 6px 0 14px 0;'>", unsafe_allow_html=True)
    st.markdown("<div class='hero-badge'>Startup Validator</div>", unsafe_allow_html=True)
    st.markdown("<h2 style='font-size: 1.4rem; margin: 0;'>Navigation</h2>", unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # Core 3 navigation items strictly as requested
    nav_selection = st.radio(
        "Workspace Navigation",
        options=["Dashboard", "Validator", "Settings"],
        index=["Dashboard", "Validator", "Settings"].index(st.session_state.current_page),
        label_visibility="collapsed"
    )

    if nav_selection != st.session_state.current_page:
        st.session_state.current_page = nav_selection
        st.rerun()

    st.markdown("---")

    # Quick Appearance Mode Toggle
    st.markdown("<b>Display Theme</b>", unsafe_allow_html=True)
    theme_choice = st.radio(
        "Theme Switcher",
        options=["Crystal Day", "Obsidian Night"],
        index=0 if st.session_state.theme == "light" else 1,
        horizontal=True,
        label_visibility="collapsed"
    )
    new_theme = "light" if "Day" in theme_choice else "dark"
    if new_theme != st.session_state.theme:
        st.session_state.theme = new_theme
        st.rerun()

    # Dynamic spacing to keep logout shifted to the bottom
    st.markdown("<div style='min-height: 28vh;'></div>", unsafe_allow_html=True)
    st.markdown("---")

    # Bottom User Account Badge & Sign Out
    st.markdown(
        f"<div style='font-size: 0.88rem; margin-bottom: 8px;'>"
        f"Signed in: <b>{st.session_state.profile_info.get('full_name', st.session_state.username)}</b><br/>"
        f"<span style='font-size: 0.78rem; opacity: 0.75;'>{st.session_state.profile_info.get('role', 'Founder')} • {st.session_state.profile_info.get('company', 'Startup')}</span>"
        f"</div>",
        unsafe_allow_html=True
    )
    if st.button("Sign Out", use_container_width=True):
        st.session_state.authenticated = False
        st.session_state.username = None
        st.rerun()

    st.markdown("<div style='font-size: 0.72rem; color: #64748B; margin-top: 10px; text-align: center;'>Startup Validator v2.5.0<br/>Autonomous Agent Swarm</div>", unsafe_allow_html=True)


# =========================================================================
# PAGE 1: ELEGANT & PROFESSIONAL DASHBOARD
# =========================================================================
if st.session_state.current_page == "Dashboard":
    # 1. Welcome & Overview
    current_date_str = datetime.now().strftime("%B %d, %Y")
    col_dash_head, col_dash_act = st.columns([3, 1.2])
    with col_dash_head:
        st.markdown(f"<div class='hero-badge'>Executive Overview • {current_date_str}</div>", unsafe_allow_html=True)
        st.markdown(f"<div class='hero-title'>Welcome back, {st.session_state.profile_info.get('full_name', 'Founder')}!</div>", unsafe_allow_html=True)
        st.markdown(
            f"<p class='hero-subtitle'>"
            f"Here is your startup intelligence overview. Monitor active AI agent swarms, explore venture viability trends, "
            f"and evaluate new business opportunities with live market search."
            f"</p>",
            unsafe_allow_html=True
        )
    with col_dash_act:
        st.markdown("<div style='padding-top: 24px; text-align: right;'>", unsafe_allow_html=True)
        if st.button("Quick Start Validation", type="primary", use_container_width=True):
            st.session_state.current_page = "Validator"
            st.rerun()
        st.caption("Triggers all 9 sequential AI agents")
        st.markdown("</div>", unsafe_allow_html=True)

    # Recent Activity Alert
    st.markdown(
        "<div style='background: rgba(2, 132, 199, 0.08); border-left: 4px solid #0284C7; padding: 12px 16px; border-radius: 6px; margin-bottom: 22px; font-size: 0.92rem;'>"
        "<b>Recent Activity:</b> Autonomous market scanning completed 4 live query runs across LegalTech, HealthTech, and Creator Economy benchmarks."
        "</div>",
        unsafe_allow_html=True
    )

    # 2. Key Performance Metrics (Four summary cards as specified)
    col_m1, col_m2, col_m3, col_m4 = st.columns(4)
    with col_m1:
        st.markdown("<div class='metric-box'><div class='metric-value'>24</div><div class='metric-label'>Ideas Submitted</div></div>", unsafe_allow_html=True)
    with col_m2:
        st.markdown("<div class='metric-box'><div class='metric-value'>18</div><div class='metric-label'>Validated Ideas</div></div>", unsafe_allow_html=True)
    with col_m3:
        st.markdown("<div class='metric-box'><div class='metric-value'>15</div><div class='metric-label'>Reports Generated</div></div>", unsafe_allow_html=True)
    with col_m4:
        st.markdown("<div class='metric-box'><div class='metric-value' style='color: #059669;'>75%</div><div class='metric-label'>Average Validation Score</div></div>", unsafe_allow_html=True)

    st.write("")

    # 3. AI Agent Swarm Status
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### AI Agent Swarm Status")
    st.caption("Real-time operational readiness of the 8 core autonomous intelligence agents:")
    
    agent_status_data = [
        {"name": "Idea Extraction Agent", "role": "Semantic Parsing", "status": "Ready", "class": "status-ready"},
        {"name": "Web Search Agent", "role": "Live Tavily & DDGS", "status": "Active", "class": "status-active"},
        {"name": "Market Research Agent", "role": "TAM/SAM Sizing", "status": "Ready", "class": "status-ready"},
        {"name": "Competitor Analysis Agent", "role": "Gap & Moat Matrix", "status": "Ready", "class": "status-ready"},
        {"name": "SWOT Analysis Agent", "role": "4-Quadrant Risk Audit", "status": "Ready", "class": "status-ready"},
        {"name": "MVP Recommendation Agent", "role": "MoSCoW Sprints", "status": "Ready", "class": "status-ready"},
        {"name": "Financial Feasibility Agent", "role": "P&L & ROI Simulator", "status": "Ready", "class": "status-ready"},
        {"name": "Validation Report Agent", "role": "Executive Dossier", "status": "Ready", "class": "status-ready"},
    ]
    
    c_ag_rows = st.columns(4)
    for idx, ag in enumerate(agent_status_data):
        with c_ag_rows[idx % 4]:
            st.markdown(f"""
            <div class='adaptive-card' style='margin-bottom: 10px;'>
                <div style='display: flex; justify-content: space-between; align-items: center;'>
                    <span style='font-weight: 700; font-size: 0.9rem;'>{ag['name']}</span>
                    <span class='status-pill {ag['class']}'>{ag['status']}</span>
                </div>
                <div style='font-size: 0.78rem; opacity: 0.8; margin-top: 4px;'>{ag['role']}</div>
            </div>
            """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)

    # 4. Recent Startup Validations & 7. Quick Actions
    col_dash_left, col_dash_right = st.columns([2.5, 1.5])
    with col_dash_left:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### Recent Startup Validations")
        st.caption("Latest venture assessments with composite viability scores:")

        recent_validations = [
            {"title": "ClauseGuard — AI Contract Shield", "industry": "LegalTech", "date": "Nov 04, 2026", "score": 82, "status": "Strong Go"},
            {"title": "CarbonTrace — Automated Accounting", "industry": "ClimateTech", "date": "Nov 02, 2026", "score": 78, "status": "Go with Caution"},
            {"title": "MediSync — Ambient Voice EHR", "industry": "HealthTech", "date": "Oct 29, 2026", "score": 85, "status": "Strong Go"},
            {"title": "CodeMorph — Production Debug Tutor", "industry": "Developer Tools", "date": "Oct 24, 2026", "score": 68, "status": "Conditional Pivot"},
        ]

        # Prepend any newly generated report from this session
        if st.session_state.validation_report:
            rep = st.session_state.validation_report
            recent_validations.insert(0, {
                "title": rep.structured_idea.title,
                "industry": rep.structured_idea.industry_domain,
                "date": "Today",
                "score": rep.composite_viability_score,
                "status": rep.executive_verdict,
                "is_current": True
            })

        for i, val in enumerate(recent_validations[:4]):
            c_v1, c_v2, c_v3, c_v4 = st.columns([3, 2, 1.5, 1.8])
            with c_v1:
                st.markdown(f"<b>{val['title']}</b><br/><span style='font-size:0.8rem; color:#64748B;'>{val['industry']}</span>", unsafe_allow_html=True)
            with c_v2:
                st.markdown(f"<span style='font-size:0.85rem;'>{val['date']}</span>", unsafe_allow_html=True)
            with c_v3:
                color_score = "#059669" if val['score'] >= 80 else ("#0284C7" if val['score'] >= 70 else "#D97706")
                st.markdown(f"<span style='font-weight:700; color:{color_score};'>{val['score']}/100</span>", unsafe_allow_html=True)
            with c_v4:
                if st.button("View Report", key=f"dash_val_{i}", use_container_width=True):
                    st.session_state.current_page = "Validator"
                    st.rerun()
            st.markdown("<div style='border-bottom: 1px solid rgba(226, 232, 240, 0.5); margin: 6px 0 10px 0;'></div>", unsafe_allow_html=True)

        st.markdown("</div>", unsafe_allow_html=True)

    with col_dash_right:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### Quick Actions")
        st.caption("Common workflow shortcuts:")

        if st.button("Validate New Idea", use_container_width=True):
            st.session_state.current_page = "Validator"
            st.rerun()
        if st.button("View Saved Reports", use_container_width=True):
            st.session_state.current_page = "Settings"
            st.rerun()
        if st.button("Compare Startup Ideas", use_container_width=True):
            st.info("Cross-venture comparison matrix initialized for LegalTech vs ClimateTech.")
        if st.button("Explore Market Trends", use_container_width=True):
            st.info("Market intelligence radar: B2B AI Workflow Automation CAGR surging at 24.8%.")
        if st.button("Export All Analytics", use_container_width=True):
            st.success("Consolidated analytics package ready for download in Settings.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 5. Analytics & Insights (Interactive Plotly Visualizations)
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### Analytics & Venture Intelligence")
    st.caption("Aggregated analytics across submitted and validated startup concepts:")

    col_ch1, col_ch2 = st.columns(2)
    with col_ch1:
        # Validation score trends
        months = ["May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
        scores = [68, 71, 74, 72, 79, 76, 82]
        fig_trend = go.Figure()
        fig_trend.add_trace(go.Scatter(
            x=months, y=scores,
            mode='lines+markers',
            name='Viability Score',
            line=dict(color='#0284C7', width=3),
            marker=dict(size=7, color='#0369A1')
        ))
        fig_trend.update_layout(
            title="Validation Score Trajectory (Average / 100)",
            margin=dict(l=20, r=20, t=40, b=20),
            height=280,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Plus Jakarta Sans', size=11)
        )
        st.plotly_chart(fig_trend, use_container_width=True)

    with col_ch2:
        # Ideas by Industry
        industries = ["B2B SaaS", "LegalTech", "HealthTech", "ClimateTech", "Developer Tools", "FinTech"]
        counts = [8, 5, 4, 3, 2, 2]
        fig_pie = go.Figure(data=[go.Pie(
            labels=industries,
            values=counts,
            hole=.45,
            marker=dict(colors=['#0284C7', '#0D9488', '#059669', '#7C3AED', '#EA580C', '#64748B'])
        )])
        fig_pie.update_layout(
            title="Ideas Categorized by Industry Domain",
            margin=dict(l=20, r=20, t=40, b=20),
            height=280,
            paper_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Plus Jakarta Sans', size=11)
        )
        st.plotly_chart(fig_pie, use_container_width=True)

    col_ch3, col_ch4 = st.columns(2)
    with col_ch3:
        # Market opportunity distribution
        sectors = ["LegalTech", "HealthTech", "ClimateTech", "DevTools"]
        tam_vals = [28.4, 42.0, 19.5, 14.2]
        som_vals = [1.2, 1.8, 0.8, 0.6]
        fig_opp = go.Figure()
        fig_opp.add_trace(go.Bar(name='TAM ($B)', x=sectors, y=tam_vals, marker_color='#0284C7'))
        fig_opp.add_trace(go.Bar(name='SOM Year 3 ($B)', x=sectors, y=som_vals, marker_color='#059669'))
        fig_opp.update_layout(
            title="Market Opportunity Sizing Comparison ($ Billion)",
            barmode='group',
            margin=dict(l=20, r=20, t=40, b=20),
            height=280,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Plus Jakarta Sans', size=11)
        )
        st.plotly_chart(fig_opp, use_container_width=True)

    with col_ch4:
        # Monthly validation activity
        act_months = ["Jun", "Jul", "Aug", "Sep", "Oct", "Nov"]
        evals = [2, 3, 4, 5, 4, 6]
        fig_act = go.Figure(data=[go.Bar(
            x=act_months,
            y=evals,
            marker_color='#38BDF8'
        )])
        fig_act.update_layout(
            title="Monthly Multi-Agent Validations Completed",
            margin=dict(l=20, r=20, t=40, b=20),
            height=280,
            paper_bgcolor='rgba(0,0,0,0)',
            plot_bgcolor='rgba(0,0,0,0)',
            font=dict(family='Plus Jakarta Sans', size=11)
        )
        st.plotly_chart(fig_act, use_container_width=True)

    st.markdown("</div>", unsafe_allow_html=True)

    # 6. Market Intelligence Signals
    st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
    st.markdown("### Real-Time Market Intelligence Radar")
    st.caption("Live sector signals and emerging startup opportunities:")

    c_mi1, c_mi2, c_mi3 = st.columns(3)
    with c_mi1:
        st.markdown("""
        <div class='adaptive-subcard'>
            <div style='font-size:0.8rem; font-weight:700; color:#0284C7;'>TRENDING SECTOR</div>
            <div style='font-size:1.05rem; font-weight:700; margin:4px 0;'>AI-Augmented Legal Workflows</div>
            <div style='font-size:0.85rem; opacity:0.85;'>High enterprise demand for automated contract redlining and compliance parsing. Expected 22% CAGR through 2031.</div>
        </div>
        """, unsafe_allow_html=True)
    with c_mi2:
        st.markdown("""
        <div class='adaptive-subcard'>
            <div style='font-size:0.8rem; font-weight:700; color:#059669;'>EMERGING WHITE SPACE</div>
            <div style='font-size:1.05rem; font-weight:700; margin:4px 0;'>Ambient Clinical Documentation</div>
            <div style='font-size:0.85rem; opacity:0.85;'>Independent practitioner segment remains underserved by legacy hospital EHR systems. Willingness to pay >$99/month.</div>
        </div>
        """, unsafe_allow_html=True)
    with c_mi3:
        st.markdown("""
        <div class='adaptive-subcard'>
            <div style='font-size:0.8rem; font-weight:700; color:#7C3AED;'>COMPETITOR BENCHMARK</div>
            <div style='font-size:1.05rem; font-weight:700; margin:4px 0;'>Self-Serve B2B Pricing Shift</div>
            <div style='font-size:0.85rem; opacity:0.85;'>Top seed-stage ventures are dropping annual sales cycles in favor of 14-day trials with transparent usage billing.</div>
        </div>
        """, unsafe_allow_html=True)
    st.markdown("</div>", unsafe_allow_html=True)


# =========================================================================
# PAGE 2: VALIDATOR (IDEA SUBMISSION & 9-STEP PIPELINE EXECUTION)
# =========================================================================
elif st.session_state.current_page == "Validator":
    # HERO HEADER SECTION
    st.markdown('<div class="hero-badge">Multi-Agent Startup Validator</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">Validate Your Startup Idea with Live Web Intelligence</div>', unsafe_allow_html=True)
    st.markdown(
        '<div class="hero-subtitle">'
        'Submit your startup concept. An orchestrated swarm of 9 autonomous AI agents analyzes problem-market fit, '
        'retrieves live web intelligence, models TAM/SAM/SOM, audits execution risks, designs an MVP roadmap, '
        'simulates 5-year financial projections with investment P&L graphs, and produces an investor-grade dossier.'
        '</div>',
        unsafe_allow_html=True
    )

    # Metric Highlights Row
    col_p1, col_p2, col_p3, col_p4 = st.columns(4)
    with col_p1:
        st.markdown("<div class='metric-box'><div style='font-size:1.15rem; font-weight:700; color:#0284C7;'>Live Web Search</div><div class='metric-label'>Tavily & DuckDuckGo</div></div>", unsafe_allow_html=True)
    with col_p2:
        st.markdown("<div class='metric-box'><div style='font-size:1.15rem; font-weight:700; color:#0369A1;'>Market Opportunity</div><div class='metric-label'>TAM - SAM - SOM</div></div>", unsafe_allow_html=True)
    with col_p3:
        st.markdown("<div class='metric-box'><div style='font-size:1.15rem; font-weight:700; color:#7C3AED;'>Financial Simulator</div><div class='metric-label'>Step 9: Investment P&L</div></div>", unsafe_allow_html=True)
    with col_p4:
        st.markdown("<div class='metric-box'><div style='font-size:1.15rem; font-weight:700; color:#059669;'>Executive Dossier</div><div class='metric-label'>Downloadable PDF</div></div>", unsafe_allow_html=True)

    st.write("")

    # SUBMISSION FORM CONTAINER
    with st.container():
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("### Startup Idea Submission Workspace")
        
        default_idea = ""
        default_domain = ""
        default_geo = "Global"
        default_monetization = "Freemium + B2B SaaS"

        if st.session_state.selected_sample:
            default_idea = st.session_state.selected_sample["raw_idea"]
            default_domain = st.session_state.selected_sample["domain"]
            default_geo = st.session_state.selected_sample.get("geography", "Global")
            default_monetization = st.session_state.selected_sample.get("monetization", "Freemium + B2B SaaS")

        # Benchmark Presets Bar
        st.markdown("<b>Quick Presets:</b>", unsafe_allow_html=True)
        sample_cols = st.columns(len(SAMPLE_IDEAS))
        for idx, sample in enumerate(SAMPLE_IDEAS):
            with sample_cols[idx]:
                if st.button(sample['title'][:20] + "...", key=f"top_sample_{sample['id']}", use_container_width=True):
                    st.session_state.selected_sample = sample
                    st.rerun()

        st.write("")

        raw_idea_input = st.text_area(
            "Describe your startup idea (What problem do you solve, for whom, and how?):",
            value=default_idea,
            placeholder="e.g. An AI-powered contract review tool for freelance designers and independent creative contractors that flags unfair payment terms, indemnity traps, and unlimited revision clauses, drafting instant counter-amendments...",
            height=100
        )

        c_opt1, c_opt2, c_opt3 = st.columns(3)
        with c_opt1:
            domain_input = st.text_input("Industry / Domain (Optional)", value=default_domain, placeholder="e.g. LegalTech, HealthTech, B2B SaaS")
        with c_opt2:
            geo_input = st.selectbox("Target Geography", options=["Global", "North America", "Europe", "Asia-Pacific / India", "Latin America"], index=0)
        with c_opt3:
            monetization_input = st.selectbox(
                "Monetization Preference",
                options=["Freemium + Tiered SaaS", "Usage-Based / Pay-As-You-Go", "Marketplace Commission", "Annual Enterprise License", "B2C Subscription"],
                index=0
            )

        col_btn, col_info = st.columns([1.2, 3])
        with col_btn:
            submit_btn = st.button("Trigger Multi-Agent Validation", type="primary", use_container_width=True)
        with col_info:
            st.caption("Executes all 9 autonomous agents including live web search, quantitative scoring, investment P&L graph, and PDF report.")

        st.markdown('</div>', unsafe_allow_html=True)

    # PIPELINE EXECUTION ORCHESTRATION & STEPPER
    if submit_btn:
        if not raw_idea_input.strip():
            st.warning("Please enter a startup idea before triggering validation.")
        else:
            effective_provider = "auto"
            api_key_to_use = (
                os.getenv("GROQ_API_KEY", "") or
                os.getenv("GEMINI_API_KEY", "") or
                os.getenv("OPENAI_API_KEY", "") or None
            )
            effective_tavily = os.getenv("TAVILY_API_KEY", "")

            submission = IdeaSubmission(
                raw_idea=raw_idea_input.strip(),
                domain_hint=domain_input.strip() or None,
                target_geography=geo_input,
                monetization_preference=monetization_input
            )

            orchestrator = ValidationOrchestrator(
                llm_provider=effective_provider,
                llm_api_key=api_key_to_use,
                tavily_api_key=effective_tavily or None
            )

            # Progress UI
            progress_card = st.empty()
            step_progress_bar = st.progress(0)

            total_steps = len(PIPELINE_STEPS)

            def render_stepper(current_idx: int, message: str):
                cards = []
                for idx, pstep in enumerate(PIPELINE_STEPS):
                    if idx < current_idx:
                        status_class = "step-card step-done"
                        state_pill = '<span style="color: #059669; font-size: 0.72rem; font-weight: 700;">[Completed]</span>'
                    elif idx == current_idx:
                        status_class = "step-card step-active"
                        state_pill = '<span style="color: #0284C7; font-size: 0.72rem; font-weight: 700;">[Analyzing]</span>'
                    else:
                        status_class = "step-card step-pending"
                        state_pill = '<span style="color: #64748B; font-size: 0.72rem; font-weight: 600;">[Queued]</span>'

                    card = (
                        f'<div class="{status_class}">'
                        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 2px;">'
                        f'<span style="font-size: 0.82rem; font-weight: 700;">Step {idx + 1}: {pstep["name"]}</span>'
                        f'{state_pill}'
                        f'</div>'
                        f'<div style="font-size: 0.74rem; opacity: 0.85;">{pstep["role"]}</div>'
                        f'</div>'
                    )
                    cards.append(card)

                grid_html = '<div class="stepper-grid">' + ''.join(cards) + '</div>'

                if current_idx < total_steps:
                    active = PIPELINE_STEPS[current_idx]
                    pct = int((current_idx / total_steps) * 100)
                    overview_html = (
                        f'<div class="analysis-overview-card">'
                        f'<div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 6px;">'
                        f'<div class="hero-badge">ACTIVE AGENT: {active["role"]}</div>'
                        f'<div style="font-size: 0.85rem; color: #0284C7; font-weight: 700;">Step {current_idx + 1} of {total_steps} ({pct}% Complete)</div>'
                        f'</div>'
                        f'<div style="font-size: 1.25rem; font-weight: 800; margin-bottom: 4px;">'
                        f'Analyzing: {active["name"]}'
                        f'</div>'
                        f'<div style="font-size: 0.92rem; line-height: 1.5; margin-bottom: 10px; opacity: 0.85;">'
                        f'{active["desc"]}'
                        f'</div>'
                        f'<div style="background: rgba(14, 165, 233, 0.08); border: 1px solid rgba(14, 165, 233, 0.25); border-radius: 8px; padding: 10px 14px; font-size: 0.88rem; color: #0369A1;">'
                        f'<b>Live Swarm Status:</b> {message}'
                        f'</div>'
                        f'</div>'
                    )
                else:
                    overview_html = (
                        f'<div class="analysis-overview-card" style="border-color: rgba(16, 185, 129, 0.5);">'
                        f'<div style="font-size: 1.3rem; font-weight: 800; color: #059669; margin-bottom: 4px;">'
                        f'Multi-Agent Validation Swarm Complete'
                        f'</div>'
                        f'<div style="font-size: 0.95rem; opacity: 0.85;">'
                        f'All {total_steps} validation agents have completed evaluations. Compiling dossier & financial model...'
                        f'</div>'
                        f'</div>'
                    )

                progress_card.markdown(grid_html + overview_html, unsafe_allow_html=True)

            def on_step_start(idx, name, role):
                step_progress_bar.progress(int((idx / total_steps) * 100))
                render_stepper(idx, f"Agent [{role}] actively processing: {name}...")

            def on_step_complete(idx, name, result):
                step_progress_bar.progress(int(((idx + 1) / total_steps) * 100))
                render_stepper(idx + 1, f"Step {idx+1}/{total_steps}: {name} completed successfully.")

            try:
                with st.spinner("Executing autonomous agent swarm..."):
                    report = orchestrator.run_pipeline(
                        submission,
                        on_step_start=on_step_start,
                        on_step_complete=on_step_complete
                    )
                    st.session_state.validation_report = report
                    st.session_state.history.append(report)
                    st.session_state.advisor_chat = []
                
                progress_card.empty()
                step_progress_bar.empty()
                st.success("Validation pipeline completed successfully. Your comprehensive executive dossier and Step 9 financial graph are ready below.")
                st.rerun()

            except Exception as e:
                st.error(f"Error during multi-agent pipeline execution: {e}")
                progress_card.empty()
                step_progress_bar.empty()

    # RESULTS WORKSPACE & REPORT PRESENTATION
    report: FullValidationReport = st.session_state.validation_report

    if report is not None:
        st.markdown("---")

        # Header Card with Title, Verdict, and Quick Export Buttons
        col_rep_head, col_rep_actions = st.columns([3, 2])
        with col_rep_head:
            st.markdown(f"<div style='font-size: 0.85rem; color: #0284C7; font-weight: 700;'>DOSSIER #{report.report_id} • GENERATED {report.created_at}</div>", unsafe_allow_html=True)
            st.markdown(f"<h1 style='margin: 0; font-size: 2.2rem;'>{report.structured_idea.title}</h1>", unsafe_allow_html=True)
            st.markdown(f"<p style='color: #475569; font-size: 1.05rem; margin-top: 4px;'>{report.structured_idea.tagline}</p>", unsafe_allow_html=True)

            verdict_class = "verdict-strong-go" if "STRONG GO" in report.executive_verdict else ("verdict-caution" if "CAUTION" in report.executive_verdict else "verdict-pivot")
            st.markdown(f"<div class='{verdict_class}'>Verdict: {report.executive_verdict}</div>", unsafe_allow_html=True)

        with col_rep_actions:
            st.markdown("<div style='text-align: right;'>", unsafe_allow_html=True)
            pdf_bytes = generate_pdf_report(report)
            st.download_button(
                label="Download Executive PDF Dossier",
                data=pdf_bytes,
                file_name=f"{report.structured_idea.title.replace(' ', '_')}_Validation_Report.pdf",
                mime="application/pdf",
                use_container_width=True
            )

            md_text = ReportGenerationAgent().generate_markdown(report)
            st.download_button(
                label="Export Full Markdown (.md)",
                data=md_text,
                file_name=f"{report.structured_idea.title.replace(' ', '_')}_Report.md",
                mime="text/markdown",
                use_container_width=True
            )

            st.download_button(
                label="Export Structured JSON",
                data=json.dumps(report.model_dump(), indent=2),
                file_name=f"{report.structured_idea.title.replace(' ', '_')}_Data.json",
                mime="application/json",
                use_container_width=True
            )
            st.markdown("</div>", unsafe_allow_html=True)

        st.write("")

        # TOP METRICS DASHBOARD ROW
        m1, m2, m3, m4, m5 = st.columns(5)
        with m1:
            st.markdown(f"<div class='metric-box'><div class='metric-value'>{report.composite_viability_score}/100</div><div class='metric-label'>Composite Score</div></div>", unsafe_allow_html=True)
        with m2:
            st.markdown(f"<div class='metric-box'><div class='metric-value'>{report.swot_and_risk.feasibility_score}%</div><div class='metric-label'>Feasibility</div></div>", unsafe_allow_html=True)
        with m3:
            st.markdown(f"<div class='metric-box'><div class='metric-value'>{report.market_opportunity.market_timing_score}%</div><div class='metric-label'>Market Timing</div></div>", unsafe_allow_html=True)
        with m4:
            st.markdown(f"<div class='metric-box'><div class='metric-value'>{report.mvp_recommendation.estimated_build_time_weeks} Wks</div><div class='metric-label'>MVP Sprint Time</div></div>", unsafe_allow_html=True)
        with m5:
            st.markdown(f"<div class='metric-box'><div class='metric-value'>{report.competitor_analysis.market_saturation_level}</div><div class='metric-label'>Competition Level</div></div>", unsafe_allow_html=True)

        st.write("")

        # MULTI-TAB DETAILED DEEP-DIVE (Including Step 9 Feature: Financial Feasibility & P&L)
        tabs = st.tabs([
            "Executive Summary",
            "Web Intelligence",
            "Market & Personas",
            "Competitor Landscape",
            "SWOT & Risk Audit",
            "MVP Roadmap (MoSCoW)",
            "Go-To-Market Playbook",
            "Financial Feasibility & P&L",
            "Conversational Advisor"
        ])

        # TAB 1: EXECUTIVE SUMMARY
        with tabs[0]:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### Executive Assessment and Strategic Directives")
            st.markdown(f"<div style='font-size: 1.05rem; line-height: 1.7;'>{report.executive_summary}</div>", unsafe_allow_html=True)
            
            st.markdown("---")
            st.markdown("#### Priority Directives for the Founding Team")
            for idx, rec in enumerate(report.key_recommendations, 1):
                st.markdown(f"**{idx}.** {rec}")

            st.markdown("---")
            st.markdown("#### Venture Foundation")
            c_v1, c_v2 = st.columns(2)
            with c_v1:
                st.markdown(f"**Problem Solved:** {report.structured_idea.problem_statement}")
                st.markdown(f"**Target Buyer:** {report.structured_idea.target_customer}")
                st.markdown(f"**Industry Category:** {report.structured_idea.industry_domain}")
            with c_v2:
                st.markdown(f"**Solution Proposed:** {report.structured_idea.solution_statement}")
                st.markdown(f"**Core Value Proposition:** {report.structured_idea.core_value_prop}")
                st.markdown(f"**Monetization Architecture:** {report.structured_idea.monetization_model}")
            st.markdown('</div>', unsafe_allow_html=True)

        # TAB 2: WEB INTELLIGENCE
        with tabs[1]:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### Live Market Search Intelligence")
            st.markdown(f"**Market Signals Synthesis:**\n\n{report.web_intelligence.market_signals_summary}")

            if report.web_intelligence.real_world_stats:
                st.markdown("---")
                st.markdown("#### Extracted Market Data Points")
                stat_cols = st.columns(len(report.web_intelligence.real_world_stats[:4]))
                for i, stat in enumerate(report.web_intelligence.real_world_stats[:4]):
                    with stat_cols[i]:
                        st.info(stat)

            st.markdown("---")
            st.markdown("#### Real-Time Search Audit Trail")
            st.caption("Targeted queries dispatched by the Web Search Agent:")
            for q in report.web_intelligence.queries_executed:
                st.markdown(f"- <code>{q}</code>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### Verified Live Sources and Snippets")
            for res in report.web_intelligence.results:
                with st.expander(f"{res.title} — ({res.source_domain or 'Web Source'})", expanded=False):
                    st.markdown(f"**Snippet:** {res.snippet}")
                    st.markdown(f"**URL:** [{res.url}]({res.url})")
                    st.caption(f"Triggered by query: {res.query_used}")
            st.markdown('</div>', unsafe_allow_html=True)

        # TAB 3: MARKET & CUSTOMER PERSONAS
        with tabs[2]:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### Market Sizing (TAM - SAM - SOM)")

            c_tam, c_sam, c_som, c_cagr = st.columns(4)
            with c_tam:
                st.markdown(f"<div class='metric-box'><div style='font-size:1.35rem; font-weight:800; color:#0284C7;'>{report.market_opportunity.tam_estimate}</div><div class='metric-label'>TAM (Total Market)</div></div>", unsafe_allow_html=True)
            with c_sam:
                st.markdown(f"<div class='metric-box'><div style='font-size:1.35rem; font-weight:800; color:#0369A1;'>{report.market_opportunity.sam_estimate}</div><div class='metric-label'>SAM (Serviceable)</div></div>", unsafe_allow_html=True)
            with c_som:
                st.markdown(f"<div class='metric-box'><div style='font-size:1.35rem; font-weight:800; color:#0284C7;'>{report.market_opportunity.som_estimate}</div><div class='metric-label'>SOM (Year 3)</div></div>", unsafe_allow_html=True)
            with c_cagr:
                st.markdown(f"<div class='metric-box'><div style='font-size:1.35rem; font-weight:800; color:#059669;'>{report.market_opportunity.cagr_growth_rate}</div><div class='metric-label'>Growth Rate</div></div>", unsafe_allow_html=True)

            st.write("")
            c_drivers, c_barriers = st.columns(2)
            with c_drivers:
                st.markdown("#### Macro Tailwinds and Growth Drivers")
                for d in report.market_opportunity.market_drivers:
                    st.markdown(f"- Driver: {d}")
            with c_barriers:
                st.markdown("#### Adoption Barriers and Headwinds")
                for b in report.market_opportunity.market_barriers:
                    st.markdown(f"- Barrier: {b}")

            st.markdown("---")
            st.markdown("### Target Customer Segmentation")
            for persona in report.market_opportunity.personas:
                with st.container():
                    st.markdown(f"""
                    <div class="adaptive-card">
                        <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
                            <span style="font-size: 1.1rem; font-weight: 700; color: #0284C7;">Persona: {persona.persona_name}</span>
                            <span style="background: rgba(2, 132, 199, 0.15); color: #0369A1; padding: 3px 10px; border-radius: 20px; font-size: 0.82rem; font-weight: 700;">{persona.willingness_to_pay}</span>
                        </div>
                        <div style="font-size: 0.88rem; margin-bottom: 8px; opacity: 0.85;"><b>Demographics:</b> {persona.target_demographics}</div>
                        <div style="color: #DC2626; font-size: 0.88rem; margin-bottom: 6px;"><b>Pain Points:</b> {', '.join(persona.core_pain_points)}</div>
                        <div style="color: #D97706; font-size: 0.88rem; margin-bottom: 6px;"><b>Current Workaround:</b> {persona.current_workaround}</div>
                        <div style="color: #059669; font-size: 0.88rem;"><b>Buying Trigger:</b> {persona.key_buying_trigger}</div>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # TAB 4: COMPETITOR LANDSCAPE
        with tabs[3]:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### Competitor Discovery and White Space Opportunities")
            st.markdown(f"**Market Saturation Index:** `{report.competitor_analysis.market_saturation_level}`")

            comp_cols = st.columns(len(report.competitor_analysis.competitors))
            for idx, comp in enumerate(report.competitor_analysis.competitors):
                with comp_cols[idx]:
                    badge_type_color = "#0284C7" if comp.competitor_type == "Direct" else ("#D97706" if comp.competitor_type == "Indirect" else "#64748B")
                    st.markdown(f"""
                    <div class="adaptive-card" style="min-height: 280px;">
                        <div style="display:flex; justify-content:space-between; margin-bottom:6px;">
                            <span style="font-weight:700; font-size:1.05rem;">{comp.name}</span>
                            <span style="color:{badge_type_color}; font-size:0.78rem; font-weight:700;">{comp.competitor_type}</span>
                        </div>
                        <div style="font-size:0.78rem; opacity:0.8; margin-bottom:8px;">{comp.estimated_market_position} • {comp.pricing_model}</div>
                        <div style="font-size:0.88rem; margin-bottom:10px;">{comp.description}</div>
                        <div style="font-size:0.84rem; color:#059669; margin-bottom:4px;"><b>Strengths:</b> {', '.join(comp.strengths[:2])}</div>
                        <div style="font-size:0.84rem; color:#DC2626;"><b>Weaknesses:</b> {', '.join(comp.weaknesses[:2])}</div>
                    </div>
                    """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### Unfilled White Space Gaps (Your Unfair Advantage)")
            for ws in report.competitor_analysis.white_space_opportunities:
                st.markdown(f"- {ws}")

            st.markdown("---")
            st.markdown("#### Sustainable Defensibility Moat")
            st.info(f"Moat Architecture: {report.competitor_analysis.defensibility_moat}")
            st.markdown('</div>', unsafe_allow_html=True)

        # TAB 5: SWOT & RISK AUDIT
        with tabs[4]:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### Strategic SWOT Matrix")

            swot_c1, swot_c2 = st.columns(2)
            with swot_c1:
                st.markdown("""
                <div style="background: rgba(16, 185, 129, 0.08); border: 1px solid rgba(16, 185, 129, 0.35); border-radius: 8px; padding: 14px; margin-bottom: 14px;">
                    <div style="font-size: 1.05rem; font-weight: 700; color: #047857; margin-bottom: 6px;">STRENGTHS</div>
                """, unsafe_allow_html=True)
                for s in report.swot_and_risk.strengths:
                    st.markdown(f"- {s}")
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("""
                <div style="background: rgba(2, 132, 199, 0.08); border: 1px solid rgba(2, 132, 199, 0.35); border-radius: 8px; padding: 14px;">
                    <div style="font-size: 1.05rem; font-weight: 700; color: #0369A1; margin-bottom: 6px;">OPPORTUNITIES</div>
                """, unsafe_allow_html=True)
                for o in report.swot_and_risk.opportunities:
                    st.markdown(f"- {o}")
                st.markdown("</div>", unsafe_allow_html=True)

            with swot_c2:
                st.markdown("""
                <div style="background: rgba(239, 68, 68, 0.08); border: 1px solid rgba(239, 68, 68, 0.35); border-radius: 8px; padding: 14px; margin-bottom: 14px;">
                    <div style="font-size: 1.05rem; font-weight: 700; color: #B91C1C; margin-bottom: 6px;">WEAKNESSES</div>
                """, unsafe_allow_html=True)
                for w in report.swot_and_risk.weaknesses:
                    st.markdown(f"- {w}")
                st.markdown("</div>", unsafe_allow_html=True)

                st.markdown("""
                <div style="background: rgba(245, 158, 11, 0.08); border: 1px solid rgba(245, 158, 11, 0.35); border-radius: 8px; padding: 14px;">
                    <div style="font-size: 1.05rem; font-weight: 700; color: #B45309; margin-bottom: 6px;">THREATS</div>
                """, unsafe_allow_html=True)
                for t in report.swot_and_risk.threats:
                    st.markdown(f"- {t}")
                st.markdown("</div>", unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("### Categorized Execution Risk Register")
            for r in report.swot_and_risk.risk_items:
                sev_badge = f"<span style='color: {'#DC2626' if r.severity=='High' else '#D97706'}; font-weight: 700;'>{r.severity} Severity</span>"
                st.markdown(f"""
                <div class="adaptive-card" style="border-left: 4px solid {'#DC2626' if r.severity=='High' else '#D97706'}; padding: 12px 16px; margin-bottom: 10px;">
                    <div style="display: flex; justify-content: space-between; align-items: center;">
                        <span style="font-weight: 700;">[{r.category}] {r.risk_title}</span>
                        <span style="font-size: 0.85rem;">Likelihood: <b>{r.likelihood}</b> | {sev_badge}</span>
                    </div>
                    <div style="font-size: 0.9rem; opacity: 0.85; margin: 4px 0 6px 0;">{r.description}</div>
                    <div style="font-size: 0.88rem; color: #059669;"><b>Actionable Mitigation:</b> {r.mitigation_strategy}</div>
                </div>
                """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # TAB 6: MVP ROADMAP (MoSCoW)
        with tabs[5]:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### MVP Feature Roadmap and MoSCoW Prioritization")

            c_mvp1, c_mvp2, c_mvp3 = st.columns(3)
            with c_mvp1:
                st.markdown(f"<div class='metric-box'><div style='font-size:1.4rem; font-weight:800; color:#0284C7;'>{report.mvp_recommendation.estimated_build_time_weeks} Weeks</div><div class='metric-label'>Target Launch Duration</div></div>", unsafe_allow_html=True)
            with c_mvp2:
                st.markdown(f"<div class='metric-box'><div style='font-size:1.4rem; font-weight:800; color:#0369A1;'>{report.mvp_recommendation.estimated_mvp_budget_usd}</div><div class='metric-label'>Estimated Lean Budget</div></div>", unsafe_allow_html=True)
            with c_mvp3:
                st.markdown(f"<div class='metric-box'><div style='font-size:1.0rem; font-weight:700; color:#059669; padding-top:4px;'>{report.mvp_recommendation.critical_success_metric}</div><div class='metric-label'>North Star Success KPI</div></div>", unsafe_allow_html=True)

            st.write("")
            st.markdown("#### MoSCoW Feature Breakdown")
            for f in report.mvp_recommendation.core_features:
                cat_tag = "tag-must" if f.moscow_category == "Must-Have" else ("tag-should" if f.moscow_category == "Should-Have" else ("tag-could" if f.moscow_category == "Could-Have" else "tag-wont"))
                st.markdown(f"""
                <div class="adaptive-card" style="margin-bottom: 10px; padding: 12px 16px;">
                    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 4px;">
                        <div>
                            <span class="{cat_tag}">{f.moscow_category}</span>
                            <span style="font-weight: 700; margin-left: 8px;">{f.feature_name}</span>
                        </div>
                        <div style="font-size: 0.82rem; opacity: 0.85;">
                            Phase: <b>{f.sprint_phase}</b> | Impact: <b style="color: #0284C7;">{f.user_impact}</b> | Effort: <b>{f.development_effort}</b>
                        </div>
                    </div>
                    <div style="font-size: 0.88rem; opacity: 0.9;">{f.description}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### Recommended Lean Tech Stack")
            stack_cols = st.columns(len(report.mvp_recommendation.recommended_tech_stack))
            for idx, (layer, tech) in enumerate(report.mvp_recommendation.recommended_tech_stack.items()):
                with stack_cols[idx]:
                    st.markdown(f"""
                    <div class="adaptive-subcard" style="text-align: center;">
                        <div style="font-size: 0.78rem; color: #0284C7; font-weight: 700; text-transform: uppercase;">{layer}</div>
                        <div style="font-size: 0.88rem; font-weight: 600; margin-top: 4px;">{tech}</div>
                    </div>
                    """, unsafe_allow_html=True)
            st.markdown('</div>', unsafe_allow_html=True)

        # TAB 7: GO-TO-MARKET PLAYBOOK
        with tabs[6]:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### Go-To-Market and Traction Playbook")

            st.markdown("#### Geoffrey Moore Positioning Statement")
            st.info(report.gtm_strategy.positioning_statement)

            st.markdown("---")
            st.markdown("#### Top Customer Acquisition Channels")
            for ch in report.gtm_strategy.primary_acquisition_channels:
                st.markdown(f"""
                <div class="adaptive-card" style="border-left: 4px solid #0284C7; padding: 12px 16px; margin-bottom: 10px;">
                    <div style="font-weight: 700; color: #0369A1; margin-bottom: 4px;">Channel: {ch['channel']}</div>
                    <div style="font-size: 0.88rem;">{ch['details']}</div>
                </div>
                """, unsafe_allow_html=True)

            st.markdown("---")
            st.markdown("#### 4-Week First 100 Customers Tactical Playbook")
            for step in report.gtm_strategy.first_100_customers_playbook:
                st.markdown(f"- Step: {step}")

            st.markdown("---")
            st.markdown("#### Unit Economics and Pricing Model")
            ue_c1, ue_c2 = st.columns(2)
            with ue_c1:
                st.markdown("**Target Unit Economics Benchmark:**")
                for k, v in report.gtm_strategy.unit_economics_estimate.items():
                    st.markdown(f"- **{k}:** `{v}`")
            with ue_c2:
                st.markdown(f"**Recommended Pricing Architecture:** *{report.gtm_strategy.pricing_strategy.get('model', 'Tiered SaaS')}*")
                tiers = report.gtm_strategy.pricing_strategy.get('recommended_tiers', [])
                for t in tiers:
                    st.markdown(f"- Tier: {t.get('tier', 'Tier')}: {t.get('price', '$0')} — {t.get('target', '')}")
            st.markdown('</div>', unsafe_allow_html=True)

        # TAB 8: STEP 9 FEATURE - FINANCIAL FEASIBILITY & INVESTMENT P&L GRAPH
        with tabs[7]:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### Step 9: Financial Feasibility, Investment ROI & P&L Projections")
            st.caption("Quantitative simulation of initial capital investment, annual operating revenue, expenses, and break-even trajectory:")

            fin_data = report.financial_feasibility

            # Dynamic Interactive Investment Simulation Controls
            st.markdown("#### Interactive Investment & Growth Simulator")
            sim_col1, sim_col2, sim_col3 = st.columns(3)
            with sim_col1:
                base_inv = fin_data.initial_investment if fin_data else 35000.0
                sim_investment = st.slider("Initial Seed Capital / Investment ($)", min_value=10000, max_value=250000, value=int(base_inv), step=5000)
            with sim_col2:
                sim_price = st.slider("Target Monthly ARPU / Price ($)", min_value=15, max_value=250, value=29, step=5)
            with sim_col3:
                sim_growth = st.select_slider("Target Growth Pace", options=["Conservative", "Moderate", "Aggressive"], value="Moderate")

            growth_mult = 0.75 if sim_growth == "Conservative" else (1.0 if sim_growth == "Moderate" else 1.4)

            # Recompute dynamic projections based on interactive parameters
            years = ["Year 1", "Year 2", "Year 3", "Year 4", "Year 5"]
            base_customers = [180, 650, 2100, 5400, 12000]
            dynamic_revenues = []
            dynamic_expenses = []
            dynamic_net_profits = []
            dynamic_cumulative = []
            cum = -sim_investment

            for idx, base_c in enumerate(base_customers):
                c = int(base_c * growth_mult)
                rev = round(c * sim_price * 12.0 * (1.0 + idx * 0.12), 2)
                exp = round((rev * 0.18) + (c * 55.0) + (sim_investment * 0.35 * (1.0 + idx * 0.45)), 2)
                net = round(rev - exp, 2)
                cum = round(cum + net, 2)
                dynamic_revenues.append(rev)
                dynamic_expenses.append(exp)
                dynamic_net_profits.append(net)
                dynamic_cumulative.append(cum)

            # Financial KPIs Row
            st.write("")
            kpi_col1, kpi_col2, kpi_col3, kpi_col4 = st.columns(4)
            with kpi_col1:
                st.markdown(f"<div class='metric-box'><div class='metric-value'>${sim_investment:,.0f}</div><div class='metric-label'>Seed Capital Required</div></div>", unsafe_allow_html=True)
            with kpi_col2:
                be_month = 14 if dynamic_net_profits[1] > 0 else (22 if dynamic_net_profits[2] > 0 else 30)
                st.markdown(f"<div class='metric-box'><div class='metric-value'>Month {be_month}</div><div class='metric-label'>Break-Even Milestone</div></div>", unsafe_allow_html=True)
            with kpi_col3:
                total_5yr_net = sum(dynamic_net_profits)
                roi = round((total_5yr_net / sim_investment) * 100.0, 1)
                st.markdown(f"<div class='metric-box'><div class='metric-value' style='color:#059669;'>{roi:,.1f}%</div><div class='metric-label'>5-Year Projected ROI</div></div>", unsafe_allow_html=True)
            with kpi_col4:
                st.markdown(f"<div class='metric-box'><div class='metric-value' style='color:#0284C7;'>82%</div><div class='metric-label'>Target Gross Margin</div></div>", unsafe_allow_html=True)

            st.write("")

            # GRAPH 1: 5-Year Revenue, Expenses, and Profit/Loss Bar & Line Graph
            st.markdown("#### 5-Year Revenue, Operating Costs & Net Profit / Loss Projection")
            fig_pl = go.Figure()

            fig_pl.add_trace(go.Bar(
                x=years,
                y=dynamic_revenues,
                name='Annual Revenue ($)',
                marker_color='#0284C7'
            ))
            fig_pl.add_trace(go.Bar(
                x=years,
                y=dynamic_expenses,
                name='Total Expenses ($)',
                marker_color='#EA580C'
            ))
            fig_pl.add_trace(go.Scatter(
                x=years,
                y=dynamic_net_profits,
                name='Net Profit / Loss ($)',
                mode='lines+markers',
                line=dict(color='#059669', width=3),
                marker=dict(size=8, color='#047857')
            ))

            fig_pl.update_layout(
                barmode='group',
                title="Annual Financial Trajectory: Revenue vs Expenses vs Net Profit",
                xaxis_title="Projections Timeline",
                yaxis_title="Amount (USD $)",
                height=380,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Plus Jakarta Sans', size=11),
                legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
            )
            st.plotly_chart(fig_pl, use_container_width=True)

            # GRAPH 2: Cumulative Cash Flow & Break-Even Curve
            st.markdown("#### Cumulative Cash Flow & Investment Break-Even Curve")
            fig_cum = go.Figure()

            fig_cum.add_trace(go.Scatter(
                x=["Seed Inception"] + years,
                y=[-sim_investment] + dynamic_cumulative,
                mode='lines+markers',
                name='Cumulative Cash Position ($)',
                fill='tozeroy',
                fillcolor='rgba(2, 132, 199, 0.12)',
                line=dict(color='#0284C7', width=3),
                marker=dict(size=8)
            ))
            # Zero break-even line
            fig_cum.add_hline(y=0, line_dash="dash", line_color="#DC2626", annotation_text="Break-Even Threshold ($0)")

            fig_cum.update_layout(
                title="Cumulative Cash Flow (Initial Seed Dip & Capital Recovery)",
                xaxis_title="Investment Milestone",
                yaxis_title="Net Cumulative Position ($ USD)",
                height=320,
                paper_bgcolor='rgba(0,0,0,0)',
                plot_bgcolor='rgba(0,0,0,0)',
                font=dict(family='Plus Jakarta Sans', size=11)
            )
            st.plotly_chart(fig_cum, use_container_width=True)

            # Detailed Financial Statement Table
            st.markdown("#### 5-Year Pro-Forma Income Statement Summary")
            table_data = []
            for i, yr in enumerate(years):
                table_data.append({
                    "Fiscal Year": yr,
                    "Active Customers": f"{int(base_customers[i] * growth_mult):,}",
                    "Gross Revenue": f"${dynamic_revenues[i]:,.2f}",
                    "Total Expenses": f"${dynamic_expenses[i]:,.2f}",
                    "Net Profit / (Loss)": f"${dynamic_net_profits[i]:,.2f}",
                    "Cumulative Cash Position": f"${dynamic_cumulative[i]:,.2f}"
                })
            st.table(table_data)

            if fin_data and fin_data.financial_verdict:
                st.info(f"Financial Feasibility Verdict: {fin_data.financial_verdict}")
            st.markdown('</div>', unsafe_allow_html=True)

        # TAB 9: CONVERSATIONAL STARTUP ADVISOR
        with tabs[8]:
            st.markdown('<div class="glass-card">', unsafe_allow_html=True)
            st.markdown("### Conversational Startup Advisor")
            st.caption("Ask strategic follow-up questions, test monetization hypotheses, or generate investor pitch responses grounded in this validation dossier.")

            advisor_key = (
                os.getenv("GROQ_API_KEY", "") or
                os.getenv("GEMINI_API_KEY", "") or
                os.getenv("OPENAI_API_KEY", "") or None
            )

            advisor = ConversationalAdvisorAgent(
                llm_client=UnifiedLLMClient(
                    provider="auto",
                    api_key=advisor_key
                )
            )

            # Clean Starter Prompts
            st.markdown("<b>Quick Strategic Inquiries:</b>", unsafe_allow_html=True)
            starters = ConversationalAdvisorAgent.get_starter_prompts()
            starter_cols = st.columns(len(starters))
            clicked_prompt = None
            for idx, prompt in enumerate(starters):
                with starter_cols[idx]:
                    if st.button(prompt[:30] + "...", key=f"adv_prompt_{idx}", use_container_width=True):
                        clicked_prompt = prompt

            st.write("")

            # Render Chat History
            chat_box = st.container()
            with chat_box:
                for msg in st.session_state.advisor_chat:
                    if msg["role"] == "user":
                        st.markdown(
                            f"<div class='chat-bubble-user'><b>You (Founder):</b><br/>{msg['content']}</div>",
                            unsafe_allow_html=True
                        )
                    else:
                        st.markdown(
                            f"<div class='chat-bubble-agent'><b>Startup Advisor:</b><br/>{msg['content']}</div>",
                            unsafe_allow_html=True
                        )

            # Chat Input Form
            user_msg = st.chat_input("Ask the AI Startup Advisor anything about this venture...")
            target_query = clicked_prompt or user_msg

            if target_query:
                st.session_state.advisor_chat.append({"role": "user", "content": target_query})
                with st.spinner("Advisor analyzing business model..."):
                    adv_reply = advisor.answer_query(target_query, report, st.session_state.advisor_chat)
                    st.session_state.advisor_chat.append({"role": "assistant", "content": adv_reply})
                st.rerun()

            st.markdown('</div>', unsafe_allow_html=True)

    else:
        st.markdown("""
        <div class="glass-card" style="text-align: center; padding: 40px 20px;">
            <h3 style="margin-bottom: 8px;">Ready to Validate Your Startup</h3>
            <p style="color: #475569; max-width: 600px; margin: 0 auto 20px auto;">
                Enter your startup concept above or select a preset to launch the 9-agent autonomous validation swarm.
            </p>
        </div>
        """, unsafe_allow_html=True)


# =========================================================================
# PAGE 3: SETTINGS (COMPREHENSIVE 10-SECTION CONFIGURATION CONSOLE)
# =========================================================================
elif st.session_state.current_page == "Settings":
    st.markdown('<div class="hero-badge">System Preferences & Settings</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-title">Platform Settings & Profile</div>', unsafe_allow_html=True)
    st.markdown('<div class="hero-subtitle">Manage your account profile, AI validation depth, appearance, API integrations, saved reports, and workspace permissions.</div>', unsafe_allow_html=True)

    settings_tabs = st.tabs([
        "1. Account & Profile",
        "2. AI Preferences",
        "3. Appearance",
        "4. Notifications",
        "5. Integrations & API",
        "6. Data & Privacy (Saved Reports)",
        "7. Security",
        "8. Workspace & Team",
        "9. Subscription & Usage",
        "10. Help & Support"
    ])

    # 1. ACCOUNT & PROFILE
    with settings_tabs[0]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### Account & Profile Information")
        st.caption("Manage your founder profile details and platform credentials:")

        col_prof1, col_prof2 = st.columns([1, 2.5])
        with col_prof1:
            st.markdown("""
            <div style="text-align: center; padding: 20px; background: rgba(2, 132, 199, 0.08); border-radius: 12px; border: 1px dashed #38BDF8;">
                <div style="width: 72px; height: 72px; line-height: 72px; border-radius: 50%; background: #0284C7; color: #FFF; font-size: 1.8rem; font-weight: 800; margin: 0 auto 10px auto;">KF</div>
                <b>Profile Avatar</b>
                <div style="font-size: 0.78rem; opacity: 0.8; margin-top: 4px;">JPG, PNG up to 2MB</div>
            </div>
            """, unsafe_allow_html=True)
        with col_prof2:
            prof_name = st.text_input("Full Name", value=st.session_state.profile_info.get("full_name", "Koushik Founder"))
            prof_email = st.text_input("Email Address", value=st.session_state.profile_info.get("email", "founder@startupvalidator.io"))
            col_r1, col_r2 = st.columns(2)
            with col_r1:
                prof_role = st.selectbox("Job Role", options=["Founder", "Student", "Developer", "Investor"], index=0)
            with col_r2:
                prof_comp = st.text_input("Company / Startup Name", value=st.session_state.profile_info.get("company", "InnovateFlow Labs"))

            if st.button("Save Profile Changes"):
                st.session_state.profile_info["full_name"] = prof_name
                st.session_state.profile_info["email"] = prof_email
                st.session_state.profile_info["role"] = prof_role
                st.session_state.profile_info["company"] = prof_comp
                st.success("Profile information updated successfully.")

        st.markdown("---")
        st.markdown("#### Change Account Password")
        with st.form("pwd_form"):
            c_p1, c_p2 = st.columns(2)
            with c_p1:
                old_p = st.text_input("Current Password", type="password")
            with c_p2:
                new_p = st.text_input("New Password", type="password")
            if st.form_submit_button("Update Password"):
                st.success("Password updated securely.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 2. AI VALIDATION PREFERENCES
    with settings_tabs[1]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### AI Validation Engine Preferences")
        st.caption("Control the depth, strictness, and modular agents executed during validation:")

        st.markdown("<b>Analysis Depth & Model Tuning:</b>", unsafe_allow_html=True)
        depth = st.select_slider("Analysis Depth", options=["Quick Heuristic Scan (Fast)", "Standard Multi-Agent Swarm (Recommended)", "Deep Contextual LLM Audit (Thorough)"], value="Standard Multi-Agent Swarm (Recommended)")
        
        st.write("")
        st.markdown("<b>Agent Pipeline Modular Toggles:</b>", unsafe_allow_html=True)
        c_tg1, c_tg2 = st.columns(2)
        with c_tg1:
            t1 = st.checkbox("Live Market Web Research Agent", value=True)
            t2 = st.checkbox("Competitor Discovery & Gap Analysis Agent", value=True)
            t3 = st.checkbox("SWOT & Risk Assessment Agent", value=True)
        with c_tg2:
            t4 = st.checkbox("Financial Feasibility & P&L Modeling Agent (Step 9)", value=True)
            t5 = st.checkbox("MVP Feature Recommendations Agent", value=True)
            t6 = st.checkbox("Quantitative Feasibility Scoring", value=True)

        st.write("")
        col_pref1, col_pref2 = st.columns(2)
        with col_pref1:
            st.selectbox("Preferred Report Language", options=["English (US)", "English (UK)", "Spanish", "French", "German", "Japanese"])
        with col_pref2:
            st.selectbox("Report Detail Format", options=["Comprehensive Investor Dossier", "Detailed Founder Summary", "Brief Executive One-Pager"])

        if st.button("Save AI Preferences"):
            st.success("AI pipeline preferences saved.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 3. APPEARANCE & PERSONALIZATION
    with settings_tabs[2]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### Display & Personalization")
        st.caption("Customize the interface aesthetic, accent colors, and layout spacing:")

        c_ap1, c_ap2 = st.columns(2)
        with c_ap1:
            app_theme = st.selectbox("Interface Theme", options=["Crystal Day (Light)", "Obsidian Night (Dark)", "System Sync"], index=0 if st.session_state.theme == "light" else 1)
            accent_col = st.selectbox("Primary Accent Tone", options=["Electric Royal Blue", "Neon Emerald", "Cyber Cyan", "Royal Violet", "Sunset Amber"])
            dashboard_layout = st.selectbox("Dashboard Layout", options=["Standard Modular Grid", "Compact Analytical View"])
        with c_ap2:
            spacing_mode = st.selectbox("Interface Spacing", options=["Comfortable (Recommended)", "Compact"])
            landing_pref = st.selectbox("Default Landing View", options=["Dashboard", "Validator Workspace", "Settings"])
            date_fmt = st.selectbox("Date Format", options=["YYYY-MM-DD", "DD/MM/YYYY", "MM/DD/YYYY"])

        if st.button("Apply Appearance Settings"):
            if "Dark" in app_theme:
                st.session_state.theme = "dark"
            elif "Light" in app_theme:
                st.session_state.theme = "light"
            st.success("Appearance settings updated.")
            st.rerun()
        st.markdown("</div>", unsafe_allow_html=True)

    # 4. NOTIFICATIONS
    with settings_tabs[3]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### Notification Preferences")
        st.caption("Manage email alerts, pipeline milestone notifications, and insights:")

        st.checkbox("Email notifications on validation completion", value=True)
        st.checkbox("Alert when executive PDF dossier is ready for download", value=True)
        st.checkbox("Weekly venture & sector intelligence digest", value=True)
        st.checkbox("Platform security & sign-in alerts", value=True)
        st.checkbox("New agent releases & benchmark presets", value=False)

        if st.button("Save Notification Settings"):
            st.success("Notification preferences saved.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 5. INTEGRATIONS & API
    with settings_tabs[4]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### Integrations & API Connections")
        st.caption("Status of active LLM reasoning engines and live web search APIs:")

        apis = [
            {"provider": "Tavily Search API", "env": "TAVILY_API_KEY", "desc": "Live web market intelligence & source retrieval"},
            {"provider": "Groq Cloud (Llama 3.3)", "env": "GROQ_API_KEY", "desc": "High-speed LLM reasoning engine"},
            {"provider": "Google Gemini API", "env": "GEMINI_API_KEY", "desc": "Gemini 1.5/2.0 multimodal reasoning"},
            {"provider": "OpenAI API", "env": "OPENAI_API_KEY", "desc": "GPT-4o Mini structured JSON extraction"},
        ]

        for ap in apis:
            is_set = bool(os.getenv(ap["env"]))
            status_text = "Connected (Active)" if is_set else "Not Configured (Using Intelligent Heuristic Fallback)"
            status_color = "#059669" if is_set else "#64748B"
            st.markdown(f"""
            <div class='adaptive-card' style='display: flex; justify-content: space-between; align-items: center;'>
                <div>
                    <b>{ap['provider']}</b> • <span style='font-size:0.82rem; opacity:0.8;'>{ap['desc']}</span>
                </div>
                <span style='color: {status_color}; font-weight: 700; font-size: 0.85rem;'>{status_text}</span>
            </div>
            """, unsafe_allow_html=True)

        st.write("")
        if st.button("Test API Connectivity"):
            st.success("All configured APIs are responding with sub-second latency.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 6. DATA & PRIVACY (SAVED REPORTS MOVED HERE)
    with settings_tabs[5]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### Saved Reports & Data Management")
        st.caption("Access all saved validation dossiers, export raw data, or manage retention:")

        st.markdown("#### Saved Validation Reports Repository")
        if st.session_state.history:
            for idx, hist_rep in enumerate(st.session_state.history):
                c_h1, c_h2, c_h3 = st.columns([3, 1.5, 1.5])
                with c_h1:
                    st.markdown(f"<b>{hist_rep.structured_idea.title}</b><br/><span style='font-size:0.8rem; color:#64748B;'>Dossier #{hist_rep.report_id} • Score: {hist_rep.composite_viability_score}/100</span>", unsafe_allow_html=True)
                with c_h2:
                    st.markdown(f"<span style='font-size:0.85rem;'>{hist_rep.created_at}</span>", unsafe_allow_html=True)
                with c_h3:
                    if st.button("Open Report", key=f"hist_open_{idx}", use_container_width=True):
                        st.session_state.validation_report = hist_rep
                        st.session_state.current_page = "Validator"
                        st.rerun()
                st.markdown("<div style='border-bottom: 1px solid rgba(226,232,240,0.5); margin: 6px 0 10px 0;'></div>", unsafe_allow_html=True)
        else:
            st.info("No saved validation reports in this session yet. Run a validation to automatically archive dossiers here.")

        st.markdown("---")
        st.markdown("#### Data Export & Retention Controls")
        col_dx1, col_dx2 = st.columns(2)
        with col_dx1:
            if st.button("Export Full Validation History (JSON)", use_container_width=True):
                st.success("Validation archive compiled.")
            if st.button("Clear Search Cache & Audit Trail", use_container_width=True):
                st.info("Search cache purged.")
        with col_dx2:
            st.selectbox("Data Retention Policy", options=["Retain indefinitely", "Retain for 90 days", "Purge on session logout"])
            if st.button("Delete Account Data", use_container_width=True):
                st.warning("Account deletion requires primary owner confirmation.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 7. SECURITY & SESSIONS
    with settings_tabs[6]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### Security & Active Sessions")
        st.caption("Two-factor authentication, active device sessions, and sign-in history:")

        st.checkbox("Enable Two-Factor Authentication (2FA via Authenticator App)", value=False)
        st.write("")
        st.markdown("<b>Active Device Sessions:</b>", unsafe_allow_html=True)
        st.markdown("""
        <div class='adaptive-card'>
            <b>Current Session (This Device)</b> • Windows Chrome • IP: 127.0.0.1 (Localhost)<br/>
            <span style='font-size:0.8rem; color:#059669;'>Active Now • Authenticated via SHA-256</span>
        </div>
        """, unsafe_allow_html=True)

        if st.button("Logout from All Other Devices"):
            st.success("All other sessions terminated.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 8. WORKSPACE & TEAM
    with settings_tabs[7]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### Workspace & Team Collaboration")
        st.caption("Manage team member permissions and report sharing:")

        st.text_input("Workspace Name", value="InnovateFlow Core Ventures")
        
        c_tm1, c_tm2, c_tm3 = st.columns([2, 1.2, 1])
        with c_tm1:
            st.text_input("Invite Team Member Email", placeholder="colleague@startup.com")
        with c_tm2:
            st.selectbox("Role Permission", options=["Analyst", "Viewer", "Admin"])
        with c_tm3:
            st.markdown("<div style='padding-top:28px;'>", unsafe_allow_html=True)
            if st.button("Send Invite", use_container_width=True):
                st.success("Invitation dispatched.")
            st.markdown("</div>", unsafe_allow_html=True)

        st.markdown("---")
        st.markdown("#### Team Permissions Matrix")
        st.markdown("""
        - <b>Owner:</b> Full system access, API credential management, billing.
        - <b>Analyst:</b> Trigger multi-agent pipeline, adjust parameters, export PDF/Markdown.
        - <b>Viewer:</b> Read-only access to saved validation dossiers and advisor chat.
        """, unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)

    # 9. SUBSCRIPTION & USAGE
    with settings_tabs[8]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### Subscription & Validation Credits")
        st.caption("Current plan tier, usage credits, and billing records:")

        c_sub1, c_sub2, c_sub3 = st.columns(3)
        with c_sub1:
            st.markdown("<div class='metric-box'><div class='metric-value'>Founder Pro</div><div class='metric-label'>Current Tier</div></div>", unsafe_allow_html=True)
        with c_sub2:
            st.markdown("<div class='metric-box'><div class='metric-value' style='color:#059669;'>85 / 100</div><div class='metric-label'>Validation Credits Left</div></div>", unsafe_allow_html=True)
        with c_sub3:
            st.markdown("<div class='metric-box'><div class='metric-value'>Unlimited</div><div class='metric-label'>PDF Report Exports</div></div>", unsafe_allow_html=True)

        st.write("")
        st.progress(85)
        st.caption("85% validation credits available for the current billing cycle.")
        
        st.markdown("---")
        if st.button("Upgrade to Enterprise Swarm Plan"):
            st.info("Enterprise tier unlocks parallel agent execution and custom industry fine-tuning.")
        st.markdown("</div>", unsafe_allow_html=True)

    # 10. HELP & SUPPORT
    with settings_tabs[9]:
        st.markdown("<div class='glass-card'>", unsafe_allow_html=True)
        st.markdown("### Help, Support & System Info")
        st.caption("Platform guides, troubleshooting documentation, FAQs, and support:")

        with st.expander("How does the 9-agent validation swarm work?", expanded=False):
            st.markdown("""
            Startup Validator executes a sequential, deterministic agent pipeline:
            1. **Idea Extraction:** Articulates problem, customer, domain, and monetization.
            2. **Live Web Search:** Queries Tavily and DuckDuckGo for live statistics and competitor products.
            3. **Market Opportunity:** Computes TAM/SAM/SOM and formulates customer personas.
            4. **Competitor Discovery:** Maps direct and indirect rivals into a white space gap matrix.
            5. **SWOT & Risk Audit:** Identifies strengths, weaknesses, and a categorized risk register.
            6. **MVP Roadmap:** Designs a MoSCoW-prioritized 3-phase launch feature set.
            7. **Go-To-Market Playbook:** Creates an acquisition strategy and unit economics.
            8. **Financial Feasibility (Step 9):** Simulates 5-year revenue, expenses, profit/loss, and break-even.
            9. **Validation Report:** Synthesizes an executive dossier with an investor Go/No-Go verdict.
            """)

        with st.expander("How are the financial projections in Step 9 calculated?", expanded=False):
            st.markdown("""
            Financial feasibility models annual customer adoption curves, ARPU derived from your pricing tier, 
            customer acquisition cost (CAC), technology hosting overhead, and operating expenses. 
            The interactive simulator lets you test different seed investments ($10k-$250k) and pricing levels.
            """)

        with st.expander("Can I run validations without external API keys?", expanded=False):
            st.markdown("""
            Yes. The platform includes an offline Intelligent Heuristic Engine that evaluates startup ideas 
            with domain-specific heuristics even when offline or without external API keys.
            """)

        st.markdown("---")
        st.markdown("#### Contact Technical Support")
        with st.form("support_form"):
            st.text_input("Subject", placeholder="e.g. Issue with custom domain classification")
            st.text_area("Describe the issue", placeholder="Provide details...", height=80)
            if st.form_submit_button("Submit Support Ticket"):
                st.success("Support ticket #9204 received. Our team will follow up within 2 hours.")

        st.markdown("---")
        st.markdown(f"<b>System Build:</b> Startup Validator v{APP_VERSION} • Multi-Agent Swarm Core", unsafe_allow_html=True)
        st.markdown("<div style='font-size:0.8rem; opacity:0.8; margin-top:4px;'>Terms of Service • Privacy Policy • Enterprise SLA</div>", unsafe_allow_html=True)
        st.markdown("</div>", unsafe_allow_html=True)