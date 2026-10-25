"use strict";

/*
 * GroundTruth production UI (issue #57).
 *
 * Security rule for this file: document-derived and API-derived strings
 * are rendered ONLY through textContent / createTextNode. Uploaded
 * documents are untrusted input; nothing from them (or from an answer
 * generated over them) may ever reach the DOM as markup.
 *
 * The API is unchanged: documents list, upload (200 stored / 202
 * processing), ingestion status polling, and query all behave exactly
 * as before. This file only presents them better: a document library,
 * a conversation thread, and upload states that never go silent.
 */

const $ = (id) => document.getElementById(id);

function clearChildren(el) {
  el.replaceChildren();
}

function makeEl(tag, className, text) {
  const el = document.createElement(tag);
  if (className) el.className = className;
  if (text !== undefined) el.textContent = text;
  return el;
}

async function readErrorDetail(response) {
  try {
    const body = await response.json();
    if (body && typeof body.detail === "string") return body.detail;
  } catch (err) {
    /* fall through to the generic message */
  }
  return "Request failed with status " + response.status + ".";
}

/* ---------------- status ---------------- */

async function refreshStatus() {
  const dot = $("status-dot");
  const text = $("status-text");
  try {
    const response = await fetch("/ready");
    if (response.ok) {
      dot.className = "status-dot status-ready";
      text.textContent = "Ready — evidence library available";
    } else {
      dot.className = "status-dot status-down";
      text.textContent = "Not configured — the document store is not set up yet";
    }
  } catch (err) {
    dot.className = "status-dot status-down";
    text.textContent = "Cannot reach the service — check your connection and try again";
  }
}

/* ---------------- documents ---------------- */

function renderDocuments(documents) {
  const list = $("documents-list");
  const empty = $("documents-empty");
  const count = $("library-count");
  clearChildren(list);
  empty.hidden = documents.length > 0;
  count.textContent = String(documents.length);
  for (const doc of documents) {
    const item = makeEl("li", "doc-card");
    item.appendChild(makeEl("span", "doc-badge", "PDF"));
    const body = makeEl("div");
    body.appendChild(makeEl("div", "doc-name", doc.filename || doc.title || doc.document_id));
    const bits = [];
    if (doc.pages != null) bits.push(doc.pages + (doc.pages === 1 ? " page" : " pages"));
    bits.push(doc.chunk_count + (doc.chunk_count === 1 ? " chunk" : " chunks"));
    if (doc.created_at) bits.push("stored " + new Date(doc.created_at).toLocaleString());
    body.appendChild(makeEl("div", "doc-meta", bits.join(" · ")));
    item.appendChild(body);
    /* Listed documents are stored by definition: the list endpoint
     * excludes documents still processing or failed, so a row here is
     * a stored document. Live job state shows in the upload activity
     * card, never as a guessed badge on a library row. */
    item.appendChild(makeEl("span", "doc-status", "Stored"));
    list.appendChild(item);
  }
}

const sleep = (ms) => new Promise((resolve) => window.setTimeout(resolve, ms));

/* Bounded retries for the documents-list fetch (GT-44): a free-tier
 * instance can drop a single request while waking, and a one-shot
 * failure used to leave the panel showing "No documents stored yet"
 * when the list had simply never loaded. */
const DOCUMENTS_FETCH_ATTEMPTS = 3;
const DOCUMENTS_FETCH_RETRY_MS = 1000;

async function refreshDocuments() {
  const errorLine = $("documents-error");
  const empty = $("documents-empty");
  errorLine.hidden = true;
  let lastError = null;
  for (let attempt = 1; attempt <= DOCUMENTS_FETCH_ATTEMPTS; attempt++) {
    try {
      const response = await fetch("/api/v1/documents");
      if (!response.ok) throw new Error(await readErrorDetail(response));
      renderDocuments(await response.json());
      return;
    } catch (err) {
      lastError = err;
      if (attempt < DOCUMENTS_FETCH_ATTEMPTS) await sleep(DOCUMENTS_FETCH_RETRY_MS);
    }
  }
  /* A failed load is not an empty store: hide the empty-state claim so
   * the panel never reports "no documents" when it simply could not
   * load. A later successful refresh restores the correct state. */
  empty.hidden = true;
  errorLine.textContent = "Could not load the document list: " + lastError.message;
  errorLine.hidden = false;
}

/* ---------------- upload ---------------- */

/* Poll interval for background ingestion jobs (GT-11). Polling also
 * keeps a free-tier instance awake while a long job runs. */
const INGESTION_POLL_MS = 3000;

/* A single failed status check (e.g. the free-tier instance hiccuping
 * mid-job) used to stop polling forever (GT-44), orphaning the job
 * indicator and the list refresh that only runs on success. Tolerate
 * a few consecutive failures instead; only a sustained outage stops
 * the poll. */
