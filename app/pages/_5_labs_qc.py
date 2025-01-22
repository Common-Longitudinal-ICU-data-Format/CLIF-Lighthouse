import streamlit as st
import pandas as pd
import logging
import time
import os
from common_qc import read_data, check_required_variables, check_categories_exist
from common_qc import replace_outliers_with_na_long, generate_facetgrid_histograms
from common_qc import validate_and_convert_dtypes, generate_summary_stats, name_category_mapping
from logging_config import setup_logging
from common_features import set_bg_hack_url


def show_labs_qc():
    '''
    '''
    set_bg_hack_url()

    #Initialize logger
    setup_logging()
    logger = logging.getLogger(__name__)

    # Page title
    TABLE = "Labs"
    table = "clif_labs"
    st.title(f"{TABLE} Quality Check")

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
        
        # 1. Labs Detailed QC 
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

                logger.info("Data loaded successfully.")
                df = data.copy()
            

            # Display the data
            logger.info("~~~ Displaying data ~~~")
            st.write(f"## {TABLE} Data Preview")
            with st.spinner("Loading data preview..."):
                progress_bar.progress(20, text='Loading data preview...')
                total_counts = data.shape[0]
                # ttl_unique_patients = data['patient_id'].nunique()
                ttl_unique_encounters = data['hospitalization_id'].nunique()
                duplicate_count = data.duplicated().sum()
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
                # st.write(f"Total unique patients: {ttl_unique_patients}")
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
                missing_counts = data.isnull().sum()
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


            # Display summary statistics  
            st.write(f"## {TABLE} Summary Statistics")
            with st.spinner("Displaying summary statistics..."):
                progress_bar.progress(55, text='Displaying summary statistics...')
                logger.info("~~~ Displaying summary statistics ~~~")  
                summary = data.describe(include="all")
                summary_csv = summary.to_csv(index=True)
                if download_path is not None:
                    with open(os.path.join(download_path, f"{TABLE}_summary_statistics.csv"), 'w') as file:
                        file.write(summary_csv)
                    logger.info(f"Summary statistics saved to {download_path}/{TABLE}_summary_statistics.csv")
                st.write(summary)
                logger.info("Displayed summary statistics.")


            # Check for required columns
            st.write(f"## {TABLE} Required Columns")
            with st.spinner("Checking for required columns..."):
                progress_bar.progress(60, text='Checking for required columns...')
                logger.info("~~~ Checking for required columns ~~~")    
                required_cols_check = check_required_variables(TABLE, data)
                st.write(required_cols_check)
                qc_summary.append(required_cols_check)
                if required_cols_check != f"All required columns present for '{TABLE}'.":
                    qc_recommendations.append("Some required columns are missing. Please ensure all required columns are present.")  
                    logger.warning("Some required columns are missing.")
                logger.info("Checked for required columns.")


            # Additional check for lab_value_numeric
            st.write("## Checking 'lab_value' for Non-Numeric Characters")
            with st.spinner("Checking lab_value for non-numeric characters..."):
                progress_bar.progress(65, text='Checking for lab_value_numeric...')
                logger.info("~~~ Checking for lab_value_numeric ~~~")
                if 'lab_value_numeric' not in data.columns:
                    if pd.to_numeric(data['lab_value'], errors='coerce').isna().any():
                        logger.info("Non-numeric characters present in lab_value.")
                        qc_summary.append("Non-numeric characters present in lab_value.")
                        qc_recommendations.append("Recommend extracting numeric values and creating a new column - 'lab_value_numeric'.")
                        col = data['lab_value'].astype(str)
                        data['lab_value_numeric'] = pd.to_numeric(col.str.extract('(\d+\.?\d*)', expand=False), errors='coerce')
                        logger.info("Created 'lab_value_numeric' column.")
                        st.write("Non-numeric characters present in lab_value.")
                    else:
                        logger.info("All values in lab_value are numeric.")
                        st.write("All values in lab_value are numeric.")
                else:
                    logger.info("lab_value_numeric already present.")
                    st.write("lab_value_numeric already present.")


            # Check for presence of all lab categories
            st.write('## Presence of All Lab Categories')
            with st.spinner("Checking for presence of all lab categories..."):
                progress_bar.progress(70, text='Checking for presence of all lab categories...')
                logger.info("~~~ Checking for presence of all lab categories ~~~")  
                labs_outlier_thresholds_filepath = "thresholds/nejm_outlier_thresholds_labs.csv"
                labs_outlier_thresholds = pd.read_csv(labs_outlier_thresholds_filepath)
                similar_cats, missing_cats = check_categories_exist(data, labs_outlier_thresholds, 'lab_category')
                if missing_cats:
                    if similar_cats:
                        qc_summary.append("Some lab categories are missing. "
                            f"Similar categories found: {', '.join([f'{orig} -> {sim}' for orig, sim in similar_cats])}. "
                            "Please ensure all lab categories are present and review similar categories for potential duplicates."
                        )
                        st.write("##### Missing categories:")
                        with st.container(border=True):
                            cols = st.columns(3) 
                            for i, missing in enumerate(missing_cats):  
                                col = cols[i % 3]  
                                col.markdown(f"{i + 1}. {missing}")
                        logger.warning("Missing lab categories found.")
                    else:
                        qc_summary.append("Some lab categories are missing. No similar categories found.")
                        qc_recommendations.append("Some lab categories are missing. Please ensure all lab categories are present. No similar categories found.")
                        st.write("##### Missing categories:")
                        with st.container(border=True):
                            cols = st.columns(3)  
                            for i, missing in enumerate(missing_cats):  
                                col = cols[i % 3]  
                                col.markdown(f"{i + 1}. {missing}")
                        logger.warning("Missing lab categories found. No similar categories found.")
                else:
                    st.write("All lab categories are present.")
                    qc_summary.append("All lab categories are present.")
                    logger.info("All lab categories are present.")
                logger.info("Checked for presence of all lab categories.")


            # Lab Category Summary Statistics
            st.write("## Lab Category Summary Statistics")
            with st.spinner("Summarizing lab categories..."):
                progress_bar.progress(75, text='Summarizing lab categories...')
                logger.info("~~~ Summarizing lab categories ~~~")  
                lab_summary_stats = generate_summary_stats(data, 'lab_category', 'lab_value_numeric')
                lab_summary_stats_csv = lab_summary_stats.to_csv(index=True)
                if download_path is not None:
                    with open(os.path.join(download_path, f"{TABLE}_summary_stats.csv"), 'w') as file:
                        file.write(lab_summary_stats_csv)
                    logger.info("Lab category summary statistics saved to lab_category_summary_stats.csv")
                st.write(lab_summary_stats)
                logger.info("Generated lab category summary statistics.")

            # Check for outliers
            st.write("## Outliers")
            with st.spinner("Checking for outliers..."):
                progress_bar.progress(77, text='Checking for outliers...')
                logger.info("Displaying outlier count...")
                data, replaced_count, _, outlier_details = replace_outliers_with_na_long(data, labs_outlier_thresholds, 'lab_category', 'lab_value_numeric')
                if replaced_count > 0:
                    st.write(replaced_count, "outliers found in the data. <a href='https://github.com/clif-consortium/CLIF/blob/main/outlier-handling/outlier_thresholds_labs.csv' id='labs_thresh'>Acceptable lab category thresholds.</a>", unsafe_allow_html=True)
                    st.write("###### * preference range")
                    all_outliers_summary = []
                    for detail in outlier_details:
                        if any(detail[3]):
                            category, lower, upper, outliers = detail
                            # Append details to the summary list
                            all_outliers_summary.append({
                                "Category": category,
                                "Range*": f"{lower} - {upper}",
                                "Outlier (%)": (len(outliers)/total_counts * 100).__round__(2),
                            })
                            outlier_percent = ((len(outliers) / total_counts) * 100).__round__(2)
                            qc_summary.append(f"A total of {len(outliers)} or {outlier_percent}% outlier(s) in {category}.")
                        qc_recommendations.append("Outliers need to be replaced. Please review the outliers and replace them with recommended values.")
                    if all_outliers_summary:
                        outliers_df = pd.DataFrame(all_outliers_summary)
                        outliers_df = outliers_df.sort_values(by='Outlier (%)', ascending=False)
                        st.write(outliers_df)
                        # Save outliers information to CSV
                        outliers_info_csv = outliers_df.to_csv(index=True)
                        if download_path is not None:
                            with open(os.path.join(download_path, f"{TABLE}_outliers.csv"), 'w') as file:
                                file.write(outliers_info_csv)
                            logger.info("Outliers information saved to lab_outliers.csv")
                else:
                    st.write("No outliers found.")
                    qc_summary.append("No outliers found.")
    

            # Lab Category Value Distribution
            st.write("## Value Distribution - Lab Categories")
            st.write("###### * Without Outliers")
            with st.spinner("Displaying lab category value distribution..."):
                progress_bar.progress(80, text='Displaying lab category value distribution...')
                logger.info("~~~ Displaying lab category value distribution ~~~")
                labs_plot = generate_facetgrid_histograms(data, 'lab_category', 'lab_value_numeric')
                if download_path is not None:
                    labs_plot.savefig(os.path.join(download_path, f"{TABLE}_category_value_distribution.png"))
                    logger.info("Lab category value distribution saved to lab_category_value_distribution.png")
                st.pyplot(labs_plot)
                logger.info("Value distribution - lab categories displayed.")
        
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

            progress_bar.progress(100, text='Quality check completed. Results displayed below.')
        

        # End time
        end_time = time.time()
        elapsed_time = end_time - start_time
        st.success(f"Quality check completed. Time taken to run summary: {elapsed_time:.2f} seconds", icon="✅")
        logger.info(f"Time taken to QC: {elapsed_time:.2f} seconds")

        # 2. Display QC Summary and Recommendations
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


