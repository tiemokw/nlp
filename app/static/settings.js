const $ = (id) => document.getElementById(id);
const fields = {
  timeouts: "baseline_timeouts_ms",
  "livekit-version": "livekit_version",
  "livekit-threshold": "livekit_threshold",
  "scribe-threshold": "scribe_threshold",
  "min-silence": "min_silence_ms",
  "max-silence": "max_silence_ms",
  "inference-interval": "inference_interval_ms",
  "vad-threshold": "vad_threshold",
};
const sections = {
  baseline: ["timeouts"],
  livekit: ["livekit-version", "livekit-threshold"],
  scribe: ["scribe-threshold"],
  shared: ["min-silence", "max-silence", "inference-interval", "vad-threshold"],
};

export function setupSettings({ api, onChange }) {
  let defaults,
    tab = "shared",
    snapshot;
  const dialog = $("model-settings");
  function read() {
    const result = Object.fromEntries(
      Object.entries(fields).map(([id, key]) => [
        key,
        id === "timeouts"
          ? $(id)
              .value.split(",")
              .map((s) => Number(s.trim()))
          : id === "livekit-version"
            ? $(id).value
            : Number($(id).value),
      ]),
    );
    if ($("livekit-auto").checked) result.livekit_threshold = null;
    return result;
  }
  function write(config) {
    for (const [id, key] of Object.entries(fields)) {
      const value = config[key] ?? defaults?.[key];
      if (key === "livekit_threshold") {
        $("livekit-auto").checked = config[key] === null;
        $(id).value = value ?? 0.5;
      } else $(id).value = Array.isArray(value) ? value.join(", ") : value;
    }
  }
  function update() {
    $("livekit-threshold").disabled = $("livekit-auto").checked;
    $("livekit-threshold").closest("label").hidden = $("livekit-auto").checked;
    $("settings-summary").textContent =
      `VAD ${$("vad-threshold").value} · erste Prüfung nach ${$("min-silence").value} ms · maximal ${$("max-silence").value} ms · Prüfintervall ${$("inference-interval").value} ms`;
    onChange();
  }
  function selectTab(name) {
    tab = name;
    for (const button of document.querySelectorAll("[data-settings-tab]")) {
      const active = button.dataset.settingsTab === name;
      button.setAttribute("aria-selected", String(active));
      button.tabIndex = active ? 0 : -1;
      $("settings-" + button.dataset.settingsTab).hidden = !active;
    }
  }
  function open(name) {
    snapshot = read();
    $("settings-error").hidden = true;
    selectTab(name);
    dialog.showModal();
    $("tab-" + name).focus();
  }
  function cancel() {
    write(snapshot);
    update();
    dialog.close();
  }
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-open-settings]");
    if (button) open(button.dataset.openSettings);
  });
  for (const button of document.querySelectorAll("[data-settings-tab]")) {
    button.onclick = () => selectTab(button.dataset.settingsTab);
    button.onkeydown = (event) => {
      const tabs = [...document.querySelectorAll("[data-settings-tab]")];
      let index = tabs.indexOf(button);
      if (event.key === "ArrowRight") index = (index + 1) % tabs.length;
      else if (event.key === "ArrowLeft")
        index = (index + tabs.length - 1) % tabs.length;
      else if (event.key === "Home") index = 0;
      else if (event.key === "End") index = tabs.length - 1;
      else return;
      event.preventDefault();
      selectTab(tabs[index].dataset.settingsTab);
      tabs[index].focus();
    };
  }
  $("settings-cancel").onclick = cancel;
  $("settings-close").onclick = cancel;
  dialog.addEventListener("cancel", (event) => {
    event.preventDefault();
    cancel();
  });
  $("livekit-auto").onchange = update;
  $("livekit-version").onchange = update;
  $("settings-reset").onclick = () => {
    const values = read();
    for (const id of sections[tab]) values[fields[id]] = defaults[fields[id]];
    write(values);
    update();
  };
  $("model-settings-form").onsubmit = (event) => {
    event.preventDefault();
    for (const [name, ids] of Object.entries(sections)) {
      const invalid = ids
        .map((id) => $(id))
        .find((input) => !input.disabled && !input.checkValidity());
      if (invalid) {
        selectTab(name);
        invalid.reportValidity();
        return;
      }
    }
    const values = read();
    let error = "";
    if (values.min_silence_ms > values.max_silence_ms)
      error = "Die Mindestpause darf die maximale Pause nicht überschreiten.";
    const timers = values.baseline_timeouts_ms;
    if (
      new Set(timers).size !== timers.length ||
      timers.length > 8 ||
      timers.some((n) => !Number.isInteger(n) || n < 250 || n > 5000)
    )
      error =
        "Bitte bis zu acht verschiedene Stillezeiten zwischen 250 und 5000 ms eingeben.";
    if (error) {
      $("settings-error").textContent = error;
      $("settings-error").hidden = false;
      return;
    }
    update();
    dialog.close();
  };
  return {
    read,
    async init() {
      defaults = await api("/experiment-defaults");
      write(defaults);
      update();
    },
  };
}
