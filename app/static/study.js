const esc = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const seconds = (ms) =>
  (ms / 1000).toLocaleString("de-DE", { maximumFractionDigits: 2 });

export function recordingMarkup(card) {
  return `<div class="recording-copy">
    <div class="delivery-note"><p class="recording-label">Sprechweise</p><p>${esc(card.delivery)}. ${esc(card.instruction)}</p></div>
    <p class="recording-label">Sprechtext</p>
    <div class="study-script">${card.segments.map((text, i) => `<span>${esc(text)}</span>${i < card.segments.length - 1 ? `<div class="study-pause">Pause · ${seconds(card.pauses_ms[i])} s</div>` : ""}`).join("")}</div>
  </div>`;
}

export function setupStudy({
  api,
  notice,
  refresh,
  showTab,
  openRecord,
  openAnnotation,
}) {
  const $ = (id) => document.getElementById(id);
  let state;
  let selectedRelease = null;
  const confirmed = (clip) =>
    clip?.annotation?.reference_method === "human_waveform_annotation";
  function cell(clip, card, source) {
    if (!clip)
      return source === "human"
        ? `<button class="quiet" data-study-record="${card.id}">Aufnehmen</button>`
        : '<span class="muted small">Noch nicht erzeugt</span>';
    return `<button class="quiet ${confirmed(clip) ? "study-confirmed" : ""}" data-study-annotate="${clip.id}">${confirmed(clip) ? "✓ Ende bestätigt" : source === "synthetic" ? "Endvorschlag prüfen" : "Ende markieren"}</button>`;
  }
  function render() {
    const c = state.counts;
    $("study-stats").innerHTML = [
      [c.human, 25, "Eigene Aufnahmen"],
      [c.synthetic, 25, "ElevenLabs-Dateien"],
      [
        c.human_annotated + c.synthetic_annotated,
        50,
        "Referenzenden bestätigt",
      ],
    ]
      .map(
        ([value, max, label]) =>
          `<article class="study-stat"><strong>${value}<small> / ${max}</small></strong><span>${label}</span><progress value="${value}" max="${max}" aria-label="${label}"></progress></article>`,
      )
      .join("");
    const selector = $("study-synthetic-release");
    selector.innerHTML = state.synthetic_releases.length
      ? state.synthetic_releases
          .map(
            (r) =>
              `<option value="${r.id}">${esc(r.voice.name || r.voice.id)} · ${esc(new Date(r.created_at).toLocaleString("de-DE"))}</option>`,
          )
          .join("")
      : '<option value="">Noch keine 25 Dateien erzeugt</option>';
    selector.value = state.synthetic_release_id || "";
    selector.disabled = !state.synthetic_releases.length;
    $("study-source-field").hidden = !state.synthetic_releases.length;
    $("study-pairs").innerHTML = state.pairs
      .map(
        ({ card, human, synthetic }) =>
          `<tr><th><button class="study-scenario" data-study-record="${card.id}"><span class="mono">${card.pair_id}</span><br>${esc(card.content_label)}</button></th><td>${esc(card.pattern_label)}<small>${card.pauses_ms.length ? "Pause: " + card.pauses_ms.map(seconds).join(" / ") + " s" : "Ohne Zusatzpause"}</small></td><td>${cell(human, card, "human")}</td><td>${cell(synthetic, card, "synthetic")}</td></tr>`,
      )
      .join("");
    $("study-release").disabled = !state.ready;
    $("study-release-status").textContent = state.ready
      ? "Vollständig · 50 Samples"
      : `${c.complete_pairs}/25 Paare vollständig. Für den Export müssen alle Referenzenden bestätigt sein.`;
    $("study-releases").innerHTML = state.releases
      .map(
        (r) =>
          `<div class="release-row"><span>50 Samples · ${esc(new Date(r.created_at).toLocaleString("de-DE"))}</span><a href="/api/releases/${r.id}/download">ZIP herunterladen</a><button class="quiet" data-study-evaluate="${r.id}">Evaluieren</button></div>`,
      )
      .join("");
  }
  async function load() {
    state = await api(
      "/study" +
        (selectedRelease
          ? "?synthetic_release_id=" + encodeURIComponent(selectedRelease)
          : ""),
    );
    render();
    return state;
  }
  $("study-synthetic-release").onchange = async () => {
    selectedRelease = $("study-synthetic-release").value || null;
    try {
      await refresh();
    } catch (e) {
      notice(e.message, true);
    }
  };
  $("study").onclick = async (event) => {
    const button = event.target.closest("button");
    if (!button) return;
    try {
      if (button.dataset.studyRecord)
        await openRecord(button.dataset.studyRecord);
      if (button.dataset.studyAnnotate)
        await openAnnotation(button.dataset.studyAnnotate);
      if (button.dataset.studyEvaluate) {
        await showTab("compare");
        $("run-release").value = button.dataset.studyEvaluate;
      }
      if (button.id === "study-release") {
        button.disabled = true;
        await api("/study/releases", {
          method: "POST",
          body: { synthetic_release_id: state.synthetic_release_id },
        });
        await refresh();
        notice(
          "Datensatz mit 50 Samples abgeschlossen. Der ZIP-Export ist bereit.",
        );
      }
    } catch (e) {
      notice(e.message, true);
      if (button.id === "study-release") button.disabled = !state.ready;
    }
  };
  return {
    load,
    state: () => state,
    useRelease: (id) => {
      selectedRelease = id;
    },
  };
}