const INGESTION_STATUS_MAX_FAILURES = 5;

/* The upload activity card is the one place that always says what an
 * upload is doing: uploading, processing with chunk progress, stored,
 * or interrupted with a retry prompt. It is never left blank mid-job. */
function setUploadActivity(kind, label, detail, progress) {
  const card = $("upload-activity");
  const labelEl = $("activity-label");
  const detailEl = $("activity-detail");
  const bar = $("upload-progress");
  const state = $("upload-state");
  card.hidden = false;
  card.className = "activity" + (kind ? " activity-" + kind : "");
  labelEl.textContent = label;
  detailEl.textContent = detail || "";
  if (progress == null) {
    bar.hidden = true;
  } else {
    bar.hidden = false;
    bar.value = progress;
  }
  state.textContent = detail || "";
}

function formatFileSize(bytes) {
  if (bytes >= 1024 * 1024) return (bytes / (1024 * 1024)).toFixed(1) + " MB";
  if (bytes >= 1024) return Math.round(bytes / 1024) + " KB";
  return bytes + " bytes";
}

function showChosenFile() {
  const input = $("file-input");
  const text = $("dropzone-text");
  if (input.files && input.files.length > 0) {
    const file = input.files[0];
    text.textContent = file.name + " (" + formatFileSize(file.size) + ")";
  } else {
    text.textContent = "Drop a PDF here, or choose a file";
  }
}

async function pollIngestion(documentId, uploadBody) {
  let timer = null;
  let inFlight = false;
  let stopped = false;
  let consecutiveFailures = 0;
  const stop = () => {
    if (timer) window.clearInterval(timer);
    timer = null;
    stopped = true;
  };
  const tick = async () => {
    if (inFlight) return;
    inFlight = true;
    try {
      const response = await fetch(
        "/api/v1/documents/" + encodeURIComponent(documentId) + "/ingestion"
      );
      if (!response.ok) throw new Error(await readErrorDetail(response));
      const job = await response.json();
      consecutiveFailures = 0;
      if (job.status === "succeeded") {
        stop();
        const result = $("upload-result");
        clearChildren(result);
        const lines = [
          "Stored " + (uploadBody.filename || "document") +
            ": " + uploadBody.pages + (uploadBody.pages === 1 ? " page" : " pages") +
            ", " + uploadBody.chunks + (uploadBody.chunks === 1 ? " chunk" : " chunks") + ".",
        ];
        for (const line of lines) result.appendChild(makeEl("div", null, line));
        result.hidden = false;
        setUploadActivity(
          "done",
          "Stored: " + (uploadBody.filename || "document"),
          lines[0],
          100
        );
        await refreshDocuments();
      } else if (job.status === "failed") {
        stop();
        /* GT-53: a job recovered after an interrupted run must not look
         * like an endless processing indicator or a generic failure —
         * the only remedy is a fresh upload, so say exactly that. The
         * backend marks such jobs with the "Ingestion was interrupted"
         * error prefix (see jobs.INTERRUPTED_ERROR_PREFIX). */
        if ((job.error || "").includes("Ingestion was interrupted")) {
          setUploadActivity(
            "alert",
            "Upload interrupted",
            "Ingestion was interrupted — please upload the document again to retry.",
            null
          );
        } else {
          setUploadActivity(
            "alert",
            "Processing failed",
            "Processing failed: " + (job.error || "unknown error") +
              " — please upload the document again to retry.",
            null
          );
        }
      } else {
        const done = job.chunks_done || 0;
        const total = job.chunks_total || uploadBody.chunks || 0;
        const pct = total > 0 ? Math.round((100 * done) / total) : 0;
        setUploadActivity(
          "",
          "Processing: " + (uploadBody.filename || "document"),
          "Processing " + (uploadBody.filename || "document") + "… " +
            done + " of " + total + " chunks. Large documents take a few minutes.",
          pct
        );
      }
    } catch (err) {
      consecutiveFailures += 1;
      if (consecutiveFailures >= INGESTION_STATUS_MAX_FAILURES) {
        stop();
        setUploadActivity(
          "alert",
          "Status check failed",
          "Could not check processing status: " + err.message,
          null
        );
      }
      /* Otherwise keep polling: the next tick retries the status
       * check, so a transient failure cannot orphan the job. */
    } finally {
      inFlight = false;
    }
  };
  await tick();
  if (!stopped) timer = window.setInterval(tick, INGESTION_POLL_MS);
}

