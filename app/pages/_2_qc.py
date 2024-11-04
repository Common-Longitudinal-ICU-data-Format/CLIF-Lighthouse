import streamlit as st
import logging
from logging_config import setup_logging
from common_features import set_bg_hack_url
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

def show_qc():
    '''
    '''
    set_bg_hack_url()

    # Initialize logger
    setup_logging()
    logger = logging.getLogger(__name__)

    _, main_qc_form, _ = st.columns([1, 3, 1])
    with main_qc_form:
        st.title("Quality Controls")
        with st.form(key='main_form', clear_on_submit=False):
        # Root location input
            root_location = st.text_input("Enter root location to proceed")   

            # File type selection
            filetype = st.selectbox("File type", ["", "csv", "parquet", "fst"], format_func=lambda x: "Select..." if x == "" else x)

            submit = st.form_submit_button(label='Submit')

            if submit:
                st.write("The quality controls for each table are displayed in the respective tabs below. Please navigate to the appropriate tab to view the relevant quality control details.")
                st.write("Allow some time for each tab to load.")
                st.info("Note that a new tab will not load until the current tab has finished loading. " \
                    "The overall progress of the quality control checks is displayed below. For detailed progress information, please expand the QC section.", 
                    icon="ℹ️")
        
        # Store user inputs in session_state
        if root_location:
            logger.info(f"Root location entered: {root_location}")
            st.session_state['root_location'] = root_location

        if filetype:
            logger.info(f"File type selected: {filetype}")
            st.session_state['filetype'] = filetype

        if root_location and filetype:
            tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(["ADT", 
                "Hospitalization", "Labs", "Medication", "Microbiology", "Patient", 
                "Patient Assessment", "Position", "Respiratory Support", "Vitals"])

            with tab1:
                show_adt_qc()
            with tab2:
                show_hosp_qc()
            with tab3:
                show_labs_qc()
            with tab4:
                show_meds_qc()
            with tab5:
                show_microbio_qc()
            with tab6:
                show_patient_qc()
            with tab7:
                show_patient_assess_qc()
            with tab8:
                show_position_qc()
            with tab9:
                show_respiratory_support_qc()
            with tab10:
                show_vitals_qc()

                





