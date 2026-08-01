"""
app.py - The Life-OS Wellbeing Dashboard
------------------------------------------
"""

import streamlit as st
import pandas as pd
import json
import base64
import plotly.graph_objects as go
from google import genai
import os
from dotenv import load_dotenv
from pathlib import Path
from datetime import date

env_path = Path(__file__).parent / ".env"
load_dotenv(dotenv_path=env_path, override=True)

st.set_page_config(
    page_title="Life-OS | Wellbeing Dashboard",
    page_icon="🧠",
    layout="wide"
)

# ---------------------------------------------------------------------------
# TIME FORMATTING HELPER
# ---------------------------------------------------------------------------
def format_time(minutes: float) -> str:
    """Converts minutes into 'Xh Ym', 'Xh', or 'Ym' format."""
    m = int(round(minutes))
    hrs = m // 60
    mins = m % 60
    if hrs > 0 and mins > 0:
        return f"{hrs}h {mins}m"
    elif hrs > 0:
        return f"{hrs}h"
    else:
        return f"{mins}m"

# ---------------------------------------------------------------------------
# BACKGROUND WALLPAPER
# ---------------------------------------------------------------------------
@st.cache_data
def get_base64_image(image_path):
    path = Path(image_path)
    if not path.exists():
        return None
    return base64.b64encode(path.read_bytes()).decode()

wallpaper_path = Path(__file__).parent / "wallpaper.png"
wallpaper_b64 = get_base64_image(wallpaper_path)

if wallpaper_b64:
    bg_layer = (
        f'linear-gradient(rgba(14, 17, 23, 0.75), rgba(14, 17, 23, 0.75)), '
        f'url("data:image/png;base64,{wallpaper_b64}")'
    )
    st.markdown(
        f"""
        <style>
        [data-testid="stAppViewContainer"] {{
            background-image: {bg_layer};
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        [data-testid="stSidebar"],
        [data-testid="stSidebarContent"] {{
            background-image: {bg_layer};
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        [data-testid="stHeader"] {{
            background-color: rgba(0, 0, 0, 0);
        }}
        </style>
        """,
        unsafe_allow_html=True
    )
else:
    st.warning("⚠️ wallpaper.png not found next to app.py — background skipped.")

# ---------------------------------------------------------------------------
# DATA INGESTION
# ---------------------------------------------------------------------------
@st.cache_data
def load_data():
    csv_path = Path(__file__).parent / "screentime.csv"
    df = pd.read_csv(csv_path)
    # CRITICAL FIX: Convert Date safely to datetime with format='mixed'
    df["Date"] = pd.to_datetime(df["Date"], format='mixed')
    return df

history_df = load_data()

# ---------------------------------------------------------------------------
# GAMIFICATION & INSIGHTS HELPERS
# ---------------------------------------------------------------------------
CATEGORY_TYPE = {
    "Coding": "Productive",
    "Education": "Productive",
    "Social Media": "Distracting",
    "Entertainment": "Distracting",
    "Other": "Neutral",
}

def compute_productivity_ratio(day_dataframe: pd.DataFrame):
    if day_dataframe.empty:
        return 0, 0, 0.0
    tagged = day_dataframe.copy()
    tagged["Type"] = tagged["Category"].map(CATEGORY_TYPE).fillna("Neutral")
    productive_minutes = tagged.loc[tagged["Type"] == "Productive", "Minutes_Used"].sum()
    total_minutes = tagged["Minutes_Used"].sum()
    ratio = (productive_minutes / total_minutes * 100) if total_minutes > 0 else 0.0
    return productive_minutes, total_minutes, ratio

def compute_time_breakdown(day_dataframe: pd.DataFrame):
    if day_dataframe.empty:
        return 0, 0, 0
    tagged = day_dataframe.copy()
    tagged["Type"] = tagged["Category"].map(CATEGORY_TYPE).fillna("Neutral")
    by_type = tagged.groupby("Type")["Minutes_Used"].sum()
    return (
        by_type.get("Productive", 0),
        by_type.get("Distracting", 0),
        by_type.get("Neutral", 0),
    )

