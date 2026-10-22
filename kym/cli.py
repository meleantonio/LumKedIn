import argparse, json
from .core import load_members, Matcher
def main():
    p=argparse.ArgumentParser(prog="kym",description="LumKedIn (Luma meets LinkedIn): intro + speaker matcher")
    p.add_argument("--members",default="data/sample_members.csv")
    p.add_argument("--backend",choices=["auto","cognee-cloud","cognee","tfidf"],default=None,help="default: $KYM_BACKEND or auto")
    p.add_argument("--dataset",default=None,help="Cognee dataset name (default: $KYM_DATASET or know-your-members-demo)")
    sp=p.add_subparsers(dest="cmd",required=True)
    i=sp.add_parser("intros"); i.add_argument("-k",type=int,default=5); i.add_argument("--drafts",action="store_true"); i.add_argument("--json",action="store_true")
    s=sp.add_parser("speakers"); s.add_argument("theme"); s.add_argument("-k",type=int,default=5); s.add_argument("--json",action="store_true")
    sp.add_parser("ingest-cloud",help="upload --members to Cognee Cloud dataset (add + cognify)")
    a=p.parse_args()
    from . import cognee_cloud as cc; cc.set_dataset(a.dataset)
    if a.cmd=="ingest-cloud":
        from .cognee_backend import profile_doc
        import time; t=time.time(); cc.ingest([profile_doc(x) for x in load_members(a.members)])
        print(f"ingested into {cc.DATASET} in {time.time()-t:.0f}s"); return
    m=Matcher(load_members(a.members),a.backend)
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
