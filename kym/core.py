"""Core: ingest, embed, store, match. Works offline with TF-IDF."""
import csv, json, os, sqlite3, itertools
import numpy as np
FIELDS=["name","role","institution","interests","teaching_topics","can_talk_about","wants_to_learn"]
DB=os.getenv("KYM_DB","kym.sqlite")

def load_members(path):
    if path.endswith(".json"): rows=json.load(open(path))
    else: rows=list(csv.DictReader(open(path,newline="")))
    return [{f:(r.get(f) or "").strip() for f in FIELDS} for r in rows if r.get("name")]

def text(m,part="all"):
    if part=="offer": return f"{m['interests']}. {m['teaching_topics']}. {m['can_talk_about']}"
    if part=="want": return m["wants_to_learn"]
    return " ".join(m[f] for f in FIELDS[3:])

class Embedder:
    def __init__(self, corpus):
        self.mode="openai" if os.getenv("OPENAI_API_KEY") else "tfidf"
        if self.mode=="tfidf":
            from sklearn.feature_extraction.text import TfidfVectorizer
            self.v=TfidfVectorizer(stop_words="english",ngram_range=(1,2),sublinear_tf=True).fit(corpus)
    def __call__(self, texts):
        if self.mode=="openai":
            from openai import OpenAI
            r=OpenAI().embeddings.create(model=os.getenv("EMBED_MODEL","text-embedding-3-small"),input=texts)
            X=np.array([d.embedding for d in r.data])
        else: X=self.v.transform(texts).toarray()
        n=np.linalg.norm(X,axis=1,keepdims=True); n[n==0]=1; return X/n

def store(members, emb, db=DB):
    c=sqlite3.connect(db); c.execute("create table if not exists members(name text primary key, data text, vec blob)")
    for m,v in zip(members,emb): c.execute("replace into members values(?,?,?)",(m["name"],json.dumps(m),v.astype("float32").tobytes()))
    c.commit(); c.close()
    if os.getenv("SUPABASE_URL") and os.getenv("SUPABASE_KEY"):
        try:
            from supabase import create_client
            sb=create_client(os.environ["SUPABASE_URL"],os.environ["SUPABASE_KEY"])
            sb.table("members").upsert([{"name":m["name"],"data":m,"embedding":v.tolist()} for m,v in zip(members,emb)]).execute()
        except Exception as e: print("Supabase sync skipped:",e)

def llm(prompt):
    if not os.getenv("OPENAI_API_KEY"): return None
    try:
        from openai import OpenAI
        r=OpenAI(base_url=os.getenv("OPENAI_BASE_URL")).chat.completions.create(model=os.getenv("LLM_MODEL","gpt-4o-mini"),messages=[{"role":"user","content":prompt}])
        return r.choices[0].message.content.strip()
    except Exception: return None

def _overlap(a,b):
    wa={w.strip().lower() for w in a.replace(";",",").split(",") if w.strip()}
    return [w for w in wa if any(t in b.lower() for t in w.split() if len(t)>4)]

class Matcher:
    def __init__(self, members):
        self.m=members
        self.e=Embedder([text(x) for x in members]+[text(x,"want") for x in members])
        self.all=self.e([text(x) for x in members]); self.offer=self.e([text(x,"offer") for x in members]); self.want=self.e([text(x,"want") for x in members])
        store(members,self.all)
    def intros(self, k=5, same_inst=False):
        sim=self.all@self.all.T; help_=self.want@self.offer.T  # i wants what j offers
        out=[]
        for i,j in itertools.combinations(range(len(self.m)),2):
            a,b=self.m[i],self.m[j]
            if not same_inst and a["institution"]==b["institution"]: continue
            s=0.4*sim[i,j]+0.3*help_[i,j]+0.3*help_[j,i]
            out.append((s,i,j))
        out.sort(reverse=True); res=[]; used={}
        for s,i,j in out:
            if used.get(i,0)>=2 or used.get(j,0)>=2: continue
            used[i]=used.get(i,0)+1; used[j]=used.get(j,0)+1
            a,b=self.m[i],self.m[j]; res.append(self._pair(a,b,s,self.help_reason(i,j,help_)))
            if len(res)>=k: break
        return res
    def help_reason(self,i,j,h):
        a,b=self.m[i],self.m[j]
        if h[i,j]>=h[j,i]: return f"{a['name'].split()[-1]} wants to learn \"{a['wants_to_learn']}\" and {b['name']} can talk about \"{b['can_talk_about']}\"."
        return f"{b['name'].split()[-1]} wants to learn \"{b['wants_to_learn']}\" and {a['name']} can talk about \"{a['can_talk_about']}\"."
    def _pair(self,a,b,s,tmpl):
        reason=llm(f"In one sentence, why should these two economics educators meet?\nA: {a}\nB: {b}") or tmpl
        draft=llm(f"Write a short warm email introducing these two community members to each other. Reason: {reason}\nA: {a}\nB: {b}") or (
f"Subject: Intro: {a['name']} <> {b['name']}\n\nHi {a['name'].split()[1]} and {b['name'].split()[1]},\n\n"
f"I'd love to introduce you two from our Generative AI in Economics Teaching community.\n\n"
f"{a['name']} ({a['role']}, {a['institution']}) works on {a['interests']} and could talk about {a['can_talk_about']}.\n"
f"{b['name']} ({b['role']}, {b['institution']}) works on {b['interests']} and could talk about {b['can_talk_about']}.\n\n"
f"Why: {reason}\n\nWould a 20-minute coffee chat in the next couple of weeks work? I'll leave it with you.\n\nBest,\nAntonio")
        return {"a":a["name"],"b":b["name"],"score":round(float(s),3),"reason":reason,"draft":draft}
    def speakers(self, theme, k=5):
        q=self.e([theme])[0]; s=self.offer@q; idx=np.argsort(-s)[:k]
        return [{"name":self.m[i]["name"],"institution":self.m[i]["institution"],"score":round(float(s[i]),3),
                 "reason":llm(f"In one sentence, why is this person a good speaker for a seminar on '{theme}'? {self.m[i]}") or f"Can talk about \"{self.m[i]['can_talk_about']}\"; teaches {self.m[i]['teaching_topics']}."} for i in idx]