def get_7day_average_by_type(full_history_df: pd.DataFrame, recent_dates, type_name: str):
    if not recent_dates or full_history_df.empty:
        return 0.0
    tagged = full_history_df.copy()
    tagged["Type"] = tagged["Category"].map(CATEGORY_TYPE).fillna("Neutral")
    subset = tagged[(tagged["Date"].dt.date.isin(recent_dates)) & (tagged["Type"] == type_name)]
    daily = subset.groupby(subset["Date"].dt.date)["Minutes_Used"].sum()
    daily = daily.reindex(recent_dates, fill_value=0)
    return daily.mean()

def compute_streak_distracting(full_history_df: pd.DataFrame, goal_minutes: int) -> int:
    """Streak calculation based strictly on Distracting time."""
    if full_history_df.empty or goal_minutes <= 0:
        return 0
    tagged = full_history_df.copy()
    tagged["Type"] = tagged["Category"].map(CATEGORY_TYPE).fillna("Neutral")
    distracting_df = tagged[tagged["Type"] == "Distracting"]
    
    daily_distracting = (
        distracting_df.groupby(distracting_df["Date"].dt.date)["Minutes_Used"]
        .sum()
        .sort_index(ascending=False)
    )
    streak = 0
    for total in daily_distracting:
        if total <= goal_minutes:
            streak += 1
        else:
            break
    return streak

def get_recent_dates(full_history_df: pd.DataFrame, n: int = 7):
    return sorted(full_history_df["Date"].dt.date.unique(), reverse=True)[:n]

def get_7day_average(full_history_df: pd.DataFrame, recent_dates, app_name: str = None):
    if not recent_dates:
        return 0.0
    subset = full_history_df[full_history_df["Date"].dt.date.isin(recent_dates)]
    if app_name is not None:
        subset = subset[subset["App_Name"] == app_name]
    daily = subset.groupby(subset["Date"].dt.date)["Minutes_Used"].sum()
    daily = daily.reindex(recent_dates, fill_value=0)
    return daily.mean()

def pct_change(current: float, average: float):
    if average == 0:
        return None
    return (current - average) / average * 100

# ---------------------------------------------------------------------------
# CONTROLS & SIDEBAR
# ---------------------------------------------------------------------------
TODAY_LABEL = "Today (Live Entry)"

if "tracked_apps" not in st.session_state:
    st.session_state.tracked_apps = {
        "Instagram": "Social Media",
        "TikTok": "Social Media",
        "YouTube": "Entertainment",
        "Spotify": "Entertainment",
        "VS Code": "Coding",
        "Duolingo": "Education",
    }

CATEGORY_OPTIONS = ["Social Media", "Entertainment", "Education", "Coding", "Other"]

st.sidebar.title("⚙️ Controls")

# Manual numeric inputs for distracting time goal limit
st.sidebar.markdown("🎯 **Daily Distracting App Limit**")
goal_col1, goal_col2 = st.sidebar.columns(2)
with goal_col1:
    goal_hrs = st.number_input(
        "Limit Hrs", min_value=0, max_value=24, value=1, step=1, key="goal_hrs_input"
    )
with goal_col2:
    goal_mins = st.number_input(
        "Limit Min", min_value=0, max_value=59, value=0, step=5, key="goal_mins_input"
    )

distracting_goal_minutes = goal_hrs * 60 + goal_mins
st.sidebar.caption(f"Target limit set to: **{format_time(distracting_goal_minutes)}**")
st.sidebar.divider()

