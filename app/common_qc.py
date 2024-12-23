import pandas as pd
import numpy as np
import pyarrow.parquet as pq
import matplotlib.pyplot as plt
import seaborn as sns
import logging
import os
from fuzzywuzzy import fuzz 
from logging_config import setup_logging
from common_features import set_bg_hack_url
from reqd_vars_dtypes import required_variables, expected_data_types

# pages_layout()
# set_bg_hack_url()
# set_sidebar()

# Initialize logger
# setup_logging()
# logger = logging.getLogger(__name__)

# Common Functions
def read_data(filepath, filetype):
    """
    Read data from file based on file type.
    Parameters:
        filepath (str): Path to the file.
        filetype (str): Type of the file ('csv' or 'parquet').
    Returns:
        DataFrame: DataFrame containing the data.
    """
    if filetype == 'csv':
        return pd.read_csv(filepath)
    elif filetype == 'parquet':
        table = pq.read_table(filepath)
        return table.to_pandas()
    elif filetype == 'fst':
        return pd.read_fwf(filepath)
    else:
        raise ValueError("Unsupported file type. Please provide either 'csv', 'fst' or 'parquet'.")

def check_required_variables(table_name, df): ### Modified from original
    """
    Check if all required variables exist in the DataFrame.
    
    Parameters:
        required_variables (list): List of required variable names.
        df (DataFrame): DataFrame to check.

    Returns:
        list: List of missing variables.
    """
    required_vars = required_variables[table_name]
    missing_variables = [var for var in required_vars if var not in df.columns]
    if missing_variables:
        return f"Missing required columns for '{table_name}': {missing_variables}"
    else:
        return f"All required columns present for '{table_name}'."

def generate_summary_stats(data, category_column, value_column):
    """
    Generate summary statistics for a DataFrame based on a specified category column and value column.

    Parameters:
        data (DataFrame): DataFrame containing the data.
        category_column (str): Name of the column containing categories.
        value_column (str): Name of the column containing values.

    Returns:
        DataFrame: DataFrame containing summary statistics.
    """
    summary_stats = data.groupby([category_column]).agg(
        N=(value_column, 'count'),
        Missing=(value_column, lambda x: (x.isnull().sum()/data.shape[0])*100),
        Min=(value_column, 'min'),
        Mean=(value_column, 'mean'),
        Q1=(value_column, lambda x: x.quantile(0.25)),
        Median=(value_column, 'median'),
        Q3=(value_column, lambda x: x.quantile(0.75)),
        Max=(value_column, 'max')
    ).reset_index().sort_values(by=[category_column], ascending=True)

    summary_stats = summary_stats.rename(columns={category_column: 'Category', 'Missing': 'Missing (%)'})

    return summary_stats

def find_closest_match(label, labels):
    closest_label = None
    highest_similarity = -1
    for lab_label in labels:
        similarity = fuzz.partial_ratio(label, lab_label)
        if similarity > highest_similarity:
            closest_label = lab_label
            highest_similarity = similarity
    return closest_label, highest_similarity

def check_categories_exist(data, outlier_thresholds, category_column):
    """
    Check if categories in outlier thresholds match with categories in the data DataFrame.

    Parameters:
        data (DataFrame): DataFrame containing the data.
        outlier_thresholds (DataFrame): DataFrame containing outlier thresholds.
        category_column (str): Name of the column containing categories.

    Returns:
        None
    """
    categories = data[category_column].unique()
    # Lower case categories
    categories = [category.lower() for category in categories]
    missing_categories = []
    similar_categories = []

    # Iterate through outlier_thresholds DataFrame
    for _, row in outlier_thresholds.iterrows():
        category = row[category_column]
        # Check if category exists in data categories
        if category not in categories:
            # If not found, find closest match
            closest_match, similarity = find_closest_match(category, categories)
            if similarity >= 90:  # Set a threshold for similarity score
                similar_categories.append((category, closest_match))
            else:
                missing_categories.append(category)  
    return similar_categories, missing_categories

