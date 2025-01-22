import streamlit as st
import pandas as pd
import logging
import time
import os
from common_qc import check_required_variables
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
    table_session_name = "clif_patient_assessments"
    st.title(f"{TABLE} Quality Check")

    logger.info(f"!!! Starting QC for {TABLE}.")

    # Main
    qc_summary = []
    qc_recommendations = []


    if table_session_name in st.session_state:

        progress_bar = st.progress(0, text="Quality check in progress. Please wait...")


        # Start time
        start_time = time.time()

        progress_bar.progress(5, text='File found...')

        progress_bar.progress(10, text='Starting QC...')

        with st.expander("Expand to view", expanded=False):
            # Load the file
            with st.spinner("Loading data..."):
                progress_bar.progress(15, text='Loading data...')
                logger.info("~~~ Loading data ~~~")

                sampling_rate = st.session_state['sampling_option']
                download_path = st.session_state['download_path'] 
                
                if sampling_rate is not None:
                    original_data = st.session_state[table_session_name]
                    try:
                        frac = sampling_rate/100
                        data = original_data.sample(frac = frac)
                    except Exception as e:
                        st.write(f":red[Error: {e}]")
    
                else:
                    data = st.session_state[table_session_name]

                logger.info("Data loaded successfully.")


            # Display the data
            logger.info("~~~ Displaying data ~~~")
            st.write(f"## {TABLE} Data Preview")
            with st.spinner("Loading data preview..."):
                progress_bar.progress(20, text='Loading data preview...')
                ttl_smpl = "Total"
                if sampling_rate is not None:
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
                mismatch_columns = [row[0] for row in validation_results if row[3] == 'Mismatch']
                if mismatch_columns:
                    qc_summary.append(f"Column(s) with mismatched data types: {mismatch_columns}")
                    qc_recommendations.append(f"Column(s) with mismatched data types: {mismatch_columns}. Please review and convert to the expected data types.")
                st.write(validation_df)
                logger.info("Data type validation completed.")

                # Download data type validation results
                if download_path is not None:
                    try:
                        validation_results_csv = validation_df.to_csv(index=True)
                        file_path = os.path.join(download_path, f"{TABLE}_validation_results.csv")
                        with open(file_path, 'w') as file:
                            file.write(validation_results_csv)
                        logger.info(f"Validation results saved to {file_path}")
                    except Exception as e:
                        logger.error(f"Failed to save validation results to {download_path}/{TABLE}_validation_results.csv: {e}")
                   

            
            # Display missingness for each column
            st.write(f"## Missingness")
            with st.spinner("Checking for missing values..."):
                progress_bar.progress(40, text='Checking for missing values...')
                logger.info("~~~ Checking for missing values ~~~")
                missing_counts = data.isna().sum()
                missingness_summary = ""  # Store the summary temporarily
                if missing_counts.any():
                    missing_percentages = (missing_counts / total_counts) * 100
                    missing_info = pd.DataFrame({
                        'Missing Count': missing_counts,
                        'Missing Percentage': missing_percentages.map('{:.2f}%'.format)
                    })
                    missing_info_sorted = missing_info.sort_values(by='Missing Count', ascending=False)
                    st.write(missing_info_sorted)
                    columns_with_missing = missing_info[missing_info['Missing Count'] > 0]
                    missingness_summary = f"Missing values found in {len(columns_with_missing)} columns:\n"
                    for idx, row in columns_with_missing.iterrows():
                        missingness_summary += f"- {idx}: {row['Missing Count']} records ({row['Missing Percentage']})\n"
                    if download_path is not None:
                        # Save missingness information to CSV
                        missing_info_sorted_csv = missing_info_sorted.to_csv(index=True)
                        with open(os.path.join(download_path, f"{TABLE}_missingness.csv"), 'w') as file:
                            file.write(missing_info_sorted_csv)
                        logger.info(f"Missingness information saved to {download_path}/{TABLE}_missingness.csv")             
                else:
                    st.write("No missing values found in all required columns.")
                    missingness_summary = "No missing values found in any columns."
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
                
                # Save mappings to CSV
                if download_path is not None:
                    try:
                        mappings_csv = pd.concat(mappings).reset_index().drop("index", axis = 1).to_csv(index=True)
                        with open(os.path.join(download_path, f"{TABLE}_mappings.csv"), 'w') as file:
                            file.write(mappings_csv)
                        logger.info(f"Name to Category Mappings saved to {download_path}/{TABLE}_mappings.csv")
                    except Exception as e:
                        logger.error(f"Failed to save Name to Category Mappings to {download_path}/{TABLE}_mappings.csv: {str(e)}")


            qc_summary.append(missingness_summary)  

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

    else:
        st.write(f"Please upload {TABLE} data to proceed.")
        logger.warning(f"Please upload {TABLE} data to proceed.")

    logger.info(f"!!! Completed QC for {TABLE}.")       



