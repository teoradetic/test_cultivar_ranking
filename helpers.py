import numpy as np
import pandas as pd
import streamlit as st
import matplotlib.pyplot as plt


def get_sheet_url(sheet_id, sheet_name):
    """Return sanitized url to access Google Sheets Sheet."""
    sheet_name = sheet_name.replace(' ', '%20')
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
    return url


def standardize_str(_str):
    """Transforms all column strings in standardized format."""
    return _str.strip().replace(' ', '_').lower()


# @st.cache_data
def clean_df(url_to_df_table, metrics_df=None):
    """Removes emtpy columns and coerces dtypes of columns into appropriate dtype for analysis."""
    df = pd.read_csv(url_to_df_table)

    # remove columns with empty values
    df.dropna(how='all', axis=1, inplace=True)

    # drop rows where second column is empty
    # prevents empty rows
    second = df.columns[1]
    df = df[df[second].notna()]

    # standardize names
    df.columns = [standardize_str(x) for x in df.columns]

    # correct data types
    if metrics_df is not None:  # wheat, peas, sunflower
        # coerce dtypes: %
        pct_cols = [x for x in list(metrics_df[metrics_df.units == '%'].metric)]
        pct_cols = [x for x in pct_cols if x in df.columns]  # in case they're not shared
        for col in pct_cols:
            df[col] = df[col].apply(lambda x: float(x.replace('%', '')) / 100)

        # coerce dtypes: date
        date_cols = [x for x in list(metrics_df[metrics_df.data_type == 'date'].metric)]
        date_cols = [x for x in date_cols if x in df.columns]  # in case they're not shared
        for col in date_cols:
            df[col] = pd.to_datetime(df[col], format='%d-%b-%Y')

        # coerce dtypes: categorical into numeric (int) to make rank work
        cat_cols = [x for x in list(metrics_df[metrics_df.data_type == 'integer'].metric)]
        cat_cols = [x for x in cat_cols if x in df.columns]  # in case they're not shared
        df[cat_cols] = df[cat_cols].astype('int64')

    else:  # catalog catalog
        df['metric'] = df['metric'].apply(lambda x: standardize_str(x))
        df['data_type'] = df['data_type'].apply(lambda x: np.nan if x == 'None' else x)

    return df


def get_metrics(df, metric_type, metrics_catalog_df, keep_cols=None):
    """Filters df to only display metrics of a given metric type + keep_cols."""
    if keep_cols is None:
        keep_cols = ['cultivar']

    _df = df.copy()

    # preselect just existing catalog
    cols_subset = keep_cols + list(metrics_catalog_df[metrics_catalog_df.type == metric_type].metric)
    cols_subset_clean = [x for x in cols_subset if x in _df.columns]
    df_metrics = _df[cols_subset_clean]

    # add derived duration metrics
    # TODO: Automate, no constants should be here
    if 'date_of_nicanje' in df_metrics.columns:
        if 'date_of_klasanje' in df_metrics.columns:
            df_metrics['days_between_nicanje_and_klasanje'] = (df['date_of_klasanje'] - df['date_of_nicanje']) \
                                                              / np.timedelta64(1, 'D')
        if 'date_of_cvetanje' in df_metrics.columns:
            df_metrics['days_between_nicanje_and_cvetanje'] = (df['date_of_cvetanje'] - df['date_of_nicanje']) \
                                                              / np.timedelta64(1, 'D')

    return df_metrics


def rank_metrics(df, metrics_catalog_df, keep_cols=None):
    """Simple ranking algorithm, column-wise."""
    if keep_cols is None:
        keep_cols = ['cultivar']
    _df = df.copy()

    # create the bases for ranking
    df = _df.copy()[keep_cols]

    # iterate through columns and rank
    for col in _df.columns:
        if col not in keep_cols:
            is_ascending = list(metrics_catalog_df[metrics_catalog_df.metric == col]['rank_ascending'])[0]
            if is_ascending is not np.nan:  # prevents ranking of non-rankable catalog
                df['rank-' + col] = _df[col].rank(ascending=is_ascending,
                                                  method="dense").astype(int)

    return df


