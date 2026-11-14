import { infoButton, setupInfo } from "./info.js";
import { Recorder } from "./recorder.js";
import { setupSynthetic } from "./synthetic.js";
import { setupSettings } from "./settings.js";
import { setupEvaluations } from "./evaluations.js";
import { recordingMarkup, setupStudy } from "./study.js";

const $ = (id) => document.getElementById(id);
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const fmt = (n, digits = 0) =>
  n === null || n === undefined
    ? "–"
    : Number(n).toLocaleString("de-DE", { maximumFractionDigits: digits });
let overview,
  scenarios = [],
  attempts = [],
  activeCard,
  draft,
  recorder,
  wave,
  annotationGoldSample = null,
  annotationAttempt;
let localURL = null;

let noticeTimer;
function notice(text, error = false) {
  clearTimeout(noticeTimer);
  $("notice-message").textContent = text;
  $("notice").className = `notice notice-banner${error ? " error" : ""}`;
  $("notice").hidden = false;
  if (!error) noticeTimer = setTimeout(() => ($("notice").hidden = true), 5000);
}
async function api(path, options = {}) {
  if (options.body && !(options.body instanceof FormData)) {
    options.headers = {
      "Content-Type": "application/json",
      ...options.headers,
    };
    options.body = JSON.stringify(options.body);
  }
  let response;
  try {
    response = await fetch("/api" + path, options);
  } catch {
    throw new Error(
      "Der lokale Server ist nicht erreichbar. Bitte die Anwendung neu starten.",
    );
  }
  let data;
  try {
    data = await response.json();
  } catch {
    throw new Error("Der Server hat keine lesbare Antwort geliefert.");
  }
  if (!response.ok)
    throw new Error(
      typeof data.detail === "string"
        ? data.detail
        : JSON.stringify(data.detail),
    );
  return data;
}
function action(id, fn) {
  $(id).addEventListener("click", async () => {
    try {
      await fn();
    } catch (e) {
      notice(e.message, true);
    }
  });
}
function lockRecording(locked) {
  $("person").disabled = locked;
  $("scenario").disabled = locked;
  $("start-record").disabled = locked;
}
function setOptions(element, items, valueFn, labelFn) {
  const old = element.value;
  element.innerHTML = items
    .map(
      (item) =>
        `<option value="${esc(valueFn(item))}">${esc(labelFn(item))}</option>`,
    )
    .join("");
  if (items.some((item) => String(valueFn(item)) === old)) element.value = old;
}

async function refresh() {
  const person = "AUTHOR";
  [overview, scenarios, attempts] = await Promise.all([
    api("/overview"),
    api("/scenarios?participant_id=" + person),
    api("/attempts"),
  ]);
  await study.load();
  setOptions(
    $("person"),
    overview.participants.filter((p) => p.id === "AUTHOR"),
    (p) => p.id,
    (p) => `${p.id} · ${p.label}${p.split === "dev" ? " · Entwicklung" : ""}`,
  );
  $("person").value = person;
  $("overview").innerHTML =
    `<span class="header-summary">${study.state().counts.human} / 25 eigene · ${study.state().counts.synthetic} / 25 synthetische</span>${infoButton("project", "25 Szenarienpaare mit insgesamt 50 manuell zu bestätigenden Referenzenden.")}`;
  const p = overview.participants.find((p) => p.id === person);
  $("person-progress").textContent = `${p.accepted} / 25 Beiträge übernommen`;
  const old = $("scenario").value;
  setOptions(
    $("scenario"),
    scenarios,
    (c) => c.id,
    (c) =>
      `${c.selected_attempt ? "✓ " : ""}${c.pair_id} · ${c.content_label} · ${c.pattern_label}`,
  );
  if (
    !old ||
    !scenarios.some((c) => c.id === old) ||
    scenarios.find((c) => c.id === old)?.selected_attempt
  )
    $("scenario").value = (
      scenarios.find((c) => !c.selected_attempt) || scenarios[0]
    ).id;
  renderCard();
  renderAttempts();
  renderAnnotationSelect();
  renderModels();
}

