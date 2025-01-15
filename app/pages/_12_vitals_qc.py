import streamlit as st
import pandas as pd
import logging
import time
from common_qc import check_required_variables, check_categories_exist
from common_qc import replace_outliers_with_na_long, generate_facetgrid_histograms, generate_summary_stats
from common_qc import validate_and_convert_dtypes, name_category_mapping, read_data
from logging_config import setup_logging
from common_features import set_bg_hack_url
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO

def show_vitals_qc():
    '''
    '''
    set_bg_hack_url()

    #Initialize logger
    setup_logging()
    logger = logging.getLogger(__name__)

    # Page title
    TABLE = "Vitals"
    table = "clif_vitals"
    st.title(f"{TABLE} Quality Check")

    logger.info(f"!!! Starting QC for {TABLE}.")

    # Main
    qc_summary = []
    qc_recommendations = []

    if table in st.session_state:
        
        # Sampling option
        if 'sampling_option' in st.session_state:
            sampling_rate = st.session_state['sampling_option']
        else:
            sampling_rate = 100

            st.info("Significant load time for Vitals QC. Please be patient.", icon="ℹ️")
            progress_bar = st.progress(0, text="Quality check in progress. Please wait...")

            # Start time
            start_time = time.time()

            progress_bar.progress(5, text='File found...')

            progress_bar.progress(10, text='Starting QC...')

            # 1. Vitals Detailed QC 
            with st.expander("Expand to view", expanded=False):
                # Load the file
                with st.spinner("Loading data..."):
                    progress_bar.progress(15, text='Loading data...')
                    logger.info("~~~ Loading data ~~~")

                    if sampling_rate < 100:
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
                st.write(f"## {TABLE} Data Preview")
                with st.spinner("Loading data preview..."):
                    progress_bar.progress(20, text='Loading data preview...')
                    logger.info("~~~ Displaying data ~~~")
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
                    data, validation_results = validate_and_convert_dtypes(TABLE, data)
                    validation_df = pd.DataFrame(validation_results, columns=['Column', 'Actual', 'Expected', 'Status'])
                    mismatch_columns = [row[0] for row in validation_results if row[3] == 'Mismatch']
                    if mismatch_columns:
                        qc_summary.append(f"Column(s) with mismatched data types: {mismatch_columns}")
                        qc_recommendations.append(f"Column(s) with mismatched data types: {mismatch_columns}. Please review and convert to the expected data types.")
                    st.write(validation_df)
                    logger.info("Data type validation completed.")


                # Display missingness for each column
                st.write(f"## Missingness")
                with st.spinner("Checking for missing values..."):
                    progress_bar.progress(40, text='Checking for missing values...')
                    logger.info("~~~ Checking for missing values ~~~")
                    missing_counts = data.isnull().sum()
                    if missing_counts.any():
                        missing_percentages = (missing_counts / total_counts) * 100
                        missing_info = pd.DataFrame({
                            'Missing Count': missing_counts,
                            'Missing Percentage': missing_percentages.map('{:.2f}%'.format)
                        })
                        missing_info_sorted = missing_info.sort_values(by='Missing Count', ascending=False)
                        st.write(missing_info_sorted)
                        qc_summary.append("Missing values found in columns - " + ', '.join(missing_info[missing_info['Missing Count'] > 0].index.tolist()))
                    else:
                        st.write("No missing values found in all required columns.")
                    logger.info("Checked for missing values.")


                # Check for required columns    
                logger.info("~~~ Checking for required columns ~~~")  
                st.write(f"## {TABLE} Required Columns")
                with st.spinner("Checking for required columns..."):
                    progress_bar.progress(50, text='Checking for required columns...')
                    required_cols_check = check_required_variables(TABLE, data)
                    st.write(required_cols_check)
                    qc_summary.append(required_cols_check)
                    if required_cols_check != f"All required columns present for '{TABLE}'.":
                        qc_recommendations.append("Some required columns are missing. Please ensure all required columns are present.")  
                        logger.warning("Some required columns are missing.")
                    logger.info("Checked for required columns.")

    
                # Check for presence of all vital categories
                logger.info("~~~ Checking for presence of all vital categories ~~~")
                vitals_outlier_thresholds_filepath = "thresholds/nejm_outlier_thresholds_vitals.csv"
                vitals_outlier_thresholds = read_data(vitals_outlier_thresholds_filepath, 'csv')
                st.write('## Presence of All Vital Categories')
                with st.spinner("Checking for presence of all vital categories..."):
                    progress_bar.progress(60, text='Checking for presence of all vital categories...')
                    similar_cats, missing_cats = check_categories_exist(data, vitals_outlier_thresholds, 'vital_category')    
                    if missing_cats:
                        if similar_cats:
                            qc_summary.append("Some vital categories are missing. Similar categories are present.")
                            qc_recommendations.append("Some vital categories are missing. Please ensure all lab categories are present. Review similar categories for potential duplicates.")
                            st.write("##### Missing categories:")
                            with st.container(border=True):
                                cols = st.columns(3)  
                                for i, missing in enumerate(missing_cats):  
                                    col = cols[i % 3]  
                                    col.markdown(f"{i + 1}. {missing}")
                            logger.warning("Missing vital categories found. Similar categories found.")
                        else:
                            qc_summary.append("Some vital categories are missing. No similar categories found.")
                            qc_recommendations.append("Some vital categories are missing. Please ensure all vital categories are present. No similar categories found.")
                            st.write("##### Missing categories:")
                            with st.container(border=True):
                                cols = st.columns(3)  
                                for i, missing in enumerate(missing_cats):  
                                    col = cols[i % 3]  
                                    col.markdown(f"{i + 1}. {missing}")
                            logger.warning("Missing vital categories found. No similar categories found.")
                    else:
                        st.write("All vital categories are present.")
                        qc_summary.append("All vital categories are present.")
                        logger.info("All vital categories are present.")
 
             
                # Vitals category summary statistics
                logger.info("~~~ Generating vital category summary statistics ~~~")
                st.write("## Vital Category Summary Statistics")
                with st.spinner("Generating vital category summary statistics..."):
                    progress_bar.progress(70, text='Generating vital category summary statistics...')
                    vitals_summary_stats = generate_summary_stats(data, 'vital_category', 'vital_value')
                    st.write(vitals_summary_stats)
                    logger.info("Vital category summary statistics displayed.")

                st.write("## Outliers")
                with st.spinner("Checking for outliers..."):
                    data, replaced_count, _, _ = replace_outliers_with_na_long(data, vitals_outlier_thresholds, 'vital_category', 'vital_value')
                    if replaced_count > 0:
                        st.write(replaced_count, "outliers found in the data.")
                        qc_summary.append("Outliers found in data.")
                        qc_recommendations.append("Outliers found. Please replace values with NA.")
                        st.write("<a href='https://github.com/kaveriC/CLIF-1.0/blob/main/outlier-handling/nejm_outlier_thresholds_vitals.csv' id='labs_thresh'>Acceptable vitals thresholds.</a>", unsafe_allow_html=True)


                # Value Distribution - Vital Categories
                st.write("## Value Distribution* - Vital Categories")
                st.write("###### * With Outliers")
                with st.spinner("Displaying value distribution - vital categories..."):
                    progress_bar.progress(80, text='Displaying value distribution - vital categories...')
                    logger.info("~~~ Displaying value distribution - vital categories ~~~") 
                    vitals_plot = generate_facetgrid_histograms(df, 'vital_category', 'vital_value')
                    st.pyplot(vitals_plot)
                    logger.info("Value distribution - vital categories displayed.")
                
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

            buffer = BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=letter)
            story = []
            
            # Title
            story.append(Paragraph("Vital Signs Quality Control Report"))
            story.append(Spacer(1, 12))
            
            # Vitals-specific sections
            if 'vital_types' in locals():
                story.append(Paragraph("Vital Signs Types Analysis"))
                # Add vital signs type distribution
                
            if 'range_analysis' in locals():
                story.append(Paragraph("Vital Signs Range Analysis"))
                # Add range analysis for each vital sign
                
            if 'frequency_analysis' in locals():
                story.append(Paragraph("Measurement Frequency Analysis"))
                # Add frequency analysis
            
            # Build and return PDF
            doc.build(story)
            pdf_value = buffer.getvalue()
            buffer.close()
            return pdf_value

    else:
        st.write(f"Please upload {TABLE} data to proceed.")
        logger.warning(f"Please upload {TABLE} data to proceed.")

    logger.info(f"!!! Completed QC for {TABLE}.")  