def weighted_rank(df_rank, metric_type, weights=None):
    """Computes average and overall ranks for a group of metrics, using all metrics."""
    # compute average rank
    rank_cols = [x for x in df_rank.columns if x.startswith('rank-')]

    # compute weighted overall rank
    if weights is None:
        weights = [1 for x in range(len(rank_cols))]

    df_rank['avg_rank-' + metric_type] = df_rank[rank_cols].mul(weights).sum(axis=1) / sum(weights)

    df_rank['overall_rank-' + metric_type] = df_rank['avg_rank-' + metric_type].rank(ascending=True,
                                                                                     method="dense").astype(int)

    cols = df_rank.columns.tolist()
    new_col_order = [cols[0]] + [cols[-1]] + [cols[-2]] + cols[1:-2]

    return df_rank[new_col_order]


def weighted_overall_rank(list_df_ranks, list_df_weights):
    """Computes overall rank for a given trial ID. The weights are selected by the user via st."""
    df_rank = pd.DataFrame()

    # edge condition: no ranking weights chosen
    if sum(list_df_weights) == 0:
        df_rank = list_df_ranks[0]
        df_rank = df_rank[['cultivar']]
        df_rank['overall_rank'] = 0
        return df_rank

    for idx, dtfrm in enumerate(list_df_ranks):
        dtfrm.columns = [x.replace('overall_', '') for x in dtfrm.columns]
        if idx == 0:
            df_rank = dtfrm
        else:
            df_rank = df_rank.merge(dtfrm, how='inner', on='cultivar')

    rank_cols = df_rank.columns[1:]
    df_rank['overall_rank'] = df_rank[rank_cols].mul([*list_df_weights]).sum(axis=1) \
                              / sum(list_df_weights)
    df_rank['overall_rank'] = df_rank['overall_rank'].rank(ascending=True, method="dense").astype(int)

    # remove columns that are not part of ranking
    cols = ['cultivar', 'overall_rank']
    candidates = df_rank.columns.tolist()[1:-1]
    for idx, c in enumerate(candidates):
        if list_df_weights[idx] > 0:
            cols.append(c)

    return df_rank[cols]


def analyze_and_rank(df, metric_type, metrics_catalog_df, weights=None, keep_cols=None):
    """Joins multiple analysis and ranking operations together."""
    if keep_cols is None:
        keep_cols = ['cultivar']
    _df = df.copy()

    df_metrics = get_metrics(_df, metric_type, metrics_catalog_df, keep_cols)
    df_rank_simple = rank_metrics(df_metrics, metrics_catalog_df, keep_cols)
    df_rank = weighted_rank(df_rank_simple, metric_type, weights)

    return df_metrics, df_rank


wheat_class_definition = [
    # in order: max moisture, min protein, min mass, max impurities
    ["I", [0.13, 0.13, 76.0, 0.04]],
    ["II", [0.13, 0.12, 76.0, 0.04]],
    ["III", [0.13, 0.13, 76.0, 0.04]],
    ["IV", [0.13, 0.105, 74.0, 0.04]],
    ["Stočna", [0.13, 0.104, 65.0, 0.12]]
]


def get_wheat_classes(moisture, protein, mass, impurities):
    """For wheat cultivars, computes the trading class."""
    for item in wheat_class_definition:
        candidate_class, metrics = item
        if moisture <= metrics[0] and protein >= metrics[1] and mass >= metrics[2] and impurities <= metrics[3]:
            return candidate_class
    return "No class"


def visualize_metrics(metric_string, metric_df, rank_df, cmap=None):
    """Simple visualizing algorithm displaying a class of metrics, their ranks, and their charts."""
    if cmap is None:
        cmap = plt.cm.get_cmap('summer')

    metric_string_pretty = metric_string.replace('_', ' ').title()

    st.markdown(f"## {metric_string_pretty} Analysis")
    st.markdown(f"#### Ranking results: {metric_string_pretty} metrics")
    st.dataframe(rank_df.style.format("{:.3}", subset=[f'avg_rank-{metric_string}'])
                 .background_gradient(cmap=cmap, subset=[f'overall_rank-{metric_string}']),
                 hide_index=True)
    st.markdown(f"#### {metric_string_pretty} metrics visualized")
    for col in metric_df.columns[1:]:
        st.bar_chart(metric_df, x='cultivar', y=col)  # TODO: Improve visualization
    st.divider()
