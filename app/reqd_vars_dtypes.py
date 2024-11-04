expected_data_types = {
    'Labs': {
        'hospitalization_id': 'object',
        'lab_order_dttm': 'datetime64',
        'lab_collect_dttm': 'datetime64',
        'lab_result_dttm': 'datetime64',
        'lab_order_name': 'object',
        'lab_order_category': 'object',
        'lab_name': 'object',
        'lab_category': 'object',
        'lab_value': 'object',
        'reference_unit': 'object',
        'lab_type_name': 'object',  
        'lab_specimen_name': 'object',
        'lab_specimen_category': 'object',
        'lab_loinc_code': 'object'
    },
    'Vitals': {
        'hospitalization_id': 'object',
        'recorded_dttm': 'datetime64',
        'vital_name': 'object',
        'vital_category': 'object',
        'vital_value': 'float64',
        'meas_site_name': 'object'
    },
    'Encounter_Demographic_Disposition': {
        'encounter_id': 'object',
        'age_at_admission': 'int64', 
        'disposition_name': 'object',
        'disposition_category': 'object'
    },
    'Respiratory_Support': {
        'hospitalization_id': 'object',
        'recorded_dttm': 'datetime64',
        'device_name': 'object',
        'device_category': 'object',
        'vent_brand_name': 'object',
        'mode_name': 'object',
        'mode_category': 'object',
        'tracheostomy': 'bool',
        'lpm_set': 'float64',
        'fio2_set': 'float64',
        'tidal_volume_set': 'float64',
        'resp_rate_set': 'float64',
        'pressure_control_set': 'float64',
        'pressure_support_set': 'float64',
        'flow_rate_set': 'float64',
        'peak_inspiratory_pressure_set': 'float64',
        'inspiratory_time_set': 'float64',
        'peep_set': 'float64',
        'tidal_volume_obs': 'float64',
        'resp_rate_obs': 'float64',
        'plateau_pressure_obs': 'float64',
        'peak_inspiratory_pressure_obs': 'float64',
        'peep_obs': 'float64',
        'minute_vent_obs': 'float64',
        'mean_airway_pressure_obs': 'float64'
    },
    'Medication_admin_continuous': {
        'hospitalization_id': 'object',
        'med_order_id': 'object',
        'admin_dttm': 'datetime64',
        'med_name': 'object',
        'med_category': 'object',
        'med_group': 'object',
        'med_route_name': 'object',
        'med_route_category': 'object',
        'med_dose': 'float64',
        'med_dose_unit': 'object',
        'mar_action_name': 'object',
        'mar_action_category': 'object'
    },
    'ADT': {
        'patient_id': 'object',
        'hospitalization_id': 'object',
        'hospital_id': 'object',
        'in_dttm': 'datetime64',
        'out_dttm': 'datetime64',
        'location_name': 'object',
        'location_category': 'object'
    },
    'Hospitalization': {
        'patient_id': 'object',
        'hospitalization_id': 'object',
        'hospitalization_joined_id': 'object',  # Optional
        'admission_dttm': 'datetime64',
        'discharge_dttm': 'datetime64',
        'age_at_admission': 'int64',
        'admission_type_name': 'object',
        'admission_type_category': 'object',
        'discharge_name': 'object',
        'discharge_category': 'object',
        'zipcode_nine_digit': 'object',
        'zipcode_five_digit': 'object',
        'census_block_code': 'object',
        'census_block_group_code': 'object',
        'census_tract': 'object',
        'state_code': 'object',
        'county_code': 'object'
    },
    'Microbiology_Culture': {
        'hospitalization_id': 'object',
        'organism_id': 'object',
        'order_dttm': 'datetime64',
        'collect_dttm': 'datetime64',
        'result_dttm': 'datetime64',
        'fluid_name': 'object',
        'fluid_category': 'object',
        'component_name': 'object',
        'component_category': 'object',
        'organism_name': 'object',
        'organism_category': 'object'
    },
    'Patient': {
        'patient_id': 'object',
        'race_name': 'object',
        'race_category': 'object',
        'ethnicity_name': 'object',
        'ethnicity_category': 'object',
        'sex_name': 'object',
        'sex_category': 'object',
        'birth_date': 'datetime64',
        'death_dttm': 'datetime64',
        'language_name': 'object',
        'language_category': 'object'
    },
    'Patient_Assessments': {
        'hospitalization_id': 'object',
        'recorded_dttm': 'datetime64',
        'assessment_name': 'object',
        'assessment_category': 'object',
        'assessment_group': 'object',
        'numerical_value': 'float64',  
        'categorical_value': 'object',
        'text_value': 'object'
    },
    'Position': {
        'patient_id': 'object',
        'hospitalization_id': 'object',
        'recorded_dttm': 'datetime64',
        'position_name': 'object',
        'position_category': 'object'
    }
}


