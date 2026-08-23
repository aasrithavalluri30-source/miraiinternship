import html
import hashlib
import io
import json
import os
import re
from datetime import datetime

import pandas as pd
import streamlit as st
from PIL import Image

try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    pass

try:
    from google import genai
    from google.genai import types
    HAS_GENAI = True
except ImportError:
    HAS_GENAI = False


st.set_page_config(
    page_title="Vibe Shelf · Find your next story",
    page_icon="✦",
    layout="wide",
    initial_sidebar_state="expanded",
)


# ─────────────────────────────────────────────────────────────────────────────
# Visual system
# ─────────────────────────────────────────────────────────────────────────────
st.markdown(
    """
<style>
@import url('https://fonts.googleapis.com/css2?family=DM+Mono:wght@400;500&family=DM+Sans:wght@400;500;600;700&family=Playfair+Display:wght@500;600;700&display=swap');

:root {
    --ink: #f8f0ff;
    --muted: #ad9fbd;
    --soft: #d7c9e5;
    --lavender: #d9b9ff;
    --pink: #ffb8d9;
    --blue: #b3dcff;
    --line: rgba(222, 190, 255, .16);
}

#MainMenu, footer, .stDeployButton { visibility: hidden; }
header, [data-testid="stHeader"] {
    visibility: visible !important;
    background: transparent !important;
}
[data-testid="stToolbar"] {
    visibility: visible !important;
}
[data-testid="stToolbarActions"] {
    visibility: hidden !important;
}
[data-testid="stSidebarCollapseButton"],
[data-testid="stExpandSidebarButton"] {
    visibility: visible !important;
    opacity: 1 !important;
    position: relative !important;
    z-index: 20 !important;
    margin: .45rem !important;
    border: 1px solid rgba(255, 184, 217, .42) !important;
    border-radius: 10px !important;
    background: rgba(24, 13, 39, .88) !important;
    box-shadow: 0 5px 18px rgba(0, 0, 0, .28), 0 0 18px rgba(255, 184, 217, .12) !important;
}
[data-testid="stSidebarCollapseButton"] svg,
[data-testid="stExpandSidebarButton"] svg {
    color: #ffd8ec !important;
    fill: #ffd8ec !important;
    opacity: 1 !important;
}
html, body, [class*="css"] { font-family: 'DM Sans', sans-serif; }
.stApp {
    color: var(--ink);
    background:
        radial-gradient(ellipse at 82% -8%, rgba(193, 111, 255, .32), transparent 34rem),
        radial-gradient(ellipse at 8% 35%, rgba(60, 113, 255, .16), transparent 28rem),
        radial-gradient(ellipse at 72% 82%, rgba(255, 104, 186, .12), transparent 32rem),
        linear-gradient(125deg, #08050e 0%, #170b2a 46%, #0d1027 72%, #08050e 100%);
    background-attachment: fixed;
}
.stApp::before, .stApp::after {
    content: "";
    position: fixed;
    inset: -20%;
    pointer-events: none;
    z-index: 0;
}
.stApp::before {
    opacity: .78;
    background-image:
        radial-gradient(1px 1px at 10% 18%, rgba(255,241,252,.95), transparent 2px),
        radial-gradient(2px 2px at 33% 72%, rgba(255,182,217,.7), transparent 3px),
        radial-gradient(1px 1px at 68% 24%, rgba(168,214,255,.9), transparent 2px),
        radial-gradient(2px 2px at 91% 63%, rgba(212,178,255,.65), transparent 3px),
        radial-gradient(1px 1px at 47% 42%, rgba(255,255,255,.7), transparent 2px);
    background-size: 270px 270px, 330px 330px, 410px 410px, 290px 290px, 180px 180px;
    animation: stardust 28s linear infinite;
}
.stApp::after {
    opacity: .82;
    background:
        radial-gradient(ellipse at 52% -20%, rgba(255, 198, 241, .16), transparent 38%),
        radial-gradient(ellipse at 94% 47%, rgba(93, 174, 255, .1), transparent 34%),
        repeating-linear-gradient(116deg, transparent 0 120px, rgba(212,178,255,.026) 121px 122px, transparent 123px 260px);
    transform: rotate(-8deg);
    mix-blend-mode: screen;
    animation: auroraShift 18s ease-in-out infinite alternate;
}
@keyframes stardust { from { transform: translate3d(0,0,0); } to { transform: translate3d(2%, -3%, 0); } }
@keyframes auroraShift {
    from { opacity: .55; filter: blur(0); }
    to { opacity: .9; filter: blur(1px); transform: rotate(-8deg) translate3d(-1%, 2%, 0) scale(1.03); }
}

.main .block-container {
    position: relative;
    z-index: 1;
    max-width: 1420px;
    padding: 3.25rem 4.5rem 5rem;
}
[data-testid="stSidebar"] {
    background:
        radial-gradient(circle at 50% 0%, rgba(166, 91, 255, .14), transparent 25rem),
        linear-gradient(180deg, rgba(12, 7, 24, .96), rgba(7, 7, 16, .98));
    border-right: 1px solid var(--line);
    box-shadow: 18px 0 60px rgba(8, 3, 18, .32);
}
[data-testid="stSidebar"] > div:first-child {
    padding: 2rem 1.35rem;
    background-blend-mode: screen, normal;
}
[data-testid="stSidebar"] .stMarkdown { color: var(--ink); }

h1, h2, h3, h4, p, label, .stCaption, [data-testid="stMetricLabel"] { position: relative; z-index: 1; }
h1 {
    font-family: 'Playfair Display', serif !important;
    font-size: clamp(3.4rem, 7vw, 6.4rem) !important;
    letter-spacing: -.06em;
    line-height: .95 !important;
    margin: 0 !important;
    background: linear-gradient(100deg, #fff5fd 0%, #d9b9ff 38%, #ffb8d9 76%, #b3dcff 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    filter: drop-shadow(0 12px 32px rgba(212, 138, 255, .18));
}
h2, h3, h4 { font-family: 'Playfair Display', serif !important; color: #f8f0ff !important; }
h3 { font-size: 1.5rem !important; }
p { color: var(--muted); }

.hero {
    position: relative;
    padding: 1.6rem 0 3rem;
    max-width: 820px;
    isolation: isolate;
}
.hero::before {
    content: "";
    position: absolute;
    width: 25rem;
    height: 25rem;
    right: -10rem;
    top: -11rem;
    border-radius: 50%;
    background: radial-gradient(circle, rgba(247, 184, 255, .16), rgba(112, 119, 255, .06) 38%, transparent 70%);
    filter: blur(4px);
    pointer-events: none;
    z-index: -1;
    animation: heroGlow 9s ease-in-out infinite alternate;
}
.hero::after {
    content: "";
    position: absolute;
    left: 0;
    bottom: 1.45rem;
    width: min(31rem, 78%);
    height: 1px;
    background: linear-gradient(90deg, rgba(255,184,217,.62), rgba(179,220,255,.2), transparent);
    box-shadow: 0 0 18px rgba(255,184,217,.35);
    pointer-events: none;
}
@keyframes heroGlow {
    from { transform: translate3d(0, 0, 0) scale(.96); opacity: .65; }
    to { transform: translate3d(-1.5rem, 1rem, 0) scale(1.08); opacity: 1; }
}
.eyebrow, .section-kicker {
    color: var(--pink);
    font: 500 .7rem 'DM Mono', monospace;
    letter-spacing: .15em;
    text-transform: uppercase;
}
.hero-subtitle { color: #c0b2cf; font-size: 1.08rem; line-height: 1.7; margin: .9rem 0 0; max-width: 700px; }
.rule { height: 1px; background: linear-gradient(90deg, rgba(212,178,255,.55), rgba(212,178,255,.08), transparent); margin: 1.1rem 0 1.7rem; }
.glass-card, .book-card, .story-card {
    position: relative;
    overflow: hidden;
    background:
        linear-gradient(145deg, rgba(255,255,255,.105), rgba(255,255,255,.025) 48%, rgba(147,94,255,.04));
    border: 1px solid rgba(222, 190, 255, .2);
    border-radius: 24px;
    box-shadow:
        0 24px 70px rgba(0,0,0,.28),
        0 0 0 1px rgba(255,255,255,.025),
        inset 0 1px 0 rgba(255,255,255,.08);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    transition: transform .35s ease, border-color .35s ease, box-shadow .35s ease;
}
.glass-card::before, .book-card::before, .story-card::before {
    content: "";
    position: absolute;
    inset: 0;
    background: linear-gradient(120deg, rgba(255,255,255,.12), transparent 24%, transparent 72%, rgba(214,179,255,.06));
    pointer-events: none;
}
.glass-card:hover, .book-card:hover, .story-card:hover {
    transform: translateY(-3px);
    border-color: rgba(255, 184, 217, .34);
    box-shadow:
        0 30px 84px rgba(0,0,0,.32),
        0 0 32px rgba(189, 119, 255, .1),
        inset 0 1px 0 rgba(255,255,255,.1);
}
.glass-card { padding: 1.35rem 1.45rem; }
.book-card { padding: 1.45rem; margin: .7rem 0; min-height: 260px; }
.story-card { padding: 1.45rem 1.6rem; margin-top: 1rem; }
.book-title { color: #fff2fb; font: 600 1.8rem/1.1 'Playfair Display', serif; margin: .7rem 0 .25rem; }
.book-author { color: var(--blue); font-size: .92rem; }
.book-copy, .story-copy { color: #cfc1da; line-height: 1.75; font-size: .95rem; margin: .95rem 0; }
.book-note { color: #9386a4; font: .68rem 'DM Mono', monospace; letter-spacing: .06em; border-top: 1px solid var(--line); padding-top: .75rem; }
.trope-tag {
    display: inline-block;
    color: #f0dcff;
    background: linear-gradient(110deg, rgba(137,91,204,.26), rgba(255,182,217,.11));
    border: 1px solid rgba(212,178,255,.3);
    border-radius: 999px;
    padding: .36rem .68rem;
    margin: .12rem .22rem .12rem 0;
    font-size: .7rem;
}
.empty-state { min-height: 460px; display: flex; align-items: center; justify-content: center; text-align: center; color: var(--muted); }
.empty-icon { font-size: 3rem; margin-bottom: .6rem; }
.small-mono { color: #9386a4; font: .68rem 'DM Mono', monospace; letter-spacing: .05em; }
.genre-signal {
    display: flex; align-items: center; gap: .75rem; margin: .8rem 0 1rem; padding: .75rem .9rem;
    color: #f2eaff; background: rgba(255,255,255,.045);
    border: 1px solid var(--genre-accent, rgba(212,178,255,.3)); border-radius: 14px;
    box-shadow: 0 0 24px var(--genre-glow, rgba(212,178,255,.08));
}
.genre-signal-icon { font-size: 1.35rem; }
.genre-signal-copy { display: flex; flex-direction: column; gap: .1rem; }
.genre-signal-copy strong { font-size: .9rem; }
.genre-signal-copy span { color: #a99db9; font-size: .75rem; }
.status-pill {
    display: inline-block; border: 1px solid rgba(168, 240, 226, .3); color: #b8f0df;
    background: rgba(83, 183, 164, .1); border-radius: 999px; padding: .3rem .62rem;
    font: .67rem 'DM Mono', monospace; letter-spacing: .04em;
}
.book-list-item {
    padding: .7rem .85rem; border: 1px solid rgba(212,178,255,.12); border-radius: 13px;
    background: rgba(255,255,255,.035); margin: .45rem 0;
}
.book-list-item strong { color: #f4eaff; font-size: .88rem; }
.book-list-item span { display: block; color: #9386a4; font-size: .75rem; margin-top: .18rem; }
.history-item {
    padding: .65rem .75rem; border-left: 2px solid var(--genre-accent, rgba(212,178,255,.5));
    background: rgba(255,255,255,.035); border-radius: 0 10px 10px 0; margin: .45rem 0;
}
.history-item strong { display: block; color: #f4eaff; font-size: .77rem; line-height: 1.35; }
.history-item span { display: block; color: #9386a4; font-size: .67rem; line-height: 1.4; margin-top: .18rem; }
.history-count { color: #cfc1da; font: .7rem 'DM Mono', monospace; letter-spacing: .04em; }
.library-card {
    position: relative; overflow: hidden; min-height: 188px; padding: 1.25rem;
    border: 1px solid rgba(255,184,217,.2); border-radius: 20px;
    background: linear-gradient(145deg, rgba(255,255,255,.09), rgba(255,255,255,.025));
    box-shadow: 0 16px 42px rgba(0,0,0,.22), inset 0 1px 0 rgba(255,255,255,.08);
    animation: shelfRise .65s both;
}
.library-card::after {
    content: "✦";
    position: absolute; right: 1rem; top: .65rem; color: rgba(255,184,217,.58);
    font-size: 1.1rem; animation: twinkle 2.8s ease-in-out infinite;
}
.library-card-title { color: #fff2fb; font: 600 1.35rem/1.1 'Playfair Display', serif; margin: .4rem 0 .2rem; }
.library-card-author { color: var(--blue); font-size: .82rem; }
.library-card-meta { color: #a99db9; font: .68rem 'DM Mono', monospace; letter-spacing: .04em; margin-top: .8rem; }
.rating-display { color: #ffd0e5; letter-spacing: .12em; font-size: .9rem; margin-top: .7rem; }
.cover-card {
    position: relative; min-height: 330px; padding: 1.2rem 1.05rem;
    display: flex; flex-direction: column; justify-content: space-between; overflow: hidden;
    border: 1px solid rgba(255,184,217,.3); border-radius: 18px 18px 10px 10px;
    background:
        radial-gradient(circle at 75% 15%, rgba(255,255,255,.22), transparent 18%),
        linear-gradient(145deg, rgba(145,83,206,.9), rgba(36,19,67,.98) 58%, rgba(12,9,25,.98));
    box-shadow: 0 18px 42px rgba(0,0,0,.34), inset 0 1px 0 rgba(255,255,255,.14);
    animation: shelfRise .65s both;
    transition: transform .35s cubic-bezier(.2,.8,.2,1), box-shadow .35s ease, border-color .35s ease;
}
.cover-card::before {
    content: ""; position: absolute; inset: 10px; border: 1px solid rgba(255,232,247,.28);
    border-radius: 12px; pointer-events: none;
}
.cover-card::after {
    content: "✦"; position: absolute; right: 1rem; top: .8rem; color: rgba(255,218,238,.8);
    font-size: 1.25rem; animation: twinkle 2.8s ease-in-out infinite;
}
.cover-card:hover {
    transform: translateY(-8px) rotate(-.6deg);
    border-color: rgba(255,238,250,.6);
    box-shadow: 0 28px 58px rgba(0,0,0,.42), 0 0 32px rgba(255,184,217,.15), inset 0 1px 0 rgba(255,255,255,.18);
}
.cover-card:nth-child(3n + 2):hover { transform: translateY(-8px) rotate(.6deg); }
.cover-kicker { color: rgba(255,235,248,.75); font: .62rem 'DM Mono', monospace; letter-spacing: .15em; text-transform: uppercase; }
.cover-title { color: #fff5fb; font: 600 1.65rem/1.05 'Playfair Display', serif; text-align: center; text-shadow: 0 4px 20px rgba(0,0,0,.35); }
.cover-author { color: #f0d7ff; font-size: .78rem; text-align: center; }
.review-label { color: #d9b9ff; font: .68rem 'DM Mono', monospace; letter-spacing: .1em; text-transform: uppercase; }
.shelf-intro {
    display: flex; align-items: center; justify-content: space-between; gap: 1rem;
    padding: 1rem 1.2rem; margin: .25rem 0 1.5rem;
    border: 1px solid rgba(255,184,217,.18); border-radius: 18px;
    background: linear-gradient(105deg, rgba(255,184,217,.09), rgba(179,220,255,.045) 55%, rgba(255,255,255,.025));
    box-shadow: inset 0 1px 0 rgba(255,255,255,.08), 0 18px 38px rgba(0,0,0,.16);
}
.shelf-intro strong { color: #fff2fb; font: 600 1rem 'Playfair Display', serif; }
.shelf-intro span { color: #a99db9; font-size: .78rem; }
.shelf-count { color: #ffd0e5; font: .72rem 'DM Mono', monospace; white-space: nowrap; }
.shelf-empty {
    padding: 3.6rem 1.5rem; text-align: center; border: 1px dashed rgba(255,184,217,.25);
    border-radius: 24px; background: radial-gradient(circle at 50% 0%, rgba(214,143,255,.12), transparent 58%);
}
.chat-shell {
    position: relative; overflow: hidden; border: 1px solid rgba(212,178,255,.24);
    border-radius: 28px; padding: 1.1rem 1.25rem 1.25rem;
    background: radial-gradient(circle at 8% 0%, rgba(217,185,255,.14), transparent 22rem), linear-gradient(145deg, rgba(255,255,255,.085), rgba(255,255,255,.018) 68%);
    box-shadow: 0 30px 90px rgba(0,0,0,.3), 0 0 45px rgba(137,91,204,.08), inset 0 1px 0 rgba(255,255,255,.1);
}
.chat-shell::before {
    content: ""; position: absolute; inset: 0; pointer-events: none; opacity: .45;
    background: repeating-linear-gradient(115deg, transparent 0 90px, rgba(255,255,255,.025) 91px 92px, transparent 93px 180px);
}
.chat-header {
    position: relative; display: flex; justify-content: space-between; align-items: center;
    gap: 1rem; padding: .25rem .15rem 1rem; border-bottom: 1px solid rgba(212,178,255,.13);
}
.chat-orbit {
    width: 42px; height: 42px; flex: 0 0 auto; border-radius: 50%; display: grid; place-items: center;
    color: #211127; font-size: 1.1rem;
    background: radial-gradient(circle at 32% 28%, #fff6fd 0 9%, #ffb8d9 28%, #c998ff 67%, #6843a0 100%);
    box-shadow: 0 0 0 7px rgba(217,185,255,.08), 0 0 28px rgba(255,184,217,.28);
    animation: orbitPulse 4.5s ease-in-out infinite;
}
.chat-header-copy { flex: 1; }
.chat-header-copy strong { display: block; color: #fff2fb; font: 600 1.05rem 'Playfair Display', serif; }
.chat-header-copy span { color: #9d90ae; font-size: .75rem; }
.chat-status { color: #b8f0df; font: .62rem 'DM Mono', monospace; letter-spacing: .08em; white-space: nowrap; }
.chat-empty { position: relative; padding: 4.8rem 1rem 5.2rem; text-align: center; }
.chat-empty .empty-icon { filter: drop-shadow(0 0 18px rgba(255,184,217,.32)); animation: floatGlyph 4s ease-in-out infinite; }
.chat-empty strong { display: block; color: #f6eaff; font: 600 1.45rem 'Playfair Display', serif; }
.chat-empty span { display: block; max-width: 480px; margin: .55rem auto 0; color: #a99db9; line-height: 1.7; }
}
.chat-bubble {
    padding: .95rem 1.05rem; margin: .6rem 0; border-radius: 16px 16px 16px 4px;
    color: #e9ddf6; background: rgba(255,255,255,.055); border: 1px solid rgba(212,178,255,.12);
    line-height: 1.65; animation: shelfRise .45s both; position: relative; max-width: 88%;
}
.chat-bubble.user {
    border-radius: 16px 16px 4px 16px; color: #27152c; margin-left: auto;
    background: linear-gradient(120deg, #d9b9ff, #ffb8d9); border-color: transparent;
}
@keyframes shelfRise { from { opacity: 0; transform: translateY(12px) scale(.985); } to { opacity: 1; transform: translateY(0) scale(1); } }
@keyframes twinkle { 0%, 100% { opacity: .45; transform: scale(.9) rotate(0); } 50% { opacity: 1; transform: scale(1.15) rotate(12deg); } }
@keyframes orbitPulse { 0%, 100% { transform: translateY(0) rotate(0); } 50% { transform: translateY(-4px) rotate(8deg); } }
@keyframes floatGlyph { 0%, 100% { transform: translateY(0) rotate(-3deg); } 50% { transform: translateY(-9px) rotate(4deg); } }

.stTextArea textarea, .stTextInput input, .stNumberInput input {
    color: var(--ink) !important; background: rgba(10,7,18,.6) !important;
    border: 1px solid rgba(212,178,255,.21) !important; border-radius: 12px !important;
}
.stTextArea textarea:focus, .stTextInput input:focus {
    border-color: rgba(212,178,255,.7) !important; box-shadow: 0 0 0 1px rgba(212,178,255,.25) !important;
}
[data-baseweb="select"], [data-baseweb="input"] { background: rgba(10,7,18,.6) !important; border-color: rgba(212,178,255,.21) !important; }
.stMultiSelect [data-baseweb="select"], .stSelectbox [data-baseweb="select"] { border-radius: 12px !important; min-height: 44px; }
.stSelectbox [data-baseweb="select"] > div, .stMultiSelect [data-baseweb="select"] > div {
    background: rgba(10,7,18,.72) !important; color: var(--ink) !important; border-color: transparent !important;
}
.stSelectbox [data-baseweb="select"] svg, .stMultiSelect [data-baseweb="select"] svg { fill: var(--lavender) !important; }
[role="listbox"] { background: #1a1128 !important; color: var(--ink) !important; border: 1px solid rgba(212,178,255,.2) !important; }
[role="option"] { color: var(--ink) !important; }
.stSlider [data-baseweb="slider"] { padding-top: .5rem; }
.stSlider [role="slider"] { background: var(--pink); border-color: var(--pink); }
.stFileUploader section, [data-testid="stAudioInput"] {
    background: rgba(10,7,18,.36) !important; border: 1px dashed rgba(212,178,255,.28) !important; border-radius: 14px !important;
}
.stForm { border: 1px solid var(--line) !important; border-radius: 24px !important; background: rgba(18, 12, 30, .47) !important; padding: 1.2rem 1.35rem !important; }
.stButton > button, .stFormSubmitButton > button {
    border: 0 !important; border-radius: 12px !important; color: #160d21 !important;
    background: linear-gradient(105deg, #d9b9ff, #ffb8d9) !important; font-weight: 700 !important;
    transition: transform .2s ease, box-shadow .2s ease !important;
}
.stButton > button:hover, .stFormSubmitButton > button:hover { transform: translateY(-2px); box-shadow: 0 8px 25px rgba(255,182,217,.22) !important; }
.secondary-button > button { color: #e7d9f7 !important; background: rgba(212,178,255,.1) !important; border: 1px solid rgba(212,178,255,.28) !important; }
.stChatInput {
    border-color: rgba(212,178,255,.3) !important; background: rgba(13,8,24,.72) !important;
    box-shadow: 0 12px 34px rgba(0,0,0,.2), 0 0 24px rgba(217,185,255,.06);
}
.stChatInput:focus-within { border-color: rgba(255,184,217,.64) !important; box-shadow: 0 0 0 1px rgba(255,184,217,.25), 0 12px 34px rgba(0,0,0,.2) !important; }
[data-testid="stChatMessage"] { background: transparent !important; }
.stExpander { background: rgba(255,255,255,.025); border: 1px solid rgba(212,178,255,.11); border-radius: 14px; margin: .55rem 0; }
.stExpander details summary p { color: #e7d9f7; font-weight: 600; }
[data-testid="stMetric"] { background: rgba(255,255,255,.045); border: 1px solid rgba(212,178,255,.15); border-radius: 16px; padding: .85rem .9rem; }
[data-testid="stMetricValue"] { color: #fff1fb; font-family: 'DM Mono', monospace; font-size: 1.45rem; }
[data-testid="stMetricDelta"] { font-size: .72rem; }
.stAlert { border-radius: 14px !important; }
@media (max-width: 900px) {
    .main .block-container { padding: 2rem 1.05rem 3rem; }
    h1 { font-size: 3.6rem !important; }
    .shelf-intro { align-items: flex-start; flex-direction: column; gap: .4rem; }
    .cover-card { min-height: 270px; }
    .chat-bubble { max-width: 94%; }
}
</style>
""",
    unsafe_allow_html=True,
)


