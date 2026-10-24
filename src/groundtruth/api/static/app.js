"use strict";

/*
 * GroundTruth one-page UI.
 *
 * Security rule for this file: document-derived and API-derived strings
 * are rendered ONLY through textContent / createTextNode. Uploaded
 * documents are untrusted input; nothing from them (or from an answer
 * generated over them) may ever reach the DOM as markup. This file
 * never assigns an HTML string to the DOM — a test asserts exactly that.
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
      text.textContent = "ready";
    } else {
      dot.className = "status-dot status-down";
      text.textContent = "not configured";
    }
  } catch (err) {
    dot.className = "status-dot status-down";
    text.textContent = "unreachable";
  }
}

/* ---------------- documents ---------------- */

function renderDocuments(documents) {
  const list = $("documents-list");
  const empty = $("documents-empty");
  clearChildren(list);
  empty.hidden = documents.length > 0;
  for (const doc of documents) {
    const item = document.createElement("li");
    const name = makeEl("span", null, doc.filename || doc.title || doc.document_id);
    const bits = [];
    if (doc.pages != null) bits.push(doc.pages + (doc.pages === 1 ? " page" : " pages"));
    bits.push(doc.chunk_count + (doc.chunk_count === 1 ? " chunk" : " chunks"));
    if (doc.created_at) bits.push(new Date(doc.created_at).toLocaleString());
    item.append(name, makeEl("span", "doc-meta", bits.join(" · ")));
    list.appendChild(item);
  }
}

async function refreshDocuments() {
  const errorLine = $("documents-error");
  errorLine.hidden = true;
  try {
    const response = await fetch("/api/v1/documents");
    if (!response.ok) throw new Error(await readErrorDetail(response));
    renderDocuments(await response.json());
  } catch (err) {
    errorLine.textContent = "Could not load the document list: " + err.message;
    errorLine.hidden = false;
  }
}

/* ---------------- upload ---------------- */

/* Poll interval for background ingestion jobs (GT-11). Polling also
 * keeps a free-tier instance awake while a long job runs. */
const INGESTION_POLL_MS = 3000;

async function pollIngestion(documentId, uploadBody) {
  const state = $("upload-state");
  const result = $("upload-result");
  let timer = null;
  let inFlight = false;
  let stopped = false;
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
      if (job.status === "succeeded") {
        stop();
        state.textContent = "";
        const lines = [
          "Stored " + (uploadBody.filename || "document") +
            ": " + uploadBody.pages + (uploadBody.pages === 1 ? " page" : " pages") +
            ", " + uploadBody.chunks + (uploadBody.chunks === 1 ? " chunk" : " chunks") + ".",
        ];
        for (const line of lines) result.appendChild(makeEl("div", null, line));
        result.hidden = false;
        await refreshDocuments();
      } else if (job.status === "failed") {
        stop();
        state.textContent = "Processing failed: " + (job.error || "unknown error");
      } else {
        state.textContent =
          "Processing " + (uploadBody.filename || "document") + "… " +
          job.chunks_done + " of " + job.chunks_total + " chunks.";
      }
    } catch (err) {
      stop();
      state.textContent = "Could not check processing status: " + err.message;
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
  const state = $("upload-state");
  const result = $("upload-result");
  result.hidden = true;
  clearChildren(result);
  if (!input.files || input.files.length === 0) {
    state.textContent = "Choose a PDF file first.";
    return;
  }
  const formData = new FormData();
  formData.append("file", input.files[0]);
  button.disabled = true;
  state.textContent = "Uploading and processing…";
  try {
    const response = await fetch("/api/v1/documents", { method: "POST", body: formData });
    if (!response.ok) throw new Error(await readErrorDetail(response));
    const body = await response.json();
    if (response.status === 202 || body.status === "processing") {
      // Large document (GT-11): ingestion continues in the background.
      // The button is re-enabled by the finally block; polling owns
      // the state line from here until the job succeeds or fails.
      state.textContent =
        "Processing " + (body.filename || "document") + "… " +
        "this can take a few minutes for large documents.";
      await pollIngestion(body.document_id, body);
      return;
    }
    state.textContent = "";
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
    await refreshDocuments();
  } catch (err) {
    state.textContent = "Upload failed: " + err.message;
  } finally {
    button.disabled = false;
  }
}

/* ---------------- ask ---------------- */

