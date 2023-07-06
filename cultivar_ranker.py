import streamlit as st
from PIL import Image

col1, col2 = st.columns([1, 5])
with col1:
    st.image(Image.open('logo_2.png'), width=50)
with col2:
    st.title("Cultivar Ranker")

st.markdown("Cultivar ranker has moved from this experimental URL to a new permanent URL.")
st.markdown("**[GET THE NEW URL](https://streamlit.logineko-analytics.org/dashboard-cultivar-ranker/)**")