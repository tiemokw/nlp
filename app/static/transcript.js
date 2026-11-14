import { infoButton } from "./info.js";
const escape = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
const seconds = (value) =>
  Number(value).toLocaleString("de-DE", { maximumFractionDigits: 2 });

export function scriptMarkup(segments, holds = [], rate = 16000) {
  return segments
    .map((text, i) => {
      const hold = holds[i];
      const pause =
        i < segments.length - 1
          ? hold
            ? `<button type="button" class="pause-marker" data-pause-start="${hold.start_sample / rate}" data-pause-end="${hold.end_sample / rate}" title="Zur Pause bei ${seconds(hold.start_sample / rate)} Sekunden springen">Pause · ${seconds((hold.end_sample - hold.start_sample) / rate)} s</button>`
            : '<span class="pause-marker">Pause</span>'
          : "";
      return `<span class="speech-segment">${escape(text)}</span>${pause}`;
    })
    .join(" ");
}

export function transcriptMarkup(record) {
  const annotation = record?.annotation || {};
  const provenance = record?.provenance || {};
  const holds = annotation.holds || [];
  const rate = record?.sample_rate || 16000;
  let segments = provenance.segments;
  if (!segments && provenance.tts_parameters?.text) {
    segments = provenance.tts_parameters.text
      .split(/\s*<break\b[^>]*\/?>\s*/i)
      .map((s) => s.trim())
      .filter(Boolean);
  }
  const matched = segments?.length > 0 && holds.length === segments.length - 1;
  const content = matched
    ? scriptMarkup(segments, holds, rate)
    : `<span class="speech-segment">${escape(annotation.transcript || "Für diese Aufnahme ist kein Transkript hinterlegt.")}</span>`;
  const extra =
    !matched && holds.length
      ? `<div class="pause-list">${holds.map((h) => `<button type="button" class="pause-marker" data-pause-start="${h.start_sample / rate}" data-pause-end="${h.end_sample / rate}">Pause bei ${seconds(h.start_sample / rate)} s · ${seconds((h.end_sample - h.start_sample) / rate)} s</button>`).join(" ")}</div>`
      : "";
  return `<section class="transcript" aria-label="Gesprochener Text mit Pausen"><div class="section-title transcript-heading"><p class="eyebrow">Text</p>${infoButton("transcript", record?.source === "synthetic" ? "Quelle: synthetisch erzeugtes Audio." : "Quelle: menschliche Aufnahme.")}</div><div class="spoken-script">${content}</div>${extra}</section>`;
}

export function bindTranscript(container, audio) {
  const buttons = [...container.querySelectorAll("[data-pause-start]")];
  for (const button of buttons)
    button.onclick = () => {
      audio.currentTime = Number(button.dataset.pauseStart);
    };
  const highlight = () => {
    for (const button of buttons)
      button.classList.toggle(
        "is-playing",
        audio.currentTime >= Number(button.dataset.pauseStart) &&
          audio.currentTime < Number(button.dataset.pauseEnd),
      );
  };
  audio.addEventListener("timeupdate", highlight);
  audio.addEventListener("seeked", highlight);
  return () => {
    audio.removeEventListener("timeupdate", highlight);
    audio.removeEventListener("seeked", highlight);
  };
}
