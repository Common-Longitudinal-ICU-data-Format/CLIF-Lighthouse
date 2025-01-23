import streamlit as st
st.set_page_config(page_title=None, page_icon=None, layout="wide", initial_sidebar_state="collapsed", menu_items=None)

import os
import logging
from streamlit_navigation_bar import st_navbar
from logging_config import setup_logging
# from common_features import set_bg_hack_url
from common_qc import read_data
from pages._3_adt_qc import show_adt_qc
from pages._4_hosp_qc import show_hosp_qc
from pages._5_labs_qc import show_labs_qc
from pages._6_med_qc import show_meds_qc
from pages._7_microbio_qc import show_microbio_qc
from pages._8_patient_qc import show_patient_qc
from pages._9_patient_assess_qc import show_patient_assess_qc
from pages._10_position_qc import show_position_qc
from pages._11_resp_qc import show_respiratory_support_qc
from pages._12_vitals_qc import show_vitals_qc

def show_home():
    # Initialize logger
    setup_logging()
    logger = logging.getLogger(__name__)

    _, main_qc_form, _ = st.columns([1, 3, 1])

    with main_qc_form:

        st.title("Quality Controls")

        with st.form(key='main_form', clear_on_submit=False):

            st.write("""
                    Welcome to LightHouse! Our Quality Controls feature is designed to streamline your data validation processes, reduce errors, and ensure that your data is always research-ready. QCs are available for:
                        """)
            c1, c2, c3, c4, c5 = st.columns(5)
            with c1:
                    st.write("""
                    - **ADT**
                    - **Hospitalization**
                    """)
            with c2:
                    st.write("""
                    - **Labs**
                    - **Medication**
                    """)
            with c3:
                    st.write("""
                    - **Patient**
                    - **Patient Assessment**
                    """)
            with c4:
                    st.write("""
                    - **Position**
                    - **Respiratory Support**
                    """)
            with c5:
                    st.write("""
                    - **Vitals**
                    """)
            
            files = st.file_uploader(
                "Select one or more files", 
                accept_multiple_files=True, 
                type=["csv", "parquet", "fst"]
            )

            # Sampling option
            s_col1, _, _, _ = st.columns(4)
            with s_col1:
                sampling_option = st.number_input("Set dataset sample(%) for QC ***(optional)***", min_value=1, max_value=100, value=None, step=5)
            download_path = st.text_input("Enter path to save automated downloads of generated tables and images ***(optional)***", value=None)

            submit = st.form_submit_button(label='Submit')

        if submit:
            st.info("Note that a new tab will not load until the current tab has finished loading. " \
                "The overall progress of the quality control checks will be displayed. For detailed progress information, please expand the required table in the QC section.", 
                icon="ℹ️")
            with st.spinner('Loading...'):
                if files:
                    st.session_state["files"] = "Yes"
                    try:
                        for file in files:
                            df = read_data(file)
                            table_name = file.name.split('.')[0]
                            st.session_state[table_name] = df
                    except Exception as e:
                        st.write("Error: No files were submitted or an issue occurred while processing the files.")
                        st.write(f"Details: {e}")

                st.session_state['sampling_option'] = None
                if sampling_option:
                    logger.info(f"Sampling option selected: {sampling_option}")
                    st.session_state['sampling_option'] = sampling_option
                
                st.session_state['download_path'] = None
                if download_path:
                    logger.info(f"Download path option selected: {download_path}")
                    st.session_state['download_path'] = download_path

            logger.info("Loading QC results page")
            # tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(["ADT", 
            #     "Hospitalization", "Labs", "Medication", "Microbiology", "Patient", 
            #     "Patient Assessment", "Position", "Respiratory Support", "Vitals"])
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9 = st.tabs(["ADT", 
                "Hospitalization", "Labs", "Medication", "Patient", 
                "Patient Assessment", "Position", "Respiratory Support", "Vitals"])

            with tab1:
                show_adt_qc()

            with tab2:
                show_hosp_qc()

            with tab3:
                show_labs_qc()

            with tab4:
                show_meds_qc()

            # with tab5:
            #     show_microbio_qc()

            with tab5:
                show_patient_qc()

            with tab6:
                show_patient_assess_qc()

            with tab7:
                show_position_qc()

            with tab8:
                show_respiratory_support_qc()

            with tab9:
                show_vitals_qc()

  
parent_dir = os.path.dirname(os.path.abspath(__file__))
logo_path = os.path.join(parent_dir, "assets/Picture1.svg")
page = [""]
styles = {
    "nav": {
        "background-color": "#2e3a59",
        "display": "flex",
        "justify-content": "right",  # Center the content horizontally
        "align-items": "right",  # Center the content vertically
        "padding": "10px 0",  # Adjust padding to increase nav bar height
        "height": "100px",
        "font-size": "1.2em",
    },
    "img": {
        "position": "absolute",  # Allow positioning relative to the nav
        "left": "50%",  # Center horizontally
        "top": "50%",   # Center vertically
        "transform": "translate(-50%, -50%)",
        "height": "150px",  # Adjust the logo size to fit the navbar
    },
    "span": {
        "color": "white",
        "font-size": "1.0em",
        "white-space": "nowrap"
    }
}


options = {
    "show_menu": False,
    "show_sidebar": False,
}

selected_page = st_navbar(page, styles=styles, logo_path=logo_path, options=options)
# set_bg_hack_url()
show_home()
