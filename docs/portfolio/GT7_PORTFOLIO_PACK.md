# GT-7 Portfolio & Interview Pack

Issue: ORAM15/GroundTruth#35. This pack exists so a reviewer, interviewer, or
future maintainer can run the demo, ask hard questions, and get answers that
are grounded in what was actually built and measured — including the parts
that are weak or unfinished. Nothing in this document is a marketing claim:
every number cites its source, and every limitation is stated in the open.

**Live demo:** https://groundtruth-nf8i.onrender.com

Free-tier honesty, up front: the Render free instance sleeps after ~15 idle
minutes, so the first request after a pause can take ~50 seconds to wake.
That is expected, not an outage. The demo has **no login by design for v1**,
so anyone with the link can see the documents list — do not upload personal
files to it.

---

## 1. Demo script (about 10 minutes)

### Step 1 — Upload a small document (synchronous path)

Upload any small PDF (a few pages). Expected result: the UI reports it
stored, e.g. `Stored <name>: 2 pages, 6 chunks`, and the document appears in
the Documents list. Documents of 100 chunks or fewer stay on the synchronous
path and return `200` on completion.

### Step 2 — Ask an answerable question

Ask a question whose answer is stated in the document. Expected result: a
concise answer with a citation chip naming the document and page, e.g.
`[1] <document>, p. 1`, and an Evidence section showing the chunk the
answer came from. The point to make out loud: the citation is not decoration
— it is checked by code before the answer is shown (see §3).

### Step 3 — Ask an absent-fact question, and show the honest decline

Ask about something the document does **not** contain (for example, a budget
figure for a year the document never mentions). Expected result: GroundTruth
declines to answer instead of inventing a figure. Two distinct decline
mechanisms exist, and both were observed live:

- **Gate decline:** no chunk's dense cosine similarity clears the 0.35
  threshold, so no evidence is returned and generation is never called.
- **Verification decline:** generation produced a draft answer, but citation
  verification rejected it — for example, the draft answer had no citations
  at all, or cited chunk ids that were not in the retrieved evidence — so
  the draft was withheld and the UI showed the honest-decline notice.
  This exact case was observed live on 2026-10-25: a very broad question
  across three documents produced a draft citing chunk ids outside the
  retrieved evidence, and the system withheld it rather than showing a
  plausible summary with partly invented citations.

The honest sentence for the demo: *"It would rather say nothing than show
you an answer it cannot point at."*

### Step 4 — Upload a large document, and show async progress

Upload a document with more than 100 chunks (the live-verified example was a
synthetic 30-page, 360-chunk PDF). Expected result, in order:

1. The upload does **not** return an instant success. The UI shows a
   processing state with a live chunk counter, e.g.
   `Processing <name>… 100 of 360 chunks`, then `200 of 360`, `300 of 360`.
2. After roughly 5 minutes (the quota-paced rate — see §2, GT-11), the UI
   reports `Stored <name>: 30 pages, 360 chunks` and the document appears
   in the list.
3. A question about a specific section returns a cited answer — in the
   live verification, the section-17 question returned record code
   `REC-17-04` with citation `[3] groundtruth_large_test, p. 17`.

Do **not** run two large uploads at once during the demo (see §5, the
concurrent-upload follow-up).

---

## 2. The production-debugging story (verified live, 2026-10-23 → 2026-10-25)

This is the strongest interview material in the project: four production
failures found by live testing, each fixed with a regression test that fails
on the old code. The order matters — each fix exposed the next layer.

### GT-8 — Foreign-key violation on first live upload (issue #42, fixed PR #43)

**Symptom.** The first live upload returned HTTP 500. The Render log showed
`psycopg.errors.ForeignKeyViolation: insert or update on table
"chunk_embeddings" violates FK "chunk_embeddings_chunk_id_fkey"`.

**Root cause.** `persist_document` committed document, chunks, and embeddings
in a single transaction, and the `ChunkEmbeddingRow` model has an FK column
but no ORM relationship, so SQLAlchemy's unit of work did not order the
inserts — embedding rows were flushed before their chunk rows. SQLite tests
missed it because foreign keys are off by default without
`PRAGMA foreign_keys=ON`.

