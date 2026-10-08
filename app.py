"""Mini Project DS - simple Streamlit market analytics dashboard."""

from __future__ import annotations

from datetime import date, timedelta
from io import BytesIO
from pathlib import Path
from zipfile import ZIP_DEFLATED, ZipFile

import pandas as pd
import streamlit as st

from modules.data_provider import filter_data, get_data


PROJECT_ROOT = Path(__file__).parent
COLLEGE = "SMT. Maherbanu College of Science & Commerce, Akola"
GUIDED_BY = "Rasika Mam"
STUDENT = "Ashishsingh Thakur"
DEPARTMENT = "BCA 3rd Year"

st.set_page_config(page_title="Ankur - AI Assistant", page_icon="📊", layout="wide")


def make_project_zip() -> bytes:
    """Package the clean student project for the download button."""
    files = {
        "app.py": PROJECT_ROOT / "app.py",
        "requirements.txt": PROJECT_ROOT / "requirements.txt",
        "README.md": PROJECT_ROOT / "project_readme.md",
        "modules/__init__.py": PROJECT_ROOT / "modules/__init__.py",
        "modules/data_provider.py": PROJECT_ROOT / "modules/data_provider.py",
        "data/README.md": PROJECT_ROOT / "data/README.md",
    }
    archive = BytesIO()
    with ZipFile(archive, "w", ZIP_DEFLATED) as project_zip:
        for name, path in files.items():
            if path.exists():
                project_zip.writestr(name, path.read_text(encoding="utf-8"))
    return archive.getvalue()


def sidebar() -> tuple[str, bool, str]:
    """Render the reference sidebar and return the selected controls."""
    with st.sidebar:
        st.markdown("# Ankur Mini Project")
        st.markdown(f"College: {COLLEGE}")
        st.markdown(f"Department: {DEPARTMENT}")
        st.markdown(f"Guided By: {GUIDED_BY}")
        st.markdown("Project By: Ankur")
        st.markdown("Project: Mini Project - AI Assistant")
        st.markdown("---")
        st.markdown(f"College: {COLLEGE}")
        st.markdown(f"Guided By: {GUIDED_BY}")
        st.markdown(f"Student: {STUDENT}")
        st.markdown(f"Department: {DEPARTMENT}")
        st.markdown("---")
        page = st.radio("Select Page", ["Chat", "About Project"], key="page")
        st.markdown("### Data Source")
        live = st.toggle("Live Data (yfinance)", value=False, key="live-data-toggle")
        symbol = st.text_input("Ticker symbol", value="AAPL", key="ticker-symbol").strip().upper()
        st.download_button(
            "Download Project ZIP",
            data=make_project_zip(),
            file_name="Mini_Project(DS).zip",
            mime="application/zip",
            key="download-zip-btn",
            use_container_width=True,
        )
    return page, live, symbol or "AAPL"


def show_timeframe(frame: pd.DataFrame) -> pd.DataFrame:
    """Render the timeframe controls and return the filtered rows."""
    st.subheader("TimeFrame")
    timeframe = st.radio(
        "Select duration",
        ["Weekly", "Monthly", "Yearly", "Custom Duration"],
        horizontal=True,
        key="timeframe-selection",
    )
    last_date = frame["Date"].max().date()
    if timeframe == "Custom Duration":
        first_date = st.date_input(
            "Start Date", value=last_date - timedelta(days=6), key="custom-start-date"
        )
        final_date = st.date_input("End Date", value=last_date, key="custom-end-date")
        if first_date > final_date:
            st.error("Start Date must be before End Date.")
            return frame.iloc[0:0]
        selected = filter_data(frame, timeframe, first_date, final_date)
    else:
        selected = filter_data(frame, timeframe)
    if selected.empty:
        st.warning("No data is available for this duration.")
        return selected
    st.write(
        f"Showing data from {selected['Date'].min():%d %b %Y} "
        f"to {selected['Date'].max():%d %b %Y}"
    )
    st.line_chart(selected.set_index("Date")["Close"], height=350, use_container_width=True)
    return selected


def chat_page(live: bool, symbol: str) -> None:
    """Render the original chat page with a data-backed timeframe chart."""
    st.title("AI Assistant")
    st.write("Ask a simple question and I will try to help you.")
    frame, mode, error = get_data(symbol, live)
    if mode == "demo":
        st.info("Demo data is active. Enable Live Data to request yfinance values.")
    elif mode == "live":
        st.success(f"Live data loaded for {symbol}.")
    else:
        st.warning(f"Live data was unavailable, so demo data is shown instead ({error}).")
    filtered = show_timeframe(frame)
    if not filtered.empty:
        latest = filtered.iloc[-1]
        previous = filtered.iloc[-2] if len(filtered) > 1 else latest
        first, second, third = st.columns(3)
        first.metric("Latest Close", f"${latest['Close']:,.2f}")
        second.metric("Range Change", f"{latest['Close'] - previous['Close']:+,.2f}")
        third.metric("Rows", f"{len(filtered):,}")
    if "messages" not in st.session_state:
        st.session_state.messages = []
    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.write(message["content"])
    question = st.chat_input("Type your question here")
    if question:
        st.session_state.messages.append({"role": "user", "content": question})
        answer = "This student project can show demo market data, timeframe charts, and project details."
        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()
    if st.button("Clear Chat", key="clear-chat-btn"):
        st.session_state.messages = []
        st.rerun()


def about_page() -> None:
    """Render the simple About Project page from the reference app."""
    st.title("About Project")
    st.write("This AI assistant helps students.")
    st.write("The application is made using basic Python and Streamlit.")
    st.write("It gives simple answers to common questions about Python, Streamlit, and the project.")
    st.subheader("Project Information")
    st.write(f"College: {COLLEGE}")
    st.write(f"Department: {DEPARTMENT}")
    st.write(f"Guided By: {GUIDED_BY}")
    st.write("Project By: Ankur")
    st.write(f"College: {COLLEGE}")
    st.write(f"Guided By: {GUIDED_BY}")
    st.write(f"Student: {STUDENT}")
    st.write(f"Department: {DEPARTMENT}")


selected_page, live_data, ticker = sidebar()
if selected_page == "About Project":
    about_page()
else:
    chat_page(live_data, ticker)