function renderCard() {
  activeCard = scenarios.find((c) => c.id === $("scenario").value);
  if (!activeCard) return;
  $("card-id").textContent = activeCard.id;
  $("scenario-card").innerHTML =
    `<h3 class="recording-title">${esc(activeCard.goal)}</h3>${recordingMarkup(activeCard)}${infoButton("recording-task", activeCard.guidance)}`;
  resetPauseCoach();
  $("pause-coach").hidden = !activeCard.pauses_ms.length;
  $("pause-coach-start").textContent = activeCard.pauses_ms.length
    ? `Pausentimer · ${fmt(activeCard.pauses_ms[0] / 1000, 1)} s`
    : "Pausentimer";
}

let pauseTimer = null;
function resetPauseCoach() {
  clearInterval(pauseTimer);
  $("pause-coach-status").textContent = "";
  $("pause-coach-start").disabled = false;
}
action("pause-coach-start", () => {
  resetPauseCoach();
  const end = performance.now() + activeCard.pauses_ms[0];
  $("pause-coach-start").disabled = true;
  function tick() {
    const left = end - performance.now();
    $("pause-coach-status").textContent =
      left > 0
        ? `Still bleiben · ${(left / 1000).toFixed(1)} s`
        : "Weiter · jetzt den restlichen Text sprechen";
    if (left <= 0) {
      clearInterval(pauseTimer);
      $("pause-coach-start").disabled = false;
    }
  }
  tick();
  pauseTimer = setInterval(tick, 50);
});

async function openRecord(id) {
  if (draft)
    throw new Error(
      "Bitte den aktuellen Versuch zuerst übernehmen, wiederholen oder abbrechen.",
    );
  await showTab("record");
  $("scenario").value = id;
  renderCard();
}
async function openAnnotation(id) {
  await showTab("annotate");
  $("annotation-attempt").value = id;
  await loadAnnotation();
}
function renderAttempts() {
  const items = attempts.filter(
    (a) => a.card.participant_id === $("person").value,
  );
  $("attempt-list").innerHTML = items.length
    ? items
        .map(
          (a) =>
            `<div class="attempt-row"><div class="grow"><strong>${esc(a.card.content_label)} · ${esc(a.card.pattern_label)}</strong><small>${esc(a.scenario_id)} · ${fmt(a.duration_ms / 1000, 1)} s · ${a.selected ? "Übernommen" : a.rejected ? "Verworfen: " + esc(a.rejected) : "Noch nicht übernommen"}</small></div><a href="/api/attempts/${a.id}/audio" target="_blank">Anhören</a><button data-annotate="${a.id}">Annotieren</button>${!a.selected ? `<button data-select="${a.id}" class="quiet">Übernehmen</button>` : ""}</div>`,
        )
        .join("")
    : '<p class="muted">Die erste Aufnahme wartet auf dich.</p>';
  document.querySelectorAll("[data-select]").forEach(
    (b) =>
      (b.onclick = async () => {
        try {
          const reason = prompt(
            "Grund für die Auswahl / den Austausch (bei erster Übernahme optional):",
            "",
          );
          if (reason === null) return;
          await api(`/attempts/${b.dataset.select}/select`, {
            method: "POST",
            body: { reason },
          });
          await refresh();
        } catch (e) {
          notice(e.message, true);
        }
      }),
  );
  document.querySelectorAll("[data-annotate]").forEach(
    (b) =>
      (b.onclick = async () => {
        try {
          if (!attempts.find((a) => a.id === b.dataset.annotate).selected)
            throw new Error("Bitte die Aufnahme zuerst übernehmen.");
          await showTab("annotate");
          $("annotation-attempt").value = b.dataset.annotate;
          await loadAnnotation();
        } catch (e) {
          notice(e.message, true);
        }
      }),
  );
}