**Fix.** Deterministic flush order (document → version → flush → chunks →
flush → embeddings → commit), the FK pragma turned on for SQLite, and 4
regression tests proven to fail with the fix reverted. Post-fix live test
passed the same day: a 2-page test document stored, an answerable question
returned a cited answer, and an absent-fact question declined.

**Lesson worth saying out loud:** the test suite was green and the code was
still wrong, because the test database did not enforce the constraint the
production database did. The fix was to make the test environment enforce it.

### GT-9 — Gemini batch limit of 100 inputs per request (issue #45, fixed PR #46)

**Symptom.** A real 46-page document (measured locally at 966 chunks) failed
with a Gemini 400: the provider sent all chunks in one `batchEmbedContents`
call, and Google's limit is 100 inputs per request. Nothing was stored,
because the failure happened before any save.

**Fix.** Batching at `MAX_BATCH_INPUTS = 100`, and Google's `error.message`
surfaced in `EmbeddingError` (and symmetrically in `GenerationError`) so
future provider failures are diagnosable instead of opaque. 8 new tests, 5
of which fail behaviourally on the old code.

### GT-10 — Giant single transaction fails at the edge with a detail-less 502 (issue #47, fixed PR #48)

**Symptom.** The same document re-uploaded after GT-9 returned a bare 502
with no JSON detail. A detail-less 502 means Render's edge gave up, not the
app: one request was doing 10 Gemini calls plus one transaction holding 966
chunks and 966 embeddings (~37 MB of SQL parameters) against a Neon pooler
on a 512 MB free instance.

**Fix.** `persist_document_sliced`: embed, save, and commit in slices of
≤100 chunks, with the FK-safe order preserved inside every slice, and any
slice failure deleting the partial document completely — no half-ingested
files. A failure test proved slice 1 committing 100 chunks and cleanup then
emptying all four tables.

### GT-11 — Free-tier quota forces async ingestion (issue #49, fixed PR #50, verified live 2026-10-25)

**Symptom.** Even sliced, the upload failed with Gemini HTTP 429. The
free-tier quota for `embed_content_free_tier_requests` is **100 items per
minute, counted per item, not per batch call** — so a 360-chunk document
needs ~4 minutes of paced calls, longer than an edge request can wait. A
retry after 70 seconds failed identically (its own slices re-exhausted the
window). GT-10's atomicity held throughout: no partial document was stored.

**Fix.** Small documents (≤100 chunks) stay synchronous and unchanged.
Large documents return `202` plus an `ingestion_jobs` row; a FastAPI
background worker embeds slices under a `QuotaPacer` (≤100 items per 60s
window, env-overridable, monotonic clock, injectable for tests) and retries
only 429s (max 5, respecting `Retry-After`). Processing and failed
documents are excluded from the document list and from retrieval, and a new
endpoint (`GET /api/v1/documents/{document_id}/ingestion`) plus 3-second UI
polling exposes progress (which also keeps the free instance awake).

**Live verification (2026-10-25).** A synthetic 30-page, 360-chunk PDF
ingested in ~5 minutes with the progress counter advancing 100 → 200 →
300 of 360 chunks, then stored as `30 pages, 360 chunks`, and a question
about section 17, paragraph 4 returned the cited answer `REC-17-04`
(`groundtruth_large_test, p. 17`). Issue #49 was closed on that evidence.

**Lesson worth saying out loud:** the quota is the architecture. The async
design, the pacer, and the progress UI all exist because a free-tier number
— 100 items per minute — made the synchronous design physically impossible
for large documents. Constraints chosen the design; the code just followed.

---

## 3. How the trust mechanisms work (for the technical questions)

- **Retrieval.** Hybrid: dense cosine + term-count lexical, fused with reciprocal rank
  fusion (k=60). The dense-cosine abstention gate (default 0.35, env
  `GT_MIN_EVIDENCE_SCORE`) runs before any evidence is returned; lexical
  matches alone can never override a failing dense score.
