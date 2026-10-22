import streamlit as st, tempfile, os, html, hashlib
from kym.core import load_members, Matcher
from kym import cognee_cloud as _cc
st.set_page_config(page_title="Know Your Members", page_icon="🤝", layout="wide")
E = lambda s: html.escape(str(s or ""))

st.markdown("""<style>
@import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700;800&display=swap');
html, body, [class*="css"], .stMarkdown, button, input, textarea {font-family:'Inter',sans-serif !important;}
.block-container{padding-top:1.6rem;max-width:1240px}
.hero{background:linear-gradient(120deg,#6d28d9 0%,#4f46e5 45%,#0ea5e9 100%);border-radius:22px;padding:30px 34px;margin-bottom:22px;
 box-shadow:0 20px 60px -20px rgba(99,102,241,.55);position:relative;overflow:hidden}
.hero:after{content:"";position:absolute;right:-80px;top:-80px;width:320px;height:320px;border-radius:50%;background:rgba(255,255,255,.08)}
.hero h1{color:#fff;font-weight:800;font-size:2.3rem;margin:0 0 4px;letter-spacing:-.02em}
.hero p{color:rgba(255,255,255,.85);margin:0 0 16px;font-size:1rem}
.pill{display:inline-flex;align-items:center;gap:8px;background:rgba(10,12,30,.35);border:1px solid rgba(255,255,255,.25);color:#fff;
 padding:6px 14px;border-radius:999px;font-size:.85rem;font-weight:600;margin-right:8px;backdrop-filter:blur(6px)}
.dot{width:8px;height:8px;border-radius:50%;background:#22c55e;box-shadow:0 0 10px #22c55e}
.dot.warn{background:#f59e0b;box-shadow:0 0 10px #f59e0b}
.grid{display:grid;grid-template-columns:repeat(auto-fill,minmax(270px,1fr));gap:16px}
.card{background:#151829;border:1px solid #262a45;border-radius:16px;padding:18px;transition:.2s}
.card:hover{border-color:#8b5cf6;transform:translateY(-2px)}
.row{display:flex;gap:12px;align-items:center}
.av{flex:none;width:44px;height:44px;border-radius:50%;display:flex;align-items:center;justify-content:center;font-weight:700;color:#fff;font-size:.95rem}
.nm{font-weight:700;color:#f3f4fb;font-size:1rem;line-height:1.2}
.sub{color:#9aa0bf;font-size:.82rem;margin-top:2px}
.chip{display:inline-block;background:#1f2340;color:#c4b5fd;border:1px solid #2e3360;border-radius:999px;padding:3px 10px;font-size:.74rem;margin:8px 6px 0 0}
.rank{font-weight:800;font-size:1.4rem;color:#8b5cf6;width:34px}
.badge{display:inline-block;background:linear-gradient(90deg,#22c55e,#10b981);color:#04140b;font-weight:700;font-size:.7rem;padding:3px 9px;border-radius:999px;margin-left:8px;vertical-align:middle}
.badge.fill{background:#2a2f52;color:#aab0d6}
.bar{height:6px;background:#23284a;border-radius:6px;margin-top:12px;overflow:hidden}
.bar>div{height:100%;background:linear-gradient(90deg,#8b5cf6,#0ea5e9);border-radius:6px}
.reason{color:#c9cde3;font-size:.9rem;margin-top:10px;line-height:1.5}
.pair{display:grid;grid-template-columns:1fr auto 1fr;gap:14px;align-items:center}
.link{font-size:1.4rem;color:#8b5cf6;font-weight:800}
.why{background:#11142a;border-left:3px solid #8b5cf6;border-radius:10px;padding:12px 14px;color:#cfd3ea;font-size:.9rem;margin:12px 0 6px;line-height:1.5}
.score{color:#9aa0bf;font-size:.8rem;font-weight:600}
[data-testid="stToolbar"],[data-testid="stDecoration"]{display:none}
div[role="tablist"]{gap:6px;background:#151829;padding:6px;border-radius:14px;border:1px solid #262a45}
button[role="tab"]{border-radius:10px !important;padding:8px 18px !important;font-weight:600}
button[role="tab"][aria-selected="true"]{background:linear-gradient(90deg,#6d28d9,#4f46e5) !important;color:#fff !important}
button[role="tab"] p{font-size:.95rem;font-weight:600}
.stTabs [data-baseweb="tab-list"]{gap:6px;background:#151829;padding:6px;border-radius:14px;border:1px solid #262a45}
.stTabs [data-baseweb="tab"]{border-radius:10px;padding:8px 18px;font-weight:600;color:#9aa0bf}
.stTabs [aria-selected="true"]{background:linear-gradient(90deg,#6d28d9,#4f46e5);color:#fff !important}
.stTabs [data-baseweb="tab-highlight"],.stTabs [data-baseweb="tab-border"]{display:none}
section[data-testid="stSidebar"]{background:#0f1222;border-right:1px solid #1f2340}
div[data-testid="stExpander"]{border:1px solid #262a45;border-radius:12px;background:#12152a}
</style>""", unsafe_allow_html=True)

PAL = ["#8b5cf6","#0ea5e9","#ec4899","#f59e0b","#10b981","#6366f1","#ef4444","#14b8a6"]
def avatar(name):
    parts=[p for p in str(name).split() if p.rstrip(".") not in ("Dr","Prof","Mr","Ms","Mrs","Mx")]
    ini=(parts[0][0]+(parts[-1][0] if len(parts)>1 else "")).upper() if parts else "?"
    c=PAL[int(hashlib.md5(str(name).encode()).hexdigest(),16)%len(PAL)]
    return f'<div class="av" style="background:linear-gradient(135deg,{c},#1e1b4b)">{E(ini)}</div>'