with st.sidebar.expander("📱 Record Today's Screentime", expanded=True):
    st.caption("Enter hours & minutes spent on each app today.")

    for app_name, category in st.session_state.tracked_apps.items():
        st.markdown(f"**{app_name}** &nbsp;·&nbsp; _{category}_")
        hr_col, min_col = st.columns(2)
        with hr_col:
            hrs = st.number_input(
                "Hrs", min_value=0, max_value=24, step=1,
                value=st.session_state.get(f"hr_{app_name}", 0),
                key=f"hr_{app_name}"
            )
        with min_col:
            mins = st.number_input(
                "Min", min_value=0, max_value=59, step=1,
                value=st.session_state.get(f"min_input_{app_name}", 0),
                key=f"min_input_{app_name}"
            )
        st.session_state[f"min_{app_name}"] = hrs * 60 + mins

    st.divider()
    st.caption("Track a different app:")

    with st.form("add_app_form", clear_on_submit=True):
        new_app_col, new_cat_col = st.columns([2, 1])
        with new_app_col:
            new_app_name = st.text_input("App name", label_visibility="collapsed", placeholder="e.g. WhatsApp")
        with new_cat_col:
            new_app_category = st.selectbox("Category", CATEGORY_OPTIONS, label_visibility="collapsed")
        add_submitted = st.form_submit_button("+ Add App", use_container_width=True)

        if add_submitted and new_app_name.strip():
            st.session_state.tracked_apps[new_app_name.strip()] = new_app_category
            st.rerun()

    st.divider()

    live_rows = [
        {"App_Name": app_name, "Category": category, "Minutes_Used": st.session_state.get(f"min_{app_name}", 0)}
        for app_name, category in st.session_state.tracked_apps.items()
        if st.session_state.get(f"min_{app_name}", 0) > 0
    ]
    live_entries_df = pd.DataFrame(live_rows, columns=["App_Name", "Category", "Minutes_Used"])

    if st.button("💾 Save Today's Log to History", use_container_width=True):
        total_live_logged = live_entries_df["Minutes_Used"].sum() if not live_entries_df.empty else 0
        
        if total_live_logged == 0:
            st.warning("Nothing to save — please enter usage time greater than 0 first.")
        else:
            csv_path = Path(__file__).parent / "screentime.csv"
            existing_df = pd.read_csv(csv_path)
            # CRITICAL FIX: Convert Date safely with format='mixed'
            existing_df["Date"] = pd.to_datetime(existing_df["Date"], format='mixed')

            # Overwrite today's existing entries if re-saved
            existing_df = existing_df[existing_df["Date"].dt.date != date.today()]

            to_save_df = live_entries_df.copy()
            to_save_df["Date"] = pd.to_datetime(date.today())
            to_save_df = to_save_df[["Date", "App_Name", "Category", "Minutes_Used"]]

            updated_df = pd.concat([existing_df, to_save_df], ignore_index=True)
            updated_df["Date"] = updated_df["Date"].dt.strftime('%Y-%m-%d')
            updated_df.to_csv(csv_path, index=False)

            load_data.clear()

            _, saved_distracting_time, _ = compute_time_breakdown(to_save_df)
            st.success(f"Saved {len(to_save_df)} app(s) for today to screentime.csv ✅")

            if distracting_goal_minutes > 0 and saved_distracting_time <= distracting_goal_minutes:
                st.balloons()

            st.rerun()

st.sidebar.divider()

available_dates = sorted(history_df["Date"].dt.date.unique(), reverse=True)
dropdown_options = [TODAY_LABEL] + [str(d) for d in available_dates]

selected_option = st.sidebar.selectbox(
    "📅 Select a day to review",
    options=dropdown_options,
    index=0
)

# Build day_df
if selected_option == TODAY_LABEL:
    live_df = live_entries_df.copy()
    if not live_df.empty:
        live_df["Date"] = pd.Timestamp(date.today())
    day_df = live_df
    display_date_label = f"{date.today().strftime('%A, %B %d, %Y')} (live entry)"
else:
    selected_date = pd.to_datetime(selected_option).date()
    day_df = history_df[history_df["Date"].dt.date == selected_date]
    display_date_label = selected_date.strftime('%A, %B %d, %Y')

if not live_entries_df.empty:
    live_for_chart = live_entries_df.copy()
    live_for_chart["Date"] = pd.Timestamp(date.today())
    chart_source_df = pd.concat([history_df, live_for_chart], ignore_index=True)
else:
    chart_source_df = history_df

total_minutes_today = day_df["Minutes_Used"].sum() if not day_df.empty else 0