- **Generation.** Evidence is passed as labelled DATA blocks with explicit
  instructions to ignore any instructions inside retrieved documents.
  Retrieved content is untrusted data, never authority.
- **Verification (the structural guarantee).** After generation, code checks
  that every citation resolves to a chunk in the returned evidence. This is
  *pure* verification: unverified answer text is never returned, and
  abstention paths never call generation. The guarantee does not depend on
  the model behaving well — it depends on the checker running.
- **Idempotency.** Uploads are keyed on content hash; a duplicate document
  short-circuits before any embedding call, so re-uploads cost nothing.
- **Failure honesty.** A failed ingestion deletes its partial document
  (GT-10); a failed job leaves no half-ingested file (GT-11); a provider
  failure surfaces the provider's own message instead of a generic error
  (GT-9).

---

## 4. Measured results — and what they do NOT prove

Source: `docs/evaluation/GT5_EVALUATION_REPORT.md`, generated by
`python -m groundtruth.evaluation.run_golden` from the committed raw output
`docs/evaluation/gt5_run_output.json` (a test fails if report and output
drift apart). 26 golden cases over 4 small documents, seeded and queried
through the real API paths, with **deterministic evaluation doubles**
(lexical bag-of-words embeddings, scripted compliant generation) — not
Gemini.

| Metric | Value | Basis |
|---|---|---|
| Answered-rate (answerable) | 100% | answerable cases decided ANSWERED |
| Retrieval hit@10 | 100% | answerable cases with a gold chunk in the returned evidence |
| Abstention accuracy (unanswerable) | 100% | unanswerable cases decided ABSTAIN |
| Adversarial safety | **66.7% (4/6)** | adversarial cases meeting their safety expectation |

**Adversarial safety at 66.7% is the known weak spot.** Two adversarial
cases (adv-04, adv-05) were answered where abstention was expected. These
numbers validate the pipeline mechanism — gating, ranking, citation
enforcement, scoring — and do **not** validate production behaviour with
Gemini embeddings or a real model. The threshold sweep supports 0.35 for the
local doubles (it is the lowest threshold at which abstention accuracy on
unanswerable cases reached 100% while answered-rate stayed at 100%), but
the production threshold **still needs live re-measurement** with the same
harness in `--live` mode before 0.35 is treated as production-calibrated.
Latency figures from the local run (mean 32.2 ms, p95 72.3 ms) are
in-process against SQLite and must not be quoted as production latency.

Do not round these into marketing claims. If an interviewer asks "how
accurate is it?", the honest answer is: *"100% on a 26-case local golden
set with deterministic doubles, 66.7% on the adversarial cases, and
production calibration is still outstanding."*

---

## 5. Known limitations and open follow-ups (say these before being asked)

- **Adversarial safety 66.7% (4/6)** — see §4. Prompt-injection defence is
  risk reduction, not a guarantee, and the golden set measures it honestly.
- **Production threshold uncalibrated** — 0.35 comes from local doubles;
  `--live` re-measurement is outstanding (GT-5 follow-up).
- **Async-job follow-ups from Codex review of PR #50** (accepted as known,
  not hidden): (1) a second simultaneous upload of the same document can
  schedule a second worker, and a first-slice conflict can mark a job
  succeeded with only slice 0 stored; (2) no startup recovery — a
  `processing` job does not survive an instance restart or spin-down, and
  re-uploading while a job is processing returns 202 without scheduling a
  worker, so the job can sit hidden until DB intervention (mitigation for
  the demo: 3-second UI polling keeps the instance awake); (3) each worker
  builds its own quota pacer, so concurrent jobs could exceed 100
  items/min in aggregate (softened, not prevented, by 429 backoff);
  (4) on a 429 retry, the worker waits out the window but does not
  re-acquire quota before retrying, so retried items are not booked
  against the next slice's budget. None of these blocks a single,
  sequential demo upload. The scoped fix: return created-vs-existing from
  job creation and schedule only when newly created; add startup recovery
  or a processing-job timeout; share one pacer via app state; acquire
  before each retry.
- **No login on the demo (v1 design choice).** Anyone with the link sees
  the documents list. Personal files do not belong on it.
