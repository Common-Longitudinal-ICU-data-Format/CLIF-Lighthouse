import pandas as pd
import streamlit as st
import logging
import os
from logging_config import setup_logging
from common_features import set_bg_hack_url
from common_qc import read_data
from reqd_vars_dtypes import required_variables


def show_cohort():

    set_bg_hack_url()
    setup_logging()
    logger = logging.getLogger(__name__)

    _, cohort_form, _ = st.columns([1, 3, 1])
    with cohort_form:
        st.title("Cohort Discovery")
        with st.form(key='cohort_form', clear_on_submit=False):
        # Root location input
            root_location = st.text_input("Enter root location to proceed") 
            # if not os.path.exists(root_location):
            #     st.error("Invalid root location. Please check the path and try again.")  

            # File type selection
            filetype = st.selectbox("File type", ["", "csv", "parquet", "fst"], format_func=lambda x: "Select..." if x == "" else x)

            st.form_submit_button(label='Submit')
        
        # Store user inputs in session_state
        if root_location:
            logger.info(f"Root location entered: {root_location}")
            st.session_state['root_location'] = root_location

        if filetype:
            logger.info(f"File type selected: {filetype}")
            st.session_state['filetype'] = filetype

    if root_location and filetype:
            tab1, tab2, tab3 = st.tabs(["Definition", "Reporting", "Export"])
            with tab1:
                # Cohort title and description
                cohort_title = st.text_input("Cohort Title")
                cohort_definition = st.text_input("Enter a description for the cohort")

                # Column layout
                col1, col2, col3 = st.columns(3)
                col1 = col1.container(height=600, border=True)
                col2 = col2.container(height=600, border=True)
                col3 = col3.container(height=600, border=True)

                with col1:
                    st.header("Cohort Entry Events")

                    # Initialize session state variables for entry criteria
                    if 'selected_table' not in st.session_state:
                        st.session_state['selected_table'] = None
                    if 'selected_column' not in st.session_state:
                        st.session_state['selected_column'] = None
                    if 'selected_event' not in st.session_state:
                        st.session_state['selected_event'] = None
                    if 'table_summary_stats' not in st.session_state:
                        st.session_state['table_summary_stats'] = {}

                    selected_table = st.selectbox(
                        "Select table",
                        options=[""] + list(required_variables.keys()),
                        format_func=lambda x: "Select table to..." if x == "" else x,
                        index=0 if st.session_state.get('selected_table') in [None, ""] else list(required_variables.keys()).index(st.session_state['selected_table']) + 1, 
                        help="Choose a table to select attributes.",
                        key="entry_table_select"
                    )

                    filepaths = {
                        "Labs": os.path.join(root_location, f"clif_labs.{filetype}"),
                        "Vitals": os.path.join(root_location, f"clif_vitals.{filetype}"),
                        # "Encounter_Demographic_Disposition": os.path.join(root_location, f"clif_encounter_demographic_disposition.{filetype}"),
                        "Respiratory_Support": os.path.join(root_location, f"clif_respiratory_support.{filetype}"),
                        "Medication_admin_continuous": os.path.join(root_location, f"clif_medication_admin_continuous.{filetype}"),
                        "ADT": os.path.join(root_location, f"clif_adt.{filetype}"),
                        "Hospitalization": os.path.join(root_location, f"clif_hospitalization.{filetype}"),
                        "Microbiology_Culture": os.path.join(root_location, f"clif_microbiology_culture.{filetype}"),
                        "Patient": os.path.join(root_location, f"clif_patient.{filetype}"),
                        "Patient_Assessments": os.path.join(root_location, f"clif_patient_assessments.{filetype}"),
                        "Position": os.path.join(root_location, f"clif_position.{filetype}")
                    }


                    if selected_table:
                            filepath = filepaths[selected_table]
                            data = read_data(filepath, filetype)

                            # Compute summary statistics for all columns
                            summary_stats = {}
                            for col in data.columns:
                                if pd.api.types.is_numeric_dtype(data[col]):
                                    summary_stats[col] = {
                                        'min': data[col].min(),
                                        'max': data[col].max(),
                                    }
                                elif pd.api.types.is_datetime64_any_dtype(data[col]):
                                    summary_stats[col] = {
                                        'min': data[col].min(),
                                        'max': data[col].max(),
                                    }
                                else:
                                    summary_stats[col] = {
                                        'unique_values': data[col].unique().tolist()
                                    }
                            st.session_state['table_summary_stats'][selected_table] = summary_stats

                    selected_column = None
                    if selected_table != st.session_state['selected_table']:
                        st.session_state['selected_table'] = selected_table
                        st.session_state['selected_column'] = None  # Reset column selection when table changes

                    if st.session_state['selected_table']:
                        selected_column = st.selectbox(
                            f"Select attribute from `{st.session_state['selected_table']}`",
                            format_func=lambda x: "Select attribute..." if x == "" else x,
                            options=[""] + required_variables[st.session_state['selected_table']],
                            index=0 if st.session_state.get('selected_column') in [None, ""] else required_variables[st.session_state['selected_table']].index(st.session_state['selected_column']) + 1,  
                            help="Choose an attribute from the selected table.",
                            key="entry_column_select"
                        )
                        st.session_state['selected_column'] = selected_column
                        
                        if selected_column != st.session_state['selected_column']:
                            st.session_state['selected_column'] = selected_column
                            st.session_state['selected_event'] = None  
                        
                    if selected_column:
                        column_stats = st.session_state['table_summary_stats'][selected_table].get(selected_column)

                        if column_stats:
                            if 'min' in column_stats and 'max' in column_stats:
                                if pd.api.types.is_numeric_dtype(data[selected_column]):
                                    st.write(f"Min: {column_stats['min']}, Max: {column_stats['max']}")
                                    selected_event = st.slider(
                                        f"Select range for `{selected_column}`",
                                        min_value=column_stats['min'],
                                        max_value=column_stats['max'],
                                        value=(column_stats['min'], column_stats['max']),
                                    )
                                    st.session_state['selected_event'] = selected_event

                                # For datetime columns
                                elif pd.api.types.is_datetime64_any_dtype(data[selected_column]):
                                    selected_event = st.date_input(
                                        f"Select date range for `{selected_column}`",
                                        value=(column_stats['min'].to_pydatetime().date(), column_stats['max'].to_pydatetime().date()),
                                        min_value=column_stats['min'].to_pydatetime().date(),
                                        max_value=column_stats['max'].to_pydatetime().date(),
                                        key=f"{selected_column}_date_range",
                                        help=f"Acceptable Date Range: {column_stats['min'].to_pydatetime().date()} to {column_stats['max'].to_pydatetime().date()}",
                                        format="MM/DD/YYYY"
                                    )
                                    st.session_state['selected_event'] = selected_event

                            elif 'unique_values' in column_stats:
                                # For categorical columns
                                selected_event = st.selectbox(
                                    f"Select initial event from `{selected_column}`",
                                    options=column_stats['unique_values'],
                                )
                                st.session_state['selected_event'] = selected_event

                    c1, c2 = st.columns(2)
                    with c1:
                        hours_bef = st.number_input(
                            "Hours Before Event", value=st.session_state.get('hours_before', 0), key="hours_bef", min_value=0
                        )
                    with c2:
                        hours_aft = st.number_input(
                            "Hours After Event", value=st.session_state.get('hours_after', 0), key="hours_aft", min_value=0
                        )

                    event = st.selectbox(
                        "Limit initial event",
                        ("", "Earliest event", "Latest event", "All events"),
                        format_func=lambda x: "Limit initial event per person to..." if x == "" else x,
                        key="entry_limit_select"
                    )

                    if st.button("Save Cohort Definition"):
                        st.session_state['cohort_title'] = cohort_title
                        st.session_state['cohort_definition'] = cohort_definition
                        st.session_state['hours_before'] = hours_bef
                        st.session_state['hours_after'] = hours_aft
                        st.session_state['event'] = event
                        st.success("Cohort definition saved!")
                
                with col2:
                    st.header("Inclusion Criteria")

                    # Initialize session state variables
                    if 'inclusion_table' not in st.session_state:
                        st.session_state['inclusion_table'] = None
                    if 'inclusion_column' not in st.session_state:
                        st.session_state['inclusion_column'] = None
                    if 'inclusion_criteria_list' not in st.session_state:
                        st.session_state['inclusion_criteria_list'] = []
                    if 'inclu_summary_stats' not in st.session_state:
                        st.session_state['inclu_summary_stats'] = {}

                    inclusion_column = None 

                    # Select table
                    inclusion_table = st.selectbox(
                        "Select inclusion criteria table",
                        options=[""] + list(required_variables.keys()),
                        format_func=lambda x: "Select table to..." if x == "" else x,
                        index=0 if st.session_state.get('inclusion_table') in [None, ""] else list(required_variables.keys()).index(st.session_state['inclusion_table']) + 1,
                        help="Choose a table to select inclusion criteria.",
                        key="inclusion_table_select"
                    )

                    filepaths = {
                        "Labs": os.path.join(root_location, f"clif_labs.{filetype}"),
                        "Vitals": os.path.join(root_location, f"clif_vitals.{filetype}"),
                        # "Encounter_Demographic_Disposition": os.path.join(root_location, f"clif_encounter_demographic_disposition.{filetype}"),
                        "Respiratory_Support": os.path.join(root_location, f"clif_respiratory_support.{filetype}"),
                        "Medication_admin_continuous": os.path.join(root_location, f"clif_medication_admin_continuous.{filetype}"),
                        "ADT": os.path.join(root_location, f"clif_adt.{filetype}"),
                        "Hospitalization": os.path.join(root_location, f"clif_hospitalization.{filetype}"),
                        "Microbiology_Culture": os.path.join(root_location, f"clif_microbiology_culture.{filetype}"),
                        "Patient": os.path.join(root_location, f"clif_patient.{filetype}"),
                        "Patient_Assessments": os.path.join(root_location, f"clif_patient_assessments.{filetype}"),
                        "Position": os.path.join(root_location, f"clif_position.{filetype}")
                    }

                    if inclusion_table:
                            filepath = filepaths[inclusion_table]
                            inclu_data = read_data(filepath, filetype)

                            # Compute summary statistics for all columns
                            inclu_summary_stats = {}
                            for col in inclu_data.columns:
                                if pd.api.types.is_numeric_dtype(inclu_data[col]):
                                    inclu_summary_stats[col] = {
                                        'min': inclu_data[col].min(),
                                        'max': inclu_data[col].max(),
                                    }
                                elif pd.api.types.is_datetime64_any_dtype(inclu_data[col]):
                                    inclu_summary_stats[col] = {
                                        'min': inclu_data[col].min(),
                                        'max': inclu_data[col].max(),
                                    }
                                else:
                                    inclu_summary_stats[col] = {
                                        'unique_values': inclu_data[col].unique().tolist()
                                    }
                            st.session_state['inclu_summary_stats'][inclusion_table] = inclu_summary_stats

                    if inclusion_table != st.session_state['inclusion_table']:
                        st.session_state['inclusion_table'] = inclusion_table
                        st.session_state['inclusion_column'] = None  # Reset column selection when table changes

                    # Select column
                    if st.session_state["inclusion_table"]:
                        inclusion_column = st.selectbox(
                            f"Select attribute from `{st.session_state['inclusion_table']}`",
                            format_func=lambda x: "Select attribute..." if x == "" else x,
                            options=[""] + required_variables[st.session_state["inclusion_table"]],
                            index=0 if st.session_state.get('inclusion_column') in [None, ""] else required_variables[st.session_state['inclusion_table']].index(st.session_state['inclusion_column']) + 1,
                            help="Choose an attribute for inclusion criteria.",
                            key="inclusion_column_select"
                        )
                        if inclusion_column != st.session_state['inclusion_column']:
                            st.session_state['inclusion_column'] = inclusion_column

                    # Select criteria
                    inclusion_criteria = None
                    if inclusion_column:
                        inclu_column_stats = st.session_state['inclu_summary_stats'][inclusion_table].get(inclusion_column)
                        if inclu_column_stats:
                            if 'min' in inclu_column_stats and 'max' in inclu_column_stats:
                                if pd.api.types.is_numeric_dtype(inclu_data[inclusion_column]):
                                    inclusion_criteria = st.slider(
                                        f"Select range for `{inclusion_column}`",
                                        min_value=inclu_column_stats['min'],
                                        max_value=inclu_column_stats['max'],
                                        value=(inclu_column_stats['min'], inclu_column_stats['max']),
                                    )
                                elif pd.api.types.is_datetime64_any_dtype(inclu_data[inclusion_column]):
                                    inclusion_criteria = st.date_input(
                                        f"Select date range for `{inclusion_column}`",
                                        value=(inclu_column_stats['min'].to_pydatetime().date(), inclu_column_stats['max'].to_pydatetime().date()),
                                        min_value=inclu_column_stats['min'].to_pydatetime().date(),
                                        max_value=inclu_column_stats['max'].to_pydatetime().date(),
                                        key=f"{inclusion_column}_date_range"
                                    )
                            elif 'unique_values' in inclu_column_stats:
                                inclusion_criteria = st.selectbox(
                                    f"Select criteria for `{inclusion_column}`",
                                    options=inclu_column_stats['unique_values'],
                                )

                    # Add criteria
                    if st.button("Add Inclusion Criteria") and inclusion_criteria is not None:
                        st.session_state['inclusion_criteria_list'].append(
                            {"table": inclusion_table, "column": inclusion_column, "criteria": inclusion_criteria}
                        )
                        st.success(f"Added criteria: `{inclusion_table}` - `{inclusion_column}` with criteria: `{inclusion_criteria}`")

                    # Display inclusion criteria
                    if st.session_state['inclusion_criteria_list']:
                        st.write("### Current Inclusion Criteria")
                        for idx, criteria in enumerate(st.session_state['inclusion_criteria_list']):
                            st.write(f"{idx + 1}. Table: `{criteria['table']}`, Column: `{criteria['column']}`, Criteria: `{criteria['criteria']}`")
                            if st.button(f"Remove Inclusion Criteria {idx + 1}"):
                                st.session_state['inclusion_criteria_list'].pop(idx)

                with col3:
                    st.header("Exclusion Criteria")

                    # Initialize session state variables
                    if 'exclusion_table' not in st.session_state:
                        st.session_state['exclusion_table'] = None
                    if 'exclusion_column' not in st.session_state:
                        st.session_state['exclusion_column'] = None
                    if 'exclusion_criteria_list' not in st.session_state:
                        st.session_state['exclusion_criteria_list'] = []
                    if 'exclu_summary_stats' not in st.session_state:
                        st.session_state['exclu_summary_stats'] = {}

                    exclusion_column = None

                    # Select table
                    exclusion_table = st.selectbox(
                        "Select exclusion criteria table",
                        options=[""] + list(required_variables.keys()),
                        format_func=lambda x: "Select table to..." if x == "" else x,
                        index=0 if st.session_state.get('exclusion_table') in [None, ""] else list(required_variables.keys()).index(st.session_state['exclusion_table']) + 1,
                        help="Choose a table to select exclusion criteria.",
                        key="exclusion_table_select"
                    )

                    filepaths = {
                        "Labs": os.path.join(root_location, f"clif_labs.{filetype}"),
                        "Vitals": os.path.join(root_location, f"clif_vitals.{filetype}"),
                        # "Encounter_Demographic_Disposition": os.path.join(root_location, f"clif_encounter_demographic_disposition.{filetype}"),
                        "Respiratory_Support": os.path.join(root_location, f"clif_respiratory_support.{filetype}"),
                        "Medication_admin_continuous": os.path.join(root_location, f"clif_medication_admin_continuous.{filetype}"),
                        "ADT": os.path.join(root_location, f"clif_adt.{filetype}"),
                        "Hospitalization": os.path.join(root_location, f"clif_hospitalization.{filetype}"),
                        "Microbiology_Culture": os.path.join(root_location, f"clif_microbiology_culture.{filetype}"),
                        "Patient": os.path.join(root_location, f"clif_patient.{filetype}"),
                        "Patient_Assessments": os.path.join(root_location, f"clif_patient_assessments.{filetype}"),
                        "Position": os.path.join(root_location, f"clif_position.{filetype}")
                    }

                    if exclusion_table:
                            filepath = filepaths[exclusion_table]
                            exclu_data = read_data(filepath, filetype)

                            # Compute summary statistics for all columns
                            exclu_summary_stats = {}
                            for col in exclu_data.columns:
                                if pd.api.types.is_numeric_dtype(exclu_data[col]):
                                    exclu_summary_stats[col] = {
                                        'min': exclu_data[col].min(),
                                        'max': exclu_data[col].max(),
                                    }
                                elif pd.api.types.is_datetime64_any_dtype(exclu_data[col]):
                                    exclu_summary_stats[col] = {
                                        'min': exclu_data[col].min(),
                                        'max': exclu_data[col].max(),
                                    }
                                else:
                                    exclu_summary_stats[col] = {
                                        'unique_values': exclu_data[col].unique().tolist()
                                    }
                            st.session_state['exclu_summary_stats'][exclusion_table] = exclu_summary_stats

                    if exclusion_table != st.session_state['exclusion_table']:
                        st.session_state['exclusion_table'] = exclusion_table
                        st.session_state['exclusion_column'] = None  # Reset column selection when table changes

                    # Select column
                    if st.session_state["exclusion_table"]:
                        exclusion_column = st.selectbox(
                            f"Select attribute from `{st.session_state['exclusion_table']}`",
                            format_func=lambda x: "Select attribute..." if x == "" else x,
                            options=[""] + required_variables[st.session_state["exclusion_table"]],
                            index=0 if st.session_state.get('exclusion_column') in [None, ""] else required_variables[st.session_state['exclusion_table']].index(st.session_state['exclusion_column']) + 1,
                            help="Choose an attribute for exclusion criteria.",
                            key="exclusion_column_select"
                        )
                        if exclusion_column != st.session_state['exclusion_column']:
                            st.session_state['exclusion_column'] = exclusion_column

                    # Select criteria
                    exclusion_criteria = None
                    if exclusion_column:
                        column_stats = st.session_state['exclu_summary_stats'][exclusion_table].get(exclusion_column)
                        if column_stats:
                            if 'min' in column_stats and 'max' in column_stats:
                                if pd.api.types.is_numeric_dtype(data[exclusion_column]):
                                    exclusion_criteria = st.slider(
                                        f"Select range for `{exclusion_column}`",
                                        min_value=column_stats['min'],
                                        max_value=column_stats['max'],
                                        value=(column_stats['min'], column_stats['max']),
                                    )
                                elif pd.api.types.is_datetime64_any_dtype(data[exclusion_column]):
                                    exclusion_criteria = st.date_input(
                                        f"Select date range for `{exclusion_column}`",
                                        value=(column_stats['min'].to_pydatetime().date(), column_stats['max'].to_pydatetime().date()),
                                        min_value=column_stats['min'].to_pydatetime().date(),
                                        max_value=column_stats['max'].to_pydatetime().date(),
                                        key=f"{exclusion_column}_date_range"
                                    )
                            elif 'unique_values' in column_stats:
                                exclusion_criteria = st.selectbox(
                                    f"Select criteria for `{exclusion_column}`",
                                    options=column_stats['unique_values'],
                                )

                    # Add criteria
                    if st.button("Add Exclusion Criteria") and exclusion_criteria is not None:
                        st.session_state['exclusion_criteria_list'].append(
                            {"table": exclusion_table, "column": exclusion_column, "criteria": exclusion_criteria}
                        )
                        st.success(f"Added criteria: `{exclusion_table}` - `{exclusion_column}` with criteria: `{exclusion_criteria}`")

                    # Display exclusion criteria
                    if st.session_state['exclusion_criteria_list']:
                        st.write("### Current Exclusion Criteria")
                        for idx, criteria in enumerate(st.session_state['exclusion_criteria_list']):
                            st.write(f"{idx + 1}. Table: `{criteria['table']}`, Column: `{criteria['column']}`, Criteria: `{criteria['criteria']}`")
                            if st.button(f"Remove Exclusion Criteria {idx + 1}"):
                                st.session_state['exclusion_criteria_list'].pop(idx)
               
            # with tab2:
            #     if not (st.session_state.get('selected_table') and st.session_state.get('selected_column') and st.session_state.get('selected_event')):
            #         st.warning("Please define a cohort in the 'Definition' tab before generating a report.")
            #     else:
            #         # Retrieve data
            #         selected_table = st.session_state['selected_table']
            #         selected_column = st.session_state['selected_column']
            #         selected_event = st.session_state['selected_event']
            #         filepath = filepaths[selected_table]

            #         try:
            #             # Read data for the selected table
            #             data = read_data(filepath, filetype)
            #         except Exception as e:
            #             logger.error(f"Failed to load data for reporting: {e}")
            #             st.error("Could not load data for reporting. Please check the file or data path.")
            #             st.stop()

            #         # Filter data based on the selected event
            #         if pd.api.types.is_numeric_dtype(data[selected_column]):
            #             # Numeric filtering (range)
            #             min_val, max_val = selected_event
            #             filtered_data = data[(data[selected_column] >= min_val) & (data[selected_column] <= max_val)]
            #         else:
            #             # Categorical filtering (exact match)
            #             filtered_data = data[data[selected_column] == selected_event]

            #         if filtered_data.empty:
            #             st.warning("No records match the selected criteria.")
            #         else:
            #             st.success(f"Filtered data contains {len(filtered_data)} records.")

            #             # Display filtered data as a preview
            #             st.subheader("Filtered Data Preview")
            #             st.dataframe(filtered_data.head())

            #             # Generate summary statistics if applicable
            #             st.subheader("Summary Statistics")
            #             if pd.api.types.is_numeric_dtype(filtered_data[selected_column]):
            #                 st.write(filtered_data[selected_column].describe())
            #             else:
            #                 st.write(filtered_data[selected_column].value_counts())

            # with tab3:
            #     with st.form(key='export_form', clear_on_submit=False):

            #         st.subheader("Export Filtered Data")
            #         export_location = st.text_input("Enter destination path to save output") 
            #         # if not os.path.exists(root_location):
            #         #     st.error("Invalid root location. Please check the path and try again.")  

            #         export_filetype = st.selectbox("Select file type for export", ["", "csv", "parquet", "fst"], format_func=lambda x: "Select..." if x == "" else x)

            #         submit = st.form_submit_button(label='Submit')
                   

            #         if submit:
            #             if not export_location:
            #                 st.error("Please specify a valid export location.")
            #             elif not export_filetype:
            #                 st.error("Please select a file format for export.")
            #             else:
            #                 try:
            #                     # Export data based on file type
            #                     if export_filetype == "csv":
            #                         export_path = os.path.join(export_location, "filtered_data.csv")
            #                         filtered_data.to_csv(export_path, index=False)
            #                     elif export_filetype == "parquet":
            #                         export_path = os.path.join(export_location, "filtered_data.parquet")
            #                         filtered_data.to_parquet(export_path, index=False)
            #                     elif export_filetype == "xlsx":
            #                         export_path = os.path.join(export_location, "filtered_data.xlsx")
            #                         with pd.ExcelWriter(export_path, engine="xlsxwriter") as writer:
            #                             filtered_data.to_excel(writer, index=False)

            #                     st.success(f"Data exported successfully to {export_path}")

            #                 except Exception as e:
            #                     logger.error(f"Error exporting data: {e}")
            #                     st.error("Failed to export data. Please check the export path and file permissions.")

