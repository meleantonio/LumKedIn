# 🤝 LumKedIn: Luma meets LinkedIn

**Live demo:** https://lumkedin.vercel.app

LumKedIn helps a community organiser answer two questions about a room full of people:

- **Who should meet whom?** It ranks pairs where one person wants to learn what the other can talk about, and gives a reason and a ready-to-send **intro email draft** for each pair.
- **Who could speak on X?** It ranks members as speakers for a seminar theme.

Matching runs on an offline TF-IDF matcher with SQLite. When Cognee Cloud credentials are set, it also uses a **Cognee Cloud memory graph** (`/api/v1/recall`), so you get "graph picks" with reasons. Any Cognee failure falls back to TF-IDF automatically. **Drafts only: nothing is ever sent.**

Built for **Track 2 "Know Your Members"** at the **Grok Bot Community Engineering London Hackathon** (22 Oct 2026).

## Data and privacy
- **The live demo** (lumkedin.vercel.app) defaults to profiles of the event's hosts, partners, community leads and judges. They were built **only from public info** on the event's Luma page and the hackathon site. Guesses are labelled "inferred" and unknown fields are left blank. A fictional sample dataset is available in the dataset picker.
- **This repo ships only fictional data** (`data/sample_members.csv`, 20 invented economics educators). Real people's data lives in `data/private/`, which is gitignored and **never committed**. It is uploaded only to the Vercel deployment by the CLI.
- **CSVs you upload in the web page** are processed in memory with TF-IDF only. They are never stored and never sent to Cognee.

## Run locally

```bash
git clone https://github.com/meleantonio/LumKedIn && cd LumKedIn
python3 -m venv .venv && . .venv/bin/activate
pip install -r requirements-app.txt          # numpy, scikit-learn, streamlit
streamlit run app.py                          # http://localhost:8501
```

**CLI**, using the same engine:

```bash
python -m kym.cli intros -k 5 --drafts
python -m kym.cli speakers "AI and assessment integrity" -k 5
python -m kym.cli --backend tfidf speakers "classroom simulations"   # force the offline backend
python -m kym.cli intros --json
```

**Static web version locally** (the same page as Vercel): `npx vercel dev`, or open `public/index.html` behind any server that runs `api/*.py`.

## Environment variables

| Var | Purpose |
|---|---|
| `COGNEE_API_URL`, `COGNEE_API_KEY` | Enable the hosted Cognee Cloud backend (optional `COGNEE_TENANT_ID`). Without them, TF-IDF is used. |
| `KYM_BACKEND` | `auto` (default), `cognee-cloud`, `cognee` (local SDK, needs `LLM_API_KEY`) or `tfidf` |
| `KYM_MEMBERS` | Path to the members CSV/JSON for Streamlit (default `data/sample_members.csv`) |
| `KYM_DATASET` | Cognee dataset name (default `know-your-members-demo`, already populated with the fictional sample) |
| `KYM_COMMUNITY` | Community name used in the hero header and intro drafts |
| `KYM_THEME` | Default speaker theme in the Streamlit app |

Copy `.env.example` to `.env`, or export the variables in your shell. Never commit keys.

## Use it for your own community

1. Make a CSV with this header (only `name` is required):
   `name,role,institution,interests,teaching_topics,can_talk_about,wants_to_learn`
   Separate list items with `;`. Put it in `data/private/` so git ignores it.
2. Optional: load it into Cognee Cloud once:
   `python -m kym.cli --members data/private/mine.csv --dataset mine ingest-cloud`
3. Run it:
   `KYM_MEMBERS=data/private/mine.csv KYM_DATASET=mine KYM_COMMUNITY="My community" scripts/demo-luma.sh`
   Add `--backend tfidf` if Cognee is slow. You can also upload the CSV in the Streamlit sidebar or on the web page.

## Deploy your own copy to Vercel

The web version is `public/index.html` (static, dark UI) plus Python serverless functions `api/members.py`, `api/speakers.py` and `api/intros.py`. They reuse `kym/` and only need `requirements.txt` (numpy and scikit-learn).

```bash
npm i -g vercel
vercel deploy --prod --yes                                   # first run creates the project
printf %s "$COGNEE_API_URL" | vercel env add COGNEE_API_URL production   # optional
printf %s "$COGNEE_API_KEY" | vercel env add COGNEE_API_KEY production   # optional
vercel deploy --prod --yes
```

If `data/private/luma-eveur09a.csv` exists, the CLI uploads it: `.vercelignore` doesn't exclude it, while `.gitignore` does. The deployment then defaults to it. Otherwise it uses the fictional sample. Edit `SETS` in `api/_shared.py` to point at your own private CSV and Cognee dataset.

API: `POST /api/speakers {"theme": "...", "k": 5, "dataset": "luma"|"sample", "csv": "<optional csv text>"}`, `POST /api/intros {"k": 3}`, `POST /api/members {}`.

## More
- `DEMO.md`: the 3-minute demo script. `docs/cognee-mcp-demo.md`: Cognee MCP remember/recall walkthrough.
- Screenshots: `docs/ui-intros.png`, `docs/ui-speakers.png`, `docs/ui-members.png` (fictional data).

## Licence
MIT. See `LICENSE`.
