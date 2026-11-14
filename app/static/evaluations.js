import { infoButton } from "./info.js";
import { transcriptMarkup, bindTranscript } from "./transcript.js";

const $ = (id) => document.getElementById(id);
const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const fmt = (value, digits = 0) =>
  value === null || value === undefined
    ? "–"
    : Number(value).toLocaleString("de-DE", { maximumFractionDigits: digits });
const date = (value) =>
  value
    ? new Date(value).toLocaleString("de-DE", {
        dateStyle: "medium",
        timeStyle: "short",
      })
    : "Datum unbekannt";
const statuses = {
  completed: "Abgeschlossen",
  running: "Läuft",
  queued: "Eingereiht",
  failed: "Fehlgeschlagen",
  interrupted: "Unterbrochen",
  cancelled: "Abgebrochen",
};
const outcomes = {
  early: "Zu früh",
  timely: "Im Zeitfenster",
  late: "Verzögert",
  failure: "Ausfall / kein Ende",
};
const modelNames = {
  baseline: "Silero VAD",
  livekit: "LiveKit",
  smart_turn: "Smart Turn",
  scribe: "Scribe v3 Live",
};
function modelTags(run) {
  return (run.config.models || [])
    .map(
      (model) =>
        `<span class="model-tag">${esc(model === "livekit" ? (run.config.livekit_version === "v1" ? "LiveKit v1 Cloud" : "LiveKit v1-mini") : modelNames[model] || model)}</span>`,
    )
    .join("");
}
function badge(run) {
  return `<span class="run-status status-${esc(run.status)}"><span aria-hidden="true">●</span> ${esc(statuses[run.status] || run.status)}</span>`;
}
function signed(value) {
  return value === null || value === undefined
    ? "–"
    : `${value >= 0 ? "+" : "−"}${fmt(Math.abs(value))} ms`;
}

