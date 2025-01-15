import streamlit as st
import pandas as pd
import logging
import time
from common_qc import read_data, check_required_variables, check_categories_exist
from common_qc import replace_outliers_with_na_long, generate_facetgrid_histograms
from common_qc import validate_and_convert_dtypes, generate_summary_stats, name_category_mapping
from logging_config import setup_logging
from common_features import set_bg_hack_url
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from reportlab.platypus import Image

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
        # Sampling option
        if 'sampling_option' in st.session_state:
            sampling_rate = st.session_state['sampling_option']
        else:
            sampling_rate = 100

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

                if sampling_rate < 100:
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
                if sampling_rate < 100:
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

        # Add this PDF generation code at the end, just before the final else statement
        buffer = BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        title_style = styles['Heading1']
        heading2_style = styles['Heading2']
        normal_style = styles['Normal']
        
        # Title
        story.append(Paragraph("Labs Quality Control Report", title_style))
        story.append(Spacer(1, 12))
        
        # Data Overview
        story.append(Paragraph("Data Overview", heading2_style))
        if 'sampling_option' in st.session_state:
            story.append(Paragraph(f"Total record count before sampling: {total_counts}", normal_style))
            story.append(Paragraph(f"Sample({sampling_rate}%) record count: {sample_counts}", normal_style))
        else:
            story.append(Paragraph(f"Total record count: {total_counts}", normal_style))
        story.append(Paragraph(f"{ttl_smpl} unique hospital encounters: {ttl_unique_encounters}", normal_style))
        if duplicate_count > 0:
            story.append(Paragraph(f"Duplicate records: {duplicate_count}", normal_style))
        else:
            story.append(Paragraph("No duplicate records found.", normal_style))
        story.append(Spacer(1, 12))
        
        # Data Type Validation
        story.append(Paragraph("Data Type Validation", heading2_style))
        validation_data = [
            [Paragraph(str(cell), normal_style) for cell in ['Column', 'Actual', 'Expected', 'Status']]
        ]
        for row in validation_results:
            validation_data.append([Paragraph(str(cell), normal_style) for cell in row])
        t = Table(validation_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('GRID', (0, 0), (-1, -1), 1, colors.black)
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

        # Missingness
        story.append(Paragraph("Missingness", heading2_style))
        if missing_counts.any():
            # Create table data for missing values
            missing_data = [['Column', 'Missing Count', 'Missing Percentage']]
            for col in missing_info_sorted.index:
                missing_data.append([
                    col,
                    str(missing_info_sorted.loc[col, 'Missing Count']),
                    missing_info_sorted.loc[col, 'Missing Percentage']
                ])
            
            # Create and style the table
            t = Table(missing_data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(t)
        else:
            story.append(Paragraph("No missing values found in all required columns.", normal_style))
        story.append(Spacer(1, 12))
        
        # Summary Statistics
        story.append(Paragraph("Summary Statistics", heading2_style))
        
        # Convert summary DataFrame to a list of lists for the table
        summary_data = [['Metric'] + list(summary.columns)]  # Header row
        for idx in summary.index:
            row = [idx] + [f"{x:.2f}" if isinstance(x, (float, int)) else str(x) for x in summary.loc[idx]]
            summary_data.append(row)
        
        # Create and style the table
        t = Table(summary_data)
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 8),  # Smaller font size to fit more columns
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('LEFTPADDING', (0, 0), (-1, -1), 3),
            ('RIGHTPADDING', (0, 0), (-1, -1), 3)
        ]))
        story.append(t)
        story.append(Spacer(1, 12))

        # Required Columns
        story.append(Paragraph(f"{TABLE} Required Columns", heading2_style))
        story.append(Paragraph(str(required_cols_check), normal_style))
        story.append(Spacer(1, 12))

        # Lab Value Numeric Check
        story.append(Paragraph("Lab Value Numeric Check", heading2_style))
        if 'lab_value_numeric' not in data.columns:
            if pd.to_numeric(data['lab_value'], errors='coerce').isna().any():
                story.append(Paragraph("Non-numeric characters present in lab_value", normal_style))
            else:
                story.append(Paragraph("All values in lab_value are numeric", normal_style))
        else:
            story.append(Paragraph("lab_value_numeric column already present", normal_style))
        story.append(Spacer(1, 12))

        # # Check for presence of all lab categories
        # story.append(Paragraph("Presence of All Lab Categories", heading2_style))

        # if missing_cats:
        #     if similar_cats:
        #         story.append(Paragraph("##### Missing categories:", normal_style))
        #         for i, missing in enumerate(missing_cats, start=1):
        #             story.append(Paragraph(f"{i}. {missing}", normal_style))
        #     else:
        #         story.append(Paragraph("##### Missing categories:", normal_style))
        #         for i, missing in enumerate(missing_cats, start=1):
        #             story.append(Paragraph(f"{i}. {missing}", normal_style))
        # else:
        #     story.append(Paragraph("All lab categories are present.", normal_style))
        # story.append(Spacer(1, 12))

        # Add summary to the story
        story.append(Spacer(1, 12))
        story.append(Paragraph("QC Summary", heading2_style))
        for point in qc_summary:
            story.append(Paragraph(f"• {point}", normal_style))
        story.append(Spacer(1, 12))

        if qc_recommendations:
            story.append(Paragraph("Recommendations", heading2_style))
            for rec in qc_recommendations:
                story.append(Paragraph(f"• {rec}", normal_style))
        story.append(Spacer(1, 12))

        
        # Lab Category Summary Statistics
        story.append(Paragraph("Lab Category Summary Statistics", heading2_style))
        story.append(Spacer(1, 12))
        
        # Convert lab_summary_stats DataFrame to table format
        lab_stats_data = [['Category'] + list(lab_summary_stats.columns)]  # Header row
        for category in lab_summary_stats.index:
            row = [category]
            for value in lab_summary_stats.loc[category]:
                if pd.isna(value):
                    row.append('N/A')
                elif isinstance(value, (float, int)):
                    row.append(f"{value:,.2f}")  # Format numbers with commas and 2 decimal places
                else:
                    row.append(str(value))
            lab_stats_data.append(row)
        
        # Create and style the table with better formatting
        t = Table(lab_stats_data, repeatRows=1)  # repeatRows=1 makes header repeat on new pages
        t.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            
            # Data cell styling
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 7),  # Smaller font size
            ('ALIGN', (0, 0), (0, -1), 'LEFT'),  # Left align category names
            ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),  # Right align numbers
            
            # Grid styling
            ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
            ('BOX', (0, 0), (-1, -1), 1, colors.black),
            
            # Padding
            ('LEFTPADDING', (0, 0), (-1, -1), 4),
            ('RIGHTPADDING', (0, 0), (-1, -1), 4),
            ('TOPPADDING', (0, 0), (-1, -1), 3),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
            
            # Alternate row colors
            ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
        ]))
        
        # Wrap table in a try-except block to handle potential width issues
        try:
            available_width = letter[0] - 40  # Page width minus margins
            story.append(t)
        except:
            # If table is too wide, create a smaller version with essential columns
            essential_cols = ['count', 'mean', 'std', 'min', 'max']
            lab_stats_essential = lab_summary_stats[essential_cols]
            lab_stats_data = [['Category'] + list(lab_stats_essential.columns)]
            for category in lab_stats_essential.index:
                row = [category]
                for value in lab_stats_essential.loc[category]:
                    if pd.isna(value):
                        row.append('N/A')
                    elif isinstance(value, (float, int)):
                        row.append(f"{value:,.2f}")
                    else:
                        row.append(str(value))
                lab_stats_data.append(row)
            
            t = Table(lab_stats_data, repeatRows=1)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#333333')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
                ('FONTSIZE', (0, 0), (-1, -1), 7),
                ('ALIGN', (0, 0), (0, -1), 'LEFT'),
                ('ALIGN', (1, 0), (-1, -1), 'RIGHT'),
                ('GRID', (0, 0), (-1, -1), 0.25, colors.grey),
                ('BOX', (0, 0), (-1, -1), 1, colors.black),
                ('LEFTPADDING', (0, 0), (-1, -1), 4),
                ('RIGHTPADDING', (0, 0), (-1, -1), 4),
                ('TOPPADDING', (0, 0), (-1, -1), 3),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 3),
                ('ROWBACKGROUNDS', (0, 0), (-1, -1), [colors.white, colors.HexColor('#f5f5f5')]),
            ]))
            story.append(t)
        
        story.append(Spacer(1, 12))

        # Outliers Section
        story.append(Paragraph("Outliers Analysis", heading2_style))
        if replaced_count > 0:
            story.append(Paragraph(f"{replaced_count} outliers found in the data.", normal_style))
            story.append(Paragraph("Outliers by Category:", normal_style))
            
            # Create table for outliers summary
            outlier_data = [['Category', 'Range*', 'Outlier (%)']]  # Header row
            for summary in all_outliers_summary:
                outlier_data.append([
                    summary['Category'],
                    summary['Range*'],
                    f"{summary['Outlier (%)']}"
                ])
            
            # Create and style the outliers table
            t = Table(outlier_data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(t)
            story.append(Paragraph("* preference range", styles['Italic']))
        else:
            story.append(Paragraph("No outliers found in the data.", normal_style))
        story.append(Spacer(1, 12))

        # Value Distribution Plot
        story.append(Paragraph("Lab Category Value Distribution", heading2_style))
        story.append(Paragraph("* Without Outliers", styles['Italic']))
        
        # Save the matplotlib figure to a temporary buffer
        img_buffer = BytesIO()
        labs_plot.savefig(img_buffer, format='png', bbox_inches='tight')
        img_buffer.seek(0)
        
        # Add the plot to the PDF
        # Scale the image to fit the page width (adjust dimensions as needed)
        img = Image(img_buffer, width=450, height=300)
        story.append(img)
        story.append(Spacer(1, 12))

        # Name to Category Mapping
        story.append(Paragraph("Name to Category Mapping", heading2_style))
        for mapping in mappings:
            mapping_name = mapping.columns[0]
            mapping_cat = mapping.columns[1]
            story.append(Paragraph(f"Mapping {mapping_name} to {mapping_cat}:", normal_style))
            mapping_data = [
                [Paragraph(str(cell), normal_style) for cell in mapping.columns.tolist()]
            ]
            for row in mapping.values:
                mapping_data.append([Paragraph(str(cell), normal_style) for cell in row])
            t = Table(mapping_data)
            t.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            story.append(t)
            story.append(Spacer(1, 12))

        # Summary and Recommendations
        story.append(Paragraph("QC Summary", heading2_style))
        for point in qc_summary:
            story.append(Paragraph(f"• {point}", normal_style))
        story.append(Spacer(1, 12))
        
        if qc_recommendations:
            story.append(Paragraph("Recommendations", heading2_style))
            for rec in qc_recommendations:
                story.append(Paragraph(f"• {rec}", normal_style))

        # Build the PDF
        doc.build(story)
        pdf_value = buffer.getvalue()
        buffer.close()
        return pdf_value

    else:
        st.write(f"Please upload {TABLE} data to proceed.")
        logger.warning(f"Please upload {TABLE} data to proceed.")

    logger.info(f"!!! Completed QC for {TABLE}.")       