required_variables = {
    'Labs': [
        'hospitalization_id', 'lab_order_dttm', 'lab_collect_dttm', 'lab_result_dttm',
        'lab_order_name', 'lab_order_category', 'lab_name', 'lab_category', 'lab_value',
        'reference_unit', 'lab_specimen_name', 'lab_specimen_category', 'lab_type_name',
        'lab_loinc_code'
    ],  # Confirm if all required
    'Vitals': [
        'hospitalization_id', 'recorded_dttm', 'vital_name', 'vital_category',
        'vital_value', 'meas_site_name'
    ],
    'Encounter_Demographic_Disposition': [
        'encounter_id', 'age_at_admission', 'disposition_name', 'disposition_category'
    ],
    'Respiratory_Support': [
        'hospitalization_id', 'recorded_dttm', 'device_name', 'device_category',
        'vent_brand_name', 'mode_name', 'mode_category', 'tracheostomy', 'lpm_set', 
        'fio2_set', 'tidal_volume_set', 'resp_rate_set', 'pressure_control_set',
        'pressure_support_set', 'flow_rate_set', 'peak_inspiratory_pressure_set',
        'inspiratory_time_set', 'peep_set', 'tidal_volume_obs', 'resp_rate_obs',
        'plateau_pressure_obs', 'peak_inspiratory_pressure_obs', 'peep_obs',
        'minute_vent_obs', 'mean_airway_pressure_obs'
    ],
    'Medication_admin_continuous': [
        'hospitalization_id', 'med_order_id', 'admin_dttm', 'med_name', 'med_category',
        'med_group', 'med_route_name', 'med_route_category', 'med_dose', 'med_dose_unit',
        'mar_action_name', 'mar_action_category'
    ],
    'ADT': [
        'patient_id', 'hospitalization_id', 'hospital_id', 'in_dttm', 
        'out_dttm', 'location_name', 'location_category'
    ],
    'Hospitalization': [
        'patient_id', 'hospitalization_id', 'hospitalization_joined_id', 'admission_dttm', 
        'discharge_dttm', 'age_at_admission', 'admission_type_name', 'admission_type_category',
        'discharge_name', 'discharge_category', 'zipcode_nine_digit', 'zipcode_five_digit',
        'census_block_code', 'census_block_group_code', 'census_tract', 'state_code',
        'county_code'
    ],
    'Microbiology_Culture': [
        'hospitalization_id', 'organism_id', 'order_dttm', 'collect_dttm', 'result_dttm',
        'fluid_name', 'fluid_category', 'component_name', 'component_category', 
        'organism_name', 'organism_category'
    ],
    'Patient': [
        'patient_id', 'race_name', 'race_category', 'ethnicity_name', 'ethnicity_category',
        'sex_name', 'sex_category', 'birth_date', 'death_dttm', 'language_name',
        'language_category'
    ],
    'Patient_Assessments': [
        'hospitalization_id', 'recorded_dttm', 'assessment_name', 'assessment_category',
        'assessment_group', 'numerical_value', 'categorical_value', 'text_value'
    ],
    'Position': [
        'patient_id', 'hospitalization_id', 'recorded_dttm', 'position_name', 'position_category'
    ]
}
