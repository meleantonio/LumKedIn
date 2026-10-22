# LumKedIn: 3-minute demo script

*LumKedIn (Luma meets LinkedIn), formerly "Know Your Members". Run locally with Streamlit; live web version on Vercel (see README).*

**0:00–0:30 Problem.** "I run the Generative AI in Economics Teaching CoP. With 100+ educators I can't remember who should meet whom, or who could give next month's seminar." Mention that the data is 20 fictional members.

**0:30–0:50 Ingest.** Run `streamlit run app.py`. The sidebar shows "20 members · embeddings: tfidf". Point out that it runs fully offline with no API key, and that you can upload any CSV or JSON.

**0:50–1:50 Intros.** On the Intros tab, show the top pair: a Head of Department who can talk about department AI policy, matched with a lecturer who *wants to learn* department AI strategy. Explain the score (similarity plus two-way "wants ↔ can offer"), the cross-institution rule, and the cap of 2 intros per member. Open the draft and stress that it is a draft to copy and send yourself, and that nothing is sent automatically.

**1:50–2:30 Speaker finder.** Type "AI and assessment integrity" to get Hale, Haddad and Bello with reasons. Change it to "classroom simulations" and the shortlist updates live.

**2:30–2:50 CLI.** Run `python -m kym.cli speakers "LLM coding for econometrics"` and `intros --json`, which you can pipe into a newsletter or a Slack workflow.

**2:50–3:00 Reuse.** It's MIT licensed. Another community exports its member form to CSV and runs it next week. Set `OPENAI_API_KEY` (or any compatible endpoint) to get LLM reasons and drafts, and Supabase for pgvector.

## Optional Cognee segment (swap into 1:50–2:30 if `LLM_API_KEY` is set)
Before the demo, run `pip install -r requirements-cognee.txt` and `export LLM_API_KEY=...`, then start the app once so `cognify` builds the graph. It takes a while, so warm it up in advance. In the sidebar, switch **Memory backend → cognee** and run "AI and assessment integrity" again. The reasons now say "Cognee graph pick #n", and the intro reasons include a "Memory graph:" sentence. If anything fails, a yellow notice appears and the demo carries on with TF-IDF.

## Hosted Cognee via the Grok Bot connector (live, about 40 s)
The dataset `know-your-members-demo` is already ingested. Ask Grok Bot to run `recall` on "Who could speak on classroom simulations?" and it answers **Ms Priya Raman**, which matches TF-IDF's #1 on screen. Then ask "Why should Prof Edwin Hale and Dr Nadia Petrova meet?" for a two-way rationale (AI policy ↔ AI tutors and wellbeing) that is richer than the template. Each recall takes a few seconds. The backup is to read the outputs from `docs/cognee-mcp-demo.md`.

## Cognee Cloud as the default (if COGNEE_API_URL + COGNEE_API_KEY are set)
Start with `streamlit run app.py`. The banner reads **Active backend: cognee-cloud**, and the speaker reasons say "cognee-cloud graph pick #n". If the cloud is unreachable, a yellow notice appears and the demo continues on TF-IDF.