# ─────────────────────────────────────────────────────────────────────────────
# Curatorial data
# ─────────────────────────────────────────────────────────────────────────────
GENRES = {
    "Fantasy": ("✦", "ancient magic, hidden realms, and impossible quests"),
    "Romance": ("♡", "charged glances, tender tension, and hearts in orbit"),
    "Mystery & Thriller": ("⌁", "sharp clues, unreliable truths, and one more chapter"),
    "Science Fiction": ("◌", "strange futures, impossible technology, and cosmic scale"),
    "Historical Fiction": ("❦", "lost letters, sweeping eras, and lives shaped by history"),
    "Horror & Gothic": ("☾", "haunted rooms, old secrets, and dread that blooms slowly"),
    "Contemporary & Literary": ("✧", "interior lives, luminous details, and complicated becoming"),
}

SIDEBAR_WALLPAPERS = {
    "Fantasy": {
        "accent": "#d9b9ff",
        "base": "#171026",
        "background": "radial-gradient(circle at 78% 8%, rgba(120,75,185,.38), transparent 30rem), radial-gradient(circle at 12% 68%, rgba(56,73,152,.2), transparent 34rem), linear-gradient(125deg, #0b0813 0%, #171026 52%, #0b0813 100%)",
        "image": "radial-gradient(circle at 18% 10%, rgba(217,185,255,.28) 0 1px, transparent 2px), radial-gradient(circle at 82% 28%, rgba(179,220,255,.2) 0 2px, transparent 3px), repeating-radial-gradient(ellipse at 90% 10%, transparent 0 32px, rgba(217,185,255,.055) 33px 34px)",
    },
    "Romance": {
        "accent": "#ffb8d9",
        "base": "#241022",
        "background": "radial-gradient(circle at 78% 8%, rgba(181,65,133,.38), transparent 30rem), radial-gradient(circle at 12% 68%, rgba(116,58,135,.24), transparent 34rem), linear-gradient(125deg, #120914 0%, #241022 52%, #0f0914 100%)",
        "image": "radial-gradient(circle at 20% 16%, rgba(255,184,217,.32) 0 2px, transparent 3px), radial-gradient(ellipse at 82% 22%, rgba(255,184,217,.18), transparent 36%), repeating-linear-gradient(130deg, transparent 0 72px, rgba(255,184,217,.055) 73px 74px, transparent 75px 145px)",
    },
    "Mystery & Thriller": {
        "accent": "#b3dcff",
        "base": "#101827",
        "background": "radial-gradient(circle at 78% 8%, rgba(45,103,153,.38), transparent 30rem), radial-gradient(circle at 12% 68%, rgba(76,57,133,.22), transparent 34rem), linear-gradient(125deg, #080d16 0%, #101827 52%, #090a13 100%)",
        "image": "radial-gradient(circle at 78% 16%, rgba(179,220,255,.3) 0 1px, transparent 2px), repeating-linear-gradient(0deg, rgba(179,220,255,.03) 0 1px, transparent 1px 9px), linear-gradient(112deg, transparent 0 62%, rgba(179,220,255,.08) 62.2% 62.6%, transparent 63%)",
    },
    "Science Fiction": {
        "accent": "#a8f0e2",
        "base": "#0e1c25",
        "background": "radial-gradient(circle at 78% 8%, rgba(29,128,141,.38), transparent 30rem), radial-gradient(circle at 12% 68%, rgba(71,61,159,.22), transparent 34rem), linear-gradient(125deg, #071115 0%, #0e1c25 52%, #080b13 100%)",
        "image": "radial-gradient(circle at 18% 18%, rgba(168,240,226,.35) 0 1px, transparent 2px), linear-gradient(rgba(168,240,226,.035) 1px, transparent 1px), linear-gradient(90deg, rgba(168,240,226,.035) 1px, transparent 1px), radial-gradient(ellipse at 78% 22%, rgba(44,157,173,.2), transparent 40%)",
    },
    "Historical Fiction": {
        "accent": "#e8c99b",
        "base": "#21181b",
        "background": "radial-gradient(circle at 78% 8%, rgba(155,93,54,.34), transparent 30rem), radial-gradient(circle at 12% 68%, rgba(109,70,112,.24), transparent 34rem), linear-gradient(125deg, #130d0c 0%, #21181b 52%, #0e0a0d 100%)",
        "image": "radial-gradient(ellipse at 82% 12%, rgba(232,201,155,.24), transparent 34%), repeating-linear-gradient(112deg, transparent 0 58px, rgba(232,201,155,.045) 59px 60px, transparent 61px 120px), radial-gradient(circle at 24% 72%, rgba(167,90,70,.17), transparent 36%)",
    },
    "Horror & Gothic": {
        "accent": "#c6b5ff",
        "base": "#171021",
        "background": "radial-gradient(circle at 78% 8%, rgba(86,49,127,.4), transparent 30rem), radial-gradient(circle at 12% 68%, rgba(28,84,91,.2), transparent 34rem), linear-gradient(125deg, #0b0811 0%, #171021 52%, #070a0d 100%)",
        "image": "radial-gradient(ellipse at 78% 18%, rgba(126,84,176,.25), transparent 36%), radial-gradient(circle at 22% 38%, rgba(198,181,255,.23) 0 1px, transparent 2px), radial-gradient(ellipse at 50% 65%, transparent 0 30%, rgba(198,181,255,.06) 31% 31.5%, transparent 32%)",
    },
    "Contemporary & Literary": {
        "accent": "#f0c8a0",
        "base": "#1d1719",
        "background": "radial-gradient(circle at 78% 8%, rgba(169,100,77,.28), transparent 30rem), radial-gradient(circle at 12% 68%, rgba(106,67,110,.2), transparent 34rem), linear-gradient(125deg, #110d0d 0%, #1d1719 52%, #0d0b0d 100%)",
        "image": "radial-gradient(ellipse at 78% 16%, rgba(240,200,160,.22), transparent 34%), repeating-linear-gradient(118deg, transparent 0 88px, rgba(240,200,160,.04) 89px 90px, transparent 91px 180px), radial-gradient(circle at 20% 75%, rgba(197,126,161,.14), transparent 36%)",
    },
}

