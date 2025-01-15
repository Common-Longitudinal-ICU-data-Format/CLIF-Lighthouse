# import streamlit as st
# import logging
# from logging_config import setup_logging
# from common_features import set_bg_hack_url
# from common_qc import read_data
# from pages._3_adt_qc import show_adt_qc
# from pages._4_hosp_qc import show_hosp_qc
# from pages._5_labs_qc import show_labs_qc
# from pages._6_med_qc import show_meds_qc
# from pages._7_microbio_qc import show_microbio_qc
# from pages._8_patient_qc import show_patient_qc
# from pages._9_patient_assess_qc import show_patient_assess_qc
# from pages._10_position_qc import show_position_qc
# from pages._11_resp_qc import show_respiratory_support_qc
# from pages._12_vitals_qc import show_vitals_qc

# def show_qc():
#     '''
#     '''
#     set_bg_hack_url()

#     # Initialize logger
#     setup_logging()
#     logger = logging.getLogger(__name__)
#     if "files" in st.session_state:
#         logger.info("Loading QC results page")
#         tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs(["ADT", 
#             "Hospitalization", "Labs", "Medication", "Microbiology", "Patient", 
#             "Patient Assessment", "Position", "Respiratory Support", "Vitals"])

#         with tab1:
#             show_adt_qc()
#         with tab2:
#             show_hosp_qc()
#         with tab3:
#             show_labs_qc()
#         with tab4:
#             show_meds_qc()
#         with tab5:
#             show_microbio_qc()
#         with tab6:
#             show_patient_qc()
#         with tab7:
#             show_patient_assess_qc()
#         with tab8:
#             show_position_qc()
#         with tab9:
#             show_respiratory_support_qc()
#         with tab10:
#             show_vitals_qc()

        





