import streamlit as st
st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="collapsed", menu_items=None)

import os
import base64
from pages._2_qc import show_qc
from pages._14_cohort import show_cohort
from streamlit_navigation_bar import st_navbar

def show_home():
    file_ = open("assets/logos.gif", "rb")
    contents = file_.read()
    data_url = base64.b64encode(contents).decode("utf-8")
    file_.close()

    st.markdown(
    f'<div style="text-align: center;"><img src="data:image/gif;base64,{data_url}" style="width:1000px; height:50;"></div>',
    unsafe_allow_html=True,
    )

    pg1, pg2, pg3 = st.columns([1, 1, 1], gap="large")
    with pg1:
        _, qc_p2, _ = st.columns([0.5, 2, 0.5], gap="small")
        with qc_p2:
            st.image("assets/QC.png", use_column_width=True)
        _, qc_p2_a, _ = st.columns([0.5, 2, 0.5], gap="small")
        with qc_p2_a:
            st.title("Quality Controls")
        _, qc_p2_b, _ = st.columns([0.15, 2, 0.15], gap="small")
        with qc_p2_b:    
            st.write("""
    Our Quality Controls feature is designed to streamline your data validation processes, reduce errors, and ensure that your data is always research-ready. QCs are available for:

    - **ADT**
    - **Hospitalization**
    - **Labs**
    - **Medication**
    - **Microbiology**
    - **Patient**
    - **Patient Assessment**
    - **Position**
    - **Respiratory Support**
    - **Vitals**

                    """)
        
    with pg2:
        _, vm_p2, _ = st.columns([0.5, 2, 0.5], gap="small")
        with vm_p2:
            st.image("assets/Vocab_map.png", use_column_width=True)
        _, vm_p2_a, _ = st.columns([0.35, 2, 0.05], gap="small")
        with vm_p2_a:
            st.title("Vocabulary Mapping")
            st.write("""Coming Soon!""")
            
    with pg3:
        _, cd_p2, _ = st.columns([0.5, 2, 0.5], gap="small")
        with cd_p2:
            st.image("assets/Cohort_dsicover.png", use_column_width=True)
        _, cd_p2_a, _ = st.columns([0.45, 2, 0.01], gap="small")
        with cd_p2_a:
            st.title("Cohort Discovery")
            st.write("""Coming Soon!""")

parent_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(parent_dir, "assets/Picture1.svg")
page = ["Home", "Quality Controls", "Vocabulary Mapping", "Cohort Discovery"]
styles = {
    "nav": {
        "background-color": "#2e3a59",
        "display": "flex",
        "justify-content": "space-between",
        "align-items": "center",
        "padding": "10px 0",  # Adjust padding to increase nav bar height
        "height": "70px",
        "font-size": "1.2em",
    },
    "img": {
        "padding-right": "0px",
        "height": "150px",
        "padding-bottom": "15px",
    },
    "span": {
        "color": "white",
        "padding": "14px",
        "flex": "1",
        "text-align": "center",
        "white-space": "nowrap",
        "font-size": "1.0em",
        
    },
    "active": {
        "background-color": "#3a4a6f",
        "color": "white",
        "padding": "20px 30px",
        "border-radius": "5px",
    }
}
options = {
    "show_menu": True,
    "show_sidebar": True,
}

selected_page = st_navbar(page, styles=styles, logo_path=logo_path, options=options)

functions = {
    "Home": show_home,
    "Quality Controls": show_qc,
    "Vocabulary Mapping": None,
    "Cohort Discovery": show_cohort,
}
go_to = functions.get(selected_page)
if go_to:
    go_to()