export function setupEvaluations({ api, notice, showTab, drawWave }) {
  let runs = [],
    current = null,
    payload = null,
    timely = 1600,
    comparisonSelection = [],
    comparisonDraft = [],
    comparisonTicket = 0,
    activeTab = "overview",
    listSignature = "",
    renameId = null,
    caseTicket = 0,
    caseCleanup = () => {},
    loading = false,
    detailTicket = 0;
  const error = (e) => notice(e.message, true);
  function stopAudio() {
    caseTicket++;
    $("case-audio")?.pause();
    caseCleanup();
    caseCleanup = () => {};
  }
  function renderList() {
    const search = $("evaluation-search").value.toLocaleLowerCase("de-DE");
    const status = $("evaluation-status").value,
      model = $("evaluation-model").value;
    const selected = runs.filter(
      (run) =>
        (!status || run.status === status) &&
        (!model || run.config.models.includes(model)) &&
        `${run.name} ${run.id} ${run.config.models.map((m) => modelNames[m]).join(" ")}`
          .toLocaleLowerCase("de-DE")
          .includes(search),
    );
    $("evaluation-count").textContent =
      `${selected.length} von ${runs.length} Evaluationen`;
    $("evaluation-stats").innerHTML = [
      [runs.filter((r) => r.status === "completed").length, "Abgeschlossen"],
      [
        runs.filter((r) => ["running", "queued"].includes(r.status)).length,
        "Aktiv",
      ],
    ]
      .map(
        ([value, label]) =>
          `<div class="library-stat"><strong>${value}</strong><span>${label}</span></div>`,
      )
      .join("");
    const signature = JSON.stringify(selected);
    if (listSignature === signature) return;
    listSignature = signature;
    $("evaluation-list").innerHTML = selected.length
      ? selected
          .map(
            (run) => `<article class="evaluation-card">
      <div class="evaluation-card-main"><div class="evaluation-card-heading"><a class="evaluation-name" href="#/evaluations/${run.id}" data-open-evaluation="${run.id}">${esc(run.name)}</a>${badge(run)}</div>
      <p class="evaluation-meta">${esc(date(run.created_at))} <span>·</span> ${run.split ? (run.split === "test" ? "Test" : "Entwicklung") + " <span>·</span> " : ""}${run.config.mode === "offline" ? "Offline / simuliert" : "Echtzeit"}${run.record_count !== undefined ? ` <span>·</span> ${run.record_count} Beiträge · ${run.condition_count} Betriebspunkte` : ""}</p>
      <div class="model-tags">${modelTags(run)}${run.source ? `<span class="source-tag">${run.source === "mixed" ? "Eigene Stimme + ElevenLabs" : run.source === "synthetic" ? "Synthetisch" : "Menschliche Aufnahmen"}</span>` : ""}</div>
      ${["running", "queued"].includes(run.status) ? `<div class="run-progress"><progress value="${run.progress || 0}" max="${run.total || 1}"></progress><span>${run.progress || 0} / ${run.total || "…"} Vergleiche</span></div>` : ""}
      ${run.error ? `<p class="run-error">${esc(run.error)}</p>` : ""}</div>
      <div class="evaluation-card-actions"><button class="quiet" data-rename-evaluation="${run.id}" aria-label="${esc(run.name)} umbenennen" title="Umbenennen">✎</button><a class="button-link quiet" href="#/evaluations/${run.id}" data-open-evaluation="${run.id}">Öffnen <span aria-hidden="true">↗</span></a></div>
    </article>`,
          )
          .join("")
      : `<div class="empty-state"><strong>${runs.length ? "Keine passenden Evaluationen" : "Hier beginnen deine Ergebnisse."}</strong><p>${runs.length ? "Passe die Suche oder die Filter an." : "Starte eine benannte Evaluation. Modelle, Einstellungen und Ergebnisse bleiben gemeinsam auffindbar."}</p><button class="primary" data-new-evaluation>Evaluation starten</button></div>`;
  }
  async function refresh() {
    runs = await api("/runs");
    renderList();
  }
  function comparisonQuery(selections = comparisonSelection) {
    const query = new URLSearchParams({ timely_ms: String(timely) });
    for (const selection of selections) query.append("selection", selection);
    return query.toString();
  }
  function pointLabel(run, condition) {
    const config = run.config;
    let threshold = "";
    if (condition.id.startsWith("livekit"))
      threshold = config.livekit_threshold == null ? "Deutsch-Standard" : config.livekit_threshold;
    if (condition.id === "scribe-v3-live") threshold = config.scribe_threshold;
    return condition.label + (threshold !== "" ? ` · Schwelle ${typeof threshold === "number" ? fmt(threshold, 4) : threshold}` : "");
  }
  function comparisonRows() {
    const available = runs.filter((r) => r.status === "completed" && r.conditions?.length);
    $("comparison-rows").innerHTML = comparisonDraft.map((selection, index) => {
      const [runId, conditionId] = selection.split(":");
      const selected = available.find((r) => r.id === runId);
      const config = selected?.config;
      const note = config
        ? `${config.mode === "offline" ? "Offline" : "Echtzeit"} · ${selected.record_count} Beiträge` +
          (conditionId?.startsWith("baseline") ? "" : ` · Mindeststille ${config.min_silence_ms} ms · Timeout ${config.max_silence_ms} ms`)
        : "Abgeschlossenen Lauf und Modell auswählen.";
      return `<div class="comparison-row"><label>Modellzeile ${index + 1}<select data-comparison-select="${index}" required><option value="">Betriebspunkt auswählen …</option>${available.map((run) => `<optgroup label="${esc(run.name)}">${run.conditions.map((condition) => {
        const value = `${run.id}:${condition.id}`;
        return `<option value="${esc(value)}"${value === selection ? " selected" : ""}>${esc(pointLabel(run, condition))} · ${esc(run.name)}</option>`;
      }).join("")}</optgroup>`).join("")}</select><small class="muted">${esc(note)}</small></label><button type="button" class="quiet" data-comparison-remove="${index}" aria-label="Modellzeile ${index + 1} entfernen"${comparisonDraft.length === 1 ? " disabled" : ""}>×</button></div>`;
    }).join("");
    $("comparison-add").disabled = comparisonDraft.length >= 12 || !available.length;
    $("comparison-apply").disabled = !available.length;
    for (const select of $("comparison-rows").querySelectorAll("[data-comparison-select]"))
      select.onchange = () => {
        comparisonDraft[Number(select.dataset.comparisonSelect)] = select.value;
        comparisonRows();
      };
    for (const button of $("comparison-rows").querySelectorAll("[data-comparison-remove]"))
      button.onclick = () => {
        comparisonDraft.splice(Number(button.dataset.comparisonRemove), 1);
        comparisonRows();
      };
  }
  async function loadComparison() {
    const ticket = ++comparisonTicket;
    const query = comparisonQuery();
    const data = await api(`/comparisons/report?${query}`);
    if (ticket !== comparisonTicket || $("comparison").hidden) return;
    payload = data;
    current = null;
    $("comparison-error").hidden = true;
    renderDetail(data);
    const href = `#/evaluations/compare?${query}`;
    history.replaceState(null, "", href);
    $("comparison-link").href = href;
    $("comparison-link").hidden = false;
    try { localStorage.setItem("eot-comparison", query); } catch { /* URL remains reusable. */ }
  }
  async function openComparison(query = "") {
    ++detailTicket;
    ++comparisonTicket;
    stopAudio();
    current = null;
    payload = null;
    $("evaluation-detail-content").innerHTML = "";
    activeTab = "overview";
    $("comparison-result").innerHTML = "";
    $("comparison-error").hidden = true;
    $("comparison-link").hidden = true;
    runs = await api("/runs");
    if (!query) {
      try { query = localStorage.getItem("eot-comparison") || ""; } catch { /* Optional preference. */ }
    }
    const params = new URLSearchParams(query || "");
    const windowValue = Number(params.get("timely_ms") ?? 1600);
    timely = Number.isInteger(windowValue) && windowValue >= 0 && windowValue <= 5000 ? windowValue : 1600;
    comparisonSelection = params.getAll("selection");
    if (!comparisonSelection.length) {
      const available = runs.filter((r) => r.status === "completed" && r.conditions?.length);
      for (const prefix of ["baseline-", "livekit", "scribe"])
        for (const run of available) {
          const condition = run.conditions.find((c) => c.id.startsWith(prefix));
          if (condition) { comparisonSelection.push(`${run.id}:${condition.id}`); break; }
        }
    }
    comparisonDraft = comparisonSelection.length ? [...comparisonSelection] : [""];
    comparisonRows();
    if (comparisonSelection.length) {
      try { await loadComparison(); } catch (e) {
        $("comparison-error").textContent = e.message;
        $("comparison-error").hidden = false;
      }
    }
  }
  function chart(kind, title, description) {
    const url = payload?.comparison
      ? `/api/comparisons/charts/${kind}?${comparisonQuery()}`
      : `/api/runs/${current}/charts/${kind}?timely_ms=${timely}`;
    return `<figure class="research-figure"><div class="figure-heading"><div><div class="section-title"><h3>${title}</h3>${infoButton("chart", description, title)}</div></div><div class="figure-downloads"><button type="button" class="quiet" data-chart-preview="${url}" data-chart-title="${esc(title)}" aria-label="Grafik vergrößern" title="Vergrößern">⤢</button><a href="${url}&format=png&download=true">PNG ↓</a><a href="${url}&format=svg&download=true">SVG ↓</a></div></div><img src="${url}" alt="${esc(title)}" width="1050" height="560" loading="${["outcomes", "cases"].includes(kind) ? "eager" : "lazy"}" onerror="this.hidden=true;this.nextElementSibling.hidden=false"><p class="notice error" hidden>Die Grafik konnte nicht geladen werden. Die Ergebnistabelle bleibt verfügbar.</p></figure>`;
  }
  function summaryTable(analysis) {
    return `<div class="table-wrap"><table class="results-table"><thead><tr><th>Verfahren</th><th>Zu früh</th><th>Im Zeitfenster</th><th>Verzögert</th><th>Ausfälle</th><th>Ø Abweichung</th><th>Zu früh · Ø / Median</th><th>Wartezeit · Median / p95</th></tr></thead><tbody>${analysis.conditions.map((s) => `<tr><th>${esc(s.label)}<small>n = ${s.n}</small></th><td class="text-early">${s.counts.early}/${s.n}<small>${fmt(s.early_rate * 100, 1)} %</small></td><td>${s.counts.timely}/${s.n}</td><td>${s.counts.late}/${s.n}</td><td>${s.counts.failure}</td><td>${signed(s.delta_mean_ms)}<small>n = ${s.delta_n} gültige Entscheidungen</small></td><td>${fmt(s.early_lead_mean_ms)} / ${fmt(s.early_lead_median_ms)} ms</td><td>${fmt(s.delay_median_ms)} / ${fmt(s.delay_p95_ms)} ms<small>n = ${s.delay_n}</small>${s.fallback_count === null ? "" : `<small>Fallbacks: ${s.fallback_count}</small>`}</td></tr>`).join("")}</tbody></table></div>`;
  }
  function renderSetup(run, report) {
    const config = run.config;
    const settings = [
      [
        "Datenquelle",
        report.dataset?.source === "mixed"
          ? "25 eigene + 25 synthetische Aufnahmen"
          : report.dataset?.source === "synthetic"
            ? "Synthetische Audiodaten"
            : "Menschliche Aufnahmen",
      ],
      ...(run.split
        ? [["Split", run.split === "test" ? "Test" : "Entwicklung"]]
        : []),
      [
        "Ausführung",
        config.mode === "offline"
          ? "Offline: simulierte Zeit"
          : "Echtzeit (1×)",
      ],
      ["Parallele Aufnahmen", config.parallelism ?? 1],
      ["VAD-Schwelle", config.vad_threshold],
      ["Erste semantische Prüfung", `${config.min_silence_ms} ms Stille`],
      ["Maximale Stille", `${config.max_silence_ms} ms`],
      [
        "Prüfintervall lokaler / abfragbarer Modelle",
        `${config.inference_interval_ms} ms`,
      ],
      ["Baseline-Timeouts", `${config.baseline_timeouts_ms.join(", ")} ms`],
      [
        "LiveKit-Schwelle",
        config.livekit_threshold === null
          ? "Herstellerkalibrierung für Deutsch"
          : config.livekit_threshold,
      ],
      ...(config.models.includes("smart_turn")
        ? [["Smart-Turn-Schwelle", config.smart_turn_threshold]]
        : []),
      ...(config.models.includes("scribe")
        ? [
            ["Scribe-Schwelle", config.scribe_threshold],
            [
              "Scribe-Policy",
              "Turn-Scores mit gemeinsamer VAD- und Timer-Regel",
            ],
          ]
        : []),
      ["Datensatz-ID", run.release_id],
      ["Lauf-ID", run.id],
    ];
    return `<details class="method-note"><summary>Messung und Bewertung</summary><p>Referenzende ist das hinterlegte Ende des Nutzerbeitrags. Negative Zeitabweichungen sind vorzeitige Abschlüsse. Positive Werte messen die Wartezeit bis zur wirksamen Entscheidung. Das Zeitfenster ist eine veränderbare Darstellungshilfe und kein nachträglich optimierter Modellparameter.</p><p>Technische Ausfälle und fehlende Entscheidungen bilden eine eigene Kategorie. Wartezeitstatistiken enthalten ausschließlich gültige Entscheidungen ab dem Referenzende; ihr Stichprobenumfang steht jeweils dabei. Timer-Fallbacks bleiben separat dokumentiert.</p><p>Cloud-Aufrufdauern enthalten Netzwerk und Dienstverarbeitung. Scribe liefert laufende Scores und hat keine vergleichbare Einzelaufrufdauer. Das ist keine Messung der gesamten Antwortlatenz eines Voicebots.</p></details>
      <dl class="setup-grid">${settings.map(([key, value]) => `<div><dt>${esc(key)}</dt><dd>${esc(value)}</dd></div>`).join("")}</dl>
      <details><summary>Gespeicherte Rohkonfiguration</summary><pre>${esc(JSON.stringify(config, null, 2))}</pre></details>
      ${report.paired_latencies ? `<details><summary>Gepaarte Wartezeitvergleiche · historische Auswertung</summary><p class="small muted">Nur gemeinsam korrekt beendete Beiträge. Rohwerte aus dem ursprünglichen Bericht; technische Sonderfälle anhand der Einzelergebnisse prüfen.</p><pre>${esc(JSON.stringify(report.paired_latencies, null, 2))}</pre></details>` : ""}`;
  }
  function renderDetail(data) {
    stopAudio();
    const { run, report, analysis, comparison } = data;
    const container = $(comparison ? "comparison-result" : "evaluation-detail-content");
    if (!report) {
      container.innerHTML = `<div class="evaluation-hero"><div><p class="eyebrow">Evaluation</p><h1 id="evaluation-title">${esc(run.name)}</h1><div class="model-tags">${modelTags(run)}</div></div>${badge(run)}</div>
        <div class="panel pending-evaluation"><span class="pending-orbit" aria-hidden="true">◌</span><h3>${["running", "queued"].includes(run.status) ? "Die Evaluation läuft." : "Für diesen Lauf liegen keine Ergebnisse vor."}</h3><p>${esc(run.error || "Die Aufnahmen werden nacheinander durch die ausgewählten Verfahren geschickt. Du kannst diese Seite verlassen und später zurückkehren.")}</p><progress value="${run.progress || 0}" max="${run.total || 1}"></progress><p class="small muted">${run.progress || 0} / ${run.total || "…"} Vergleiche verarbeitet</p><div class="actions"><button data-rename-evaluation="${run.id}">Umbenennen</button>${["running", "queued"].includes(run.status) ? `<button class="quiet" data-cancel-evaluation="${run.id}">Lauf abbrechen</button>` : ""}</div></div>`;
      return;
    }
    const goodSource = report.dataset?.source === "synthetic";
    const download = comparison ? `/api/comparisons/download?${comparisonQuery()}` : `/api/runs/${run.id}/download?timely_ms=${timely}`;
    const tags = comparison ? comparison.sources.map((s) => `<span class="model-tag">${esc(s.label)} · ${esc(s.run.name)}</span>`).join("") : modelTags(run);
    const setup = comparison
      ? comparison.sources.map((s) => `<details class="comparison-source"><summary>${esc(s.label)} · ${esc(s.run.name)}</summary>${renderSetup(s.run, report)}</details>`).join("")
      : renderSetup(run, report);
    container.innerHTML = `<div class="evaluation-hero"><div><p class="eyebrow">${comparison ? "Ausgewählte Betriebspunkte" : "Ergebnisse · " + esc(date(run.created_at))}</p><h1 id="evaluation-title">${esc(run.name)}</h1><div class="model-tags">${tags}<span class="source-tag">${report.dataset?.source === "mixed" ? "25 eigene + 25 synthetische Aufnahmen" : goodSource ? "Synthetisch" : "Menschliche Aufnahmen"}${goodSource ? infoButton("synthetic-data", `${report.dataset.independent_base_files || "Mehrere"} Basisgenerierungen in diesem Lauf.`) : ""}</span></div></div><div class="evaluation-hero-actions">${comparison ? "" : badge(run) + `<button class="quiet icon-action" data-rename-evaluation="${run.id}" aria-label="Evaluation umbenennen" title="Umbenennen">✎</button>`}<a class="button-link" href="${download}">Export ↓</a></div></div>
      <div class="analysis-kpis"><div><strong>${analysis.record_count}</strong><span>Audio-Beiträge</span></div><div><strong>${analysis.conditions.length}</strong><span>Betriebspunkte</span></div><div><strong>${analysis.observation_count}</strong><span>Einzelvergleiche</span></div><div><strong>${analysis.failure_count}</strong><span>Technische Ausfälle</span></div></div>

      ${run.config.mode === "offline" ? '<p class="notice">Offline · simulierte Entscheidungszeiten.</p>' : ""}
      ${run.status !== "completed" ? `<p class="notice error">Lauf ${esc((statuses[run.status] || run.status).toLowerCase())} · Ergebnisse vorläufig.</p>` : ""}
      <div class="report-navigation" role="tablist" aria-label="Ergebnisbereiche">${[
        ["overview", "Überblick"],
        ["timing", "Zeitverhalten"],
        ["cases", "Einzelfälle"],
        ["setup", "Versuchsaufbau"],
      ]
        .map(
          ([id, label]) =>
            `<button role="tab" id="result-tab-${id}" aria-controls="result-panel-${id}" data-result-tab="${id}">${label}</button>`,
        )
        .join("")}</div>
      <div class="analysis-toolbar"><div class="outcome-legend">${Object.entries(
        outcomes,
      )
        .map(
          ([id, label]) =>
            `<span><i class="outcome-dot ${id}"></i>${id === "timely" ? "0–" + timely + " ms" : id === "late" ? "> " + timely + " ms" : label}</span>`,
        )
        .join(
          "",
        )}${infoButton("outcomes")}</div><details class="analysis-window"><summary>Zeitfenster · ${timely} ms</summary><form id="timely-form"><label>Grenze nach Referenzende (ms)<input id="timely-window" type="number" min="0" max="5000" step="1" value="${timely}" required /></label><button type="submit" class="quiet">Anwenden</button>${infoButton("timely")}</form></details></div>
      <section id="result-panel-overview" class="result-panel" role="tabpanel" aria-labelledby="result-tab-overview">
        ${chart("outcomes", "Abschlüsse", `Alle Beiträge je Verfahren · im Zeitfenster = 0 bis ${timely} ms nach Referenzende. Ausfälle werden nicht als Erfolg gezählt.`)}
        <div class="panel"><div class="panel-heading"><h3>Die wichtigsten Zahlen</h3>${infoButton("statistics")}</div>${summaryTable(analysis)}</div>
        ${chart("cases", "Falltypen", "Vorzeitige Abschlüsse je Falltyp. Jede Zelle zeigt Anzahl / Gesamtzahl und den Prozentwert.")}
      </section>
      <section id="result-panel-timing" class="result-panel" role="tabpanel" aria-labelledby="result-tab-timing" hidden>
        ${chart("timing", "Zeitabweichung", "Jeder Punkt ist ein Beitrag. Links von null wurde vorzeitig abgeschlossen; rechts von null liegt die zusätzliche Wartezeit. Negative Werte beziehen sich auf das gesamte tatsächliche Beitragsende, nicht nur auf die aktuelle Pause.")}
        ${chart("latency", "Wartezeit", "Nur korrekt beendete Beiträge. Box: mittlere 50 %; Strich: Median; Punkte: Einzelbeobachtungen. Die Stichprobengröße steht an jeder Modellzeile.")}
        <details class="panel"><summary>Zusätzlich: Abbruchrate und Verzögerung je Betriebspunkt</summary>${chart("tradeoff", "Zielkonflikt zwischen Wartezeit und Abbruchrate", "Eine Position je Betriebspunkt. Die Legende steht außerhalb der Datenfläche; es werden keine Rangfolgen aus nur einem Wert abgeleitet.")}</details>
      </section>
      <section id="result-panel-cases" class="result-panel" role="tabpanel" aria-labelledby="result-tab-cases" hidden>
        <div class="panel"><div class="panel-heading"><div class="section-title"><h3>Einzelfall</h3>${infoButton("timeline")}</div></div>
        <div class="case-filters"><label>Ergebnisfilter<select id="case-outcome"><option value="">Alle Ergebnisse</option>${Object.entries(
          outcomes,
        )
          .map(([id, label]) => `<option value="${id}">${label}</option>`)
          .join(
            "",
          )}</select></label><label>Verfahren für Filter<select id="case-model"><option value="">Mindestens ein Verfahren</option>${analysis.conditions.map((s) => `<option value="${esc(s.condition)}">${esc(s.label)}</option>`).join("")}</select></label></div>
        <label>Beitrag<select id="case-select"></select></label><div id="case-view"></div></div>
      </section>
      <section id="result-panel-setup" class="result-panel panel" role="tabpanel" aria-labelledby="result-tab-setup" hidden>${setup}</section>`;
    $("timely-form").onsubmit = async (event) => {
      event.preventDefault();
      if (!$("timely-form").reportValidity()) return;
      timely = Number($("timely-window").value);
      await (comparison ? loadComparison() : open(current, false)).catch(error);
    };
    for (const button of container.querySelectorAll("[data-result-tab]")) {
      button.onclick = () => selectTab(button.dataset.resultTab);
      button.onkeydown = (event) => {
        const tabs = [...container.querySelectorAll("[data-result-tab]")];
        let index = tabs.indexOf(button);
        if (event.key === "ArrowRight") index = (index + 1) % tabs.length;
        else if (event.key === "ArrowLeft")
          index = (index + tabs.length - 1) % tabs.length;
        else return;
        event.preventDefault();
        selectTab(tabs[index].dataset.resultTab);
        tabs[index].focus();
      };
    }
    $("case-outcome").onchange = fillCases;
    $("case-model").onchange = fillCases;
    $("case-select").onchange = () => showCase().catch(error);
    selectTab(activeTab);
  }
  function selectTab(tab) {
    activeTab = tab;
    if (tab !== "cases") stopAudio();
    for (const button of document.querySelectorAll("[data-result-tab]")) {
      const selected = button.dataset.resultTab === tab;
      button.setAttribute("aria-selected", String(selected));
      button.tabIndex = selected ? 0 : -1;
      $("result-panel-" + button.dataset.resultTab).hidden = !selected;
    }
    if (tab === "cases") fillCases();
  }
  function fillCases() {
    if (!payload?.analysis) return;
    const outcome = $("case-outcome").value,
      condition = $("case-model").value;
    const selected = payload.analysis.rows.filter(
      (r) =>
        (!outcome || r.outcome === outcome) &&
        (!condition || r.condition === condition),
    );
    const ids = [...new Set(selected.map((r) => r.id))],
      old = $("case-select").value;
    $("case-select").innerHTML = ids
      .map((id) => {
        const clip = payload.clips.find((c) => c.id === id);
        return `<option value="${esc(id)}">${esc(clip?.scenario_id || selected.find((r) => r.id === id).scenario_id)} · ${clip?.source === "synthetic" ? "Synthetisch" : "Eigene Stimme"}${clip?.provenance?.voice_name ? " · " + esc(clip.provenance.voice_name) : ""}</option>`;
      })
      .join("");
    if (ids.includes(old)) $("case-select").value = old;
    if (!ids.length) {
      stopAudio();
      $("case-view").innerHTML =
        '<p class="empty-state">Keine Beiträge entsprechen diesem Filter.</p>';
      return;
    }
    showCase().catch(error);
  }
  async function showCase() {
    const ticket = ++caseTicket,
      chosen = $("case-select").value;
    const rows = payload.analysis.rows.filter((r) => r.id === chosen),
      clip = payload.clips.find((c) => c.id === chosen);
    const data = await api(`/clips/${chosen}/waveform`);
    if (
      ticket !== caseTicket ||
      !$("case-select") ||
      $("case-select").value !== chosen
    )
      return;
    stopAudio();
    const maximum =
      Math.max(
        rows[0].gold_eot_ms + 1000,
        ...rows.map((r) => r.commit_ms || 0),
      ) + 400;
    const reference = (rows[0].gold_eot_ms / maximum) * 100;
    const audioDuration = data.samples / data.sample_rate;
    const markerColors = [
      "#3474a4",
      "#7764aa",
      "#8a6c3c",
      "#247f68",
      "#bc672c",
      "#ab4f79",
      "#436b7c",
      "#967239",
    ];
    const markers = rows.map((row, index) => {
      const label =
        payload.analysis.conditions.find((c) => c.condition === row.condition)
          ?.label || row.condition;
      const short = row.condition.startsWith("baseline-")
        ? "VAD " + row.condition.slice(9).replace("ms", "")
        : row.condition.startsWith("livekit")
          ? "LiveKit"
          : row.condition === "smart_turn"
            ? "Smart Turn"
            : row.condition === "scribe-v3-live"
              ? "Scribe"
              : "Modell " + (index + 1);
      return {
        ...row,
        label,
        short,
        color:
          row.outcome === "failure"
            ? "#818a92"
            : markerColors[index % markerColors.length],
        visible:
          Number.isFinite(row.commit_ms) &&
          row.commit_ms >= 0 &&
          row.commit_ms <= audioDuration * 1000,
      };
    });
    const visibleMarkers = markers.filter((marker) => marker.visible);
    const referencePercent = (rows[0].gold_eot_ms / 1000 / audioDuration) * 100;
    const waveformMarks =
      `<i class="waveform-reference-line" style="left:${referencePercent}%"></i><button type="button" class="waveform-label waveform-reference-label ${referencePercent > 65 ? "align-left" : ""}" style="left:${referencePercent}%;top:4px" data-decision-seek="${rows[0].gold_eot_ms / 1000}" title="Referenzende: ${fmt(rows[0].gold_eot_ms)} ms">Referenzende</button>` +
      visibleMarkers
        .map((marker, index) => {
          const x = (marker.commit_ms / 1000 / audioDuration) * 100,
            top = 25 + index * 18;
          const title = `${marker.label}: ${fmt(marker.commit_ms)} ms ab Replaystart · ${signed(marker.delta_ms)} · ${outcomes[marker.outcome]}`;
          return `<i class="waveform-endpoint-line" style="left:${x}%;top:${top + 15}px;border-color:${marker.color}"></i><button type="button" class="waveform-label ${x > 65 ? "align-left" : ""}" style="left:${x}%;top:${top}px;color:${marker.color}" data-decision-seek="${marker.commit_ms / 1000}" aria-label="${esc(title)}" title="${esc(title)}">${esc(marker.short)}</button>`;
        })
        .join("");
    const waveformLegend = markers
      .map(
        (marker) =>
          `<button type="button" class="waveform-legend-item" ${Number.isFinite(marker.commit_ms) ? `data-decision-seek="${marker.commit_ms / 1000}"` : "disabled"} title="${esc(marker.label)}"><i style="background:${marker.color}"></i><span>${esc(marker.label)}</span><strong>${marker.commit_ms === null ? "Keine Entscheidung" : fmt(marker.commit_ms) + " ms"}</strong>${Number.isFinite(marker.commit_ms) && !marker.visible ? "<small>außerhalb der Audiospur</small>" : ""}</button>`,
      )
      .join("");

    $("case-view").innerHTML =
      `${transcriptMarkup(clip)}<audio id="case-audio" controls preload="metadata" src="/api/clips/${chosen}/audio"></audio><div class="waveform-heading section-title"><strong>Audio & Endentscheidungen</strong>${infoButton("waveform")}</div><div class="case-waveform"><div class="waveform-marker-header" style="height:${31 + visibleMarkers.length * 18}px"></div><canvas id="case-canvas" aria-label="Audio-Wellenform mit Referenzende und EOT-Markierungen"></canvas><div class="waveform-marker-layer" role="group" aria-label="Endentscheidungen direkt in der Audiospur">${waveformMarks}</div></div><div class="waveform-legend" aria-label="Modelle und Entscheidungszeitpunkte">${waveformLegend}</div>
      <div class="case-time-heading"><div class="section-title"><strong>Modellvergleich</strong>${infoButton("timeline")}</div><span>0–${fmt(maximum / 1000, 2)} s</span></div>
      <div class="decision-timeline">${rows.map((r) => `<div class="decision-row"><span class="decision-model">${esc(payload.analysis.conditions.find((s) => s.condition === r.condition)?.label || r.condition)}</span><div class="decision-track"><i class="reference-line" style="left:${reference}%"></i>${r.commit_ms !== null ? `<button type="button" class="decision-marker ${r.outcome}" style="left:${Math.max(0, Math.min(100, (r.commit_ms / maximum) * 100))}%" data-decision-seek="${r.commit_ms / 1000}" aria-label="${esc(payload.analysis.conditions.find((s) => s.condition === r.condition)?.label || r.condition)}: Entscheidung bei ${fmt(r.commit_ms)} Millisekunden" title="${fmt(r.commit_ms)} ms ab Replaystart"></button>` : ""}</div><span class="decision-delta text-${r.outcome}">${signed(r.delta_ms)}<small>${outcomes[r.outcome]}</small></span></div>`).join("")}</div>

      <details><summary>Einzelwerte und Auslöser</summary><div class="table-wrap"><table><thead><tr><th>Verfahren</th><th>Entscheidung</th><th>Abweichung</th><th>Ergebnis</th><th>Auslöser</th></tr></thead><tbody>${rows.map((r) => `<tr><td>${esc(payload.analysis.conditions.find((s) => s.condition === r.condition)?.label || r.condition)}</td><td>${fmt(r.commit_ms)} ms</td><td>${signed(r.delta_ms)}</td><td>${outcomes[r.outcome]}</td><td>${esc(r.trigger)}${r.error ? `<small>${esc(r.error)}</small>` : ""}</td></tr>`).join("")}</tbody></table></div></details>`;
    const audio = $("case-audio");
    const unbind = bindTranscript($("case-view"), audio);
    const draw = () =>
      drawWave($("case-canvas"), data, [], 1, 0, audio.currentTime);
    draw();
    $("case-canvas").onclick = (event) => {
      const bounds = $("case-canvas").getBoundingClientRect();
      audio.currentTime = Math.max(
        0,
        Math.min(
          audioDuration,
          ((event.clientX - bounds.left) / bounds.width) * audioDuration,
        ),
      );
    };
    audio.addEventListener("timeupdate", draw);
    window.addEventListener("resize", draw);
    caseCleanup = () => {
      unbind();
      audio.removeEventListener("timeupdate", draw);
      window.removeEventListener("resize", draw);
    };
    $("case-view")
      .querySelectorAll("[data-decision-seek]")
      .forEach(
        (button) =>
          (button.onclick = () => {
            audio.currentTime = Math.min(
              Number(button.dataset.decisionSeek),
              audio.duration || Infinity,
            );
          }),
      );
  }
  async function open(id, reset = true) {
    ++comparisonTicket;
    $("comparison-result").innerHTML = "";
    if (reset) {
      activeTab = "overview";
      timely = 1600;
    }
    current = id;
    const requestId = id,
      requestTicket = ++detailTicket;
    const data = await api(`/runs/${id}/report?timely_ms=${timely}`);
    if (current !== requestId || requestTicket !== detailTicket) return;
    payload = data;
    renderDetail(data);
  }
  function rename(id) {
    renameId = id;
    const run = runs.find((r) => r.id === id) || payload?.run;
    $("rename-evaluation-name").value = run?.name || "";
    $("rename-evaluation-error").hidden = true;
    $("rename-evaluation").showModal();
    $("rename-evaluation-name").select();
  }
  document.addEventListener("click", (event) => {
    const preview = event.target.closest("[data-chart-preview]");
    if (preview) {
      $("figure-preview-title").textContent = preview.dataset.chartTitle;
      $("figure-preview-image").src = preview.dataset.chartPreview;
      $("figure-preview-image").alt = preview.dataset.chartTitle;
      $("figure-preview-png").href =
        preview.dataset.chartPreview + "&format=png&download=true";
      $("figure-preview-svg").href =
        preview.dataset.chartPreview + "&format=svg&download=true";
      $("figure-preview").showModal();
    }
    const openButton = event.target.closest("[data-open-evaluation]");
    if (openButton) {
      event.preventDefault();
      showTab("evaluation-detail", openButton.dataset.openEvaluation).catch(
        error,
      );
    }
    const renameButton = event.target.closest("[data-rename-evaluation]");
    if (renameButton) rename(renameButton.dataset.renameEvaluation);
    if (event.target.closest("[data-new-evaluation]"))
      showTab("compare").catch(error);
    if (event.target.closest("[data-open-comparison]"))
      showTab("comparison").catch(error);
    if (event.target.closest("[data-comparison-back]"))
      showTab("evaluations").catch(error);
    const cancel = event.target.closest("[data-cancel-evaluation]");
    if (cancel)
      api(`/runs/${cancel.dataset.cancelEvaluation}/cancel`, { method: "POST" })
        .then(() => open(cancel.dataset.cancelEvaluation, false))
        .catch(error);
  });
  $("rename-evaluation-form").onsubmit = async (event) => {
    event.preventDefault();
    const button = $("rename-evaluation-save");
    button.disabled = true;
    try {
      const renamed = await api(`/runs/${renameId}`, {
        method: "PATCH",
        body: { name: $("rename-evaluation-name").value },
      });
      $("rename-evaluation").close();
      await refresh();
      if (current === renameId && payload) {
        payload.run.name = renamed.name;
        if ($("evaluation-title"))
          $("evaluation-title").textContent = renamed.name;
      }
      notice("Evaluationsname gespeichert.");
    } catch (e) {
      $("rename-evaluation-error").textContent = e.message;
      $("rename-evaluation-error").hidden = false;
    } finally {
      button.disabled = false;
    }
  };
  $("rename-evaluation-cancel").onclick = () => $("rename-evaluation").close();
  for (const id of [
    "evaluation-search",
    "evaluation-status",
    "evaluation-model",
  ])
    $(id).addEventListener(
      id === "evaluation-search" ? "input" : "change",
      () => {
        listSignature = "";
        renderList();
      },
    );
  $("figure-preview-close").onclick = () => $("figure-preview").close();
  $("evaluation-refresh").onclick = () => refresh().catch(error);
  $("comparison-add").onclick = () => {
    if (comparisonDraft.length < 12) comparisonDraft.push("");
    comparisonRows();
  };
  $("comparison-form").onsubmit = async (event) => {
    event.preventDefault();
    if (!$("comparison-form").reportValidity()) return;
    const button = $("comparison-apply");
    button.disabled = true;
    comparisonSelection = [...comparisonDraft];
    activeTab = "overview";
    try { await loadComparison(); } catch (e) {
      $("comparison-result").innerHTML = "";
      $("comparison-link").hidden = true;
      $("comparison-error").textContent = e.message;
      $("comparison-error").hidden = false;
    } finally { button.disabled = false; }
  };
  setInterval(async () => {
    if (loading) return;
    try {
      loading = true;
      if (!$("evaluations").hidden) await refresh();
      else if (
        !$("evaluation-detail").hidden &&
        payload &&
        ["running", "queued"].includes(payload.run.status)
      )
        await open(current, false);
    } catch (e) {
      error(e);
    } finally {
      loading = false;
    }
  }, 2500);
  return { refresh, open, openComparison, stopAudio };
}