def replace_outliers_with_na_long(df, df_outlier_thresholds, category_variable, numeric_variable):
    """
    Replace outliers in the labs DataFrame with NaNs based on outlier thresholds.

    Parameters:
        df (DataFrame): DataFrame containing lab data.
        df_outlier_thresholds (DataFrame): DataFrame containing outlier thresholds.

    Returns:
        DataFrame: Updated DataFrame with outliers replaced with NaNs.
        int: Count of replaced observations.
        float: Proportion of replaced observations.
    """
    replaced_count = 0
    outlier_details = []

    for _, row in df_outlier_thresholds.iterrows():
        rclif_category = row[category_variable]
        lower_limit = row['lower_limit']
        upper_limit = row['upper_limit']
        # Filter DataFrame for the current category
        recorded_values = df.loc[df[category_variable] == rclif_category, numeric_variable]
        # Identify outliers
        outliers = recorded_values[(recorded_values < lower_limit) | (recorded_values > upper_limit)]
        # Store outlier details for display
        outlier_details.append((rclif_category, lower_limit, upper_limit, outliers))
        # Replace values outside the specified range with NaNs
        replaced_count += len(outliers)
        df.loc[df[category_variable] == rclif_category, numeric_variable] = np.where((recorded_values < lower_limit) | (recorded_values > upper_limit), np.nan, recorded_values)

    total_count = len(df)
    proportion_replaced = replaced_count / total_count
    df.reset_index(drop=True, inplace=True)

    return df, replaced_count, proportion_replaced, outlier_details

def replace_outliers_with_na_wide(data, outlier_thresholds):
    """
    Replace outliers with NA values in a DataFrame based on specified lower and upper limits.

    Parameters:
        data (DataFrame): DataFrame containing the data.
        outlier_thresholds (DataFrame): DataFrame containing outlier thresholds.

    Returns:
        DataFrame: DataFrame with outliers replaced by NA values.
        int: Total number of observations replaced with NA.
        float: Proportion of observations replaced with NA.
    """
    # Initialize variables to record replaced observations
    total_replaced = 0
    outlier_details = []

    # Iterate over each column in the DataFrame
    for col in outlier_thresholds['variable_name']:
        # Get lower and upper limits for the current column
        lower_limit = outlier_thresholds.loc[outlier_thresholds['variable_name'] == col, 'lower_limit'].values[0]
        upper_limit = outlier_thresholds.loc[outlier_thresholds['variable_name'] == col, 'upper_limit'].values[0]

        # Replace outliers with NA values
        outliers_mask = (data[col] < lower_limit) | (data[col] > upper_limit)
        outlier_details.append((col, lower_limit, upper_limit, data.loc[outliers_mask, col]))
        total_replaced += outliers_mask.sum()
        data.loc[outliers_mask, col] = np.nan

    # Calculate proportion of replaced observations
    total_observations = data.shape[0]
    proportion_replaced = total_replaced / total_observations

    return data, total_replaced, proportion_replaced, outlier_details

def generate_facetgrid_histograms(data, category_column, value_column):
    """
    Generate histograms using seaborn's FacetGrid.

    Parameters:
        data (DataFrame): DataFrame containing the data.
        category_column (str): Name of the column containing categories.
        value_column (str): Name of the column containing values.

    Returns:
        FacetGrid: Seaborn FacetGrid object containing the generated histograms.
    """
    # Create a FacetGrid
    g = sns.FacetGrid(data, col=category_column, col_wrap=3, sharex=False, sharey=False)
    g.map(sns.histplot, value_column, bins=30, color='dodgerblue', edgecolor='black')

    # Set titles and labels
    g.set_titles(col_template='{col_name}')
    g.set_axis_labels(value_column, 'Frequency')

    # Adjust layout and add a main title
    plt.subplots_adjust(top=0.9, hspace=0.4, wspace=0.4)

    return g

def non_scientific_format(x):
    """
    Format a number in non-scientific notation with 2 decimal places.
    """
    return '%.2f' % x

def plot_histograms_by_device_category(data, selected_category, selected_mode = None):
    """
    Plot histograms of a variable for a specific device category.

    Parameters:
        data (DataFrame): DataFrame containing the data.
        selected_category (str): Selected device category.
    """
    variables_to_plot = ["fio2_set", "lpm_set", "tidal_volume_set", "resp_rate_set", 
            "pressure_control_set", "pressure_support_set", "flow_rate_set", 
            "peak_inspiratory_pressure_set", "inspiratory_time_set", "peep_set", 
            "tidal_volume_obs", "resp_rate_obs", "plateau_pressure_obs", 
            "peak_inspiratory_pressure_obs", "peep_obs", "minute_vent_obs"]
    variables_to_plot.sort()
    if selected_mode:
        filtered_df = data[(data['device_category'] == selected_category) & (data['mode_category'] == selected_mode)]
    else:
        filtered_df = data[data['device_category'] == selected_category]
    data_melted = filtered_df.melt(value_vars=variables_to_plot, 
                                var_name='Variable', value_name='Value')
    g = sns.FacetGrid(data_melted, col="Variable", col_wrap=4, sharex=False, sharey=False)
    g.map(sns.histplot, "Value", kde=False, bins=20)
    g.set_titles("{col_name}")
    g.set_axis_labels("Value", "Count")
    plt.subplots_adjust(top=0.9, hspace=0.4, wspace=0.4)
    return g


