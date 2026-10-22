import os
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

TITLES={"dr","prof","professor","mr","ms","mrs","mx","miss","sir","dame"}
def greet_name(name):
    """First name if the name starts with a title, otherwise the full name."""
    parts=name.split()
    if len(parts)>1 and parts[0].lower().rstrip(".") in TITLES: return parts[1]
    return name

def _overlap(a,b):
    wa={w.strip().lower() for w in a.replace(";",",").split(",") if w.strip()}
    return [w for w in wa if any(t in b.lower() for t in w.split() if len(t)>4)]

def _blurb(p):
    t=p['name']+(f" ({', '.join(x for x in (p.get('role',''),p.get('institution','')) if x)})" if p.get('role') or p.get('institution') else "")
    if p.get('interests'): t+=f" works on {p['interests']}"
    if p.get('can_talk_about'): t+=f" and could talk about {p['can_talk_about']}"
    return t+"."

def _spk(p):
    bits=[f"Can talk about \"{p['can_talk_about']}\"" if p.get('can_talk_about') else "",f"teaches {p['teaching_topics']}" if p.get('teaching_topics') else ""]
    return ("; ".join(b for b in bits if b) or f"Keyword match on role and interests ({p.get('interests') or p.get('role') or 'profile'})")+"."

class Matcher:
    def __init__(self, members, backend=None):
        self.m=members
        self.backend="tfidf"; self.backend_note=""
        want=(backend or os.getenv("KYM_BACKEND") or "auto").lower()
        if want=="auto":
            want="cognee-cloud" if os.getenv("COGNEE_API_KEY") else ("cognee" if os.getenv("LLM_API_KEY") else "tfidf")
            if want=="tfidf": self.backend_note="No COGNEE_API_KEY or LLM_API_KEY set - running offline TF-IDF/SQLite."
        if want=="cognee-cloud":
            from . import cognee_cloud as cc
            if not cc.available(): self.backend_note="cognee-cloud needs COGNEE_API_KEY and COGNEE_API_URL - using TF-IDF/SQLite."
            else:
                try: cc.check(); self.backend="cognee-cloud"; self.cb=cc
                except Exception as e: self.backend_note=f"Cognee Cloud unreachable ({type(e).__name__}) - using TF-IDF/SQLite."
        elif want=="cognee":
            from . import cognee_backend as cb
            if not cb.available(): self.backend_note="Cognee requested but not installed or LLM_API_KEY missing - using TF-IDF/SQLite."
            else:
                try: cb.ingest(members); self.backend="cognee"; self.cb=cb
                except Exception as e: self.backend_note=f"Cognee ingest failed ({type(e).__name__}) - using TF-IDF/SQLite."
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
        if h[i,j]<h[j,i]: a,b=b,a
        w,c=a.get('wants_to_learn','').strip(),b.get('can_talk_about','').strip()
        if w and c: return f"{a['name']} wants to learn \"{w}\" and {b['name']} can talk about \"{c}\"."
        if w: return f"{a['name']} wants to learn \"{w}\", which overlaps with {b['name']}'s work."
        if c: return f"{b['name']} can talk about \"{c}\", which overlaps with {a['name']}'s interests."
        return f"{a['name']} and {b['name']} have overlapping interests."
    def _pair(self,a,b,s,tmpl):
        if self.backend.startswith("cognee"):
            try:
                ctx=self.cb.pair_context(a,b)
                if ctx: tmpl=f"{tmpl} Memory graph: {ctx.strip()[:300]}"
            except Exception: pass
        reason=llm(f"In one sentence, why should these two economics educators meet?\nA: {a}\nB: {b}") or tmpl
        draft=llm(f"Write a short warm email introducing these two community members to each other. Reason: {reason}\nA: {a}\nB: {b}") or (
f"Subject: Intro: {a['name']} <> {b['name']}\n\nHi {greet_name(a['name'])} and {greet_name(b['name'])},\n\n"
f"I'd love to introduce you two from our {os.getenv('KYM_COMMUNITY','Generative AI in Economics Teaching')} community.\n\n"
f"{_blurb(a)}\n{_blurb(b)}\n\n"
f"Why: {reason}\n\nWould a 20-minute coffee chat in the next couple of weeks work? I'll leave it with you.\n\nBest,\nAntonio")
        return {"a":a["name"],"b":b["name"],"score":round(float(s),3),"reason":reason,"draft":draft}
    def speakers(self, theme, k=5):
        q=self.e([theme])[0]; s=self.offer@q; idx=list(np.argsort(-s)[:k])
        if self.backend.startswith("cognee"):
            try:
                hits,extra=self.cb.rank_speakers(self.m,theme,k)
                if hits:
                    idx=(hits+[i for i in idx if i not in hits])[:k]
                    def why(i,n):
                        c=self.m[i].get('can_talk_about','').strip()
                        base=f"Can talk about \"{c}\"." if c else "Keyword match on role and interests ("+(self.m[i].get('interests') or self.m[i].get('role') or 'profile')+")."
                        if i not in hits: return "TF-IDF fill. "+base
                        r=extra.get(i) if isinstance(extra,dict) else None
                        return f"{self.backend} graph pick #{n+1}: {r}" if r else f"{self.backend} graph pick #{n+1}. {base}"
                    return [{"name":self.m[i]["name"],"institution":self.m[i]["institution"],"score":round(float(s[i]),3),"reason":why(i,n)} for n,i in enumerate(idx)]
            except Exception: pass
        return [{"name":self.m[i]["name"],"institution":self.m[i]["institution"],"score":round(float(s[i]),3),
                 "reason":llm(f"In one sentence, why is this person a good speaker for a seminar on '{theme}'? {self.m[i]}") or _spk(self.m[i])} for i in idx]
