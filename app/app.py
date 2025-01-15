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
                    - **Microbiology**
                    - **Patient**
                    """)
            with c4:
                    st.write("""
                    - **Patient Assessment**
                    - **Position**
                    """)
            with c5:
                    st.write("""
                    - **Respiratory Support**
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

                if sampling_option:
                    logger.info(f"Sampling option selected: {sampling_option}")
                    st.session_state['sampling_option'] = sampling_option

            logger.info("Loading QC results page")
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(["ADT", 
                "Hospitalization", "Labs", "Medication", "Microbiology", "Patient", 
                "Patient Assessment", "Position", "Respiratory Support", "Vitals"])

            with tab1:
                tab1_results = show_adt_qc()
                if tab1_results is not None:
                    st.download_button(
                        label="Download ADT QC Report",
                        data=tab1_results,
                        file_name="adt_qc_report.pdf",
                        mime="application/pdf"
                    )

            with tab2:
                tab2_results = show_hosp_qc()
                if tab2_results is not None:
                    st.download_button(
                        label="Download Hospitalization QC Report",
                        data=tab2_results,
                        file_name="hosp_qc_report.pdf",
                        mime="application/pdf"
                    )

            with tab3:
                tab3_results = show_labs_qc()
                if tab3_results is not None:
                    st.download_button(
                        label="Download Labs QC Report",
                        data=tab3_results,
                        file_name="labs_qc_report.pdf",
                        mime="application/pdf"
                    )

            with tab4:
                tab4_results = show_meds_qc()
                if tab4_results is not None:
                    st.download_button(
                        label="Download Medications QC Report",
                        data=tab4_results,
                        file_name="meds_qc_report.pdf",
                        mime="application/pdf"
                    )

            with tab5:
                tab5_results = show_microbio_qc()
                if tab5_results is not None:
                    st.download_button(
                        label="Download Microbiology QC Report",
                        data=tab5_results,
                        file_name="micro_qc_report.pdf",
                        mime="application/pdf"
                    )

            with tab6:
                tab6_results = show_patient_qc()
                tab6_results
                # if tab6_results is not None:
                #     st.download_button(
                #         label="Download Patient QC Report",
                #         data=tab6_results,
                #         file_name="patient_qc_report.pdf",
                #         mime="application/pdf"
                #     )

            with tab7:
                tab7_results = show_patient_assess_qc()
                tab7_results
                # if tab7_results is not None:
                #     st.download_button(
                #         label="Download Patient Assessment QC Report",
                #         data=tab7_results,
                #         file_name="pat_assess_qc_report.pdf",
                #         mime="application/pdf"
                #     )

            with tab8:
                tab8_results = show_position_qc()
                tab8_results
                # if tab8_results is not None:
                #     st.download_button(
                #         label="Download Position QC Report",
                #         data=tab8_results,
                #         file_name="position_qc_report.pdf",
                #         mime="application/pdf"
                #     )

            with tab9:
                tab9_results = show_respiratory_support_qc()
                tab9_results
                # if tab9_results is not None:
                #     st.download_button(
                #         label="Download Respiratory Support QC Report",
                #         data=tab9_results,
                #         file_name="resp_qc_report.pdf",
                #         mime="application/pdf"
                #     )

            with tab10:
                tab10_results = show_vitals_qc()
                tab10_results
                # if tab10_results is not None:
                #     st.download_button(
                #         label="Download Vitals QC Report",
                #         data=tab10_results,
                #         file_name="vitals_qc_report.pdf",
                #         mime="application/pdf"
                #     )

  
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