def chips(s, n=4):
    tags=[t.strip() for t in str(s or "").replace(",",";").split(";") if t.strip()][:n]
    return "".join(f'<span class="chip">{E(t)}</span>' for t in tags)
def person(p):
    sub=" · ".join(x for x in (p.get("role",""),p.get("institution","")) if x)
    return f'<div class="row">{avatar(p["name"])}<div><div class="nm">{E(p["name"])}</div><div class="sub">{E(sub)}</div></div></div>'

# ---- sidebar / data ----
st.sidebar.markdown("### ⚙️ Settings")
up=st.sidebar.file_uploader("Member profiles (CSV or JSON)",type=["csv","json"])
path=os.getenv("KYM_MEMBERS","data/sample_members.csv")
if up: path=os.path.join(tempfile.mkdtemp(),up.name); open(path,"wb").write(up.getvalue())
ds=st.sidebar.text_input("Cognee dataset",_cc.DATASET); _cc.set_dataset(ds)
opts=["auto","cognee-cloud","cognee","tfidf"]; envb=os.getenv("KYM_BACKEND","auto").lower()
be=st.sidebar.radio("Memory backend",opts,index=opts.index(envb) if envb in opts else 0,
    help="auto = cognee-cloud if COGNEE_API_KEY, else local cognee if LLM_API_KEY, else TF-IDF. Any failure falls back to TF-IDF.")
@st.cache_resource(show_spinner="Building member memory...")
def get(p,_k,b,_ds): return Matcher(load_members(p),b)
m=get(path,up.name if up else "",be,ds)
st.sidebar.caption(f"{len(m.m)} members · backend: {m.backend} · embeddings: {m.e.mode}")
st.sidebar.caption("Drafts only: nothing is ever sent.")
@st.cache_data(show_spinner="Asking member memory...")
def intros(_m,key,k): return _m.intros(k)
@st.cache_data(show_spinner="Asking member memory...")
def speakers(_m,key,th,k): return _m.speakers(th,k)
key=(path,be,m.backend,ds)
byname={p["name"]:p for p in m.m}
comm=os.getenv("KYM_COMMUNITY","Generative AI in Economics Teaching CoP (fictional sample data)")

ok=m.backend.startswith("cognee")
st.markdown(f"""<div class="hero"><h1>🤝 Know Your Members</h1>
<p>Who should meet whom, and who can speak on what: {E(comm)}. Drafts only, nothing is sent.</p>
<span class="pill"><span class="dot{'' if ok else ' warn'}"></span>Active backend: {E(m.backend)}</span>
<span class="pill">👥 {len(m.m)} members</span><span class="pill">🧠 dataset: {E(ds)}</span></div>""",unsafe_allow_html=True)
if m.backend_note: st.warning(m.backend_note)

t1,t2,t3=st.tabs(["✨ Intros","🎤 Speaker finder","👥 Members"])
with t1:
    k=st.slider("Number of intros",1,10,5)
    for x in intros(m,key,k):
        a,b=byname.get(x["a"],{"name":x["a"]}),byname.get(x["b"],{"name":x["b"]})
        st.markdown(f"""<div class="card" style="margin-bottom:6px"><div class="pair">
<div>{person(a)}{chips(a.get('interests'),3)}</div><div class="link">⟷</div><div>{person(b)}{chips(b.get('interests'),3)}</div></div>
<div class="why">{E(x['reason'])}</div><div class="score">match score {x['score']}</div></div>""",unsafe_allow_html=True)
        with st.expander("✉️ Intro draft (copy and send it yourself)"):
            st.text_area("draft",x["draft"],height=280,key=x['a']+x['b'],label_visibility="collapsed")
        st.write("")
with t2:
    c1,c2=st.columns([4,1])
    th=c1.text_input("Seminar theme","AI and assessment integrity")
    n_=c2.number_input("Shortlist",1,10,5)
    res=speakers(m,key,th,int(n_)); mx=max([r["score"] for r in res]+[1e-9])
    for n,x in enumerate(res,1):
        g="graph pick" in x["reason"]
        w=100 if g and x["score"]==0 else max(6,int(100*x["score"]/mx))
        reason=x["reason"].split(":",1)[1].strip() if g and ":" in x["reason"] else x["reason"]
        badge='<span class="badge">◆ graph pick</span>' if g else '<span class="badge fill">TF-IDF</span>'
        p=byname.get(x["name"],{"name":x["name"],"institution":x.get("institution","")})
        st.markdown(f"""<div class="card" style="margin-bottom:12px"><div class="row"><div class="rank">{n}</div>{avatar(p['name'])}
<div style="flex:1"><div class="nm">{E(p['name'])}{badge}</div><div class="sub">{E(" · ".join(v for v in (p.get('role',''),p.get('institution','')) if v))}</div></div>
<div class="score">{x['score']}</div></div><div class="reason">{E(reason)}</div><div class="bar"><div style="width:{w}%"></div></div></div>""",unsafe_allow_html=True)
with t3:
    q=st.text_input("Filter members","",placeholder="Search name, role, interest…").lower()
    cards="".join(f'<div class="card">{person(p)}{chips(p.get("interests"))}</div>' for p in m.m
                  if not q or q in " ".join(str(v) for v in p.values()).lower())
    st.markdown(f'<div class="grid">{cards}</div>',unsafe_allow_html=True)
    with st.expander("Raw table"): st.dataframe(m.m,use_container_width=True)
