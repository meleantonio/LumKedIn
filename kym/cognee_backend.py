"""Optional Cognee memory backend (https://github.com/topoteretes/cognee).
Enable with KYM_BACKEND=cognee + LLM_API_KEY. Any failure -> caller falls back to TF-IDF."""
import asyncio, os
DATASET = os.getenv("KYM_COGNEE_DATASET", "kym_members")

def available():
    try:
        import cognee  # noqa
        return bool(os.getenv("LLM_API_KEY"))
    except ImportError:
        return False

def _run(coro):
    try: return asyncio.run(coro)
    except RuntimeError:  # already inside an event loop (e.g. Streamlit)
        loop = asyncio.new_event_loop()
        try: return loop.run_until_complete(coro)
        finally: loop.close()

def profile_doc(m):
    return (f"Member profile. Name: {m['name']}. Role: {m['role']} at {m['institution']}. "
            f"Interests: {m['interests']}. Teaches: {m['teaching_topics']}. "
            f"Can talk about: {m['can_talk_about']}. Wants to learn: {m['wants_to_learn']}.")

def ingest(members, reset=True):
    import cognee
    async def go():
        if reset:
            await cognee.prune.prune_data(); await cognee.prune.prune_system(metadata=True)
        await cognee.add([profile_doc(m) for m in members], dataset_name=DATASET)
        await cognee.cognify(datasets=[DATASET])   # builds the knowledge graph
    _run(go())

def _text(results):
    out = []
    for r in results or []:
        v = getattr(r, "search_result", r)
        out.append(v if isinstance(v, str) else str(v))
    return "\n".join(out)

def search(query, kind="GRAPH_COMPLETION"):
    import cognee
    from cognee import SearchType
    return _text(_run(cognee.search(query_text=query, query_type=getattr(SearchType, kind), datasets=[DATASET])))

def rank_speakers(members, theme, k):
    """Ask the graph for speakers; return (ordered member indices, answer text)."""
    ans = search(f"Which community members are the best speakers for a seminar on '{theme}'? "
                 f"List full names, best first, each with a one-sentence reason grounded in their profile.")
    pos = {i: ans.find(m["name"]) for i, m in enumerate(members)}
    hits = sorted([i for i, p in pos.items() if p >= 0], key=lambda i: pos[i])
    return hits[:k], ans

def pair_context(a, b):
    return search(f"What do {a['name']} and {b['name']} have in common, and what could each learn from the other? Answer in one sentence.")
