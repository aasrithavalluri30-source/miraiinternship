import streamlit as st

st.set_page_config(page_title="Calculator", page_icon="🧮", layout="centered")

st.title("🧮 Simple Calculator")

# --- Session state to hold the expression ---
if "expression" not in st.session_state:
    st.session_state.expression = ""

def press(key):
    st.session_state.expression += str(key)

def clear():
    st.session_state.expression = ""

def backspace():
    st.session_state.expression = st.session_state.expression[:-1]

def calculate():
    expr = st.session_state.expression.strip()
    allowed = "0123456789+-*/(). "
    if expr == "" or not all(c in allowed for c in expr):
        st.session_state.expression = "Error"
        return
    try:
        result = eval(expr, {"__builtins__": {}}, {})
        st.session_state.expression = str(result)
    except Exception:
        st.session_state.expression = "Error"

# --- Display screen (plain, not a widget, so no state conflicts) ---
st.markdown(
    f"""
    <div style="
        background-color:#1e1e2e;
        border:1px solid #444;
        border-radius:8px;
        padding:20px;
        text-align:right;
        font-size:32px;
        font-family:monospace;
        color:white;
        min-height:60px;
        margin-bottom:20px;
        overflow-x:auto;
        white-space:nowrap;
    ">
        {st.session_state.expression if st.session_state.expression else "0"}
    </div>
    """,
    unsafe_allow_html=True,
)

# --- Button layout ---
buttons = [
    ["7", "8", "9", "/"],
    ["4", "5", "6", "*"],
    ["1", "2", "3", "-"],
    ["0", ".", "C", "+"],
]

for r, row in enumerate(buttons):
    cols = st.columns(4)
    for c, label in enumerate(row):
        with cols[c]:
            if label == "C":
                st.button(label, key=f"btn_{r}_{c}", on_click=clear, use_container_width=True)
            else:
                st.button(label, key=f"btn_{r}_{c}", on_click=press, args=(label,), use_container_width=True)

col1, col2 = st.columns(2)
with col1:
    st.button("⌫ Backspace", key="btn_backspace", on_click=backspace, use_container_width=True)
with col2:
    st.button("= Calculate", key="btn_calculate", on_click=calculate, use_container_width=True, type="primary")

st.caption("Supports +, -, *, /, decimals, and parentheses.")