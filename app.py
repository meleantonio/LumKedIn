import streamlit as st, tempfile, os
from kym.core import load_members, Matcher
st.set_page_config(page_title="Know Your Members",layout="wide")
st.title("🤝 Know Your Members")
st.caption("Member intro + speaker matcher — piloted on the Generative AI in Economics Teaching CoP (fictional sample data). Drafts only: nothing is sent.")
up=st.sidebar.file_uploader("Member profiles (CSV or JSON)",type=["csv","json"])
path="data/sample_members.csv"
if up:
    path=os.path.join(tempfile.mkdtemp(),up.name); open(path,"wb").write(up.getvalue())
be=st.sidebar.radio("Memory backend",["tfidf","cognee"],index=1 if os.getenv("KYM_BACKEND","").lower()=="cognee" else 0,
    help="Cognee builds a knowledge graph (needs LLM_API_KEY + pip install -r requirements-cognee.txt). Falls back to TF-IDF automatically.")
@st.cache_resource(show_spinner="Building member memory...")
def get(p,_k,b): return Matcher(load_members(p),b)
m=get(path,up.name if up else "",be)
if m.backend_note: st.sidebar.warning(m.backend_note)
st.sidebar.write(f"{len(m.m)} members · backend: **{m.backend}** · embeddings: **{m.e.mode}**")
t1,t2,t3=st.tabs(["Intros","Speaker finder","Members"])
with t1:
    k=st.slider("Number of intros",1,10,5)
    for x in m.intros(k):
        with st.expander(f"**{x['a']}  ↔  {x['b']}**  · score {x['score']}",expanded=True):
            st.write(x["reason"]); st.text_area("Intro draft (copy & send yourself)",x["draft"],height=260,key=x['a']+x['b'])
with t2:
    th=st.text_input("Seminar theme","AI and assessment integrity")
    for n,x in enumerate(m.speakers(th,st.slider("Shortlist size",1,10,5)),1):
        st.markdown(f"**{n}. {x['name']}** — {x['institution']} · {x['score']}  \n{x['reason']}")
with t3: st.dataframe(m.m,use_container_width=True)
