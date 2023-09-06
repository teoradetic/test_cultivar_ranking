import numpy as np
import pandas as pd

from .data_metrics import get_metrics


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
                                                                                     method="dense",
                                                                                     na_option='bottom').astype(int)

    cols = df_rank.columns.tolist()
    new_col_order = [cols[0]] + [cols[-1]] + cols[1:-2]

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

