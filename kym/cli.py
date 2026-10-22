import argparse, json
from .core import load_members, Matcher
def main():
    p=argparse.ArgumentParser(prog="kym",description="Know Your Members: intro + speaker matcher")
    p.add_argument("--members",default="data/sample_members.csv")
    p.add_argument("--backend",choices=["tfidf","cognee"],default=None,help="default: $KYM_BACKEND or tfidf")
    sp=p.add_subparsers(dest="cmd",required=True)
    i=sp.add_parser("intros"); i.add_argument("-k",type=int,default=5); i.add_argument("--drafts",action="store_true"); i.add_argument("--json",action="store_true")
    s=sp.add_parser("speakers"); s.add_argument("theme"); s.add_argument("-k",type=int,default=5); s.add_argument("--json",action="store_true")
    a=p.parse_args(); m=Matcher(load_members(a.members),a.backend)
    r=m.intros(a.k) if a.cmd=="intros" else m.speakers(a.theme,a.k)
    if a.json: print(json.dumps(r,indent=1)); return
    if m.backend_note: print("NOTE:",m.backend_note)
    print(f"[backend: {m.backend} | embeddings: {m.e.mode}]  (drafts only - nothing is sent)\n")
    for n,x in enumerate(r,1):
        if a.cmd=="intros":
            print(f"{n}. {x['a']}  <>  {x['b']}  ({x['score']})\n   {x['reason']}")
            if a.drafts: print("\n"+x["draft"]+"\n"+"-"*60)
        else: print(f"{n}. {x['name']} ({x['institution']}) {x['score']}\n   {x['reason']}")
if __name__=="__main__": main()