TROPE_LIBRARY = [
    "Enemies to Lovers", "Enemies to Allies", "Morally Grey Protagonist", "Found Family",
    "Fake Dating", "Grumpy x Sunshine", "Slow Burn", "Rivals to Allies",
    "Forced Proximity", "One Bed", "Secret Society", "Unreliable Narrator",
    "Dark Academia", "Cozy Magic", "Small Town Secrets", "Court Intrigue",
    "Quest Across Realms", "Deadly Tournament", "Time Loop", "Dystopian Rebellion",
    "Locked Room Mystery", "Lush & Lyrical", "Gothic Fairytale", "Second Chance",
]

PACE_LABELS = ["slow-blooming", "measured", "balanced", "propulsive", "breathless"]
TONE_LABELS = ["tender", "warm", "moody", "intense", "dark"]
MOOD_PALETTES = {
    "Dreamy": "#9d79d8",
    "Romantic": "#e88bb9",
    "Calm": "#6f9bd8",
    "Cozy": "#c58c63",
    "Moody": "#5f4c9b",
    "Fresh": "#56b6a9",
    "Custom": None,
}
BOOKSTORE_CITIES = pd.DataFrame(
    [
        {"city": "London", "lat": 51.5074, "lon": -0.1278},
        {"city": "New York", "lat": 40.7128, "lon": -74.0060},
        {"city": "Paris", "lat": 48.8566, "lon": 2.3522},
        {"city": "Mumbai", "lat": 19.0760, "lon": 72.8777},
        {"city": "Tokyo", "lat": 35.6762, "lon": 139.6503},
        {"city": "Melbourne", "lat": -37.8136, "lon": 144.9631},
    ]
)


@st.cache_resource(show_spinner=False)
def get_client():
    """Use the Replit environment secret without ever rendering its value."""
    if not HAS_GENAI:
        return None
    api_key = next(
        (os.environ.get(name, "") for name in ("GEMINI_API_KEY", "GOOGLE_API_KEY") if os.environ.get(name, "")),
        "",
    )
    if not api_key:
        return None
    try:
        return genai.Client(api_key=api_key)
    except Exception:
        return None


