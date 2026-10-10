# ! Precision scientific calculator. Run with streamlit run app.py.

import streamlit as st

from ui.components import render

st.set_page_config(
    page_title="Precision Calculator",
    page_icon="🧮",
    layout="centered",
    initial_sidebar_state="collapsed",
)

render()
