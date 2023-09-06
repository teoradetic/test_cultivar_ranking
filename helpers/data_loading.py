import pandas as pd
from .utils import camel_case_string
from .data_cleaning import remove_listed_columns


def get_sheet_url(sheet_id, sheet_name):
    """Return sanitized url to access Google Sheets Sheet."""
    sheet_name = sheet_name.replace(' ', '%20')
    url = f'https://docs.google.com/spreadsheets/d/{sheet_id}/gviz/tq?tqx=out:csv&sheet={sheet_name}'
    return url


def load_csv_file(file_path):
    """Loads CSV file at @file_path and coerces columns into right format."""
    return pd.read_csv(file_path)


def load_multiple_csv_files(file_paths):
    data_frames = [load_csv_file(file) for file in file_paths]
    return data_frames


def get_dfs_for_cultivar_ranker(sheet_id: str, catalog_sheet: str, crop_sheets: list[str]):
    """
    The function takes as inputs the filepaths to Google Sheets where the data resides,
    and returns two data frames: df (all crops) and catalog (the metrics used to evaluate crops).

    The function assumes all the data for crops and cataloged metrics is found on
    @sheet_id, where each crop has its own sheet (separately listed within @crop_sheets) and
    the catalog of metrics has its own sheet (@catalog_sheet).
    """
    # get Google Sheets urls for crops and catalog
    crop_urls = [get_sheet_url(sheet_id, sheet_name) for sheet_name in crop_sheets]
    catalog_url = get_sheet_url(sheet_id, catalog_sheet)

    # create data frames from data
    crop_dfs = load_multiple_csv_files(crop_urls)
    catalog_df = load_csv_file(catalog_url)

    # standardize column names
    all_dfs = crop_dfs + [catalog_df]
    for _df in all_dfs:
        _df.columns = [camel_case_string(x) for x in _df.columns]

    # standardize metric names in catalog_df
    catalog_df['metric'] = catalog_df['metric'].apply(lambda x: camel_case_string(x))

    # join all crop metrics into one df
    all_cols = [camel_case_string(x) for x in list(catalog_df.metric)]
    df_crops = pd.DataFrame(columns=all_cols)
    df_crops = pd.concat([df_crops, *crop_dfs], axis=0, ignore_index=True)

    # remove columns that are not part of the catalog
    extra_columns = [x for x in df_crops.columns if x not in all_cols]
    df_crops = remove_listed_columns(df_crops, extra_columns)

    # derive helpers columns
    df_crops['crop'] = df_crops.trial_id.apply(lambda x: x.split('_')[1].lower())
    df_crops['season'] = df_crops.trial_id.apply(lambda x: "20" + x.split('_')[-1])
    df_crops['location'] = df_crops.plot_id.apply(lambda x: x[:2])

    return df_crops, catalog_df