def extract_json(text):
    cleaned = re.sub(r"```(?:json)?", "", text or "").strip()
    try:
        return json.loads(cleaned)
    except json.JSONDecodeError:
        pass
    for opener, closer in [("[", "]"), ("{", "}")]:
        start, end = cleaned.find(opener), cleaned.rfind(closer)
        if start >= 0 and end > start:
            try:
                return json.loads(cleaned[start:end + 1])
            except json.JSONDecodeError:
                continue
    return None


def model_name():
    return os.environ.get("GEMINI_MODEL", "gemini-3.5-flash-lite")


def safe_hex_color(value, fallback):
    """Accept only six-digit hex colors before placing a user choice in CSS."""
    value = str(value or "").strip()
    return value if re.fullmatch(r"#[0-9a-fA-F]{6}", value) else fallback


def apply_mood_background(color, glow_position="82% -8%"):
    """Tint the current page without allowing arbitrary CSS from user input."""
    color = safe_hex_color(color, "#8d6bd8")
    st.markdown(
        f"""
        <style>
        .stApp {{
            background:
                radial-gradient(ellipse at {glow_position}, {color}66, transparent 35rem),
                radial-gradient(ellipse at 8% 38%, {color}20, transparent 30rem),
                linear-gradient(125deg, #08050e 0%, #170b2a 48%, #0d1027 76%, #08050e 100%) !important;
        }}
        .stApp::after {{
            background:
                radial-gradient(ellipse at {glow_position}, {color}2e, transparent 38%),
                repeating-linear-gradient(116deg, transparent 0 120px, {color}09 121px 122px, transparent 123px 260px) !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )


def mood_color_control(label, state_key, default):
    """Render a mood preset and persistent color picker for a page."""
    st.session_state.setdefault(state_key, default)
    palette_key = f"{state_key}_palette"
    current_color = safe_hex_color(st.session_state[state_key], default)
    if palette_key not in st.session_state:
        st.session_state[palette_key] = next(
            (name for name, color in MOOD_PALETTES.items() if color == current_color),
            "Custom",
        )
    palette = st.selectbox(
        "Mood palette",
        list(MOOD_PALETTES),
        key=palette_key,
        help="Pick a ready-made atmosphere or choose Custom to fine-tune the glow.",
    )
    if palette == "Custom":
        picker_key = f"{state_key}_custom"
        if picker_key not in st.session_state:
            st.session_state[picker_key] = current_color
        color = st.color_picker(label, key=picker_key)
    else:
        color = MOOD_PALETTES[palette]
        st.caption(f"{palette} atmosphere · {color}")
    color = safe_hex_color(color, default)
    st.session_state[state_key] = color
    return color


def sync_matchmaker_state():
    """Copy transient matchmaker widgets into durable session keys before navigation."""
    for widget_key, state_key in (
        ("_match_genre", "match_genre"),
        ("_match_genre_blend", "match_genre_blend"),
        ("_match_mood", "match_mood"),
        ("_match_tropes", "match_tropes"),
        ("_match_pacing", "match_pacing"),
        ("_match_tone", "match_tone"),
    ):
        if widget_key in st.session_state:
            st.session_state[state_key] = st.session_state[widget_key]


LEAK_MARKERS = (
    "wait,",
    "actually,",
    "replacing this",
    "i'll replace",
    "i should replace",
    "let me verify",
    "let me check",
    "checking this candidate",
    "self-check",
    "internal reasoning",
    "verification:",
)


def _looks_like_leaked_reasoning(value):
    """Detect model self-check narration that should never reach a book card."""
    if isinstance(value, dict):
        return any(_looks_like_leaked_reasoning(item) for item in value.values())
    if isinstance(value, (list, tuple)):
        return any(_looks_like_leaked_reasoning(item) for item in value)
    text = str(value or "").casefold()
    return any(marker in text for marker in LEAK_MARKERS)


def transcribe_audio(client, audio_bytes, audio_type="audio/wav"):
    """Turn the recorded voice note into visible text before matching."""
    if not client or not audio_bytes:
        return ""
    response = client.models.generate_content(
        model=model_name(),
        contents=[
            "Transcribe this voice note exactly. Return only the spoken words, with no preamble or commentary.",
            types.Part.from_bytes(data=audio_bytes, mime_type=audio_type or "audio/wav"),
        ],
        config=types.GenerateContentConfig(temperature=0),
    )
    return (response.text or "").strip()


def recommend_books(
    client,
    genre,
    tropes,
    mood,
    pacing,
    tone,
    genre_blend="",
    image_bytes=None,
    audio_bytes=None,
    audio_transcript="",
    audio_type="audio/wav",
):
    """
    Returns (matches, debug_prompt) so the caller can optionally show what was sent.
    """
    icon, description = GENRES[genre]
    trope_text = ", ".join(tropes) if tropes else "not provided"

    prompt = f"""
You are a deeply thoughtful, accurate book curator for Vibe Shelf.
Find exactly three real, published books that genuinely match the reader's signal.

═══════════════════════════════════════════════════
RULE 1 — HARD REQUIREMENT, HIGHEST PRIORITY
═══════════════════════════════════════════════════
If the reader's mood, genre blend, or trope list names a specific creature,
subgenre, plot device, or setting (for example: vampires, dragons, time travel,
a heist, a locked-room murder, a secret society, a court/political intrigue),
then EVERY one of the three books you return MUST actually and centrally
feature that element. This overrides everything else, including originality.
Do not substitute a book that is only atmospherically similar but does not
actually contain the named element. If you are not confident a candidate book
contains the named element, do not include it — pick a different real book
that you are confident does.

═══════════════════════════════════════════════════
RULE 2 — SECONDARY PRIORITY
═══════════════════════════════════════════════════
Among books that already satisfy Rule 1, prefer specific, well-loved, and
atmospheric matches over the single most generic bestseller guess. But if
satisfying Rule 1 well requires using an obvious, famous title, use it —
Rule 1 always wins over "being original."

═══════════════════════════════════════════════════
RULE 3 — NO FABRICATION
═══════════════════════════════════════════════════
Do not invent titles, authors, plot details, or awards. Only recommend real,
published books you are confident exist and match. If genuinely fewer than
three real books satisfy Rule 1 for this exact combination, return fewer
than three rather than padding with a mismatch — but three is expected for
common genres/creatures/tropes, so exhaust your knowledge before shortening
the list.

═══════════════════════════════════════════════════
SELF-CHECK BEFORE YOU ANSWER
═══════════════════════════════════════════════════
For each of the three books, silently verify: "Does this book actually
contain every specific element the reader named (mood keywords, genre blend,
tropes)?" If any book fails this check, replace it before responding.

READER SIGNAL
- Genre room: {genre} ({description})
- Reader's custom genre blend: {genre_blend or "not provided"}
- Mood in their own words (read carefully for named elements/creatures/settings): {mood or "not provided"}
- Spoken vibe transcript: {audio_transcript or "not provided"}
- Tropes and themes: {trope_text}
- Pacing: {pacing}/10, from {PACE_LABELS[0]} to {PACE_LABELS[-1]}
- Tone: {tone}/10, from {TONE_LABELS[0]} to {TONE_LABELS[-1]}

If a spoken vibe recording is provided, treat its transcript and audio as the
reader's primary signal. Do not require a separate mood, trope, or genre blend.

Return ONLY a JSON array with exactly three objects using this shape:
[
  {{
    "title": "real book title",
    "author": "author name",
    "score": 88,
    "pace_alignment": 84,
    "atmosphere_index": 93,
    "tags": ["short tag", "short tag", "short tag"],
    "why_it_fits": "2-3 specific sentences explaining the match, explicitly naming how it satisfies the reader's stated elements, without quoting copy",
    "content_note": "brief, useful note if relevant, otherwise empty string"
  }}
]
Scores are integers from 70 to 99. Keep each explanation spoiler-free.
Return ONLY the JSON array. No preamble, no markdown fences, no commentary.
Never include your private verification process or self-correction narration in the
JSON. In particular, do not write phrases like "wait", "actually", "replacing
this", "let me verify", or anything describing a candidate being checked, rejected,
or replaced. The "why_it_fits" value must contain only the final reader-facing
explanation, never model thoughts or drafting notes.
"""
    parts = [prompt]
    if image_bytes:
        try:
            parts.append(Image.open(io.BytesIO(image_bytes)))
            parts[0] += "\nA moodboard image is attached. Read its palette and visual atmosphere as an additional signal, but it does not override Rule 1 above."
        except Exception:
            pass
    if audio_bytes:
        parts.append(
            types.Part.from_bytes(
                data=audio_bytes,
                mime_type=audio_type or "audio/wav",
            )
        )
        parts[0] += (
            "\nA spoken vibe recording is attached. Use the visible transcript "
            "above as the reader's words and use the audio only as supporting "
            "emotional context."
        )
    response = client.models.generate_content(
        model=model_name(),
        contents=parts,
        config=types.GenerateContentConfig(
            # Lower temperature: this is a constraint-following / factual-retrieval
            # task, not a creative one. Lower temp keeps the model honest about
            # Rule 1 instead of drifting toward "interesting but wrong" picks.
            temperature=0.2,
            response_mime_type="application/json",
        ),
    )
    data = extract_json(response.text)
    if isinstance(data, dict):
        data = data.get("books") or data.get("recommendations") or [data]
    if not isinstance(data, list):
        return None, prompt
    clean_data = [
        book for book in data
        if isinstance(book, dict) and not _looks_like_leaked_reasoning(book)
    ]
    return clean_data or None, prompt


def story_assistant(client, book, chapter, task, question, notes):
    title = book["title"]
    author = book.get("author") or "unknown author"
    prompt = f"""
You are the Story Desk inside Vibe Shelf, helping a reader understand "{title}" by {author}.
They have read through chapter {chapter}. The task is: {task}.
Their optional personal notes and pasted context are below:
--- READER CONTEXT ---
{notes or "No personal notes were provided."}
--- END CONTEXT ---

Answer warmly and clearly, with useful specifics only when supported by the context
or your reliable knowledge. Never reveal plot events, character fates, twists, or
symbolic meanings that happen after chapter {chapter}. Do not guess chapter numbering
or pretend certainty about a book's details. If the request needs information beyond
the reader's progress, say what is safe to say and what you are holding back.
For a recap, organize the answer with a short "So far" overview, "People to remember",
and "Threads to watch". For a question, answer directly in 2-5 short paragraphs.
For a character or world explanation, define terms before adding interpretation.
{f"Reader's question: {question}" if question else ""}
"""
    response = client.models.generate_content(
        model=model_name(),
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.35),
    )
    return response.text.strip()


def book_chat_assistant(client, messages, question, assistant_name="Book Chat"):
    saved_books = "\n".join(
        f'- "{book["title"]}" by {book.get("author") or "unknown author"}'
        for book in st.session_state.get("books", [])
    )
    transcript = "\n".join(
        f'{message["role"].upper()}: {message["text"]}'
        for message in messages[-12:]
    )
    prompt = f"""
You are {assistant_name}, the Vibe Shelf book companion: warm, imaginative, and
strictly accurate.
This is a single open conversation, not a menu of modes. Infer what the reader
wants from each message and respond naturally.

You can discuss books, authors, genres, literary history, characters, plots,
recommendations, reading habits, and reading data. If the reader asks for
roleplay, immediately inhabit the requested fictional character, narrator,
archetype, or bookish companion with a distinct voice. Stay clear that it is
roleplay when that matters, and never claim to be a real person. If they ask
for facts, statistics, timelines, comparisons, or other data, answer precisely,
use clear structure, explain uncertainty, and never invent sources or details.
If they ask about a specific book, avoid spoilers only when they request that.
Keep answers useful and vivid in 2-6 short paragraphs unless a list or table is
clearly the best format.

ACCURACY RULES — FOLLOW SILENTLY:
- For a character or author identity, silently verify the name, title, author,
  role, and relationships before answering. Never merge details from different
  books or characters with similar names.
- If the reader gives only an ambiguous first name or a name you cannot verify,
  ask which book or author they mean instead of guessing.
- If you are not confident in a fact, say "I’m not certain enough to state that
  as fact" and explain what detail would let you answer. Never fill gaps with a
  plausible-sounding invention.
- Put the direct answer first. For "who is X?", give the verified identity,
  source book, and author before adding a few relevant details.
- Never show drafting, self-correction, memory-search, or verification language.
  Do not write "wait", "actually", "no, let me correct that", "my memory is",
  "let me check", or any narration about choosing or replacing an answer.
- Do not fabricate citations, quotes, statistics, publication details, or plot
  events. When useful, label general knowledge versus an estimate.
- Fact check example: Rhys Larsen is the bodyguard male lead in *Twisted Games*
  by Ana Huang. Do not place him in *Twisted Hate* or merge those books' casts.

BOOKS SAVED IN THE READER'S MY BOOKS SHELF:
{saved_books or "No books have been saved yet."}

RECENT CONVERSATION:
{transcript or "No earlier messages."}

READER MESSAGE:
{question}
"""
    response = client.models.generate_content(
        model=model_name(),
        contents=prompt,
        config=types.GenerateContentConfig(temperature=0.3),
    )
    return response.text.strip()


def add_book(title, author, chapter, total_chapters, notes, source="personal"):
    title = title.strip()
    if not title:
        return False
    for existing in st.session_state.books:
        if existing["title"].casefold() == title.casefold():
            existing.update({
                "author": author.strip(),
                "chapter": chapter,
                "total_chapters": total_chapters,
                "notes": notes.strip(),
            })
            existing.setdefault("rating", 0)
            existing.setdefault("review", "")
            return "updated"
    st.session_state.books.append({
        "title": title,
        "author": author.strip(),
        "chapter": chapter,
        "total_chapters": total_chapters,
        "notes": notes.strip(),
        "source": source,
        "rating": 0,
        "review": "",
    })
    return "added"


def remove_book(index):
    """Remove a shelf item and keep Story Desk focus on a valid book."""
    if not 0 <= index < len(st.session_state.books):
        return None
    removed = st.session_state.books.pop(index)
    active_index = st.session_state.get("active_book_index", 0)
    if active_index > index:
        st.session_state.active_book_index = active_index - 1
    elif active_index >= len(st.session_state.books):
        st.session_state.active_book_index = max(0, len(st.session_state.books) - 1)
    return removed


def record_session_event(kind, title, detail, meta=""):
    """Keep lightweight activity history for this browser session only."""
    if "session_history" not in st.session_state:
        st.session_state.session_history = []
    st.session_state.session_history.append({
        "kind": kind,
        "title": str(title),
        "detail": str(detail),
        "meta": str(meta),
        "time": datetime.now().strftime("%I:%M %p"),
    })
    st.session_state.session_history = st.session_state.session_history[-30:]


def render_result_card(book, index):
    tags = book.get("tags") or []
    tags_html = "".join(
        f'<span class="trope-tag">{html.escape(str(tag))}</span>' for tag in tags[:5]
    )
    st.markdown(
        f"""
        <div class="book-card">
            <div class="small-mono" style="color:#d9b9ff; margin-bottom:.35rem;">MATCH {index:02d} · {int(book.get("score", 80))}% VIBE FIT</div>
            <div>{tags_html}</div>
            <div class="book-title">{html.escape(str(book.get("title", "Untitled")))}</div>
            <div class="book-author">by {html.escape(str(book.get("author", "Unknown author")))}</div>
            <div class="book-copy">{html.escape(str(book.get("why_it_fits", "")))}</div>
            {f'<div class="book-note">CONTENT NOTE · {html.escape(str(book.get("content_note")))}</div>' if book.get("content_note") else ""}
        </div>
        """,
        unsafe_allow_html=True,
    )
    metric_a, metric_b = st.columns(2)
    metric_a.metric("Pacing sync", f'{int(book.get("pace_alignment", 80))}%', delta=f'{int(book.get("pace_alignment", 80)) - 80}%')
    metric_b.metric("Atmosphere", f'{int(book.get("atmosphere_index", 80))}%', delta=f'{int(book.get("atmosphere_index", 80)) - 80}%')
    if st.button("＋ Add to My Books", key=f"add_match_{index}", use_container_width=True):
        result = add_book(str(book.get("title", "")), str(book.get("author", "")), 1, 0, "", "match")
        if result == "added":
            record_session_event("book", str(book.get("title", "")), "Book saved to My Books", "From Matchmaker")
            st.toast("Saved to My Books.")
            st.rerun()
        else:
            st.info("That title is already in My Books.")


def _clear_session_history_callback():
    """
    Runs BEFORE the rerun that a button click triggers, so by the time the
    script body executes again, session_history is already empty. This
    avoids relying on manual st.rerun()/scope behavior, which differs
    across Streamlit versions and was the reason the button appeared to
    do nothing.
    """
    st.session_state.session_history = []
    st.session_state.history_cleared_notice = True


# Use st.fragment when available (isolates reruns to this block for a
# snappier feel), but fall back to a no-op decorator on older Streamlit
# versions so the app never breaks because of it.
_fragment_decorator = st.fragment if hasattr(st, "fragment") else (lambda func: func)


@_fragment_decorator
def render_session_history_fragment():
    st.markdown('<div class="eyebrow">SESSION HISTORY</div>', unsafe_allow_html=True)
    session_history = st.session_state.get("session_history", [])
    if session_history:
        st.markdown(
            f'<div class="history-count">{len(session_history)} RECENT ACTIVITIES · THIS SESSION</div>',
            unsafe_allow_html=True,
        )
        for event in reversed(session_history[-8:]):
            icon = {"match": "✦", "story": "◈", "book": "＋"}.get(event["kind"], "·")
            meta = f' · {html.escape(event["meta"])}' if event.get("meta") else ""
            st.markdown(
                f'<div class="history-item"><strong>{icon} {html.escape(event["title"])}</strong><span>{html.escape(event["detail"])} · {html.escape(event["time"])}{meta}</span></div>',
                unsafe_allow_html=True,
            )
    else:
        st.caption("Your recommendations and Story Desk activity will appear here.")
    st.button(
        "Clear session history",
        key="clear_session_history",
        use_container_width=True,
        on_click=_clear_session_history_callback,
    )
    if st.session_state.pop("history_cleared_notice", False):
        st.success("Session history cleared.")


def render_sidebar(client):
    sync_matchmaker_state()
    selected_genre = st.session_state.get("match_genre", "Fantasy")
    wallpaper = SIDEBAR_WALLPAPERS.get(selected_genre, SIDEBAR_WALLPAPERS["Fantasy"])
    st.markdown(
        f"""
        <style>
        [data-testid="stSidebar"] > div:first-child {{
            background-color: {wallpaper["base"]} !important;
            background-image: {wallpaper["image"]} !important;
            background-size: auto, auto, auto;
            box-shadow: inset -1px 0 0 rgba(255,255,255,.03);
        }}
        [data-testid="stSidebar"] > div:first-child::after {{
            content: "";
            position: absolute;
            inset: 0;
            pointer-events: none;
            border-right: 1px solid {wallpaper["accent"]}22;
            box-shadow: inset 0 0 80px {wallpaper["accent"]}0d;
        }}
        [data-testid="stSidebar"] .eyebrow {{
            color: {wallpaper["accent"]} !important;
        }}
        </style>
        """,
        unsafe_allow_html=True,
    )
    with st.sidebar:
        st.markdown('<div class="eyebrow">VIBE SANCTUARY</div>', unsafe_allow_html=True)
        st.markdown("### Your reading room")
        st.caption(f"Theme · {selected_genre}")
        if st.session_state.get("page_navigation") == "Story Desk":
            st.session_state.page_navigation = "My Books"
        page = st.radio(
            "Open",
            ["Matchmaker", "My Books", "Book Chat"],
            format_func=lambda value: {
                "Matchmaker": "✦  Matchmaker",
                "My Books": "♡  My Books",
                "Book Chat": "◈  Book Chat",
            }[value],
            key="page_navigation",
            on_change=sync_matchmaker_state,
        )
        if page == "My Books":
            st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
            st.markdown('<div class="eyebrow">YOUR SHELF</div>', unsafe_allow_html=True)
            count = len(st.session_state.books)
            st.caption(f"{count} {'book' if count == 1 else 'books'} on your cover shelf")
            return page
        if page == "Book Chat":
            st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
            st.markdown('<div class="eyebrow">OPEN CONVERSATION</div>', unsafe_allow_html=True)
            st.caption("Ask naturally. The chat can roleplay, explain, compare, and share reading data.")
            return page
        st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">AI ENGINE</div>', unsafe_allow_html=True)
        if client:
            st.markdown('<span class="status-pill">● GEMINI CONNECTED</span>', unsafe_allow_html=True)
            st.caption(f"Using {model_name()} · stable flash model recommended for matching and story help.")
        elif not HAS_GENAI:
            st.error("The Gemini package is not installed.")
        else:
            st.warning("No Gemini key is available in this workflow.")
            st.caption("The app will not invent recommendations or story facts when the engine is offline.")
        st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
        st.markdown('<div class="eyebrow">YOUR LIBRARY</div>', unsafe_allow_html=True)
        count = len(st.session_state.books)
        st.markdown(f"**{count}** {'book' if count == 1 else 'books'} saved in My Books")
        if count:
            for book in st.session_state.books[:5]:
                st.markdown(
                    f'<div class="book-list-item"><strong>{html.escape(book["title"])}</strong><span>Chapter {book["chapter"]}</span></div>',
                    unsafe_allow_html=True,
                )
        else:
            st.caption("Add a book on My Books to keep its context close.")
        st.markdown('<div class="rule"></div>', unsafe_allow_html=True)
        render_session_history_fragment()
        return page


def render_matchmaker(client):
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">✦ YOUR NEXT OBSESSION, CURATED</div>
            <h1>Find the feeling.</h1>
            <p class="hero-subtitle">Tell us the atmosphere you want to disappear into. Mix genres, invent your own tropes, and get three thoughtful matches instead of one obvious answer.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    st.session_state.setdefault("match_genre", "Fantasy")
    st.session_state.setdefault("match_genre_blend", "")
    st.session_state.setdefault("match_mood", "")
    st.session_state.setdefault("match_tropes", [])
    st.session_state.setdefault("match_pacing", 5)
    st.session_state.setdefault("match_tone", 6)
    for widget_key, state_key in (
        ("_match_genre", "match_genre"),
        ("_match_genre_blend", "match_genre_blend"),
        ("_match_mood", "match_mood"),
        ("_match_tropes", "match_tropes"),
        ("_match_pacing", "match_pacing"),
        ("_match_tone", "match_tone"),
    ):
        if widget_key not in st.session_state:
            st.session_state[widget_key] = st.session_state[state_key]

    input_column, output_column = st.columns([1.02, .98], gap="large")
    with input_column:
        st.markdown('<div class="section-kicker">01 · Tune the signal</div>', unsafe_allow_html=True)
        st.markdown("### Build your reading atmosphere")
        genre = st.selectbox(
            "Genre room",
            list(GENRES),
            key="_match_genre",
            help="This sets the starting point, not a limit. Your mood and custom choices matter just as much.",
        )
        st.session_state.match_genre = genre
        genre_blend = st.text_input(
            "Or write a genre blend",
            placeholder="e.g. gothic fantasy + literary mystery",
            key="_match_genre_blend",
            help="Optional: type a hybrid or niche genre if the room above is not quite right.",
        )
        theme = SIDEBAR_WALLPAPERS[genre]
        st.markdown(
            f"""
            <style>
            :root {{
                --genre-accent: {theme["accent"]};
                --genre-glow: {theme["accent"]}2e;
            }}
            .stApp {{
                background: {theme["background"]} !important;
            }}
            .stApp::before {{
                background-image: {theme["image"]} !important;
                opacity: .72 !important;
            }}
            .stSlider [role="slider"] {{
                background: {theme["accent"]} !important;
                border-color: {theme["accent"]} !important;
                box-shadow: 0 0 0 4px {theme["accent"]}2e !important;
            }}
            </style>
            """,
            unsafe_allow_html=True,
        )
        icon, description = GENRES[genre]
        st.markdown(
            f'<div class="genre-signal"><div class="genre-signal-icon">{icon}</div><div class="genre-signal-copy"><strong>{html.escape(genre_blend.strip() or genre)} room</strong><span>{html.escape(description)} · every field below can be customized</span></div></div>',
            unsafe_allow_html=True,
        )
        with st.form("vibe_match_form", clear_on_submit=False):
            mood = st.text_area(
                "Describe the mood",
                placeholder="Rainy midnight in an overgrown Victorian library, velvet jackets, a secret society with impeccable manners…",
                height=115,
                key="_match_mood",
                help="Specific sensory details give better answers than a genre label alone. Name specific elements (e.g. 'vampires') directly for the strongest match.",
            )
            moodboard = st.file_uploader(
                "Moodboard image",
                type=["jpg", "jpeg", "png", "webp"],
                help="Optional visual reference for palette, setting, and atmosphere.",
            )
            voice_prompt = st.audio_input(
                "Spoken vibe note",
                help="Record your vibe, then stop recording to transcribe it.",
            )
            st.markdown('<div class="small-mono" style="margin:1rem 0 .4rem;">TROPE ALCHEMY · CHOOSE OR TYPE YOUR OWN</div>', unsafe_allow_html=True)
            tropes = st.multiselect(
                "Tropes and themes",
                TROPE_LIBRARY,
                accept_new_options=True,
                placeholder="Select a suggestion or type a niche trope and press Enter…",
                key="_match_tropes",
                help="Custom entries are fully included in the AI prompt. Press Enter after typing to add it.",
            )
            left, right = st.columns(2)
            with left:
                pacing = st.slider(
                    "Pacing",
                    1, 10,
                    key="_match_pacing",
                    help="1 is slow-blooming and immersive; 10 is breathless and propulsive.",
                )
                st.caption(f"{PACE_LABELS[0].title()}  ·  {PACE_LABELS[-1].title()}")
            with right:
                tone = st.slider(
                    "Emotional tone",
                    1, 10,
                    key="_match_tone",
                    help="1 is tender and light; 10 is intense and dark.",
                )
                st.caption(f"{TONE_LABELS[0].title()}  ·  {TONE_LABELS[-1].title()}")
            submitted = st.form_submit_button("✦ Find my three matches", use_container_width=True)
        audio_bytes = voice_prompt.getvalue() if voice_prompt else None
        audio_type = getattr(voice_prompt, "type", "audio/wav") if voice_prompt else "audio/wav"
        voice_transcript = ""
        if audio_bytes:
            audio_hash = hashlib.sha256(audio_bytes).hexdigest()
            transcript_key = f"voice_transcript_{audio_hash}"
            if transcript_key not in st.session_state:
                if client:
                    with st.spinner("Transcribing your voice note…"):
                        try:
                            st.session_state[transcript_key] = transcribe_audio(
                                client,
                                audio_bytes,
                                audio_type,
                            )
                        except Exception as error:
                            st.session_state[transcript_key] = ""
                            st.warning(f"Could not transcribe the voice note: {error}")
                else:
                    st.session_state[transcript_key] = ""
            voice_transcript = st.session_state.get(transcript_key, "")
            if voice_transcript:
                st.text_area(
                    "Transcript sent with your prompt",
                    value=voice_transcript,
                    height=90,
                    disabled=True,
                    key=f"voice_transcript_display_{audio_hash}",
                )
                st.caption("This transcript will be included with your mood and sent to Gemini.")
            elif not client:
                st.info("Connect Gemini to transcribe the recorded voice note.")
        st.session_state.match_genre_blend = genre_blend
        st.session_state.match_mood = mood
        st.session_state.match_tropes = tropes
        st.session_state.match_pacing = pacing
        st.session_state.match_tone = tone
        if submitted:
            has_voice_signal = bool(audio_bytes or voice_transcript)
            if not client:
                st.error("Connect Gemini in the sidebar before asking for live recommendations.")
            elif not mood.strip() and not tropes and not genre_blend.strip() and not has_voice_signal:
                st.warning("Give the signal a little more to read: add a mood, a trope, or both.")
            else:
                with st.spinner("Reading the shelves for your signal…"):
                    try:
                        matches, debug_prompt = recommend_books(
                            client, genre, tropes, mood, pacing, tone, genre_blend.strip(),
                            image_bytes=moodboard.getvalue() if moodboard else None,
                            audio_bytes=audio_bytes,
                            audio_transcript=voice_transcript,
                            audio_type=audio_type,
                        )
                        if matches:
                            st.session_state.matches = matches[:3]
                            st.session_state.match_meta = {
                                "genre": genre,
                                "has_image": bool(moodboard),
                                "has_audio": bool(audio_bytes),
                                "has_transcript": bool(voice_transcript),
                            }
                            st.session_state.last_debug_prompt = debug_prompt
                            record_session_event(
                                "match",
                                f"{genre} match",
                                mood.strip() or genre_blend.strip() or "Custom reading signal",
                                f"{len(matches[:3])} recommendations",
                            )
                        else:
                            st.error("Gemini returned an unreadable answer. Try again with a more specific mood.")
                    except Exception as error:
                        st.error(f"Gemini could not complete the match: {error}")
    with output_column:
        st.markdown('<div class="section-kicker">02 · Read the signal</div>', unsafe_allow_html=True)
        st.markdown("### Your next chapters")
        if st.session_state.matches:
            meta = st.session_state.get("match_meta", {})
            extra = []
            if meta.get("has_image"):
                extra.append("image read")
            if meta.get("has_transcript"):
                extra.append("voice transcript read")
            if extra:
                st.caption("✦ Multimodal signal received · " + " · ".join(extra))
            for index, book in enumerate(st.session_state.matches, start=1):
                render_result_card(book, index)
            with st.expander("🔍 Debug: exact prompt sent to Gemini", expanded=False):
                st.caption("If a match seems off, check here first — this is exactly what the model received and returned.")
                st.code(st.session_state.get("last_debug_prompt", ""), language="text")
                st.json(st.session_state.matches)
        else:
            st.markdown(
                """
                <div class="glass-card empty-state">
                    <div>
                        <div class="empty-icon">☾</div>
                        <div style="color:#e9ddf6; font:600 1.25rem 'Playfair Display',serif;">Your next story is listening.</div>
                        <div style="margin-top:.45rem;">Describe a feeling on the left<br>and let the signal find its books.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_story_desk(client):
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">◈ STORY DESK · SPOILER-FREE BY DESIGN</div>
            <h1>Stay inside<br>the story.</h1>
            <p class="hero-subtitle">Add any book you are reading, tell us where you are, and get a recap, character refresher, or careful answer without stepping past your chapter.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    add_column, desk_column = st.columns([.86, 1.14], gap="large")
    with add_column:
        st.markdown('<div class="section-kicker">01 · Add a book</div>', unsafe_allow_html=True)
        st.markdown("### Bring your own story")
        st.caption("No pre-filled titles. Your library belongs to you.")
        with st.form("add_book_form", clear_on_submit=True):
            title = st.text_input("Book title", placeholder="The book on your nightstand")
            author = st.text_input("Author", placeholder="Author name (optional)")
            chapter_col, total_col = st.columns(2)
            with chapter_col:
                chapter = st.number_input("Current chapter", min_value=1, max_value=5000, value=1)
            with total_col:
                total_chapters = st.number_input("Total chapters", min_value=0, max_value=5000, value=0, help="Optional; leave 0 if unknown.")
            notes = st.text_area(
                "Your context so far",
                placeholder="Paste your notes, a chapter outline, or details you want Story Desk to remember…",
                height=155,
                help="This helps the assistant with less famous or newly released books. Add only what you are comfortable sharing.",
            )
            add_submitted = st.form_submit_button("＋ Save to Story Desk", use_container_width=True)
        if add_submitted:
            if not title.strip():
                st.warning("Add a title first.")
            else:
                result = add_book(title, author, int(chapter), int(total_chapters), notes)
                record_session_event(
                    "book",
                    title.strip(),
                    "Book added to Story Desk" if result == "added" else "Book details updated",
                    f"Chapter {int(chapter)}",
                )
                st.success("Book updated." if result == "updated" else "Book added to Story Desk.")
                st.rerun()
        if st.session_state.books:
            st.markdown('<div class="small-mono" style="margin-top:1.7rem;">YOUR BOOKS</div>', unsafe_allow_html=True)
            for index, book in enumerate(st.session_state.books):
                label = f'{book["title"]} · ch. {book["chapter"]}'
                if st.button(label, key=f"select_book_{index}", use_container_width=True):
                    st.session_state.active_book_index = index
                    st.session_state.story_output = None
                    st.rerun()
    with desk_column:
        st.markdown('<div class="section-kicker">02 · Open the desk</div>', unsafe_allow_html=True)
        if not st.session_state.books:
            st.markdown(
                """
                <div class="glass-card empty-state" style="min-height:430px;">
                    <div>
                        <div class="empty-icon">⌂</div>
                        <div style="color:#e9ddf6; font:600 1.25rem 'Playfair Display',serif;">A quiet desk, for now.</div>
                        <div style="margin-top:.45rem;">Add a book on the left to unlock<br>recaps and spoiler-safe help.</div>
                    </div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            return
        active_index = min(st.session_state.get("active_book_index", 0), len(st.session_state.books) - 1)
        st.session_state.active_book_index = active_index
        active_book = st.session_state.books[active_index]
        book_title = f'{active_book["title"]} · {active_book["author"]}' if active_book.get("author") else active_book["title"]
        selected = st.selectbox(
            "Book in focus",
            range(len(st.session_state.books)),
            index=active_index,
            format_func=lambda index: st.session_state.books[index]["title"],
        )
        if selected != active_index:
            st.session_state.active_book_index = selected
            st.session_state.story_output = None
            st.rerun()
        progress_col, update_col = st.columns([1, 1])
        with progress_col:
            current_chapter = st.number_input(
                "I am on chapter",
                min_value=1,
                max_value=5000,
                value=int(active_book.get("chapter", 1)),
                key=f"progress_{active_index}",
            )
        with update_col:
            st.markdown("<div style='height:1.8rem'></div>", unsafe_allow_html=True)
            if st.button("Save progress", key="save_progress", use_container_width=True):
                active_book["chapter"] = int(current_chapter)
                st.toast("Progress saved.")
                st.rerun()
        st.caption(f'In focus: **{book_title}** · Story Desk will not intentionally cross chapter {current_chapter}.')
        task = st.radio(
            "What would you like?",
            ["Recap what I've read", "Refresh a character", "Explain the world", "Ask a spoiler-safe question"],
            horizontal=True,
            key="story_task",
        )
        question = ""
        if task == "Ask a spoiler-safe question":
            question = st.text_area("Your question", placeholder="Why did they make that choice?", height=90)
        updated_notes = st.text_area(
            "Private reading context",
            value=active_book.get("notes", ""),
            placeholder="Add notes or paste a passage summary to ground the answer…",
            height=120,
            key=f"notes_{active_index}",
        )
        if st.button("✦ Open the story desk", use_container_width=True):
            if not client:
                st.error("Connect Gemini in the sidebar before asking for story help.")
            elif task == "Ask a spoiler-safe question" and not question.strip():
                st.warning("Write a question for the desk.")
            else:
                active_book["chapter"] = int(current_chapter)
                active_book["notes"] = updated_notes
                with st.spinner("Checking the story boundary before answering…"):
                    try:
                        answer = story_assistant(
                            client, active_book, int(current_chapter),
                            task, question.strip(), updated_notes,
                        )
                        st.session_state.story_output = {
                            "task": task,
                            "chapter": int(current_chapter),
                            "text": answer,
                        }
                        record_session_event(
                            "story",
                            active_book["title"],
                            task if task != "Ask a spoiler-safe question" else question.strip(),
                            f"Chapter {int(current_chapter)}",
                        )
                    except Exception as error:
                        st.error(f"Gemini could not open this story desk: {error}")
        output = st.session_state.get("story_output")
        if output:
            st.markdown(
                f"""
                <div class="story-card">
                    <div class="small-mono">SAFE TO CHAPTER {output["chapter"]} · {html.escape(output["task"].upper())}</div>
                    <div class="story-copy">{html.escape(output["text"]).replace(chr(10), "<br>")}</div>
                    <div class="book-note">✦ LORE GUARD ACTIVE · FUTURE EVENTS ARE OFF LIMITS</div>
                </div>
                """,
                unsafe_allow_html=True,
            )


def render_my_books_legacy(client):
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">♡ MY BOOKS · YOUR LITTLE CONSTELLATION</div>
            <h1>Keep the stories<br>close.</h1>
            <p class="hero-subtitle">Save the books that matter, leave a little starry feeling beside each one, and let your reading life become a shelf worth returning to.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    add_column, shelf_column = st.columns([.78, 1.22], gap="large")
    with add_column:
        st.markdown('<div class="section-kicker">01 · Add to your constellation</div>', unsafe_allow_html=True)
        st.markdown("### Save a book")
        st.caption("Your shelf is personal, session-based, and completely yours.")
        with st.form("my_books_add_form", clear_on_submit=True):
            title = st.text_input("Book title", placeholder="The book on your nightstand")
            author = st.text_input("Author", placeholder="Author name (optional)")
            chapter_col, total_col = st.columns(2)
            with chapter_col:
                chapter = st.number_input("Current chapter", min_value=1, max_value=5000, value=1)
            with total_col:
                total_chapters = st.number_input(
                    "Total chapters", min_value=0, max_value=5000, value=0,
                    help="Optional; leave 0 if unknown.",
                )
            notes = st.text_area(
                "Your context so far",
                placeholder="Notes, a chapter outline, or details you want Book Chat to remember…",
                height=145,
            )
            add_submitted = st.form_submit_button("＋ Save to My Books", use_container_width=True)
        if add_submitted:
            if not title.strip():
                st.warning("Add a title first.")
            else:
                result = add_book(title, author, int(chapter), int(total_chapters), notes)
                record_session_event(
                    "book",
                    title.strip(),
                    "Book saved to My Books" if result == "added" else "Book details updated",
                    f"Chapter {int(chapter)}",
                )
                st.success("Book updated." if result == "updated" else "Book saved to My Books.")
                st.rerun()
    with shelf_column:
        st.markdown('<div class="section-kicker">02 · Your enchanted shelf</div>', unsafe_allow_html=True)
        st.markdown("### All your saved stories")
        if not st.session_state.books:
            st.markdown(
                """
                <div class="shelf-empty">
                    <div class="empty-icon">✧</div>
                    <div style="color:#e9ddf6; font:600 1.35rem 'Playfair Display',serif;">Your shelf is waiting for its first star.</div>
                    <div style="margin-top:.5rem; color:#a99db9;">Add a book on the left and give it a little home here.</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
        else:
            st.caption(f'{len(st.session_state.books)} saved {"story" if len(st.session_state.books) == 1 else "stories"} · rate them whenever the feeling changes')
            shelf_columns = st.columns(2)
            for index, book in enumerate(st.session_state.books):
                with shelf_columns[index % 2]:
                    rating = int(book.get("rating", 0))
                    stars = "★" * rating + "☆" * (5 - rating)
                    author = html.escape(book.get("author") or "Author unknown")
                    title = html.escape(book["title"])
                    current_chapter = int(book.get("chapter", 1))
                    total_chapters = int(book.get("total_chapters", 0))
                    progress = min(100, round(current_chapter / total_chapters * 100)) if total_chapters else 0
                    progress_copy = f"{progress}% of the way through" if total_chapters else f"Chapter {current_chapter}"
                    st.markdown(
                        f"""
                        <div class="library-card">
                            <div class="small-mono">SAVED STORY · {index + 1:02d}</div>
                            <div class="library-card-title">{title}</div>
                            <div class="library-card-author">by {author}</div>
                            <div class="rating-display">{stars}</div>
                            <div class="library-card-meta">{html.escape(progress_copy)}</div>
                        </div>
                        """,
                        unsafe_allow_html=True,
                    )
                    new_rating = st.slider(
                        "Your rating",
                        0, 5, rating,
                        key=f"book_rating_{index}",
                        format="%d / 5 stars",
                        label_visibility="collapsed",
                    )
                    if new_rating != rating:
                        book["rating"] = int(new_rating)
                        record_session_event("book", book["title"], "Rating updated", f"{new_rating}/5 stars")
                        st.toast("Your shelf star is glowing.")
                    chat_action, remove_action = st.columns(2)
                    with chat_action:
                        if st.button("◈ Chat", key=f"chat_about_book_{index}", use_container_width=True):
                            st.session_state.active_book_index = index
                            st.session_state.page_navigation = "Book Chat"
                            st.rerun()
                    with remove_action:
                        if st.button("✕ Remove", key=f"remove_book_{index}", use_container_width=True):
                            removed = remove_book(index)
                            record_session_event("book", removed["title"], "Removed from My Books")
                            st.toast("Removed from your shelf.")
                            st.rerun()


def render_bookstore_map():
    st.markdown('<div class="section-kicker" style="margin-top:2.2rem;">04 · Bookstore cities</div>', unsafe_allow_html=True)
    st.caption("A small constellation of bookish cities around the world — a place-inspired touch, not a claim about any saved book’s setting.")
    st.map(
        BOOKSTORE_CITIES,
        latitude="lat",
        longitude="lon",
        zoom=1,
        height=360,
    )


def render_my_books(client):
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">♡ MY BOOKS · YOUR LITTLE CONSTELLATION</div>
            <h1>Keep the stories<br>close.</h1>
            <p class="hero-subtitle">Add your own books, turn them into beautiful covers, then leave a rating and a few words underneath.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    mood_color_col, mood_copy_col = st.columns([.28, .72], vertical_alignment="center")
    with mood_color_col:
        shelf_mood_color = mood_color_control("Shelf mood color", "my_books_mood_color", "#9d79d8")
    with mood_copy_col:
        st.markdown(
            '<div class="small-mono" style="padding-top:1.5rem;">SET THE SHELF GLOW TO MATCH YOUR MOOD · THIS COLOR STAYS WITH YOUR COVERS</div>',
            unsafe_allow_html=True,
        )
    apply_mood_background(shelf_mood_color, "80% -8%")
    st.markdown('<div class="section-kicker">01 · Add your own book</div>', unsafe_allow_html=True)
    with st.form("simple_add_book_form", clear_on_submit=True):
        title_col, author_col, add_col = st.columns([1.2, 1, .68], vertical_alignment="bottom")
        with title_col:
            title = st.text_input("Book title", placeholder="The book on your nightstand")
        with author_col:
            author = st.text_input("Author", placeholder="Author (optional)")
        with add_col:
            add_submitted = st.form_submit_button("＋ Add to shelf", use_container_width=True)
    if add_submitted:
        if not title.strip():
            st.warning("Add a title first.")
        else:
            result = add_book(title, author, 1, 0, "")
            record_session_event(
                "book",
                title.strip(),
                "Book saved to My Books" if result == "added" else "Book details updated",
            )
            st.toast("Cover added to your shelf." if result == "added" else "Cover details updated.")
            st.rerun()

    st.markdown(
        f"""
        <div class="shelf-intro">
            <div><strong>02 · Your saved covers</strong><span> — rate each book and write your review directly below it.</span></div>
            <div class="shelf-count">{len(st.session_state.books):02d} ON THE SHELF</div>
        </div>
        """,
        unsafe_allow_html=True,
    )
    if not st.session_state.books:
        st.markdown(
            """
            <div class="shelf-empty">
                <div class="empty-icon">✧</div>
                <div style="color:#e9ddf6; font:600 1.35rem 'Playfair Display',serif;">Your first cover is waiting.</div>
                <div style="margin-top:.5rem; color:#a99db9;">Add a book above and give it a little home here.</div>
            </div>
            """,
            unsafe_allow_html=True,
        )
        st.markdown('<div class="section-kicker" style="margin-top:2.2rem;">03 · Quick edit shelf</div>', unsafe_allow_html=True)
        st.caption("Your editable shelf table will fill in as soon as you add a book.")
        st.data_editor(
            pd.DataFrame({
                "Title": pd.Series(dtype="string"),
                "Author": pd.Series(dtype="string"),
                "Chapter": pd.Series(dtype="int64"),
                "Rating": pd.Series(dtype="int64"),
                "Review": pd.Series(dtype="string"),
            }),
            key="my_books_editor_empty",
            hide_index=True,
            num_rows="fixed",
            width="stretch",
            column_config={
                "Title": st.column_config.TextColumn("Title", disabled=True),
                "Author": st.column_config.TextColumn("Author", disabled=True),
                "Chapter": st.column_config.NumberColumn("Chapter", min_value=1, step=1),
                "Rating": st.column_config.NumberColumn("Rating", min_value=0, max_value=5, step=1),
                "Review": st.column_config.TextColumn("Review", width="large"),
            },
        )
        render_bookstore_map()
        return
    cover_palettes = [
        "linear-gradient(145deg, rgba(145,83,206,.94), rgba(35,18,67,.98) 58%, rgba(12,9,25,.98))",
        "linear-gradient(145deg, rgba(194,83,143,.94), rgba(57,18,58,.98) 58%, rgba(18,8,23,.98))",
        "linear-gradient(145deg, rgba(58,128,177,.94), rgba(17,31,65,.98) 58%, rgba(8,10,24,.98))",
        "linear-gradient(145deg, rgba(62,157,145,.94), rgba(12,55,59,.98) 58%, rgba(7,17,22,.98))",
    ]
    cover_columns = st.columns(3)
    for index, book in enumerate(st.session_state.books):
        with cover_columns[index % 3]:
            rating = int(book.get("rating", 0))
            stars = "★" * rating + "☆" * (5 - rating)
            title = html.escape(book["title"])
            author = html.escape(book.get("author") or "Author unknown")
            palette = cover_palettes[index % len(cover_palettes)]
            st.markdown(
                f"""
                <div class="cover-card" style="background:{palette};">
                    <div class="cover-kicker">VIBE SHELF · {index + 1:02d}</div>
                    <div>
                        <div class="cover-title">{title}</div>
                        <div class="cover-author" style="margin-top:.8rem;">{author}</div>
                    </div>
                    <div class="rating-display" style="text-align:center;">{stars}</div>
                </div>
                """,
                unsafe_allow_html=True,
            )
            new_rating = st.slider(
                "Your rating",
                0, 5, rating,
                key=f"simple_book_rating_{index}",
                format="%d / 5 stars",
            )
            if new_rating != rating:
                book["rating"] = int(new_rating)
                record_session_event("book", book["title"], "Rating updated", f"{new_rating}/5 stars")
                st.toast("Rating saved.")
            review = st.text_area(
                "Your review",
                value=book.get("review", ""),
                key=f"book_review_{index}",
                height=105,
                placeholder="What stayed with you?",
            )
            book["review"] = review
            if st.button(
                "Remove from shelf",
                key=f"remove_shelf_book_{index}",
                type="secondary",
                use_container_width=True,
            ):
                removed = remove_book(index)
                record_session_event("book", removed["title"], "Removed from My Books")
                st.toast("Removed from your shelf.")
                st.rerun()

    st.markdown('<div class="section-kicker" style="margin-top:2.2rem;">03 · Quick edit shelf</div>', unsafe_allow_html=True)
    st.caption("Update reading progress, ratings, and reviews in one place. Titles and authors stay locked to protect your saved books.")
    editor_rows = [
        {
            "Title": book["title"],
            "Author": book.get("author") or "Author unknown",
            "Chapter": int(book.get("chapter", 1)),
            "Rating": int(book.get("rating", 0)),
            "Review": book.get("review", ""),
        }
        for book in st.session_state.books
    ]
    editor_signature = "|".join(
        f'{book["title"]}:{book.get("author", "")}' for book in st.session_state.books
    )
    edited_rows = st.data_editor(
        editor_rows,
        key=f"my_books_editor_{len(editor_rows)}_{editor_signature}",
        hide_index=True,
        num_rows="fixed",
        width="stretch",
        column_config={
            "Title": st.column_config.TextColumn("Title", disabled=True),
            "Author": st.column_config.TextColumn("Author", disabled=True),
            "Chapter": st.column_config.NumberColumn("Chapter", min_value=1, step=1),
            "Rating": st.column_config.NumberColumn("Rating", min_value=0, max_value=5, step=1),
            "Review": st.column_config.TextColumn("Review", width="large"),
        },
    )
    if edited_rows != editor_rows:
        for book, edited in zip(st.session_state.books, edited_rows):
            try:
                book["chapter"] = max(1, int(edited.get("Chapter", book.get("chapter", 1))))
            except (TypeError, ValueError):
                pass
            try:
                book["rating"] = min(5, max(0, int(edited.get("Rating", book.get("rating", 0)))))
            except (TypeError, ValueError):
                pass
            book["review"] = str(edited.get("Review", book.get("review", "")) or "")
    render_bookstore_map()


def render_book_chat(client):
    st.markdown(
        """
        <div class="hero">
            <div class="eyebrow">◈ BOOK CHAT · ONE CONVERSATION, MANY WORLDS</div>
            <h1>A room for<br>every story.</h1>
            <p class="hero-subtitle">Ask anything about books, invite a character to speak, request a recommendation, or explore literary facts and reading data. Just type naturally.</p>
        </div>
        """,
        unsafe_allow_html=True,
    )
    mood_color_col, mood_copy_col = st.columns([.28, .72], vertical_alignment="center")
    with mood_color_col:
        chat_mood_color = mood_color_control("Chat mood color", "book_chat_mood_color", "#6f64d8")
    with mood_copy_col:
        st.markdown(
            '<div class="small-mono" style="padding-top:1.5rem;">CHOOSE THE ATMOSPHERE FOR THIS CONVERSATION · YOUR CHAT GLOW IS REMEMBERED</div>',
            unsafe_allow_html=True,
        )
    apply_mood_background(chat_mood_color, "82% -8%")
    messages = st.session_state.get("book_chat_messages", [])
    assistant_name = st.session_state.get("chatbot_name", "Book Chat").strip() or "Book Chat"
    st.markdown('<div class="section-kicker">01 · Open the conversation</div>', unsafe_allow_html=True)
    name_column, top_right = st.columns([.78, .22])
    with name_column:
        assistant_name = st.text_input(
            "Name your chatbot",
            key="chatbot_name",
            max_chars=32,
            placeholder="Book Chat",
            help="Give your book companion any name you like.",
        ).strip() or "Book Chat"
    with top_right:
        if messages and st.button("Clear", key="clear_book_chat", use_container_width=True):
            st.session_state.book_chat_messages = []
            st.rerun()

    st.markdown(
        f"""
        <div class="chat-shell">
            <div class="chat-header">
                <div class="chat-orbit">✦</div>
                <div class="chat-header-copy">
                    <strong>{html.escape(assistant_name)} is listening.</strong>
                    <span>Roleplay, facts, recommendations, deep dives — one open doorway.</span>
                </div>
                <div class="chat-status">● READY</div>
            </div>
        """,
        unsafe_allow_html=True,
    )
    if not messages:
        st.markdown(
            """
            <div class="chat-empty">
                <div class="empty-icon">◈</div>
                <strong>What shall we wander into?</strong>
                <span>Try “become a mysterious librarian,” “compare the data behind reading habits,” or “what should I read after this?”</span>
            </div>
            """,
            unsafe_allow_html=True,
        )
    else:
        for message in messages:
            css_class = "chat-bubble user" if message["role"] == "user" else "chat-bubble"
            label = "YOU" if message["role"] == "user" else html.escape(assistant_name.upper())
            text = html.escape(message["text"]).replace("\n", "<br>")
            st.markdown(
                f'<div class="{css_class}"><div class="small-mono">{label}</div>{text}</div>',
                unsafe_allow_html=True,
            )
    st.markdown("</div>", unsafe_allow_html=True)

    question = st.chat_input("Ask anything about books, roleplay, or reading data…")
    if question:
        if not client:
            st.error("Connect Gemini in the sidebar before opening Book Chat.")
        else:
            st.session_state.book_chat_messages.append({"role": "user", "text": question})
            with st.spinner("The story is gathering its thoughts…"):
                try:
                    answer = book_chat_assistant(
                        client, st.session_state.book_chat_messages[:-1], question, assistant_name,
                    )
                    st.session_state.book_chat_messages.append({"role": "assistant", "text": answer})
                    record_session_event("story", "Book Chat", question, "Open conversation")
                    st.rerun()
                except Exception as error:
                    st.session_state.book_chat_messages.pop()
                    st.error(f"Book Chat could not answer: {error}")


if "books" not in st.session_state:
    st.session_state.books = []
if "match_genre" not in st.session_state:
    st.session_state.match_genre = "Fantasy"
if "match_genre_blend" not in st.session_state:
    st.session_state.match_genre_blend = ""
if "match_mood" not in st.session_state:
    st.session_state.match_mood = ""
if "match_tropes" not in st.session_state:
    st.session_state.match_tropes = []
if "match_pacing" not in st.session_state:
    st.session_state.match_pacing = 5
if "match_tone" not in st.session_state:
    st.session_state.match_tone = 6
if "matches" not in st.session_state:
    st.session_state.matches = None
if "match_meta" not in st.session_state:
    st.session_state.match_meta = {}
if "story_output" not in st.session_state:
    st.session_state.story_output = None
if "active_book_index" not in st.session_state:
    st.session_state.active_book_index = 0
if "session_history" not in st.session_state:
    st.session_state.session_history = []
if "last_debug_prompt" not in st.session_state:
    st.session_state.last_debug_prompt = ""
if "book_chat_messages" not in st.session_state:
    st.session_state.book_chat_messages = []
if "chatbot_name" not in st.session_state:
    st.session_state.chatbot_name = "Book Chat"
if "my_books_mood_color" not in st.session_state:
    st.session_state.my_books_mood_color = "#9d79d8"
if "book_chat_mood_color" not in st.session_state:
    st.session_state.book_chat_mood_color = "#6f64d8"

client = get_client()
page = render_sidebar(client)
if page == "Matchmaker":
    render_matchmaker(client)
elif page == "My Books":
    render_my_books(client)
else:
    render_book_chat(client)
