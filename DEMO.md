# 3-minute demo script

**0:00–0:30 Problem.** "I run the Generative AI in Economics Teaching CoP. With 100+ educators I can't remember who should meet whom, or who could give next month's seminar." Mention that the data is 20 fictional members.

**0:30–0:50 Ingest.** Run `streamlit run app.py`. The sidebar shows "20 members · embeddings: tfidf". Point out that it runs fully offline with no API key, and that you can upload any CSV or JSON.

**0:50–1:50 Intros.** On the Intros tab, show the top pair: a Head of Department who can talk about department AI policy, matched with a lecturer who *wants to learn* department AI strategy. Explain the score (similarity plus two-way "wants ↔ can offer"), the cross-institution rule, and the cap of 2 intros per member. Open the draft and stress that it is a draft to copy and send yourself, and that nothing is sent automatically.

**1:50–2:30 Speaker finder.** Type "AI and assessment integrity" to get Hale, Haddad and Bello with reasons. Change it to "classroom simulations" and the shortlist updates live.

**2:30–2:50 CLI.** Run `python -m kym.cli speakers "LLM coding for econometrics"` and `intros --json`, which you can pipe into a newsletter or a Slack workflow.

**2:50–3:00 Reuse.** It's MIT licensed. Another community exports its member form to CSV and runs it next week. Set `OPENAI_API_KEY` (or any compatible endpoint) to get LLM reasons and drafts, and Supabase for pgvector.
