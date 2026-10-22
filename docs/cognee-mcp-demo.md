# Cognee hosted connector: sample run (22 Oct 2026, London time, UTC+1)

The 20 **fictional** profiles were stored through the hosted Cognee MCP connector inside Grok Bot (`remember`, dataset `know-your-members-demo`, background mode). They are the same text that `kym/cognee_backend.py:profile_doc` produces.

| Step | Result | Time |
|---|---|---|
| remember (add + cognify + improve) | queued at 19:17:28; `DATASET_PROCESSING_STARTED` at about 19:19:30; `DATASET_PROCESSING_COMPLETED` by 19:21:03 | ~2–3.5 min |
| recall "Who could speak on AI and assessment integrity?" | `[graph] Dr Tomasz Wilk and Prof Edwin Hale.` | a few seconds |
| recall "Who could speak on classroom simulations?" | `[graph] Ms Priya Raman.` | a few seconds |
| recall "Why should Prof Edwin Hale and Dr Nadia Petrova meet…?" | see below | a few seconds |

> Prof Edwin Hale can share how to create and run a department‑wide AI policy that protects academic integrity, while Dr Nadia Petrova can explain how AI tutors affect student wellbeing.
> - **Why meet:** Hale needs insight on a department‑level AI strategy, and Petrova is looking to develop that same strategy.
> - **What each learns:** Hale gains practical knowledge about the wellbeing impacts of AI tutoring that will inform his plans for using AI tutors in large courses; Petrova learns how to design and implement a coherent AI policy and integrity framework across a department.

(Note that the "Why meet" line has the direction backwards. In the data, Petrova wants to learn department AI strategy and Hale can offer it. The "What each learns" line has it right.)

**Comparison with TF-IDF (offline default)**
- *Assessment integrity:* TF-IDF ranks Hale, Haddad, Bello. Cognee picks Hale (agrees) and Wilk (not in the TF-IDF top 3). It misses Haddad ("authentic assessment that resists AI shortcuts") and Bello ("oral exams… as AI-proof assessment").
- *Classroom simulations:* both pick Priya Raman as #1 (exact match).
- *Top intro pair:* TF-IDF's #1 pair (Hale and Petrova) is explained richly by the graph. It also adds the reverse direction, wellbeing → Hale's "AI tutors in large courses", which the template reason didn't capture.