if not day_df.empty:
    most_used_app = day_df.groupby("App_Name")["Minutes_Used"].sum().idxmax()
    most_used_app_minutes = day_df.groupby("App_Name")["Minutes_Used"].sum().max()
else:
    most_used_app = "N/A"
    most_used_app_minutes = 0

recent_dates = get_recent_dates(history_df, n=7)
avg_app_7d = get_7day_average(history_df, recent_dates, app_name=most_used_app)
app_pct_change = pct_change(most_used_app_minutes, avg_app_7d)

productive_minutes_today, distracting_minutes_today, neutral_minutes_today = compute_time_breakdown(day_df)
avg_productive_7d = get_7day_average_by_type(history_df, recent_dates, "Productive")
avg_distracting_7d = get_7day_average_by_type(history_df, recent_dates, "Distracting")
productive_pct_change = pct_change(productive_minutes_today, avg_productive_7d)
distracting_pct_change = pct_change(distracting_minutes_today, avg_distracting_7d)

current_streak = compute_streak_distracting(history_df, distracting_goal_minutes)
distracting_delta_vs_goal = distracting_minutes_today - distracting_goal_minutes

# ---------------------------------------------------------------------------
# DASHBOARD UI & METRICS
# ---------------------------------------------------------------------------
st.title("Life-OS Wellbeing Dashboard")
st.caption(f"Showing data for **{display_date_label}**")

headline_col1, headline_col2, headline_col3 = st.columns(3)

with headline_col1:
    prod_delta_label = f"{productive_pct_change:+.0f}% vs 7-day avg" if productive_pct_change is not None else "No 7-day history yet"
    st.metric(
        label="📚 Productive Time",
        value=format_time(productive_minutes_today),
        delta=prod_delta_label,
        delta_color="normal" if productive_pct_change is not None else "off"
    )

with headline_col2:
    st.metric(
        label="📱 Distracting Time",
        value=format_time(distracting_minutes_today),
        delta=f"{distracting_delta_vs_goal:+d}m vs {format_time(distracting_goal_minutes)} goal",
        delta_color="inverse"
    )
    if distracting_goal_minutes > 0:
        pct_of_goal = min(distracting_minutes_today / distracting_goal_minutes, 1.0)
        st.progress(pct_of_goal, text=f"{int(pct_of_goal * 100)}% of daily limit used")

with headline_col3:
    st.metric(
        label="🔥 Distraction Streak",
        value=f"{current_streak} day{'s' if current_streak != 1 else ''}"
    )

support_col1, support_col2 = st.columns(2)

with support_col1:
    st.metric(
        label="Total Screen Time Today",
        value=format_time(total_minutes_today),
        delta=f"Productive: {format_time(productive_minutes_today)}",
        delta_color="off"
    )

with support_col2:
    app_delta_label = f"{app_pct_change:+.0f}% vs 7-day avg" if app_pct_change is not None else format_time(most_used_app_minutes)
    st.metric(
        label="Most Used App",
        value=f"{most_used_app} ({format_time(most_used_app_minutes)})",
        delta=app_delta_label,
        delta_color="inverse" if app_pct_change is not None else "off"
    )

st.divider()

# ---------------------------------------------------------------------------
# PRODUCTIVITY RATIO
# ---------------------------------------------------------------------------
st.subheader("🎯 Productivity Ratio")

productive_minutes, total_minutes_for_ratio, productivity_ratio = compute_productivity_ratio(day_df)

if total_minutes_for_ratio == 0:
    st.caption("No usage logged for this day yet - nothing to chart.")
else:
    other_minutes = total_minutes_for_ratio - productive_minutes
    donut_fig = go.Figure(data=[go.Pie(
        labels=["Productive", "Distracting / Other"],
        values=[productive_minutes, other_minutes],
        hole=0.65,
        marker=dict(colors=["#00CC96", "#EF553B"]),
        textinfo="label+percent",
        sort=False
    )])
    donut_fig.update_layout(
        showlegend=False,
        margin=dict(t=10, b=10, l=10, r=10),
        height=280,
        annotations=[dict(
            text=f"{productivity_ratio:.0f}%",
            x=0.5, y=0.5,
            font_size=32,
            showarrow=False
        )]
    )
    chart_col, caption_col = st.columns([1, 1])
    with chart_col:
        st.plotly_chart(donut_fig, use_container_width=True)
    with caption_col:
        st.metric("Productive Time", format_time(productive_minutes))
        st.metric("Total Time", format_time(total_minutes_for_ratio))
        st.caption("Productive = Coding & Education. Distracting / Other = Social Media, Entertainment, Other.")

