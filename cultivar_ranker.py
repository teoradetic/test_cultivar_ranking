from PIL import Image
from helpers import *
import streamlit as st

######################
# Prepare dataframes #
######################
# found in .streamlit/secrets.toml
SHEET_ID = st.secrets.sheet_id
CATALOG_SHEET = st.secrets.catalog_sheet
WHEAT_SHEET = st.secrets.wheat_sheet
PEAS_SHEET = st.secrets.peas_sheet
SUNFLOWER_SHEET = st.secrets.sunflower_sheet

# get urls of the sheets for each df
catalog_url = get_sheet_url(SHEET_ID, CATALOG_SHEET)
wheat_url = get_sheet_url(SHEET_ID, WHEAT_SHEET)
peas_url = get_sheet_url(SHEET_ID, PEAS_SHEET)
sunflower_url = get_sheet_url(SHEET_ID, SUNFLOWER_SHEET)

# get dataframes for each crop type & the catalog of metrics
catalog = clean_df(catalog_url, None)
wheat = clean_df(wheat_url, catalog)
peas = clean_df(peas_url, catalog)
sunflower = clean_df(sunflower_url, catalog)

# join all metrics into one df
all_cols = list(wheat.columns[:4]) + list(catalog.metric)
df = pd.DataFrame(columns=all_cols)
df = pd.concat([df, wheat, peas, sunflower], axis=0, ignore_index=True)

#################
# STREAMLIT APP #
#################

###########
# SIDEBAR #
###########
# select potential trial_id
id_options = df.trial_id.unique()
TRIAL_ID = st.sidebar.selectbox(
    '**Pick the trial ID**',
    id_options
)
df = df[df.trial_id == TRIAL_ID]

# get basic info to be used in filtering
crop = df.crop.unique()[0].split('_')[0]
season = " ".join([x for x in df.season.unique()[0].split('_')[:2]])

# some additional cleaning
df.drop(columns=['crop', 'season', 'trial_id'], inplace=True)
df.dropna(how='all', axis=1, inplace=True)

# determine boundary metric
if crop == 'sunflower':
    boundary = 'oil_content'
else:
    boundary = 'protein_content'

boundary_string = boundary.replace('_', ' ').title()

st.sidebar.markdown("**Pick importance for ranking:**")
# TODO: update it as a state change to always sum up to 100
# https://discuss.streamlit.io/t/make-value-of-multiple-number-inputs-dependent-of-each-other/33444/2
BOUNDARY = st.sidebar.slider(boundary_string, min_value=0.0, max_value=100.0, step=1.0, value=40.0)
YIELD = st.sidebar.slider('Yield', min_value=0.0, max_value=100.0, step=1.0, value=30.0)
QUALITY = st.sidebar.slider('Quality/trading', min_value=0.0, max_value=100.0, step=1.0, value=30.0)
DISEASES = st.sidebar.slider('Diseases', min_value=0.0, max_value=100.0, step=1.0, value=0.0)
AGRONOMIST = st.sidebar.slider('Agronomist', min_value=0.0, max_value=100.0, step=1.0, value=0.0)
ABIOTIC = st.sidebar.slider('Abiotic', min_value=0.0, max_value=100.0, step=1.0, value=0.0)
MORPHOLOGICAL = st.sidebar.slider('Morphological', min_value=0.0, max_value=100.0, step=1.0, value=0.0)

##############
# Title page #
##############
col1, col2 = st.columns([1, 5])
with col1:
    st.image(Image.open('logo_2.png'), width=50)
with col2:
    st.title("Cultivar Ranker")

st.text(f"Crop: {crop}")
st.text(f"Season: {season}")

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
         morpho_rank[['cultivar', 'overall_rank-morphological']]
         ]
weights = [BOUNDARY, YIELD, QUALITY, DISEASES, AGRONOMIST, ABIOTIC, MORPHOLOGICAL]

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
if crop == 'wheat':
    st.markdown("## Wheat class")
    st.text("The trading class the wheat cultivars can reach based on their quality metrics.")
    class_cols = ['moisture_at_harvest', 'protein_content', 'hectoliter_mass', 'impurities']
    df['wheat_class'] = df[class_cols].apply(lambda x: get_wheat_classes(*x), axis=1)
    st.dataframe(df[['cultivar', 'wheat_class'] + class_cols], hide_index=True)
    st.divider()

# BOUNDARY METRIC #
boundary_rank.columns = [x.replace('quality', boundary) for x in boundary_rank.columns]
visualize_metrics(boundary, boundary_metrics, boundary_rank, 1)

# ALL OTHER METRICS METRIC #
visualize_metrics('yield', yield_metrics, yield_rank, 2)
visualize_metrics('quality', qual_metrics, qual_rank, 3)
visualize_metrics('diseases', disease_metrics, disease_rank, 4)
visualize_metrics('agronomist', agro_metrics, agro_rank, 5)
visualize_metrics('abiotic', abio_metrics, abio_rank, 6)
visualize_metrics('morphological', morpho_metrics, morpho_rank, 7)