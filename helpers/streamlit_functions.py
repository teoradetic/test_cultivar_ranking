import numpy as np

from .data_metrics import get_wheat_classes

import streamlit as st
from streamlit import session_state as ss


def select_user_parameters(data_frame, blup_df):
    crop_options = data_frame.crop.unique()
    crop_id = st.selectbox(
        '**Pick the crop**',
        crop_options
    )
    data_frame = data_frame[data_frame.crop == crop_id]
    # todo: handle BLUP data better
    blup_df = blup_df[blup_df.crop == crop_id]

    # Select location
    location_options = np.append(data_frame.location.unique(), ['ALL'])
    location = st.selectbox(
        '**Pick the location**',
        location_options
    )
    if location != 'ALL':
        data_frame = data_frame[data_frame.location == location]
    # todo: handle BLUP data better
    blup_df = blup_df[blup_df.location == location]

    # Select season
    season_options = np.append(data_frame.season.unique(), ['ALL'])
    season = st.selectbox(
        '**Pick the season**',
        season_options
    )
    if season != 'ALL':
        data_frame = data_frame[data_frame.season == season]
        # todo: handle BLUP data better
        blup_df = blup_df[blup_df.season.astype(str) == str(season)]

    return data_frame, blup_df


def select_ranking_importance_for_metrics(boundary_string):
    """
    State-aware function that lets users pick the importance of metric categories for ranking
    while keeping the importance assignment to be max 100 across all ranking metrics.
    """
    st.markdown("**Pick importance for ranking:**",
                help="""At most, you can assign 100 points across all metric categories.
                If you assign more than 100 points, the program will automatically lower
                the sliders to keep it under 100.
                """)

    sliders = ['boundary', 'crop_yield', 'quality', 'diseases', 'agronomist', 'abiotic', 'weeds', 'morphological']

    def make_all_metrics_equally_important():
        total = 100
        available_per_slider = total // len(sliders)
        for s in sliders:
            ss[s] = available_per_slider

    def reset_all_metrics_to_zero():
        for s in sliders:
            ss[s] = 0

    def get_used_points():
        """
        Calculates how many importance points are already picked by the user.
        Uses ss (state) and the key identifiers for the sliders.
        """
        s = (
                    ss.boundary + ss.crop_yield + ss.quality + ss.diseases + ss.agronomist + ss.abiotic + ss.weeds + ss.morphological)
        return s

    def get_available_points(total_points, used_points):
        return total_points - used_points

    def get_active_sliders(all_sliders, slider_to_exclude):
        return [x for x in all_sliders if
                ss[all_sliders[all_sliders.index(x)]] > 0  # make sure to only change the sliders the user changed
                and x != all_sliders[slider_to_exclude]]  # do not change the last slider the user changed

    def update(last):
        """ State function to prevents users picking sliders that sum up to > 100. """
        total = 100
        available = get_available_points(total, get_used_points())
        last = sliders.index(last)

        # change state only if user uses too many points (aka > 100)
        while available < 0:
            # change only sliders that are non-zero in value & are not the last slider the user changed
            change_sliders = get_active_sliders(sliders, last)
            # ceil division, to avoid race conditions
            correction = - (- abs(available) // len(change_sliders))

            for slider in change_sliders:
                ss[slider] -= correction

                # edge case: st keeps state (can be negative) separate from presentation (min = 0)
                if ss[slider] < 0:
                    ss[slider] = 0

            available = get_available_points(total, get_used_points())

    col1, col2 = st.columns(2)
    with col1:
        boundary = st.slider(boundary_string, key='boundary', min_value=0, max_value=100, step=1,
                             on_change=update, args=('boundary',))
        crop_yield = st.slider('Yield', key='crop_yield', min_value=0, max_value=100, step=1,
                               on_change=update, args=('crop_yield',))
        quality = st.slider('Quality/trading', key='quality', min_value=0, max_value=100, step=1,
                            on_change=update, args=('quality',))
        diseases = st.slider('Diseases', key='diseases', min_value=0, max_value=100, step=1, on_change=update,
                             args=('diseases',))

        st.button(label="Equalize", on_click=make_all_metrics_equally_important)
    with col2:
        agronomist = st.slider('Agronomist', key='agronomist', min_value=0, max_value=100, step=1,
                               on_change=update, args=('agronomist',))
        abiotic = st.slider('Abiotic', key='abiotic', min_value=0, max_value=100, step=1,
                            on_change=update, args=('abiotic',))
        weeds = st.slider('Weed competition', key='weeds', min_value=0, max_value=100, step=1,
                          on_change=update, args=('weeds',))
        morphological = st.slider('Morphological', key='morphological', min_value=0, max_value=100, step=1,
                                  on_change=update, args=('morphological',))

        st.button(label="Reset to 0", on_click=reset_all_metrics_to_zero)

    return boundary, crop_yield, quality, diseases, agronomist, abiotic, weeds, morphological


def present_wheat_class(data_frame):
    st.markdown("## Wheat class")
    st.text("The trading class the wheat cultivars can reach based on their quality metrics.")
    class_cols = ['moisture_at_harvest', 'protein_content', 'hectoliter_mass', 'impurities']
    missing_metrics = [x for x in class_cols if x not in data_frame.columns]
    if len(missing_metrics) > 0:
        st.text(f"Error: Trading class cannot be computed. Missing metrics:")
        for x in missing_metrics:
            st.text(f"- {x}")
    else:
        data_frame['wheat_class'] = data_frame[class_cols].apply(lambda x: get_wheat_classes(*x), axis=1)
        st.dataframe(data_frame[['cultivar', 'wheat_class'] + class_cols], hide_index=True)