async function showTab(tab, id = null, writeHistory = true) {
  if (recorder?.active)
    throw new Error(
      "Bitte die laufende Aufnahme zuerst beenden oder abbrechen.",
    );
  const valid = [
    "study",
    "generate",
    "record",
    "annotate",
    "compare",
    "evaluations",
    "evaluation-detail",
    "comparison",
  ];
  if (!valid.includes(tab)) return;
  if (draft?.blob && tab !== "record")
    throw new Error(
      "Bitte die Aufnahme zuerst übernehmen oder begründet wiederholen.",
    );
  evaluations.stopAudio();
  $("annotation-audio").pause();
  $("record-audio").pause();
  resetPauseCoach();
  for (const id of ["figure-preview", "rename-evaluation", "info-dialog"])
    if ($(id).open) $(id).close();
  document.querySelectorAll(".tab").forEach((x) => (x.hidden = x.id !== tab));
  document
    .querySelectorAll("nav button")
    .forEach((x) =>
      x.classList.toggle(
        "active",
        x.dataset.tab === (["evaluation-detail", "comparison"].includes(tab) ? "evaluations" : tab),
      ),
    );
  $("page-title").textContent = {
    study: "Datensatz",
    generate: "ElevenLabs",
    record: "Aufnahmen",
    annotate: "Referenzenden",
    compare: "Evaluation starten",
    evaluations: "Evaluationen",
    "evaluation-detail": "Ergebnisse verstehen.",
    comparison: "Modellvergleich",
  }[tab];
  $("overview").hidden = ["study", "evaluations", "evaluation-detail", "comparison"].includes(
    tab,
  );
  $("page-title").closest("header").hidden = ["evaluation-detail", "comparison"].includes(tab);
  window.scrollTo(0, 0);
  const route =
    tab === "compare"
      ? "start"
      : tab === "comparison"
        ? `evaluations/compare${id ? "?" + id : ""}`
      : tab === "evaluation-detail"
        ? `evaluations/${id}`
        : tab;
  if (writeHistory && location.hash !== `#/${route}`)
    history.pushState(null, "", `#/${route}`);
  if (tab === "generate") await synthetic.load();
  if (["study", "record", "annotate"].includes(tab)) await refresh();
  if (tab === "annotate") await loadAnnotation();
  if (tab === "compare") {
    await refresh();
    await refreshComparisons();
  }
  if (tab === "evaluations") await evaluations.refresh();
  if (tab === "comparison") await evaluations.openComparison(id);
  if (tab === "evaluation-detail") {
    $("evaluation-detail-content").innerHTML =
      '<p class="panel muted">Ergebnisse werden geladen …</p>';
    await evaluations.open(id);
  }
}
function restoreRoute() {
  const [path, query = ""] = location.hash.replace(/^#\/?/, "").split("?");
  const [route, id] = path.split("/");
  if (route === "evaluations" && id === "compare")
    return showTab("comparison", query, false);
  if (route === "evaluations" && id && /^[A-Za-z0-9_-]+$/.test(id))
    return showTab("evaluation-detail", id, false);
  return showTab(route === "start" ? "compare" : route || "study", null, false);
}
window.addEventListener("hashchange", () =>
  restoreRoute().catch((e) => notice(e.message, true)),
);

document
  .querySelectorAll("nav button")
  .forEach(
    (b) =>
      (b.onclick = () =>
        showTab(b.dataset.tab).catch((e) => notice(e.message, true))),
  );
$("person").onchange = () => refresh().catch((e) => notice(e.message, true));
$("scenario").onchange = renderCard;
action("edit-person", async () => {
  const p = overview.participants.find((p) => p.id === $("person").value);
  const label = prompt("Anzeigename (keine echten Namen nötig):", p.label);
  if (label === null) return;
  const age = prompt("Altersgruppe (freiwillig):", p.age_group);
  if (age === null) return;
  await api("/participants/" + p.id, {
    method: "PUT",
    body: { label, age_group: age, notes: p.notes },
  });
  await refresh();
});

async function uploadDraft() {
  if (!draft) throw new Error("Keine Aufnahme vorhanden.");
  if (draft.uploaded) return draft.uploaded;
  const body = new FormData();
  body.set("attempt_id", draft.id);
  body.set("scenario_id", draft.scenarioId);
  body.set("metadata", JSON.stringify(draft.metadata));
  body.set("audio", draft.blob, "aufnahme.wav");
  const uploaded = await api("/attempts", { method: "POST", body });
  draft.uploaded = uploaded;
  $("upload-note").textContent =
    "Versuch gespeichert. " +
    (uploaded.warnings.join(" ") || "Bitte anhören und dann übernehmen.");
  await refresh();
  return uploaded;
}

recorder = new Recorder(
  (update) => {
    $("record-time").textContent =
      `${String(Math.floor(update.seconds / 60)).padStart(2, "0")}:${String(Math.floor(update.seconds % 60)).padStart(2, "0")}`;
    $("level").style.width = Math.min(100, update.level * 500) + "%";
    if (update.tail) {
      $("record-state").textContent = "Nachlauf";
      $("record-hint").textContent = "Bitte noch ruhig bleiben";
    }
  },
  async (blob, metadata) => {
    if (!draft) return;
    draft.blob = blob;
    draft.metadata = {
      ...metadata,
      study_id: draft.card.study_id,
      scenario_version: draft.card.version,
      planned_transcript: draft.card.transcript,
      planned_pauses_ms: draft.card.pauses_ms,
    };
    if (localURL) URL.revokeObjectURL(localURL);
    localURL = URL.createObjectURL(blob);
    $("record-audio").src = localURL;
    $("local-download").href = localURL;
    $("record-review").hidden = false;
    $("finish-record").hidden = true;
    $("abort-record").hidden = true;
    $("record-state").textContent = "Anhören";
    $("record-hint").textContent = "Aufnahme abgeschlossen";
    $("level").style.width = "0";
    try {
      await uploadDraft();
    } catch (e) {
      $("upload-note").textContent =
        "Upload fehlgeschlagen. Die lokale Sicherung bleibt verfügbar.";
      notice(e.message, true);
    }
  },
  (error) => {
    lockRecording(false);
    $("finish-record").hidden = true;
    $("abort-record").hidden = true;
    $("record-state").textContent = "Bereit";
    draft = null;
    notice(error.message, true);
  },
);

action("start-record", async () => {
  if (draft?.blob)
    throw new Error(
      "Bitte die vorhandene Aufnahme übernehmen oder begründet wiederholen.",
    );
  draft = {
    id: crypto.randomUUID(),
    scenarioId: activeCard.id,
    card: activeCard,
  };
  lockRecording(true);
  $("record-review").hidden = true;
  $("record-state").textContent = "Vorbereiten";
  $("record-time").textContent = "00:00";
  await recorder.start();
  if (recorder.active) {
    $("finish-record").hidden = false;
    $("abort-record").hidden = false;
    $("record-state").textContent = "Aufnahme läuft";
    $("record-hint").textContent = "Jetzt natürlich sprechen";
  }
});
action("finish-record", async () => {
  $("finish-record").disabled = true;
  recorder.finish();
});
action("abort-record", async () => {
  await recorder.abort();
  draft = null;
  lockRecording(false);
  $("finish-record").hidden = true;
  $("finish-record").disabled = false;
  $("abort-record").hidden = true;
  $("record-state").textContent = "Bereit";
});
action("save-record", async () => {
  $("record-audio").pause();
  const record = await uploadDraft();
  const prior = attempts.find(
    (a) =>
      a.scenario_id === record.scenario_id && a.selected && a.id !== record.id,
  );
  const reason = prior
    ? prompt("Warum ersetzt dieser Versuch die bisherige Aufnahme?", "")
    : "";
  if (reason === null) return;
  await api(`/attempts/${record.id}/select`, {
    method: "POST",
    body: { reason },
  });
  draft = null;
  lockRecording(false);
  $("record-review").hidden = true;
  $("finish-record").disabled = false;
  $("record-state").textContent = "Bereit";
  await refresh();
  notice(
    scenarios.every((c) => c.selected_attempt)
      ? "Alle 25 eigenen Aufnahmen sind übernommen. Bitte jetzt die Referenzenden prüfen."
      : "Aufnahme übernommen. Die nächste Karte ist bereit.",
  );
});
action("retry-record", async () => {
  $("record-audio").pause();
  const reason = prompt("Warum soll die Aufnahme wiederholt werden?", "");
  if (reason === null) return;
  if (!reason.trim())
    throw new Error("Bitte einen Wiederholungsgrund angeben.");
  const record = await uploadDraft();
  await api(`/attempts/${record.id}/reject`, {
    method: "POST",
    body: { reason },
  });
  draft = null;
  lockRecording(false);
  $("record-review").hidden = true;
  $("finish-record").disabled = false;
  $("record-state").textContent = "Bereit";
  await refresh();
});

function renderAnnotationSelect() {
  const selected = annotationClips();
  setOptions(
    $("annotation-attempt"),
    selected,
    (a) => a.id,
    (a) =>
      `${a.scenario_id} · ${a.source === "synthetic" ? "ElevenLabs" : "Deine Stimme"} · ${a.annotation?.reference_method === "human_waveform_annotation" ? "✓ Ende bestätigt" : a.annotation?.status === "generated" ? "Endvorschlag prüfen" : "Offen"}`,
  );
  $("annotation-empty").hidden = selected.length > 0;
}
function annotationClips() {
  return (study.state()?.pairs || [])
    .flatMap((p) => [p.human, p.synthetic])
    .filter(Boolean);
}
let annotationLoadVersion = 0;
async function loadAnnotation() {
  const version = ++annotationLoadVersion;
  wave = null;
  for (const id of ["save-annotation", "annotation-next"])
    $(id).disabled = true;
  annotationAttempt = annotationClips().find(
    (a) => a.id === $("annotation-attempt").value,
  );
  $("annotation-editor").hidden = !annotationAttempt;
  if (!annotationAttempt) return;
  const a = annotationAttempt.annotation;
  const card = annotationAttempt.card || annotationAttempt.scenario;
  $("annotation-info").textContent =
    `${annotationAttempt.source === "synthetic" ? "ElevenLabs" : "Deine Stimme"} · ${card.goal} · ${fmt(annotationAttempt.samples / 16000, 2)} Sekunden${a?.status === "generated" ? " · Endvorschlag" : ""}`;
  $("annotation-audio").src = `/api/clips/${annotationAttempt.id}/audio`;
  annotationGoldSample = a?.gold_eot_sample ?? null;
  renderGoldEnd();
  $("transcript").value = a?.transcript || card.transcript || "";
  $("annotation-status").textContent = a
    ? a.status === "generated"
      ? "Endvorschlag"
      : "Gespeichert"
    : "Noch nicht gespeichert";
  const loadedWave = await api(`/clips/${annotationAttempt.id}/waveform`);
  if (version !== annotationLoadVersion) return;
  wave = loadedWave;
  for (const id of ["save-annotation", "annotation-next"])
    $(id).disabled = false;
  $("wave-offset").value = 0;
  $("wave-zoom").value = "1";
  drawAnnotation();
}
function drawWave(
  canvas,
  data,
  markers = [],
  zoom = 1,
  offset = 0,
  playhead = null,
) {
  const dpr = window.devicePixelRatio || 1,
    width = canvas.clientWidth || 800,
    height = 160;
  canvas.width = width * dpr;
  canvas.height = height * dpr;
  const ctx = canvas.getContext("2d");
  ctx.scale(dpr, dpr);
  ctx.fillStyle = "#f2f5ed";
  ctx.fillRect(0, 0, width, height);
  const duration = data.samples / data.sample_rate,
    span = duration / zoom;
  ctx.strokeStyle = "#7e9e83";
  ctx.beginPath();
  for (let i = 0; i < data.peaks.length; i++) {
    const t = (i / data.peaks.length) * duration,
      x = ((t - offset) / span) * width;
    if (x < 0 || x > width) continue;
    ctx.moveTo(x, 80 + data.peaks[i][0] * 65);
    ctx.lineTo(x, 80 + data.peaks[i][1] * 65);
  }
  ctx.stroke();
  for (const marker of [
    ...markers,
    ...(playhead === null
      ? []
      : [{ time: playhead, color: "#7d8d84", text: "" }]),
  ]) {
    const x = ((marker.time - offset) / span) * width;
    if (x < 0 || x > width) continue;
    ctx.strokeStyle = marker.color;
    ctx.beginPath();
    ctx.moveTo(x, 12);
    ctx.lineTo(x, 148);
    ctx.stroke();
    ctx.fillStyle = marker.color;
    ctx.font = "11px system-ui";
    ctx.fillText(marker.text, Math.min(x + 5, width - 110), marker.y || 23);
  }
  ctx.fillStyle = "#6b7970";
  ctx.font = "10px system-ui";
  ctx.fillText(`${offset.toFixed(2)} s`, 8, 154);
  ctx.fillText(`${(offset + span).toFixed(2)} s`, width - 65, 154);
}
function drawAnnotation() {
  if (!wave) return;
  const zoom = Number($("wave-zoom").value),
    duration = wave.samples / 16000;
  $("wave-offset").max = Math.max(0, duration - duration / zoom);
  $("wave-navigation").hidden = zoom === 1;
  const maxOffset = Number($("wave-offset").max);
  $("wave-offset").style.setProperty(
    "--range-progress",
    `${maxOffset ? (Number($("wave-offset").value) / maxOffset) * 100 : 0}%`,
  );
  const markers = [];
  if (annotationGoldSample !== null)
    markers.push({
      time: annotationGoldSample / 16000,
      color: "#bd662e",
      text: "Gold-Ende",
    });
  drawWave(
    $("waveform"),
    wave,
    markers,
    zoom,
    Number($("wave-offset").value),
    $("annotation-audio").currentTime,
  );
}
$("annotation-attempt").onchange = () =>
  loadAnnotation().catch((e) => notice(e.message, true));
$("waveform").onclick = (e) => {
  if (!wave) return;
  const r = $("waveform").getBoundingClientRect();
  $("annotation-audio").currentTime =
    Number($("wave-offset").value) +
    (((e.clientX - r.left) / r.width) * wave.samples) /
      16000 /
      Number($("wave-zoom").value);
  drawAnnotation();
};
$("annotation-audio").ontimeupdate = drawAnnotation;
$("wave-zoom").onchange = drawAnnotation;
$("wave-offset").oninput = drawAnnotation;
$("playback-rate").onchange = () => {
  $("annotation-audio").playbackRate = Number($("playback-rate").value);
};
function renderGoldEnd() {
  $("gold-end").textContent =
    annotationGoldSample === null
      ? "Gold-Ende nicht gesetzt"
      : `Gold-Ende: ${fmt(annotationGoldSample / 16000, 3)} s`;
}
action("mark-gold", () => {
  if (!wave) return;
  annotationGoldSample = Math.round($("annotation-audio").currentTime * 16000);
  renderGoldEnd();
  drawAnnotation();
});
async function saveAnnotation(advance = false) {
  if (!annotationAttempt) throw new Error("Bitte eine Aufnahme auswählen.");
  if (annotationGoldSample === null || annotationGoldSample <= 0)
    throw new Error("Bitte eine Abspielposition als Gold-Ende setzen.");
  await api(`/clips/${annotationAttempt.id}/annotation`, {
    method: "POST",
    body: {
      gold_eot_sample: annotationGoldSample,
      transcript: $("transcript").value,
    },
  });
  await refresh();
  if (advance) {
    const next = annotationClips().find(
      (a) => a.annotation?.reference_method !== "human_waveform_annotation",
    );
    if (next) $("annotation-attempt").value = next.id;
    else notice("Alle vorhandenen Referenzenden sind bestätigt.");
  }
  await loadAnnotation();
  notice("Annotation als neue Revision gespeichert.");
}
action("save-annotation", () => saveAnnotation());
action("annotation-next", () => saveAnnotation(true));

function renderModels() {
  if (!overview) return;
  const variant = $("livekit-version").value;
  const models = overview.models
    .filter((m) => m.id !== "smart_turn")
    .map((m) => {
      if (m.id !== "livekit") return m;
      const cloud = variant === "v1";
      return {
        ...m,
        name: cloud ? "LiveKit v1 Cloud" : "LiveKit v1-mini lokal",
        ready: cloud
          ? Boolean(m.cloud_configured && m.local_ready)
          : Boolean(m.local_ready),
        detail: cloud
          ? m.cloud_configured
            ? "Cloud-Zugang konfiguriert. Laufzeit enthält Netzwerk und Dienstverarbeitung."
            : "LIVEKIT_API_KEY und LIVEKIT_API_SECRET fehlen in der lokalen .env-Datei."
          : "Lokale Agents-Inferenz mit 1,2 s Audiofenster. Kein Cloud-Zugang nötig.",
      };
    });
  if (!$("model-options").children.length) {
    $("model-options").innerHTML = models
      .map(
        (m) =>
          `<article class="model-card" data-model-card="${m.id}"><div class="model-card-heading"><label class="model-choice"><input type="checkbox" data-model="${m.id}" ${m.default_selected !== false && (m.ready || m.id === "livekit") ? "checked" : ""}><strong data-model-name="${m.id}"></strong></label>${infoButton("model-" + m.id, m.detail)}</div><span class="model-state" data-model-state="${m.id}"></span><span hidden data-model-detail="${m.id}"></span><p class="model-preset" data-model-summary="${m.id}"></p><button type="button" class="quiet" data-open-settings="${m.id}">Einstellungen</button></article>`,
      )
      .join("");
    $("model-options").addEventListener("change", renderModels);
  }
  const summaries = {
    baseline: `Stille-Timeouts: ${$("timeouts").value} ms`,
    livekit: $("livekit-auto").checked
      ? "Schwelle automatisch · Deutsch"
      : `Eigene EOT-Schwelle: ${$("livekit-threshold").value}`,
    scribe: `Turn-Schwelle: ${$("scribe-threshold").value} · Streaming-Dienst`,
  };
  for (const m of models) {
    document.querySelector(`[data-model-name="${m.id}"]`).textContent = m.name;
    const state = document.querySelector(`[data-model-state="${m.id}"]`);
    state.textContent = m.ready ? "Bereit" : "Vorbereitung nötig";
    state.className = `model-state ${m.ready ? "ready" : "not-ready"}`;
    document.querySelector(`[data-model-detail="${m.id}"]`).textContent =
      m.detail;
    document.querySelector(
      `[data-model-card="${m.id}"] [data-info-topic]`,
    ).dataset.infoExtra = m.detail;
    document.querySelector(`[data-model-summary="${m.id}"]`).textContent =
      summaries[m.id];
    document
      .querySelector(`[data-model-card="${m.id}"]`)
      .classList.toggle(
        "is-selected",
        document.querySelector(`[data-model="${m.id}"]`).checked,
      );
  }
}
action("model-refresh", async () => {
  await refresh();
  notice("Modellstatus aus der lokalen Konfiguration aktualisiert.");
});
function getConfig() {
  return {
    models: [...document.querySelectorAll("[data-model]:checked")].map(
      (x) => x.dataset.model,
    ),
    ...settings.read(),
    mode: "realtime",
  };
}
async function refreshComparisons() {
  const releases = await api("/releases");
  const availableReleases = releases.filter(
    (r) => r.kind !== "study_synthetic",
  );
  setOptions(
    $("run-release"),
    availableReleases,
    (r) => r.id,
    (r) =>
      `${r.kind === "study_paired" ? "Studie · eigene Stimme + ElevenLabs" : r.kind} · ${r.records.length} Beiträge · ${r.id.slice(0, 8)}`,
  );
  $("releases").innerHTML = releases
    .map(
      (r) =>
        `<div class="release-row"><span>${esc(r.kind)} · ${r.records.length} Beiträge</span><a href="/api/releases/${r.id}/download">ZIP exportieren</a></div>`,
    )
    .join("");
}
action("run-start", async () => {
  const release_id = $("run-release").value;
  if (!release_id)
    throw new Error("Bitte zuerst einen Datensatzstand erstellen.");
  const config = getConfig();
  if (!config.models.length)
    throw new Error("Bitte mindestens ein Modell auswählen.");
  const button = $("run-start");
  if (button.disabled) return;
  button.disabled = true;
  try {
    const job = await api("/runs", {
      method: "POST",
      body: { name: $("run-name").value.trim(), release_id, config },
    });
    await showTab("evaluation-detail", job.id);
    notice("Evaluation gestartet.");
  } finally {
    button.disabled = false;
  }
});

window.addEventListener("beforeunload", (e) => {
  if (recorder.active || (draft?.blob && !draft.uploaded)) {
    e.preventDefault();
    e.returnValue = "";
  }
});
window.addEventListener("resize", drawAnnotation);
setupInfo();
$("notice-dismiss").onclick = () => ($("notice").hidden = true);
const settings = setupSettings({ api, onChange: renderModels });
const study = setupStudy({
  api,
  notice,
  refresh,
  showTab,
  openRecord,
  openAnnotation,
});
const synthetic = setupSynthetic({
  api,
  notice,
  refresh,
  showTab,
  useRelease: study.useRelease,
});
const evaluations = setupEvaluations({ api, notice, showTab, drawWave });
$("back-evaluations").onclick = () =>
  showTab("evaluations").catch((e) => notice(e.message, true));
settings
  .init()
  .then(() => refresh())
  .then(() => restoreRoute())
  .catch((e) => notice(e.message, true));