st.divider()

# ---------------------------------------------------------------------------
# VISUALIZATIONS
# ---------------------------------------------------------------------------
st.subheader("📈 Screen Time Trend")

trend_df = (
    chart_source_df.groupby([chart_source_df["Date"].dt.date, "Category"])["Minutes_Used"]
      .sum()
      .unstack(fill_value=0)
)

tab1, tab2 = st.tabs(["Bar Chart", "Line Chart"])
with tab1:
    st.bar_chart(trend_df)
with tab2:
    st.line_chart(trend_df)

st.divider()

# ---------------------------------------------------------------------------
# AI COACHING
# ---------------------------------------------------------------------------
def summarize_day_for_ai(day_dataframe: pd.DataFrame) -> str:
    if day_dataframe.empty:
        return "No screen time data recorded for this day."

    category_summary = day_dataframe.groupby("Category")["Minutes_Used"].sum()
    app_summary = day_dataframe.groupby("App_Name")["Minutes_Used"].sum().sort_values(ascending=False)

    summary_text = "CATEGORY BREAKDOWN:\n"
    for cat, mins in category_summary.items():
        summary_text += f"- {cat}: {format_time(mins)}\n"
    summary_text += "\nAPP BREAKDOWN:\n"
    for app, mins in app_summary.items():
        summary_text += f"- {app}: {format_time(mins)}\n"
    return summary_text

data_summary_string = summarize_day_for_ai(day_df)

st.subheader("💬 Your Coach")

def get_opening_advice(summary: str, goal_minutes: int, distracting_minutes: int):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return None, "⚠️ No GEMINI_API_KEY found. Add it to your .env file to enable AI coaching."

    client = genai.Client(api_key=api_key)
    over_by = max(0, distracting_minutes - goal_minutes)

    prompt = f"""
You are a brutal-but-fair life coach reviewing a client's daily screen time report.

Today's data:
{summary}

Distracting app limit target: {format_time(goal_minutes)}. 
Actual distracting app usage: {format_time(distracting_minutes)}.

Write a short, motivational pep-talk that:
1. Names the SPECIFIC distracting app(s) that ate up the most time today.
2. Analyzes the specific categories used and suggests physical, real-world replacements (e.g., physical fitness, meal prepping, reading, outdoor activities) instead of just saying "use your phone less."
3. Ends on an encouraging note.

Respond ONLY with valid JSON in this shape:
{{
  "headline": "short punchy headline",
  "advice": "motivational paragraph (80-120 words)"
}}
"""
    response = client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
    raw_text = response.text.strip().replace("```json", "").replace("```", "").strip()

    try:
        parsed = json.loads(raw_text)
        return parsed, None
    except json.JSONDecodeError:
        return None, raw_text

def get_chat_reply(question: str, summary: str, prior_messages: list):
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        return "⚠️ No GEMINI_API_KEY found."

    client = genai.Client(api_key=api_key)
    transcript = "\n".join(f"{m['role'].upper()}: {m['content']}" for m in prior_messages)

    prompt = f"""
You are a warm, honest life coach in an ongoing chat with a client about their screen time.

Client's data for today:
{summary}

Conversation so far:
{transcript}

Client asks: "{question}"

Reply directly in 2-4 sentences.
"""
    response = client.models.generate_content(model="gemini-3.5-flash-lite", contents=prompt)
    return response.text.strip()

# Isolated chat session per selected date
date_chat_key = f"coach_messages_{selected_option}"
if date_chat_key not in st.session_state:
    st.session_state[date_chat_key] = []

start_col, _ = st.columns([1, 3])
with start_col:
    start_clicked = st.button("Coaching Session", type="primary", use_container_width=True)

