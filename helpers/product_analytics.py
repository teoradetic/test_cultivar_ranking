from bs4 import BeautifulSoup
import pathlib
import shutil
import streamlit as st

# or take it from the env
GA_MEASUREMENT_ID = st.secrets.ga4_measurement_id

GA_SCRIPT = f"""
<!-- Google tag (gtag.js) -->
<script async src="https://www.googletagmanager.com/gtag/js?id={GA_MEASUREMENT_ID}"></script>
<script id='google_analytics'>
  window.dataLayer = window.dataLayer || [];
  function gtag(){{dataLayer.push(arguments);}}
  gtag('js', new Date());
  gtag('config', '{GA_MEASUREMENT_ID}');
</script>
"""


def inject_ga():
    index_path = pathlib.Path(st.__file__).parent / "static" / "index.html"
    soup = BeautifulSoup(index_path.read_text(), features="html.parser")
    if not soup.find(id="google_analytics"):
        bck_index = index_path.with_suffix('.bck')
        if bck_index.exists():
            shutil.copy(bck_index, index_path)
        else:
            shutil.copy(index_path, bck_index)
        html = str(soup)
        new_html = html.replace('<head>', '<head>\n' + GA_SCRIPT)
        index_path.write_text(new_html)

def start_tracking(tracking_snippet):
    a = os.path.dirname(st.__file__) + '/static/index.html'

    with open(a, 'r') as f:
        data = f.read()
        if len(re.findall('G-', data)) == 0:
            with open(a, 'w') as ff:
                new_data = re.sub('<head>', '<head>' + tracking_snippet, data)
                ff.write(new_data)
