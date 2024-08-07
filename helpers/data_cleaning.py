import pandas as pd
from .data_metrics import compute_duration_metrics
from .utils import intersect_lists


###########
# FILTERS #
###########


def remove_duplicates(data_frame):
    return data_frame.drop_duplicates()


def remove_columns_with_all_nas(data_frame):
    return data_frame.dropna(axis='columns', how='all')


def remove_columns_with_nas_over_threshold(data_frame, threshold: float = 0.5):
    return data_frame.dropna(axis='columns', thresh=round(threshold * len(data_frame)))


def remove_listed_columns(data_frame, lst_columns):
    return data_frame.drop(columns=intersect_lists(data_frame.columns, lst_columns))


def remove_column_if_all_values_are_target_value(data_frame, cell_value: str):
    return data_frame.T[~data_frame.eq(cell_value).all()].T


def remove_rows_if_all_na_in_specified_columns(data_frame, lst_columns):
    return data_frame.dropna(axis='rows', subset=intersect_lists(data_frame.columns, lst_columns), how='all')


def remove_rows_if_val_in_col(data_frame, col, val):
    """Drop all rows that have @val as value in columns @col. Used for manual filtering of data."""
    return data_frame.drop(data_frame[data_frame[col] == val].index)


def filter_data(data_frame,
                columns_to_drop: list,
                value_to_drop_col_if_only_value_in_column,
                cols_with_na_rows: list,
                filter_col,
                val_of_filer_col,
                na_threshold=0.75):
    data_frame = remove_rows_if_val_in_col(data_frame, filter_col, val_of_filer_col)
    data_frame = remove_listed_columns(data_frame, columns_to_drop)
    data_frame = remove_duplicates(data_frame)
    data_frame = remove_columns_with_all_nas(data_frame)
    data_frame = remove_columns_with_nas_over_threshold(data_frame, na_threshold)
    data_frame = remove_column_if_all_values_are_target_value(data_frame, value_to_drop_col_if_only_value_in_column)
    data_frame = remove_rows_if_all_na_in_specified_columns(data_frame, cols_with_na_rows)

    return data_frame


##################
# VALUE RECODING #
##################

def rename_columns(data_frame, dict_of_renames):
    cleaned_df = data_frame.rename(columns=dict_of_renames)
    return cleaned_df


def coerce_float_columns(data_frame, lst_columns):
    data_frame[lst_columns] = data_frame[lst_columns].astype('float')


def coerce_int_columns(data_frame, lst_columns):
    for c in lst_columns:
        try:
            data_frame[c] = pd.to_numeric(data_frame[c], errors='coerce').astype('Int64')
        except Exception as e:
            data_frame[c] = data_frame[c].astype('float')


def coerce_date_columns(data_frame, lst_columns, date_format='%B %d, %Y'):
    for col in lst_columns:
        data_frame[col] = pd.to_datetime(data_frame[col], format=date_format)


def coerce_dtypes(data_frame, catalog_df):
    float_cols = intersect_lists(data_frame.columns, list(catalog_df[catalog_df['data_type'] == "float"].metric))
    int_cols = intersect_lists(data_frame.columns,
                               list(catalog_df[catalog_df['data_type'].isin(['integer', 'category'])].metric))
    date_cols = intersect_lists(data_frame.columns, list(catalog_df[catalog_df.data_type == "date"].metric))

    coerce_float_columns(data_frame, float_cols)
    coerce_int_columns(data_frame, int_cols)
    coerce_date_columns(data_frame, date_cols)

    return data_frame


##################
# AGGREGATE DATA #
##################

def aggregate_object_cols(data_frame, group_by_cols=None):
    if group_by_cols is None:
        group_by_cols = ['trial_id', 'cultivar']
    _df = data_frame.copy().select_dtypes(include='object')

    # Trim whitespace from all object columns
    _df = _df.applymap(lambda x: x.strip() if isinstance(x, str) else x)

    # remove duplicated rows
    _df = remove_duplicates(_df)

    return _df


def filter_df_numeric_columns(data_frame, keep_cols):
    if not isinstance(keep_cols, list):
        keep_cols = [keep_cols]
    else:
        keep_cols = [x for x in keep_cols]

    types = data_frame.copy().dtypes.reset_index()
    types.columns = ['metric', 'dtype']
    types = types[types.dtype != 'object']

    keep_cols += list(types.metric)

    numeric_df = data_frame[keep_cols]

    return numeric_df


def aggregate_numeric_cols(data_frame, group_by_cols):
    _df = filter_df_numeric_columns(data_frame, group_by_cols)
    _df = _df.groupby(group_by_cols).mean()
    _df = _df.round(2)
    return _df


def aggregate_data(data_frame, group_by_cols=None):
    if group_by_cols is None:
        group_by_cols = ['trial_id', 'cultivar']
    obj_df = aggregate_object_cols(data_frame, group_by_cols)
    num_df = aggregate_numeric_cols(data_frame, group_by_cols)

    agg_data_frame = obj_df.merge(num_df, on=group_by_cols, how='left')

    return agg_data_frame


###########################
# ALL CLEANING PROCEDURES #
###########################

def clean_df_for_cr(data_frame, catalog_df, blup_df=None):
    # set params - anti-pattern within funct, but easier
    cols_to_drop = ['qr_code_seed', 'qr_code_plant_material', 'crop', 'season', 'location', 'plot_id',
                    'experiment_type', 'exclude_from_analysis']
    row_vals_to_drop_col = 'canceled'
    quality_cols = list(catalog_df[catalog_df['type'] == 'quality'].metric)
    cols_with_na_rows = [x for x in data_frame.columns if x in quality_cols]
    filter_col = 'exclude_from_analysis'
    filter_val = True

    # clean data frame
    data_frame = filter_data(data_frame, cols_to_drop, row_vals_to_drop_col, cols_with_na_rows, filter_col, filter_val)
    data_frame = rename_columns(data_frame, {'genotype': 'cultivar'})
    data_frame = coerce_dtypes(data_frame, catalog_df)

    # get derived duration metrics and drop date columns
    date_cols = list(catalog_df[catalog_df['data_type'] == 'date'].metric)
    data_frame = compute_duration_metrics(data_frame)
    data_frame = remove_listed_columns(data_frame, date_cols)

    # aggregate data - aggregated per cultivar & trial_id, needed for blup join
    data_frame = aggregate_data(data_frame, ['trial_id', 'cultivar'])

    # correct blup metrics if they exist
    if len(blup_df) > 0:
        merged_df = pd.merge(data_frame,
                             blup_df,
                             how='left',
                             on=['trial_id', 'cultivar'],
                             suffixes=('', '_blup')
                             )
        # Replace values in the merged DataFrame
        for col in data_frame.columns:
            if col in ['trial_id', 'cultivar']:
                continue  # Skip the join columns
            blup_col = f"{col}_blup"
            if blup_col in merged_df.columns:
                merged_df[col] = merged_df[blup_col].combine_first(merged_df[col])
                merged_df.drop(columns=[blup_col], inplace=True)
        data_frame = merged_df

    # remove artefacts needed for blup overriding
    data_frame = data_frame.drop(columns=['trial_id', 'crop'], errors='ignore')

    # reaggregate - if blup_df was on a different granularity
    data_frame = aggregate_data(data_frame, ['cultivar'])

    return data_frame
