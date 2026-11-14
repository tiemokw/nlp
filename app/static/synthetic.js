import { infoButton } from "./info.js";
import { recordingMarkup } from "./study.js";

export function setupSynthetic({ api, notice, refresh, showTab, useRelease }) {
  const $ = (id) => document.getElementById(id);
  const esc = (value) =>
    String(value ?? "").replace(
      /[&<>"']/g,
      (c) =>
        ({
          "&": "&amp;",
          "<": "&lt;",
          ">": "&gt;",
          '"': "&quot;",
          "'": "&#39;",
        })[c],
    );
  let status,
    voices = [],
    timer = null,
    signature = null,
    starting = false,
    pendingJob = null;
  const female = (v) =>
    ["female", "woman", "weiblich"].includes(v?.labels?.gender?.toLowerCase());
  const male = (v) =>
    ["male", "man", "männlich"].includes(v?.labels?.gender?.toLowerCase());
  function act(id, fn) {
    $(id).onclick = async () => {
      try {
        await fn();
      } catch (error) {
        notice(error.message, true);
      }
    };
  }
  function selected() {
    return voices.find((v) => v.id === $("synthesis-voice-0")?.value);
  }
  function updateReady() {
    const voice = selected();
    $("synthesis-gender-confirmation").hidden = !voice || female(voice);
    const ready =
      status?.configured &&
      voice &&
      (female(voice) || $("synthesis-female-confirmed").checked);
    $("synthesis-start").disabled = !ready || starting;
    $("synthesis-preview").disabled = !ready || starting;
  }
  function config() {
    const voice = selected();
    if (!voice)
      throw new Error(
        "Bitte zuerst Stimmen laden und eine weibliche Stimme auswählen.",
      );
    if (!female(voice) && !$("synthesis-female-confirmed").checked)
      throw new Error(
        "Bitte bestätigen, dass die Stimme ohne Anbieterlabel weiblich ist.",
      );
    const seed = Number($("synthesis-seed").value);
    if (!Number.isInteger(seed) || seed < 0 || seed > 4294967295)
      throw new Error(
        "Der Seed muss eine ganze Zahl von 0 bis 4294967295 sein.",
      );
    return {
      voices: [
        { id: voice.id, name: voice.name, gender: voice.labels?.gender || "" },
      ],
      size: "study25",
      female_voice_confirmed: $("synthesis-female-confirmed").checked,
      model_id: $("synthesis-model").value,
      seed,
    };
  }
  function renderVoices() {
    const old = $("synthesis-voice-0")?.value;
    const eligible = voices.filter((v) => !male(v));
    const ordered = [
      ...eligible.filter(female),
      ...eligible.filter((v) => !female(v)),
    ];
    $("synthesis-voices").innerHTML =
      `<label>Weibliche Stimme für alle 25 Beispiele<select id="synthesis-voice-0"><option value="">Bitte auswählen</option>${ordered.map((v) => `<option value="${esc(v.id)}">${esc(v.name)} · ${female(v) ? "weiblich" : "Geschlecht nicht angegeben"}${v.labels?.language ? " · " + esc(v.labels.language) : ""}${v.labels?.accent ? " · " + esc(v.labels.accent) : ""}</option>`).join("")}</select></label>`;
    if (ordered.some((v) => v.id === old)) $("synthesis-voice-0").value = old;
    $("synthesis-voice-0").onchange = () => {
      $("synthesis-female-confirmed").checked = false;
      $("synthesis-plan").innerHTML = "";
      updateReady();
    };
    updateReady();
  }
  async function load() {
    status = await api("/synthesis/status");
    $("synthesis-status").innerHTML =
      `<span class="connection-dot ${status.configured ? "" : "is-error"}"></span><span>${status.configured ? "Zugang konfiguriert" : "ElevenLabs-Schlüssel fehlt"}</span>${infoButton("elevenlabs-access", "Aktiver Endpunkt: " + status.api_base_url)}`;
    $("synthesis-status").className =
      "connection-status" + (status.configured ? "" : " is-error");
    $("synthesis-templates").innerHTML = status.study_templates
      .map(
        (t) =>
          `<article class="example-card"><h3>${esc(t.pair_id)} · ${esc(t.title)}</h3>${recordingMarkup(t)}</article>`,
      )
      .join("");
    if (!$("synthesis-voice-0")) renderVoices();
    updateReady();
    await jobs();
    if (!timer)
      timer = setInterval(() => {
        if (!$("generate").hidden) jobs().catch((e) => notice(e.message, true));
      }, 2500);
  }
  async function jobs() {
    const list = (await api("/synthesis/jobs")).filter(
      (j) => j.config.size === "study25",
    );
    const next = JSON.stringify(list);
    if (signature === next) return;
    signature = next;
    $("synthesis-jobs").innerHTML = list.length
      ? list
          .map(
            (j) =>
              `<div class="run-row"><div class="grow"><strong>25 Beispiele · ${esc(j.config.voices[0].name || j.config.voices[0].id)}</strong><small>${esc({ completed: "Fertig · Referenzenden noch manuell prüfen", running: "Wird erzeugt", queued: "Eingereiht", failed: "Fehlgeschlagen · erneuter Start nutzt den Cache", cancelled: "Abgebrochen · Cache bleibt erhalten", interrupted: "Unterbrochen · Cache bleibt erhalten" }[j.status] || j.status)} · ${j.progress}/${j.total} Dateien${j.error ? " · " + esc(j.error) : ""}</small></div>${["queued", "running"].includes(j.status) ? `<button data-synth-cancel="${j.id}">Abbrechen</button>` : ""}${j.release_id ? `<button class="primary" data-synth-review="${j.release_id}">Anhören & Enden prüfen</button>` : ""}</div>`,
          )
          .join("")
      : '<p class="muted">Noch keine Studienbeispiele erzeugt.</p>';
    $("synthesis-jobs")
      .querySelectorAll("[data-synth-cancel]")
      .forEach((b) => {
        b.onclick = async () => {
          try {
            await api(`/synthesis/jobs/${b.dataset.synthCancel}/cancel`, {
              method: "POST",
            });
            await jobs();
          } catch (e) {
            notice(e.message, true);
          }
        };
      });
    $("synthesis-jobs")
      .querySelectorAll("[data-synth-review]")
      .forEach((b) => {
        b.onclick = async () => {
          try {
            useRelease(b.dataset.synthReview);
            await refresh();
            await showTab("annotate");
          } catch (e) {
            notice(e.message, true);
          }
        };
      });
    const finished = list.find(
      (j) => j.id === pendingJob && j.status === "completed",
    );
    if (finished) {
      pendingJob = null;
      useRelease(finished.release_id);
      await refresh();
      notice(
        "25 Dateien erzeugt. Bitte jetzt alle Referenzenden anhören und bestätigen.",
      );
    }
  }
  act("synthesis-connect", async () => {
    $("synthesis-connect").disabled = true;
    try {
      await load();
      if (!status.configured)
        throw new Error(
          "Bitte ELEVENLABS_API_KEY in der lokalen .env eintragen.",
        );
      voices = await api("/synthesis/voices");
      renderVoices();
      notice(
        `${voices.filter((v) => !male(v)).length} mögliche Stimmen geladen. Wähle eine weibliche Stimme mit deutscher Aussprache.`,
      );
    } finally {
      $("synthesis-connect").disabled = false;
    }
  });
  $("synthesis-female-confirmed").onchange = updateReady;
  act("synthesis-preview", async () => {
    const plan = await api("/synthesis/preview", {
      method: "POST",
      body: config(),
    });
    $("synthesis-plan").innerHTML =
      `<div class="facts"><strong>25 Dateien · eine Stimme · 25 Basisgenerierungen</strong><p>Maximal ${plan.characters_before_cache.toLocaleString("de-DE")} Textzeichen vor Cache-Nutzung. Diese Vorschau ruft ElevenLabs nicht auf.</p><p>6 Inhaltsarten × 4 Sprechverläufe + 1 IBAN mit 3,5 s Suchpause. Pausenziele: 0,4 / 0,7 / 1,8 / 2,2 / 3,5 Sekunden.</p><p class="small">${esc(plan.note)}</p></div>`;
  });
  act("synthesis-start", async () => {
    const body = config();
    starting = true;
    updateReady();
    try {
      const job = await api("/synthesis/jobs", { method: "POST", body });
      pendingJob = job.id;
      await jobs();
      notice(
        "Generierung der 25 Beispiele gestartet. Erfolgreiche Basisdateien bleiben im Cache.",
      );
    } finally {
      starting = false;
      updateReady();
    }
  });
  return { load };
}
