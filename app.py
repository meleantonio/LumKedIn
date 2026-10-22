import streamlit as st, tempfile, os
from kym.core import load_members, Matcher
st.set_page_config(page_title="Know Your Members",layout="wide")
st.title("🤝 Know Your Members")
st.caption("Member intro + speaker matcher — piloted on the Generative AI in Economics Teaching CoP (fictional sample data). Drafts only: nothing is sent.")
up=st.sidebar.file_uploader("Member profiles (CSV or JSON)",type=["csv","json"])
path="data/sample_members.csv"
if up:
    path=os.path.join(tempfile.mkdtemp(),up.name); open(path,"wb").write(up.getvalue())
@st.cache_resource
def get(p,_k): return Matcher(load_members(p))
m=get(path,up.name if up else "")
st.sidebar.write(f"{len(m.m)} members · embeddings: **{m.e.mode}**")
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