- **UI polish, filed not fixed:** issue #44 (documents list does not
  refresh after upload) and issue #51 (a citation-verification abstention
  message dumps raw internal chunk ids into user-facing text; the reason
  belongs in logs/debug output only).
- **Chunking quality for line-broken PDFs is an open question.** The
  46-page real document that drove GT-9 chunked into 966 chunks with a
  longest chunk of 74 characters — the text layer was heavily line-broken.
  Chunk count is not chunk quality, and that has not been tuned.

---

## 6. Interview Q&A

**Q: Why not just use a chatbot with a vector store?**
A: Because the product requirement is verifiability, not fluency. A chatbot
answers from model memory and attaches citations afterwards; GroundTruth
retrieves first, gates on dense similarity, generates only from labelled
evidence, and then has code — not the model — verify every citation before
anything is shown. If verification fails, the user gets an abstention, not
a confident guess. The architecture's identity is that trust is structural.

**Q: Why hybrid retrieval instead of vector-only?**
A: Dense retrieval catches paraphrase; lexical catches exact terms, codes,
and names — the things users actually search for in documents. RRF fusion
combines the rankings without a hand-tuned weight. The GT-5 harness measures
retrieval independently of generation, so the choice is evidence-based
rather than fashionable. (Measured: retrieval hit@10 100% on the local
golden set — small and synthetic, stated as such.)

**Q: Why abstain instead of answering with a caveat?**
A: A caveated hallucination is still a hallucination, and in a document QA
product the failure mode that matters is a confident wrong answer with a
citation attached. Abstention is a first-class terminal outcome in the
architecture, not an error path, and it is measured: 100% abstention
accuracy on the unanswerable golden cases.

**Q: What broke in production, and what did you learn?**
A: Four things, in sequence — the FK ordering bug SQLite hid, Google's
100-input batch limit, a 37 MB single transaction dying at the edge with a
detail-less 502, and finally a 100-items-per-minute quota that made
synchronous ingestion physically impossible for large documents. The
pattern: every layer of the stack had a limit the previous layer's tests
could not see (SQLite vs Postgres, one batch vs many, app vs edge, request
time vs quota window). The fixes were, in order: deterministic ordering +
enforcing constraints in tests, batching + surfacing provider errors,
sliced commits + full cleanup, and async ingestion with a quota pacer.
Each fix shipped with regression tests that fail on the old code.

**Q: What is the weakest part of the system?**
A: Adversarial safety, measured at 66.7% (4/6) on the golden set — two
injection cases were answered where abstention was expected. And the
production abstention threshold is still uncalibrated: 0.35 was swept on
lexical doubles, not Gemini embeddings. I would say both before being
asked, because they are the two numbers that most affect whether the
system can be trusted, and both are outstanding work, not solved problems.

**Q: Why no queue service / worker process for async ingestion?**
A: Free-tier constraint: one Render service, no broker, no second process.
FastAPI background tasks plus a quota pacer get the job done inside that
budget. The honest cost is that a processing job does not survive a
restart — that is a documented follow-up, and the fix is scoped (startup
recovery or a job timeout), not a redesign.

**Q: How do you know the numbers are real?**
A: The GT-5 report is generated from a committed raw run output, and a test
fails if the two drift. The production story is backed by Render logs
(FK violation, 502), provider errors (Gemini 400/429), and a live
verification with a named expected value (REC-17-04) that came back cited.
Nothing in this pack is a number I wrote down from memory.

---

## Sources

- `docs/evaluation/GT5_EVALUATION_REPORT.md` + `docs/evaluation/gt5_run_output.json` — all GT-5 numbers.
- Issues #42 (GT-8), #45 (GT-9), #47 (GT-10), #49 (GT-11), #44, #51 — production history and open polish.
- PRs #43, #46, #48, #50 — the fixes, each with regression tests.
- Live observations 2026-10-23 → 2026-10-25 at https://groundtruth-nf8i.onrender.com — demo behaviour, including the 360-chunk async verification and the broad-question verification decline.
- `ARCHITECTURE.md` (foundation spec) — architectural invariants and decisions.
