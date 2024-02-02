import os
import re

import streamlit as st

# or take it from the env
GA4_MID = st.secrets.ga4_measurement_id

ga4_code = f"""
    <!-- Google tag (gtag.js) -->
    <script async src="https://www.googletagmanager.com/gtag/js?id={GA4_MID}"></script>
    <script>
      window.dataLayer = window.dataLayer || [];
      function gtag(){{dataLayer.push(arguments);}}
      gtag('js', new Date());

      gtag('config', '{GA4_MID}');
    </script>
    """


def start_tracking(tracking_snippet):
    a = os.path.dirname(st.__file__) + '/static/index.html'

    with open(a, 'r') as f:
        data = f.read()
        if len(re.findall(tracking_snippet, data)) == 0:
            with open(a, 'w') as ff:
                new_data = re.sub('<head>', '<head>' + tracking_snippet, data)
                ff.write(new_data)