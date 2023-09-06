from .utils import title_case_string
import numpy as np
import pandas as pd
import streamlit as st


def get_boundary_metric(crop_name):
    """Used to determine a boundary metric. A boundary metric is a metric that is analyzed separately, because
    it's of great interest in and of itself."""

    if crop_name == 'sunflower':
        boundary = 'oil_content'
    else:
        boundary = 'protein_content'

    boundary_string = title_case_string(boundary)

    return boundary, boundary_string


def derive_duration_column(data_frame, new_col_name, start_date_col, end_date_col):
    """Computes the duration in days between @start_date_col and @end_date_col and saves it under @new_col_name."""
    data_frame[new_col_name] = (data_frame[end_date_col] - data_frame[start_date_col]) / np.timedelta64(1, 'D')
    return data_frame


def compute_duration_metrics(data_frame):
    if 'date_of_emergence' in data_frame.columns:
        if 'date_of_heading' in data_frame.columns:
            data_frame = derive_duration_column(data_frame,
                                                'days_between_emergence_and_heading',
                                                'date_of_emergence',
                                                'date_of_heading'
                                                )
        if 'date_of_flowering' in data_frame.columns:
            data_frame = derive_duration_column(data_frame,
                                                'days_between_emergence_and_flowering',
                                                'date_of_emergence',
                                                'date_of_flowering'
                                                )
    return data_frame


def overwrite_metrics(df1, df2, key):
    df = df1.copy()
    merged_df = pd.merge(df1, df2, on=key, how='left', suffixes=('_old_', '_new_'))
    """for col in merged_df:
        if '_new_' in col:
            data_frame[col] = merged_df[col]
    return data_frame"""
    return merged_df


def compute_blup_metrics(data_frame, blup_df):
    """For the time being, this just overwrites existing metrics with new ones"""
    pass


def get_wheat_classes(moisture, protein, mass, impurities):
    wheat_class_definition = [
        # in order: max moisture, min protein, min mass, max impurities
        ["I", [0.13, 0.13, 76.0, 0.04]],
        ["II", [0.13, 0.12, 76.0, 0.04]],
        ["III", [0.13, 0.13, 76.0, 0.04]],
        ["IV", [0.13, 0.105, 74.0, 0.04]],
        ["Stočna", [0.13, 0.104, 65.0, 0.12]]
    ]

    """For wheat cultivars, computes the trading class."""
    for item in wheat_class_definition:
        candidate_class, metrics = item
        if moisture <= metrics[0] and protein >= metrics[1] and mass >= metrics[2] and impurities <= metrics[3]:
            return candidate_class
    return "No class"


def get_metrics(data_frame, metric_type, metrics_catalog_df, keep_cols=None):
    """Filters data_frame to only display metrics of a given metric type + keep_cols."""
    if keep_cols is None:
        keep_cols = ['cultivar']

    _df = data_frame.copy()

    # preselect just existing catalog
    cols_subset = keep_cols + list(metrics_catalog_df[metrics_catalog_df.type == metric_type].metric)
    cols_subset_clean = [x for x in cols_subset if x in _df.columns]
    df_metrics = _df[cols_subset_clean]

    return df_metrics