async function handleUpload(event) {
  event.preventDefault();
  const input = $("file-input");
  const button = $("upload-button");
  const result = $("upload-result");
  result.hidden = true;
  clearChildren(result);
  if (!input.files || input.files.length === 0) {
    setUploadActivity("alert", "No file chosen", "Choose a PDF file first.", null);
    return;
  }
  const formData = new FormData();
  formData.append("file", input.files[0]);
  button.disabled = true;
  setUploadActivity("", "Uploading…", "Uploading and processing…", 0);
  try {
    const response = await fetch("/api/v1/documents", { method: "POST", body: formData });
    if (!response.ok) throw new Error(await readErrorDetail(response));
    const body = await response.json();
    if (response.status === 202 || body.status === "processing") {
      // Large document (GT-11): ingestion continues in the background.
      // The button is re-enabled by the finally block; polling owns
      // the activity card from here until the job succeeds or fails.
      setUploadActivity(
        "",
        "Processing: " + (body.filename || "document"),
        "Processing " + (body.filename || "document") + "… " +
          "this can take a few minutes for large documents.",
        0
      );
      await pollIngestion(body.document_id, body);
      return;
    }
    const lines = [
      "Stored " + (body.filename || "document") +
        ": " + body.pages + (body.pages === 1 ? " page" : " pages") +
        ", " + body.chunks + (body.chunks === 1 ? " chunk" : " chunks") + ".",
    ];
    if (body.duplicate) {
      lines.push("This exact document was already stored; nothing was duplicated.");
    }
    for (const line of lines) result.appendChild(makeEl("div", null, line));
    result.hidden = false;
    setUploadActivity(
      "done",
      "Stored: " + (body.filename || "document"),
      lines.join(" "),
      100
    );
    await refreshDocuments();
  } catch (err) {
    setUploadActivity("alert", "Upload failed", "Upload failed: " + err.message, null);
  } finally {
    button.disabled = false;
  }
}

/* ---------------- conversation ---------------- */

let turnCounter = 0;

function evidenceCardId(turnId, chunkId) {
  return "evidence-card-" + turnId + "-" + chunkId;
}

function scrollToEvidence(turnId, chunkId) {
  const card = document.getElementById(evidenceCardId(turnId, chunkId));
  if (!card) return;
  card.scrollIntoView({ behavior: "smooth", block: "center" });
  card.classList.add("highlight");
  window.setTimeout(() => card.classList.remove("highlight"), 2000);
}

function makeChip(turnId, item, label) {
  const chip = makeEl("button", "chip", label);
  chip.type = "button";
  chip.addEventListener("click", () => scrollToEvidence(turnId, item.chunk_id));
  return chip;
}

function chipLabel(item, index) {
  const name = item.title || item.filename || "source";
  const pages = item.page_start != null
    ? "p. " + item.page_start + (item.page_end && item.page_end !== item.page_start ? "–" + item.page_end : "")
    : null;
  return "[" + (index + 1) + "] " + name + (pages ? ", " + pages : "");
}

function renderAnswerWithCitations(container, turnId, answerText, citationsByChunkId, evidenceIndexByChunkId) {
  clearChildren(container);
  const pattern = /\[([^\[\]]+)\]/g;
  let lastIndex = 0;
  let match;
  while ((match = pattern.exec(answerText)) !== null) {
    const chunkId = match[1];
    if (!citationsByChunkId.has(chunkId)) continue;
    if (match.index > lastIndex) {
      container.appendChild(document.createTextNode(answerText.slice(lastIndex, match.index)));
    }
    const item = citationsByChunkId.get(chunkId);
    const index = evidenceIndexByChunkId.get(chunkId) || 0;
    container.appendChild(makeChip(turnId, item, chipLabel(item, index)));
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < answerText.length) {
    container.appendChild(document.createTextNode(answerText.slice(lastIndex)));
  }
}

function renderEvidenceInto(section, turnId, evidence) {
  clearChildren(section);
  if (evidence.length === 0) return;
  section.appendChild(makeEl("h3", null, "Evidence"));
  evidence.forEach((item, index) => {
    const card = makeEl("article", "evidence-card");
    card.id = evidenceCardId(turnId, item.chunk_id);
    const title = item.title || item.filename || item.document_id;
    card.appendChild(makeEl("h4", null, "[" + (index + 1) + "] " + title));
    const metaBits = [];
    if (item.filename && item.filename !== title) metaBits.push(item.filename);
    if (item.page_start != null) {
      metaBits.push(
        "pages " + item.page_start +
        (item.page_end && item.page_end !== item.page_start ? "–" + item.page_end : "")
      );
    }
    metaBits.push("score " + item.score.toFixed(3));
    if (item.dense_score != null) metaBits.push("dense " + item.dense_score.toFixed(3));
    metaBits.push(item.method);
    card.appendChild(makeEl("p", "card-meta", metaBits.join(" · ")));
    card.appendChild(makeEl("p", "snippet", item.snippet));
    section.appendChild(card);
  });
}