function evidenceCardId(chunkId) {
  return "evidence-card-" + chunkId;
}

function scrollToEvidence(chunkId) {
  const card = document.getElementById(evidenceCardId(chunkId));
  if (!card) return;
  card.scrollIntoView({ behavior: "smooth", block: "center" });
  card.classList.add("highlight");
  window.setTimeout(() => card.classList.remove("highlight"), 2000);
}

function makeChip(item, label) {
  const chip = makeEl("button", "chip", label);
  chip.type = "button";
  chip.addEventListener("click", () => scrollToEvidence(item.chunk_id));
  return chip;
}

function chipLabel(item, index) {
  const name = item.title || item.filename || "source";
  const pages = item.page_start != null
    ? "p. " + item.page_start + (item.page_end && item.page_end !== item.page_start ? "–" + item.page_end : "")
    : null;
  return "[" + (index + 1) + "] " + name + (pages ? ", " + pages : "");
}

function renderAnswerWithCitations(answerText, citationsByChunkId, evidenceIndexByChunkId) {
  const container = $("answer-text");
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
    container.appendChild(makeChip(item, chipLabel(item, index)));
    lastIndex = match.index + match[0].length;
  }
  if (lastIndex < answerText.length) {
    container.appendChild(document.createTextNode(answerText.slice(lastIndex)));
  }
}

function renderEvidence(evidence) {
  const panel = $("evidence-panel");
  const list = $("evidence-list");
  clearChildren(list);
  panel.hidden = evidence.length === 0;
  evidence.forEach((item, index) => {
    const card = makeEl("article", "evidence-card");
    card.id = evidenceCardId(item.chunk_id);
    const title = item.title || item.filename || item.document_id;
    card.appendChild(makeEl("h3", null, "[" + (index + 1) + "] " + title));
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
    list.appendChild(card);
  });
}

function showError(message) {
  const banner = $("error-banner");
  banner.textContent = message;
  banner.hidden = false;
}

async function handleAsk(event) {
  event.preventDefault();
  const input = $("question-input");
  const button = $("ask-button");
  const state = $("ask-state");
  $("error-banner").hidden = true;
  $("answer-area").hidden = true;
  $("abstain-area").hidden = true;
  $("evidence-panel").hidden = true;
  const question = input.value.trim();
  if (!question) {
    state.textContent = "Type a question first.";
    return;
  }
  button.disabled = true;
  state.textContent = "Searching the stored evidence…";
  try {
    const response = await fetch("/api/v1/query", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ question: question, top_k: 10 }),
    });
    if (!response.ok) throw new Error(await readErrorDetail(response));
    const body = await response.json();
    state.textContent = "";
    renderEvidence(body.evidence || []);
    if (body.decision === "ANSWERED" && body.answer) {
      const citations = body.citations || [];
      const evidence = body.evidence || [];
      const byChunkId = new Map(citations.map((item) => [item.chunk_id, item]));
      // Chip numbers match the evidence card numbers (ranking order),
      // not the order citations happen to appear in the answer.
      const evidenceIndex = new Map(evidence.map((item, i) => [item.chunk_id, i]));
      $("answer-heading").textContent = "Answer";
      renderAnswerWithCitations(body.answer, byChunkId, evidenceIndex);
      const chips = $("citation-chips");
      clearChildren(chips);
      citations.forEach((item) =>
        chips.appendChild(makeChip(item, chipLabel(item, evidenceIndex.get(item.chunk_id) || 0)))
      );
      $("answer-area").hidden = false;
    } else if (body.decision === "ABSTAIN") {
      $("abstain-message").textContent = body.message;
      $("abstain-area").hidden = false;
    } else {
      // e.g. EVIDENCE_FOUND without generation: show the message and the
      // evidence cards below; there is no answer text to present.
      $("answer-heading").textContent = "Result";
      $("answer-text").textContent = body.message;
      clearChildren($("citation-chips"));
      $("answer-area").hidden = false;
    }
  } catch (err) {
    state.textContent = "";
    showError("The question could not be answered: " + err.message);
  } finally {
    button.disabled = false;
  }
}

/* ---------------- wiring ---------------- */

document.addEventListener("DOMContentLoaded", () => {
  $("upload-form").addEventListener("submit", handleUpload);
  $("ask-form").addEventListener("submit", handleAsk);
  refreshStatus();
  refreshDocuments();
});
