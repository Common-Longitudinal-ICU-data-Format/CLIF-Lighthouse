import streamlit as st
import pandas as pd
import logging
import time
import os
from common_qc import check_required_variables
from common_qc import replace_outliers_with_na_wide
from common_qc import validate_and_convert_dtypes, name_category_mapping
from logging_config import setup_logging
from common_features import set_bg_hack_url


def show_respiratory_support_qc():
    '''
    '''
    set_bg_hack_url()

    #Initialize logger
    setup_logging()
    logger = logging.getLogger(__name__)

    # Page title
    TABLE = 'Respiratory_Support'
    table = 'clif_respiratory_support'
    st.title(f"Respiratory Support Quality Check")

    logger.info(f"!!! Starting QC for {TABLE}.")

    # Main 
    qc_summary = []
    qc_recommendations = []

    if table in st.session_state:

        progress_bar = st.progress(0, text="Quality check in progress. Please wait...")

        # Start time
        start_time = time.time()

        progress_bar.progress(5, text='File found...')

        progress_bar.progress(10, text='Starting QC...')

        # 1. Respiratory Support Detailed QC 
        with st.expander("Expand to view", expanded=False):
                # Load the file
            with st.spinner("Loading data..."):
                progress_bar.progress(15, text='Loading data...')
                logger.info("~~~ Loading data ~~~")
                
                sampling_rate = st.session_state['sampling_option']
                download_path = st.session_state['download_path'] 
                
                if sampling_rate is not None:
                    original_data = st.session_state[table]
                    try:
                        frac = sampling_rate/100
                        data = original_data.sample(frac = frac)
                    except Exception as e:
                        st.write(f":red[Error: {e}]")
    
                else:
                    data = st.session_state[table]

                df = data.copy()
                logger.info("Data loaded successfully.")

                
            # Display the data
            logger.info("~~~ Displaying data ~~~")
            st.write(f"## Respiratory Support Data Preview")
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
                logger.info("Displayed data.")


            # Validate and convert data types
            st.write("## Data Type Validation")
            with st.spinner("Validating data types..."):
                progress_bar.progress(30, text='Validating data types...')
                logger.info("~~~ Validating data types ~~~")
                data, validation_results = validate_and_convert_dtypes(TABLE, data)
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
                        validation_results_csv = validation_df.to_csv(index=False)
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
                        missing_info_sorted_csv = missing_info_sorted.reset_index().to_csv(index=False)
                        with open(os.path.join(download_path, f"{TABLE}_missingness.csv"), 'w') as file:
                            file.write(missing_info_sorted_csv)
                        logger.info(f"Missingness information saved to {download_path}/{TABLE}_missingness.csv")             
                else:
                    st.write("No missing values found in all required columns.")
                    missingness_summary = "No missing values found in any columns."
                logger.info("Checked for missing values.")


            # Display summary statistics
            st.write(f"## Respiratory Support Summary Statistics")
            with st.spinner("Displaying summary statistics..."):  
                progress_bar.progress(50, text='Displaying summary statistics...')
                logger.info("~~~ Displaying summary statistics ~~~")  
                summary = data.describe()
                summary_csv = summary.reset_index().to_csv(index=False)
                if download_path is not None:
                    with open(os.path.join(download_path, f"{TABLE}_summary_statistics.csv"), 'w') as file:
                        file.write(summary_csv)
                    logger.info(f"Summary statistics saved to {download_path}/{TABLE}_summary_statistics.csv")
                st.write(summary)
                logger.info("Displayed summary statistics.")

            
            # Check for required columns
            logger.info("~~~ Checking for required columns ~~~")    
            st.write(f"## Respiratory Support Required Columns")
            with st.spinner("Checking for required columns..."):
                progress_bar.progress(60, text='Checking for required columns...')
                required_cols_check = check_required_variables(TABLE, data)
                st.write(required_cols_check)
                qc_summary.append(required_cols_check)
                if required_cols_check != f"All required columns present for '{TABLE}'.":
                    qc_recommendations.append("Some required columns are missing. Please ensure all required columns are present.")  
                    logger.warning("Some required columns are missing.")
                logger.info("Checked for required columns.")

            # Check for outliers
            st.write("## Outliers")
            with st.spinner("Checking for outliers..."):
                resp_outlier_thresholds_filepath = "thresholds/nejm_outlier_thresholds_respiratory_support.csv"
                resp_outlier_thresholds = pd.read_csv(resp_outlier_thresholds_filepath)
                data, replaced_count, _, _ = replace_outliers_with_na_wide(data, resp_outlier_thresholds)
                if replaced_count > 0:
                    qc_summary.append("Outliers found in the data.")
                    qc_recommendations.append("Outliers found. Please replace values with NA.")
                    st.write("Outliers found in the data.")
            
            st.write("## Device Category Summaries")
            st.write("###### * Without Outliers")
            with st.spinner("Displaying summaries by device category..."):
                progress_bar.progress(70, text='Displaying summaries by device category...')
                logger.info("~~~ Displaying summaries by device category ~~~")
                
                # Overall Device Category Summary
                st.write("### Overall Device Category Summary")
                columns_to_pair = [
                    'tracheostomy', 'fio2_set', 'lpm_set', 'tidal_volume_set', 'resp_rate_set',
                    'pressure_control_set', 'pressure_support_set', 'flow_rate_set',
                    'peak_inspiratory_pressure_set', 'inspiratory_time_set',
                    'inspiratory_time_percent_set', 'inspiratory_time_ratio_set', 'peep_set',
                    'tidal_volume_obs', 'resp_rate_obs', 'plateau_pressure_obs',
                    'peak_inspiratory_pressure_obs', 'peep_obs', 'minute_vent_obs',
                    'mean_airway_pressure_obs'
                ]
                long_format = pd.melt(
                    data,
                    id_vars=['device_category'],  
                    value_vars=columns_to_pair,  
                    var_name='attribute',        
                    value_name='value'           
                )
                overall_category_summary = long_format.groupby(['device_category', 'attribute'])['value'].describe()
                overall_category_summary = overall_category_summary.reset_index()
                st.write(overall_category_summary)
                cat_summary_csv = overall_category_summary.to_csv(index=False)
                if download_path is not None:
                    with open(os.path.join(download_path, f"{TABLE}_category_summary_stats.csv"), 'w') as file:
                        file.write(cat_summary_csv)
                    logger.info(f"Summary statistics saved to {download_path}/{TABLE}_category_summary_stats.csv")
                logger.info("Displayed category summary statistics.")
                
                # Device Category with Mode Category Summary
                st.write("### Device Category with Mode Category Summary")
                mode_long_format = pd.melt(
                    df,
                    id_vars=['device_category', 'mode_category'],  
                    value_vars=columns_to_pair,  
                    var_name='attribute',        
                    value_name='value'           
                )
                mode_category_summary = mode_long_format.groupby(['device_category', 'mode_category', 'attribute'])['value'].describe()
                mode_category_summary = mode_category_summary.reset_index()
                st.write(mode_category_summary)
                mode_summary_csv = mode_category_summary.to_csv(index=False)
                if download_path is not None:
                    with open(os.path.join(download_path, f"{TABLE}_mode_summary_stats.csv"), 'w') as file:
                        file.write(mode_summary_csv)
                    logger.info(f"Summary statistics saved to {download_path}/{TABLE}_mode_summary_stats.csv")
                logger.info("Displayed category mode summary statistics.")
        
            
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
                            # mapping_csv = mapping.drop("index", axis = 1).to_csv(index=False)
                            mapping_csv = mapping.reset_index(drop=True).to_csv(index=False)
                            with open(os.path.join(download_path, f"{TABLE}_{mapping_name}_mapping.csv"), 'w') as file:
                                file.write(mapping_csv)
                            logger.info(f"Name to Category Mappings saved to {download_path}/{TABLE}_{mapping_name}_mapping.csv")
                        except Exception as e:
                            logger.error(f"Failed to save Name to Category Mappings to {download_path}/{TABLE}_{mapping_name}_mapping.csv: {str(e)}")


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
            # if st.session_state:
                st.write("## Summary")
                for i, point in enumerate(qc_summary):
                    st.markdown(f"{i + 1}. {point}")

                st.write("## Recommendations")
                for i, recommendation in enumerate(qc_recommendations):
                    st.markdown(f"{i + 1}. {recommendation}")
        
        logger.info("Displayed QC Summary and Recommendations.")

    else:
        st.write(f"Please upload {TABLE} data to proceed.")
        logger.warning(f"Please upload {TABLE} data to proceed.")

    logger.info(f"!!! Completed QC for {TABLE}.")   

