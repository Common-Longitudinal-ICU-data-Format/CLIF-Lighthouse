import streamlit as st
import pandas as pd
import os
import logging
import time
from common_qc import read_data, check_required_variables
from common_qc import validate_and_convert_dtypes, name_category_mapping
from logging_config import setup_logging
from common_features import set_bg_hack_url

def show_patient_assess_qc():
    '''
    '''
    set_bg_hack_url()

    #Initialize logger
    setup_logging()
    logger = logging.getLogger(__name__)

    # Page title
    TABLE = "Patient Assessments"
    table = "Patient_Assessments"
    st.title(f"{TABLE} Quality Check")

    logger.info(f"!!! Starting QC for {TABLE}.")

    # Main
    qc_summary = []
    qc_recommendations = []


    if 'root_location' in st.session_state and 'filetype' in st.session_state:
        root_location = st.session_state['root_location']
        filetype = st.session_state['filetype']
        filepath = os.path.join(root_location, f'clif_patient_assessments.{filetype}')
        # Sampling option
        if 'sampling_option' in st.session_state:
            sampling_rate = st.session_state['sampling_option']
        else:
            sampling_rate = 100

        logger.info(f"Filepath set to {filepath}")

        if os.path.exists(filepath):
            progress_bar = st.progress(0, text="Quality check in progress. Please wait...")
            logger.info(f"File {filepath} exists.")

            # Start time
            start_time = time.time()

            progress_bar.progress(5, text='File found...')

            progress_bar.progress(10, text='Starting QC...')
    
            with st.expander("Expand to view", expanded=False):
                # Load the file
                with st.spinner("Loading data..."):
                    progress_bar.progress(15, text='Loading data...')
                    logger.info("~~~ Loading data ~~~")

                    if sampling_rate < 100:
                        original_data = read_data(filepath, filetype)
                        try:
                            frac = sampling_rate/100
                            data = original_data.sample(frac = frac)
                        except Exception as e:
                            st.write(f":red[Error: {e}]")
        
                    else:
                        data = read_data(filepath, filetype)

                    logger.info("Data loaded successfully.")


                # Display the data
                logger.info("~~~ Displaying data ~~~")
                st.write(f"## {TABLE} Data Preview")
                with st.spinner("Loading data preview..."):
                    progress_bar.progress(20, text='Loading data preview...')
                    ttl_smpl = "Total"
                    if sampling_rate < 100:
                        ttl_smpl = "Sample"
                        total_counts = original_data.shape[0]
                        sample_counts = data.shape[0]
                        st.write(f"Total record count before sampling: {total_counts}")
                        st.write(f"Sample({sampling_rate}%) record count: {sample_counts}")
                    else:
                        total_counts = data.shape[0]
                        st.write(f"Total record count: {total_counts}")
                    ttl_unique_encounters = data['hospitalization_id'].nunique()
                    duplicate_count = data.duplicated().sum()
                    st.write(f"{ttl_smpl} records: {total_counts}")
                    st.write(f"{ttl_smpl} unique hospital encounters: {ttl_unique_encounters}")
                    if duplicate_count > 0:
                        st.write(f"{ttl_smpl} duplicate records: {duplicate_count}")
                        qc_summary.append(f"{duplicate_count} duplicate(s) found in the data.")
                        qc_recommendations.append("Duplicate records found. Please review and remove duplicates.")
                    else:
                        st.write("No duplicate records found.")
                    st.write(data.head())
                    logger.info("Data displayed.")

                
                # Validate and convert data types
                st.write("## Data Type Validation")
                with st.spinner("Validating data types..."):
                    progress_bar.progress(30, text='Validating data types...')
                    logger.info("~~~ Validating data types ~~~")
                    data, validation_results = validate_and_convert_dtypes(table, data)
                    validation_df = pd.DataFrame(validation_results, columns=['Column', 'Actual', 'Expected', 'Status'])
                    mismatch_columns = [row[0] for row in validation_results if row[1] != row[2]]
                    convert_dtypes = False
                    if mismatch_columns:
                        convert_dtypes = True
                        qc_summary.append("Some columns have mismatched data types.")
                        qc_recommendations.append("Some columns have mismatched data types. Please review and convert to the expected data types.")
                    st.write(validation_df)
                    logger.info("Data type validation completed.")

                
                # Display missingness for each column
                st.write(f"## Missingness")
                with st.spinner("Checking for missing values..."):
                    progress_bar.progress(40, text='Checking for missing values...')
                    logger.info("~~~ Checking for missing values ~~~")
                    missing_counts = data.isnull().sum()
                    if missing_counts.sum() > 0:
                        missing_percentages = (missing_counts / total_counts) * 100
                        missing_info = pd.DataFrame({
                            'Missing Count': missing_counts,
                            'Missing Percentage': missing_percentages.map('{:.2f}%'.format)
                        })
                        missing_info_filtered = missing_info[missing_info['Missing Count'] > 0]
                        st.write(missing_info_filtered)
                        qc_summary.append("Missing values found in columns - " + ', '.join(missing_info[missing_info['Missing Count'] > 0].index.tolist()))
                    else:
                        st.write("No missing values found in all required columns.")
                    logger.info("Checked for missing values.")

            
                # Check for required columns    
                logger.info("~~~ Checking for required columns ~~~")  
                st.write(f"## {TABLE} Required Columns")
                with st.spinner("Checking for required columns..."):
                    progress_bar.progress(60, text='Checking for required columns...')
                    required_cols_check = check_required_variables(table, data)
                    st.write(required_cols_check)
                    qc_summary.append(required_cols_check)
                    if required_cols_check != f"All required columns present for '{TABLE}'.":
                        qc_recommendations.append("Some required columns are missing. Please ensure all required columns are present.")  
                        logger.warning("Some required columns are missing.")
                    logger.info("Checked for required columns.")
                
                 # Name to Category mappings
                logger.info("~~~ Mapping ~~~")
                st.write('## Name to Category Mapping')
                with st.spinner("Displaying Name to Category Mapping..."):
                    progress_bar.progress(90, text='Displaying Name to Category Mapping...')
                    mappings = name_category_mapping(data)
                    n = 1
                    for i, mapping in enumerate(mappings):
                        mapping_name = mapping.columns[0]
                        mapping_cat = mapping.columns[1]
                        st.write(f"{n}. Mapping `{mapping_name}` to `{mapping_cat}`")
                        st.write(mapping.reset_index().drop("index", axis = 1))
                        n += 1

                progress_bar.progress(100, text='Quality check completed. Displaying results...')
             

            # End time
            end_time = time.time()
            elapsed_time = end_time - start_time
            st.success(f"Quality check completed. Time taken to run summary: {elapsed_time:.2f} seconds", icon="✅")
            logger.info(f"Time taken to run summary: {elapsed_time:.2f} seconds")
            
            # Display QC Summary and Recommendations
            st.write("# QC Summary and Recommendations")
            logger.info("Displaying QC Summary and Recommendations.")

            with st.expander("Expand to view", expanded=False):
                st.write("## Summary")
                for i, point in enumerate(qc_summary):
                    st.markdown(f"{i + 1}. {point}")

                st.write("## Recommendations")
                for i, recommendation in enumerate(qc_recommendations):
                    st.markdown(f"{i + 1}. {recommendation}")

            logger.info("QC Summary and Recommendations displayed.")

            # Select and Download revisions to the data
            def apply_changes(data, convert_dtypes, apply_deduplication):
                if convert_dtypes:
                    data = validate_and_convert_dtypes(table, data)[0]

                if apply_deduplication:
                    data = data.drop_duplicates()

                return data

            def convert_df_to_file_format(data, file_format):
                if file_format == 'csv':
                    return data.to_csv(index=False).encode('utf-8')
                elif file_format == 'parquet':
                    return data.to_parquet(index=False)
                else:
                    return None

            st.write("# Select and Download Recommended Revisions to the Data")
            st.info("The entire page will reload before applying changes. Please wait for the page to reload and changes to be applied before proceeding to download. This may take a while.", icon="ℹ️")
            with st.expander("Exapnd to View"):
            # if st.session_state:
                st.write("#### Select changes to apply")
                with st.form(key='apply_patient_assess_changes_form'):
                    # Create checkboxes for changes
                    if duplicate_count > 0:
                        apply_deduplication = st.checkbox("Remove duplicates")
                    else:
                        apply_deduplication = False

                    if mismatch_columns:
                        convert_dtypes = st.checkbox("Convert to expected data types")
                    else:
                        convert_dtypes = False

                    st.write("#### Select file format for download")
                    file_type = st.selectbox("Select file type for download", ["csv", "parquet"])
                    submit_button = st.form_submit_button(label='Submit')

                if submit_button:
                    with st.spinner("Applying changes..."):
                        time.sleep(10)
                        revised_data = apply_changes(data.copy(), convert_dtypes, apply_deduplication)
                        revised_data_file = convert_df_to_file_format(revised_data, file_type)
                        st.write("Successfully applied changes. Click to download revised data.")
                    if revised_data_file:
                        st.download_button(
                            label="Download revised data",
                            data=revised_data_file,
                            file_name=f"revised_{table}_data.{file_type}",
                        )

        else:
            st.write(f"File not found. Please provide the correct root location and file type to proceed.")

    else:
        st.write("Please provide the root location and file type to proceed.")
        logger.warning("Root location and/or file type not provided.")

    logger.info(f"!!! Completed QC for {TABLE}.")       