function appendTurn(question) {
  turnCounter += 1;
  const turnId = turnCounter;
  $("conversation-empty").hidden = true;
  const thread = $("conversation-thread");
  const turn = makeEl("article", "turn");
  turn.appendChild(makeEl("div", "turn-question", question));
  const body = makeEl("div", "turn-body");
  body.appendChild(makeEl("p", "state-line", "Searching the stored evidence…"));
  turn.appendChild(body);
  thread.appendChild(turn);
  turn.scrollIntoView({ behavior: "smooth", block: "end" });
  return { turnId, body };
}

async function handleAsk(event) {
  event.preventDefault();
  const input = $("question-input");
  const button = $("ask-button");
  const state = $("ask-state");
  state.textContent = "";
  const question = input.value.trim();
  if (!question) {
    state.textContent = "Type a question first.";
    return;
  }
  const { turnId, body } = appendTurn(question);
  input.value = "";
  button.disabled = true;
  try {
    const response = await fetch("/api/v1/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question, top_k: 10 }),
    });
    if (!response.ok) throw new Error(await readErrorDetail(response));
    const payload = await response.json();
    clearChildren(body);
    const evidence = payload.evidence || [];
    if (payload.decision === "ANSWERED" && payload.answer) {
      const citations = payload.citations || [];
      const byChunkId = new Map(citations.map((item) => [item.chunk_id, item]));
      // Chip numbers match the evidence card numbers (ranking order),
      // not the order citations happen to appear in the answer.
      const evidenceIndex = new Map(evidence.map((item, i) => [item.chunk_id, i]));
      const answerBox = makeEl("div", "turn-answer");
      const answerText = makeEl("p");
      renderAnswerWithCitations(answerText, turnId, payload.answer, byChunkId, evidenceIndex);
      answerBox.appendChild(answerText);
      const chips = makeEl("div", "citation-chips");
      citations.forEach((item) =>
        chips.appendChild(makeChip(turnId, item, chipLabel(item, evidenceIndex.get(item.chunk_id) || 0)))
      );
      answerBox.appendChild(chips);
      body.appendChild(answerBox);
    } else if (payload.decision === "ABSTAIN") {
      const decline = makeEl("div", "turn-decline");
      decline.appendChild(makeEl("h3", null, "GroundTruth declined to answer"));
      // The server message is already plain language (see #51): no
      // internal ids reach the user. The hint below explains, in
      // plain terms, what usually fixes a decline.
      decline.appendChild(makeEl("p", null, payload.message));
      decline.appendChild(makeEl(
        "p",
        "decline-hint",
        "Why this happens: the answer could only come from stored evidence, and " +
          "what was retrieved was not enough to support one. A more specific " +
          "question, or uploading the document that covers it, usually helps."
      ));
      body.appendChild(decline);
    } else {
      // e.g. EVIDENCE_FOUND without generation: show the message and the
      // evidence below; there is no answer text to present.
      const answerBox = makeEl("div", "turn-answer");
      answerBox.appendChild(makeEl("p", null, payload.message));
      body.appendChild(answerBox);
    }
    const evidenceSection = makeEl("div", "turn-evidence");
    renderEvidenceInto(evidenceSection, turnId, evidence);
    body.appendChild(evidenceSection);
  } catch (err) {
    clearChildren(body);
    body.appendChild(makeEl("div", "turn-error", "The question could not be answered: " + err.message));
  } finally {
    button.disabled = false;
  }
}

/* ---------------- wiring ---------------- */

document.addEventListener("DOMContentLoaded", () => {
  $("upload-form").addEventListener("submit", handleUpload);
  $("ask-form").addEventListener("submit", handleAsk);
  $("file-input").addEventListener("change", showChosenFile);
  $("clear-conversation").addEventListener("click", () => {
    clearChildren($("conversation-thread"));
    $("conversation-empty").hidden = false;
  });
  const dropzone = $("dropzone");
  dropzone.addEventListener("dragover", (event) => {
    event.preventDefault();
    dropzone.classList.add("drag-over");
  });
  dropzone.addEventListener("dragleave", () => dropzone.classList.remove("drag-over"));
  dropzone.addEventListener("drop", (event) => {
    event.preventDefault();
    dropzone.classList.remove("drag-over");
    if (event.dataTransfer && event.dataTransfer.files.length > 0) {
      $("file-input").files = event.dataTransfer.files;
      showChosenFile();
    }
  });
  // Enter asks; Shift+Enter keeps a newline in the composer.
  $("question-input").addEventListener("keydown", (event) => {
    if (event.key === "Enter" && !event.shiftKey) {
      event.preventDefault();
      $("ask-form").requestSubmit();
    }
  });
  refreshStatus();
  refreshDocuments();
});
