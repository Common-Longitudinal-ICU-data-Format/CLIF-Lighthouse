import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import os
import logging
import time
from common_qc import read_data, check_required_variables, non_scientific_format
from common_qc import validate_and_convert_dtypes
from common_qc import setup_logging
from common_features import set_bg_hack_url

def show_encounter_demographic_disposition_qc():
    '''
    '''
    set_bg_hack_url()

    #Initialize logger
    setup_logging()
    logger = logging.getLogger(__name__)

    # Page title
    TABLE = "Encounter_Demographic_Disposition"
    table = "Encounter Demographic Disposition"
    st.title("Encounter Demographic Disposition Quality Check")

    logger.info(f"!!! Starting QC for {TABLE}.")

    # Main 
    qc_summary = []
    qc_recommendations = []

    if 'root_location' in st.session_state and 'filetype' in st.session_state:
        root_location = st.session_state['root_location']
        filetype = st.session_state['filetype']
        filepath = f"{root_location}/rclif/clif_encounter_demographics_dispo.{filetype}"

        logger.info(f"Filepath set to {filepath}")

        if os.path.exists(filepath):
            progress_bar = st.progress(0, text="Quality check in progress. Please wait...")
            logger.info(f"File {filepath} exists.")

            # Start time
            start_time = time.time()

            progress_bar.progress(5, text='File found...')

            progress_bar.progress(10, text='Starting QC...')

            # 1. Encounter Demographic Disposition Detailed QC 
            with st.expander("Expand to view", expanded=False):
                # Load the file
                with st.spinner("Loading data..."):
                    progress_bar.progress(15, text='Loading data...')
                    logger.info("~~~ Loading data ~~~")
                    data = read_data(filepath, filetype)
                    logger.info("Data loaded successfully.")

                # Display the data
                st.write(f"## {table} Data Preview")
                with st.spinner("Loading data preview..."):
                    progress_bar.progress(20, text='Loading data preview...')
                    logger.info("~~~ Displaying data ~~~")
                    total_counts = data.shape[0]
                    ttl_unique_encoutners = data['encounter_id'].nunique()
                    duplicate_count = data.duplicated().sum()
                    st.write(f"Total records: {total_counts}")
                    st.write(f"Total unique encounters: {ttl_unique_encoutners}")
                    if duplicate_count > 0:
                        st.write(f"Duplicate records: {duplicate_count}")
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

               
                # Display summary statistics
                st.write(f"## {table} Summary Statistics")
                with st.spinner("Displaying summary statistics..."):
                    progress_bar.progress(50, text='Displaying summary statistics...')
                    logger.info("~~~ Displaying summary statistics ~~~")
                    pd.options.display.float_format = non_scientific_format
                    encounter_stats = data.describe()
                    st.write(encounter_stats)
                    logger.info("Displayed summary statistics.")

            
                # Check for required columns 
                logger.info("~~~ Checking for required columns ~~~")   
                st.write(f"## {table} Required Columns")
                with st.spinner("Checking for required columns..."):
                    progress_bar.progress(60, text='Checking for required columns...')
                    required_cols_check = check_required_variables(TABLE, data)
                    st.write(required_cols_check)
                    qc_summary.append(required_cols_check)
                    if required_cols_check != f"All required columns present for '{TABLE}'.":
                        qc_recommendations.append("Some required columns are missing. Please ensure all required columns are present.")  
                        logger.warning("Some required columns are missing.")
                    logger.info("Checked for required columns.")

               
                # Check for presence of disposition categories 
                logger.info("~~~ Checking for disposition categories ~~~")
                st.write('## Presence of All Disposition Categories')
                with st.spinner("Checking for disposition categories..."):
                    progress_bar.progress(70, text='Checking for disposition categories...')
                    reqd_categories = pd.DataFrame(["Home", "Discharged to another facility", "Other",
                                "Hospice", "Dead" , "Admitted"], columns=['disposition_category'])
                    categories = data['disposition_category'].unique()
                    if reqd_categories.equals(categories):
                        st.write("All disposition categories are present.")
                        qc_summary.append("All disposition categories are present.")
                        logger.info("All disposition categories are present.")
                    else:
                        st.write("Some disposition categories are missing.")
                        missing_cats = [category for category in reqd_categories['disposition_category'] if category not in categories]
                        with st.container(border=True):
                            cols = st.columns(3)  
                            for i, missing in enumerate(missing_cats):  
                                col = cols[i % 3]  
                                col.markdown(f"{i + 1}. {missing}")
                        qc_summary.append("Some disposition categories are missing.")
                        qc_recommendations.append("Some disposition categories are missing. Please ensure all disposition categories are present.")
                        logger.warning("Some disposition categories are missing.")

                
                    # Disposition category counts
                    st.write("## Disposition Category Counts")
                    with st.spinner("Displaying disposition category counts..."):
                        progress_bar.progress(80, text='Displaying disposition category counts...')
                        logger.info("~~~ Displaying disposition category counts ~~~")
                        counts_disp_categ = data.groupby('disposition_category').size().reset_index(name='n').sort_values(by='n', ascending=False)
                        st.write(counts_disp_categ)
                        logger.info("Displayed disposition category counts.")


                # Check for age at admission outliers
                logger.info("~~~ Checking for age at admission outliers ~~~")
                st.write("## Age at Admission Outliers")
                with st.spinner("Checking for age at admission outliers..."):
                    progress_bar.progress(90, text='Checking for age at admission outliers...')
                    if any(data['age_at_admission'] > 119):
                        qc_summary.append("Age at admission greater than 119 years.")
                        qc_recommendations.append("Age at admission greater than 119 years found. Please replace outliers with 'NaN'.")       
                        st.write("##### Age at admission greater than 119 years found.")          
                    else:
                        qc_summary.append("No age at admission outliers found.")
                        st.write("No age at admission outliers found.")
                    logger.info("Age at admission outliers checked.")

                # Distribution of Age at Admission
                logger.info("~~~ Displaying distribution of age at admission ~~~")
                st.write("## Distribution of Age at Admission")
                with st.spinner("Displaying distribution of age at admission..."):
                    progress_bar.progress(95, text='Displaying distribution of age at admission...')
                    fig, ax = plt.subplots()
                    plt.xlabel("Age at Admission")
                    plt.ylabel("Frequency")
                    ax.hist(data['age_at_admission'], bins=20, color='skyblue', edgecolor='black')
                    st.pyplot(fig)
                    logger.info("Generated facet grid histograms.")

                progress_bar.progress(100, text='Quality check completed. Displaying results...')
                    

            # End time
            end_time = time.time()
            elapsed_time = end_time - start_time
            st.success(f"Quality check completed. Time taken to run summary: {elapsed_time:.2f} seconds", icon="✅")
            logger.info(f"Time taken to run summary: {elapsed_time:.2f} seconds")


            # Display QC Summary and Recommendations
            st.write("# QC Summary and Recommendations")
            logger.info("~~~ Displaying QC Summary and Recommendations ~~~")    

            with st.expander("Expand to view", expanded=False):
                # if st.session_state:
                    st.write("## Summary")
                    for i, point in enumerate(qc_summary):
                        st.markdown(f"{i + 1}. {point}")

                    st.write("## Recommendations")
                    for i, recommendation in enumerate(qc_recommendations):
                        st.markdown(f"{i + 1}. {recommendation}")
            
            logger.info("Displayed QC Summary and Recommendations.")


            # Select and Download revisions to the data
            def apply_changes(data, convert_dtypes, apply_deduplication, apply_outlier_replacement):
                if convert_dtypes:
                    data = validate_and_convert_dtypes(TABLE, data)[0]
                
                if apply_deduplication:
                    data = data.drop_duplicates()

                if apply_outlier_replacement:
                    data.loc[data['age_at_admission'] > 119, 'age_at_admission'] = np.nan

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
                with st.form(key='apply_demog_changes_form'):
                    # Create checkboxes for changes
                    if any(data['age_at_admission'] > 119):
                        apply_outlier_replacement = st.checkbox("Replace age at admission outliers")
                    else:
                        apply_outlier_replacement = False
                    
                    if any(data.duplicated()):
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
                        df = data.copy()
                        revised_data = apply_changes(df, convert_dtypes, apply_deduplication, apply_outlier_replacement)
                        revised_data_file = convert_df_to_file_format(revised_data, file_type)
                        st.write("Successfully applied changes. Click to download revised data.")
                    if revised_data_file:
                        st.download_button(
                            label="Download revised data",
                            data=revised_data_file,
                            file_name=f"revised_{TABLE}_data.{file_type}",
                        )


        else:
            st.write(f"File not found. Please provide the correct root location and file type to proceed.")

    else:
        st.write("Please provide the root location and file type to proceed.")
        logger.warning("Root location and/or file type not provided.")



