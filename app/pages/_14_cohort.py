from pygwalker.api.streamlit import StreamlitRenderer
import pandas as pd
import streamlit as st
from common_features import set_bg_hack_url

def show_cohort():
    set_bg_hack_url()
    _, cohort_form, _ = st.columns([1, 3, 1])
    with cohort_form:
        with st.form(key='cohort_form', clear_on_submit=False):
            filepath = st.text_input("Input filepath")  
            submit_button = st.form_submit_button(label='Submit') 
        
    def get_pyg_renderer() -> "StreamlitRenderer":
        df = pd.read_csv(filepath)
        return StreamlitRenderer(df, dark='light', spec_io_mode="rw")
    
    if submit_button:
        renderer = get_pyg_renderer()
        renderer.explorer()
    
    



