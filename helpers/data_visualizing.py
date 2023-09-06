import altair as alt
import matplotlib.pyplot as plt
import streamlit as st


def plot_column(column_name, metric_df):
    viz_title = f"{column_name.replace('_', ' ').title()} vs Cultivar"
    base = alt.Chart(metric_df, title=alt.Title(viz_title)).encode(
        x=column_name,
        y="cultivar:O",
        text=column_name,
        color=alt.Color('cultivar').legend(None).scale(scheme='tableau20'),
    )
    chart = base.mark_bar() + base.mark_text(align='left', dx=2)
    st.altair_chart(chart, use_container_width=True)


def visualize_metrics(metric_string, metric_df, rank_df, catalog, idx, cmap=None):
    """Simple visualizing algorithm displaying a class of metrics, their ranks, and their charts."""
    if cmap is None:
        cmap = plt.cm.get_cmap('summer')

    metric_string_pretty = metric_string.replace('_', ' ').title()

    st.markdown(f"## {idx}. {metric_string_pretty} Analysis")
    st.markdown(
        f"""
        Within the {metric_string_pretty} Analysis you can find:
        1. **Metric details** - a table with {metric_string_pretty} metrics collected for each cultivar.
        2. **Metric visualized** - charts and graphs visualizing {metric_string_pretty} metrics for each cultivar.
        3. **Ranked metrics** - cultivars ranked based on the {metric_string_pretty} metrics from best (1) to worst ({len(rank_df)}).
        """
    )
    # metrics dataframe
    st.markdown(f"#### {idx}.1 {metric_string_pretty} metrics - details")
    st.text("Check metrics values for each cultivar.")
    with st.expander(f"Explain the {metric_string_pretty} metrics"):
        explanations = catalog[catalog.metric.isin(metric_df.columns)][['metric', 'explanation']]
        for _, row in explanations.iterrows():
            st.markdown(f"- **{row.metric}**: {row.explanation}")
    st.dataframe(metric_df, hide_index=True)

    # metrics visualized
    st.markdown(f"#### {idx}.2 {metric_string_pretty} metrics visualized")
    st.text("Each metric is visualized by cultivar.")
    for col in metric_df.columns[1:]:
        # skip date visualizations
        if col.startswith('date_of_'):
            continue

        plot_column(col, metric_df)

    # metrics ranked
    st.markdown(f"#### {idx}.3 Ranking results: {metric_string_pretty} metrics")
    st.text(
        f"The overall rank takes all the {metric_string_pretty} metrics, \nranks each column separately (from best to worst) "
        f"\nand then computes the overall rank from all ranks.")
    st.dataframe(rank_df.style.background_gradient(cmap=cmap, subset=[f'overall_rank-{metric_string}']),
                 hide_index=True)
    st.divider()