def validate_and_convert_dtypes(table_name, data):
    """
    Validate and convert data types of columns in the DataFrame 
    based on expected data types.

    Parameters:
        table_name (str): Name of the table.
        data (DataFrame): DataFrame to validate and convert data types.

    Returns:
        DataFrame: The converted DataFrame.
        List: Validation results containing column name, actual dtype, 
              expected dtype, and validation status.
    """
    expected_dtypes = expected_data_types[table_name]
    validation_results = []

    for column, expected_dtype in expected_dtypes.items():
        if column in data.columns:
            actual_dtype = data[column].dtype

            # Check if the expected type is datetime64
            if expected_dtype == 'datetime64':
                # Ensure the column is in a valid datetime format
                if not pd.api.types.is_datetime64_any_dtype(actual_dtype):
                    validation_results.append((column, actual_dtype, 'datetime64', 'Mismatch'))
                    try:
                        # Attempt to convert to datetime, coerce errors to NaT
                        data[column] = pd.to_datetime(data[column], errors='coerce')
                        # validation_results[-1] = (column, actual_dtype, expected_dtype, 'Converted')
                    except Exception as e:
                        logger.error(f"Error converting column {column} to datetime: {e}")
                else:
                    validation_results.append((column, actual_dtype, 'datetime64', 'Match'))

            # Handle non-datetime expected types
            elif actual_dtype != expected_dtype:
                validation_results.append((column, actual_dtype, expected_dtype, 'Mismatch'))
                try:
                    # Convert to the expected dtype
                    if expected_dtype == 'float64':
                        data[column] = pd.to_numeric(data[column], errors='coerce')
                    elif expected_dtype == 'bool':
                        data[column] = data[column].astype('bool')
                    else:
                        data[column] = data[column].astype(expected_dtype)

                    # validation_results[-1] = (column, actual_dtype, expected_dtype, 'Converted')

                except Exception as e:
                    logger.error(f"Error converting column {column} to {expected_dtype}: {e}")
            else:
                validation_results.append((column, actual_dtype, expected_dtype, 'Match'))
        else:
            # Log missing columns
            validation_results.append((column, 'Not Found', expected_dtype, 'Missing'))

    return data, validation_results         


def name_category_mapping(data):
    """
    
    """
    mappings = []
    vars = [col for col in data.columns if col.endswith('_name')]

    for var in vars:
        var_category = var.replace('_name', '_category')
        if var_category in data.columns:
            frequency = data.groupby([var, var_category]).size().reset_index(name='counts')
            frequency = frequency.sort_values(by='counts', ascending=False)
            mappings.append(frequency)
    return mappings

def check_time_overlap(data, conn):
    try:
        # Check if 'patient_id' exists in the data
        if 'patient_id' not in data.columns:
            # Query hospitalization table from DuckDB
            try:
                query = "SELECT hospitalization_id, patient_id FROM hospitalization"
                hospitalization_table = conn.execute(query).fetchdf() 
            except Exception as e:
                raise ValueError(f"Unable to query hospitalization table: {str(e)}")

            if hospitalization_table.empty:
                raise ValueError("Hospitalization table is empty or not provided.")
            
            # Join adt_table with hospitalization_table to get patient_id
            data = data.merge(
                hospitalization_table[['hospitalization_id', 'patient_id']],
                on='hospitalization_id',
                how='left'
            )
            
            # Check if the join was successful
            if 'patient_id' not in data.columns or data['patient_id'].isnull().all():
                raise ValueError("Unable to retrieve patient_id after joining with hospitalization_table.")
        
        
        # Sort by patient_id and in_dttm to make comparisons easier
        data = data.sort_values(by=['patient_id', 'in_dttm'])
        
        overlaps = []
        
        # Group by patient_id to compare bookings for each patient
        for patient_id, group in data.groupby('patient_id'):
            for i in range(len(group) - 1):
                # Current and next bookings
                current = group.iloc[i]
                next = group.iloc[i + 1]

                # Check if the locations are different and times overlap
                if (
                    current['location_name'] != next['location_name'] and
                    current['out_dttm'] > next['in_dttm']
                ):
                    overlaps.append({
                        'patient_id': patient_id,
                        'Initial Location': (current['location_name'], current['location_category']),
                        'Overlapping Location': (next['location_name'], next['location_name']),
                        'Admission Start': current['in_dttm'],
                        'Admission End': current['out_dttm'],
                        'Next Admission Start': next['in_dttm']
                    })
        
        return overlaps
    
    except Exception as e:
        # Handle errors gracefully
        raise RuntimeError(f"Error checking time overlap: {str(e)}")