if start_clicked:
    with st.spinner("Your coach is reviewing your data..."):
        advice, error_or_fallback_text = get_opening_advice(
            data_summary_string, distracting_goal_minutes, distracting_minutes_today
        )
    if advice is None:
        st.session_state[date_chat_key] = [{"role": "assistant", "content": error_or_fallback_text}]
    else:
        headline_text = advice.get('headline', "Your Coach's Take")
        advice_text = advice.get('advice', '')
        st.session_state[date_chat_key] = [
            {"role": "assistant", "content": f"**{headline_text}**\n\n{advice_text}"}
        ]

for msg in st.session_state[date_chat_key]:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

if st.session_state[date_chat_key]:
    follow_up = st.chat_input("Ask a follow-up...")
    if follow_up:
        st.session_state[date_chat_key].append({"role": "user", "content": follow_up})
        with st.chat_message("user"):
            st.markdown(follow_up)
        with st.chat_message("assistant"):
            with st.spinner("Thinking..."):
                reply_text = get_chat_reply(
                    follow_up, data_summary_string, st.session_state[date_chat_key]
                )
            st.markdown(reply_text)
        st.session_state[date_chat_key].append({"role": "assistant", "content": reply_text})

st.divider()

# ---------------------------------------------------------------------------
# RECEIPT CARD
# ---------------------------------------------------------------------------
st.subheader("🧾 Your Screentime Receipt")

top_apps_df = (
    day_df.groupby("App_Name")["Minutes_Used"].sum()
    .sort_values(ascending=False)
    .head(3)
)

if top_apps_df.empty:
    st.caption("No usage logged for this day yet.")
else:
    def esc(text):
        return (
            str(text).replace("&", "&amp;").replace("<", "&lt;")
            .replace(">", "&gt;").replace('"', "&quot;")
        )

    app_rows_html = "".join(
        f'<div style="display:flex;justify-content:space-between;font-size:14px;padding:3px 0;">'
        f'<span>{esc(app_name)}</span><span>{format_time(mins)}</span></div>'
        for app_name, mins in top_apps_df.items()
    )

    receipt_html = f"""
    <div style="max-width:340px;margin:16px auto;padding:24px;border-radius:18px;
                background:linear-gradient(135deg,#6a11cb 0%,#2575fc 100%);
                color:white;font-family:'Courier New',monospace;
                box-shadow:0 10px 28px rgba(0,0,0,0.35);">
        <div style="text-align:center;font-size:20px;font-weight:bold;letter-spacing:2px;">
            📱 SCREENTIME RECEIPT
        </div>
        <div style="text-align:center;font-size:12px;opacity:0.8;margin-bottom:14px;">
            {esc(display_date_label)}
        </div>
        <div style="border-top:2px dashed rgba(255,255,255,0.5);margin:10px 0;"></div>
        <div style="font-size:12px;opacity:0.75;margin-bottom:4px;">TOP APPS</div>
        {app_rows_html}
        <div style="border-top:2px dashed rgba(255,255,255,0.5);margin:10px 0;"></div>
        <div style="display:flex;justify-content:space-between;font-weight:bold;font-size:16px;">
            <span>TOTAL SCREEN TIME</span><span>{format_time(total_minutes_today)}</span>
        </div>
        <div style="text-align:center;margin-top:16px;font-size:13px;">
            🎯 Productivity: {productivity_ratio:.0f}% &nbsp;·&nbsp; 🔥 Streak: {current_streak}d
        </div>
    </div>
    """
    st.markdown(receipt_html, unsafe_allow_html=True)

st.divider()

# ---------------------------------------------------------------------------
# ACCOUNTABILITY LINK
# ---------------------------------------------------------------------------
st.subheader("🔗 Accountability Link")

st.query_params["total"] = str(total_minutes_today)
st.query_params["date"] = str(display_date_label)
st.query_params["distracting_goal"] = str(distracting_goal_minutes)

st.code(f"?total={total_minutes_today}&date={display_date_label}&goal={distracting_goal_minutes}", language="text")
