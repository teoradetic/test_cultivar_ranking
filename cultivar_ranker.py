import os
import numpy as np
from PIL import Image
import matplotlib.pyplot as plt
from helpers.data_loading import get_dfs_for_cultivar_ranker, load_csv_file, get_sheet_url
from helpers.data_cleaning import clean_df_for_cr, remove_listed_columns, remove_columns_with_all_nas
from helpers.data_metrics import get_boundary_metric
from helpers.data_ranking import analyze_and_rank, weighted_overall_rank
from helpers.data_visualizing import visualize_metrics
from helpers.streamlit_functions import (select_user_parameters,
                                         select_ranking_importance_for_metrics,
                                         present_wheat_class)
from helpers.product_analytics import inject_ga
import streamlit as st

inject_ga()

st.markdown("This is the **TEST** version of Cultivar Ranker")
st.markdown("**[GET THE LIVE VERSION HERE](https://streamlit.logineko-analytics.org/dashboard-cultivar-ranker/)**")

######################
# Prepare dataframes #
######################
# declare constants specifying data assets
SHEET_ID = st.secrets.sheet_id
CATALOG_SHEET = "Metrics catalog"
WHEAT_SHEET = "Wheat"
PEAS_SHEET = "Peas"
SUNFLOWER_SHEET = "Sunflower"
RANKER_VIZ = "images/ranking_process_visualized.png"
LOGO_IMG = "images/logo.png"
BLUP_SHEET = 'BLUP'

df, catalog = get_dfs_for_cultivar_ranker(SHEET_ID, CATALOG_SHEET, crop_sheets=[WHEAT_SHEET, PEAS_SHEET])
# todo: handle BLUP data better
blup_df = load_csv_file(get_sheet_url(SHEET_ID, BLUP_SHEET))

#################
# STREAMLIT APP #
#################

###########
# SIDEBAR #
###########
with st.sidebar:
    st.markdown("**Select the parameters below**")
    # todo: handle BLUP data better
    df, blup_df = select_user_parameters(df, blup_df)
    st.divider()

crop = df.crop.unique()[0]
season = df.season.unique()[0]

# clean data to make it ready for analysis
# todo: handle BLUP data better
blup_df = remove_columns_with_all_nas(remove_listed_columns(blup_df, ['trial_id', 'location', 'season']))
df = clean_df_for_cr(df, catalog, blup_df)

# determine boundary metric
boundary, boundary_string = get_boundary_metric(crop)

# collect user input for ranking importance
with st.sidebar:
    BOUNDARY, YIELD, QUALITY, DISEASES, AGRONOMIST, ABIOTIC, WEEDS, MORPHOLOGICAL = select_ranking_importance_for_metrics(boundary_string)


##############
# Title page #
##############
col1, col2 = st.columns([1, 5])
with col1:
    st.image(Image.open(LOGO_IMG), width=50)
with col2:
    st.title("Cultivar Ranker")

st.text(f"Crop: {crop}")
st.text(f"Season: {season}")
with st.expander("Show me how the ranking algorithm works."):
    st.text("Ranks are computed in 9 steps visualized below.")
    st.image(RANKER_VIZ)

##############################
# METRICS & RANK COMPUTATION #
##############################

# create boundary metric
boundary_df = df.copy()
boundary_df = boundary_df[['cultivar', boundary]]


# compute all ranks and metrics
boundary_metrics, boundary_rank = analyze_and_rank(boundary_df, 'quality', catalog)
qual_metrics, qual_rank = analyze_and_rank(df, 'quality', catalog)
yield_metrics, yield_rank = analyze_and_rank(df, 'yield', catalog)
disease_metrics, disease_rank = analyze_and_rank(df, 'diseases', catalog)
agro_metrics, agro_rank = analyze_and_rank(df, 'agronomist', catalog)
abio_metrics, abio_rank = analyze_and_rank(df, 'abiotic', catalog)
weeds_metrics, weeds_rank = analyze_and_rank(df, 'weed_competition', catalog)
morpho_metrics, morpho_rank = analyze_and_rank(df, 'morphological', catalog)

############################
# OVERALL RANK COMPUTATION #
############################
# create list with all rank dfs
ranks = [boundary_rank[['cultivar', 'overall_rank-quality']]
         .rename(columns={'overall_rank-quality': 'overall_rank-quality'.replace('quality', boundary)}),
         yield_rank[['cultivar', 'overall_rank-yield']],
         qual_rank[['cultivar', 'overall_rank-quality']],
         disease_rank[['cultivar', 'overall_rank-diseases']],
         agro_rank[['cultivar', 'overall_rank-agronomist']],
         abio_rank[['cultivar', 'overall_rank-abiotic']],
         weeds_rank[['cultivar', 'overall_rank-weed_competition']],
         morpho_rank[['cultivar', 'overall_rank-morphological']]
         ]
weights = [BOUNDARY, YIELD, QUALITY, DISEASES, AGRONOMIST, ABIOTIC, WEEDS, MORPHOLOGICAL]

df_rank = weighted_overall_rank(ranks, weights)

###################
# PRESENT RESULTS #
###################

# OVERALL RANKINGS #
st.markdown("## Overall Ranking")
cmap = plt.cm.get_cmap('summer')  # spectral
st.dataframe(df_rank.style.background_gradient(cmap=cmap, subset=['overall_rank']), hide_index=True)
st.divider()

# CONDITIONAL WHEAT CLASSES #
# temporarily commented out until we understand if needed
if crop == 'wheat':
    #present_wheat_class(df)
    #st.divider()
    pass

# BOUNDARY METRIC #
boundary_rank.columns = [x.replace('quality', boundary) for x in boundary_rank.columns]
visualize_metrics(boundary, boundary_metrics, boundary_rank, catalog, 1)

# ALL OTHER METRICS METRIC #
visualize_metrics('yield', yield_metrics, yield_rank, catalog, 2)
visualize_metrics('quality', qual_metrics, qual_rank, catalog, 3)
visualize_metrics('diseases', disease_metrics, disease_rank, catalog, 4)
visualize_metrics('agronomist', agro_metrics, agro_rank, catalog, 5)
visualize_metrics('abiotic', abio_metrics, abio_rank, catalog, 6)
visualize_metrics('weed_competition', weeds_metrics, weeds_rank, catalog, 7)
visualize_metrics('morphological', morpho_metrics, morpho_rank, catalog, 8)
