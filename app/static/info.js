const TOPICS = {
  "study-design": {
    title: "Versuchsaufbau",
    text: "25 Szenarien werden jeweils vom Autor und von einer weiblichen ElevenLabs-Stimme gesprochen. Beide Quellen verwenden dieselben Texte und Sprechvorgaben. Insgesamt entstehen 50 Samples.\n\nSechs Inhaltsarten × vier Sprechverläufe ergeben 24 Kombinationen. Ein IBAN-Fall mit 3,5 Sekunden Suchpause ergänzt sie auf 25.\n\nDer Bezugstimeout für die Pausenplanung beträgt 1000 ms. Mehrere Pausen überschreiten ihn. Bei Eigenaufnahmen sind die Dauern Zielwerte. Die Evaluation speichert ihre tatsächlich gewählten Timeouts separat.",
  },
  project: {
    title: "Projektstatus",
    text: "Synthetische Dateien und manuelle Aufnahmen werden getrennt verwaltet. Datensatzstände sind gespeicherte, unveränderliche Auswahlen für die Evaluation.",
  },
  generation: {
    title: "Synthetische Audiodaten",
    text: "Für die Studie werden dieselben 25 Szenarien einmal vom Autor und einmal von einer ausgewählten weiblichen ElevenLabs-Stimme gesprochen. Das ergibt 50 Samples.\n\nSechs Inhaltsarten und vier Sprechverläufe ergeben 24 Kombinationen. Ein zusätzlicher IBAN-Fall mit 3,5 Sekunden Pause ergänzt sie auf 25. Die Referenzenden müssen bei beiden Quellen durch Anhören und Markieren in der Wellenform bestätigt werden.",
  },
  "pause-construction": {
    title: "Wie die Pausen entstehen",
    text: "Ein vollständiger Basisbeitrag wird mit TTS-Pausen erzeugt. Anhand der Zeichenzeitmarken findet die Anwendung leise Zwischenbereiche und ersetzt sie samplegenau durch definierte Stille. Sprachanteile bleiben erhalten.\n\nDas vorgeschlagene Referenzende stammt aus den TTS-Zeitmarken und der Sampleverschiebung. Für den gemeinsamen Studiendatensatz musst du diesen Vorschlag durch Anhören und Markieren in der Wellenform prüfen. Weitere natürliche Pausen können im Audio vorkommen. Der Bezugstimeout für die Pausenplanung beträgt 1000 ms; die Evaluation speichert ihre tatsächlich gewählten Timeouts separat.",
  },
  costs: {
    title: "Kosten und Cache",
    text: "Erzeugen verwendet dein ElevenLabs-Kontingent. Erfolgreiche Basisgenerierungen werden zwischengespeichert; Pausenvarianten entstehen lokal.\n\nDie Vorschau zeigt Dateien, Basisgenerierungen und Textzeichen vor Cache-Nutzung. Diese Zeichenmenge ist keine verbindliche Credit-Abrechnung. Nach Fehlern wird nicht automatisch kostenpflichtig neu versucht.",
  },
  "elevenlabs-access": {
    title: "ElevenLabs-Zugang",
    text: "ELEVENLABS_API_KEY wird lokal in der ignorierten .env-Datei hinterlegt. Für EU Data Residency ist ELEVENLABS_BASE_URL=https://api.eu.residency.elevenlabs.io erforderlich. EU- und globale Workspaces verwenden getrennte Schlüssel.\n\nDer Schlüssel benötigt TTS-Zugriff und Leserechte für Stimmen. Scribe braucht zusätzlich STT-Rechte. Zugangsdaten werden nicht im Browser gespeichert. „Zugang konfiguriert“ bestätigt den Eintrag; „Stimmen laden“ prüft den tatsächlichen Zugriff.",
  },
  dataset: {
    title: "Datensatzstände",
    text: "Der gemeinsame Studienstand enthält genau 25 menschliche und 25 synthetische Aufnahmen mit 50 manuell bestätigten Referenzenden. Er wird unter „Datensatz“ abgeschlossen. Eine Evaluation verwendet alle Aufnahmen des ausgewählten Datensatzstands und läuft in Echtzeit. Die aktuellen Einstellungen werden beim Start automatisch mit dem Lauf gespeichert. Jeder Datensatzstand ist unveränderlich.",
  },
  evaluation: {
    title: "Evaluation starten",
    text: "Die ausgewählten Modelle werten den gesamten Datensatz aus. Pro Modell laufen bis zu sechs Aufnahmen parallel, jeweils mit eigenem VAD- und Modellzustand. Jede Aufnahme wird weiterhin in Originalgeschwindigkeit abgespielt.\n\nDie Parallelität wird mit den Einstellungen gespeichert. Gleichzeitige Verarbeitung kann die gemessenen Latenzen durch zusätzliche Rechner- oder Dienstlast beeinflussen. Der Name ist optional und später änderbar.",
  },
  settings: {
    title: "Modelleinstellungen",
    text: "Empfohlene Startwerte sind vorbelegt und können überschrieben werden. Änderungen gelten für den nächsten Lauf; bestehende Ergebnisse behalten ihre Konfiguration. „Abbrechen“ verwirft Änderungen im Dialog.",
  },
  "synthetic-data": {
    title: "Synthetischer Datensatz",
    text: "Kontrollierter synthetischer Test. Varianten derselben Basisgenerierung sind voneinander abhängig. Referenzmarken stammen aus TTS-Zeitmarken und Sampleverschiebung, nicht aus menschlicher Annotation. Die Ergebnisse beschreiben diesen Datensatz; die Variantenzahl entspricht nicht der Zahl unabhängiger Äußerungen.",
  },
  outcomes: {
    title: "Ergebniskategorien",
    text: "Zu früh: Entscheidung vor dem Referenzende. Im Zeitfenster: Entscheidung zwischen Referenzende und gewählter Grenze. Verzögert: Entscheidung nach dieser Grenze.\n\nTechnische Fehler und fehlende Entscheidungen bilden eine eigene Kategorie und werden nicht als Erfolg gezählt. Zeitabweichung = Entscheidung minus Referenzende. Negative Werte beschreiben die Zeit bis zum Ende des ganzen Beitrags, nicht nur die Restdauer einer einzelnen Pause.",
  },
  timely: {
    title: "Zeitfenster zur Darstellung",
    text: "Standard: 0–1600 ms ab Referenzende. Das ist das gewählte Bewertungsfenster der Auswertung und kein universeller Qualitätsstandard.\n\nDie Grenze verändert Kategorien und Grafiken, aber keine gespeicherten Modellentscheidungen oder Parameter. Vorzeitige Abschlüsse bleiben bei jeder Fenstergröße Fehler. Das gewählte Fenster wird in die Exporte übernommen.",
  },
  statistics: {
    title: "Kennzahlen lesen",
    text: "Der Nenner umfasst alle beobachteten Beiträge eines Betriebspunkts. Ø Abweichung: mittlere Entscheidung minus Referenzende über gültige Entscheidungen, einschließlich vorzeitiger Abschlüsse. Negative und positive Werte können sich dabei aufheben.\n\nZu früh: mittlerer und medianer Abstand vorzeitiger Entscheidungen zum Referenzende. Wartezeit: Verzögerung ausschließlich gültiger Entscheidungen ab dem Referenzende, einschließlich verzögerter Abschlüsse. Beide Gruppen haben eigene Fallzahlen; Ausfälle werden aus Zeitstatistiken ausgeschlossen. p95 ist das 95. Perzentil. Timer-Fallbacks werden separat ausgewiesen; bei der Baseline ist der Timer die vorgesehene Methode.",
  },
  chart: {
    title: "Grafik lesen",
    text: "",
  },
  transcript: {
    title: "Text und Pausen",
    text: "Pausenmarkierungen sind anklickbar und springen im Audio zur zugehörigen Zeit. Bei synthetischen Dateien sind die gezielt eingefügten Pausen markiert; zusätzliche natürliche Pausen im Audio sind möglich. Bei menschlichen Aufnahmen stammen die Zeitmarken aus der Annotation.",
  },
  waveform: {
    title: "Markierungen in der Audiospur",
    text: "Farbige Linien zeigen die Endentscheidungen der Modelle; die gestrichelte Linie markiert das Referenzende. Beschriftungen und Legende sind anklickbar. Auch ein Klick auf die Wellenform setzt die Abspielposition.\n\nZeitpunkte gelten ab Replaystart. Der Sprung im Audio entspricht dieser Zeit näherungsweise. Entscheidungen außerhalb der Audiospur sind in der Legende gekennzeichnet.",
  },
  timeline: {
    title: "Endentscheidungen vergleichen",
    text: "Jede Zeile zeigt ein Verfahren mit derselben Zeitachse. Die senkrechte Linie ist das Referenzende; die farbigen Punkte sind die Endentscheidungen. Negative Abstände sind zu früh, positive sind zusätzliche Wartezeit.\n\nBei technischen Ausfällen zählt eine eventuell gespeicherte Entscheidung nicht als gültiger Erfolg. Marker sind anklickbar und springen ungefähr zur entsprechenden Replay-Zeit im Audio.",
  },
  "recording-task": {
    title: "Aufnahmehinweise",
    text: "Lies den Sprechtext der Karte wortgetreu. Beachte Tempo, Betonung und Pausenziele; Regieanweisungen nicht mitsprechen. Der optionale visuelle Pausentimer hilft beim Einhalten der Zielpause. Klicke erst nach dem letzten Laut des gesamten Beitrags auf „Beitrag fertig“. Danach werden sechs Sekunden Raumton aufgezeichnet; bitte dabei ruhig bleiben.",
  },
  annotation: {
    title: "Referenzende annotieren",
    text: "Gold-Ende ist das Ende des letzten gesprochenen Lauts. Der Klick auf „Beitrag fertig“ ist keine Gold-Marke. Mindestens sechs Sekunden Nachlauf müssen übrig bleiben. Die Annotation erfolgt ohne Modellvorhersagen.",
  },
  rename: {
    title: "Evaluationsname",
    text: "Der Name ändert die Bezeichnung. Messdaten, Audiodateien und gespeicherte Einstellungen bleiben erhalten. Bis zu 120 Zeichen sind möglich.",
  },
  "model-baseline": {
    title: "Silero VAD + Stille-Timeout",
    text: "Die Baseline beendet den Beitrag nach der gewählten Stilledauer. Mehrere Werte erzeugen getrennte Vergleichsbedingungen.\n\nStartwerte der Studie: 500, 1000 und 1500 ms. Der gemeinsame Silero-Sprachaktivitätsschwellwert steht unter Messbedingungen.",
    links: [],
  },
  "model-livekit": {
    title: "LiveKit Audio Turn Detector",
    text: "Die automatische Schwelle kommt aus dem SDK bzw. der Cloud-Sitzung und wird je Score protokolliert. Höhere Werte machen den Detektor geduldiger. Cloud v1 benötigt Echtzeitmodus und lokale Projektzugangsdaten.",
    links: [
      {
        url: "https://docs.livekit.io/agents/logic/turns/turn-detector/",
        label: "Modell- und Parameterdokumentation ↗",
      },
    ],
  },
  "model-scribe": {
    title: "ElevenLabs Scribe v3 Live",
    text: "Startwert 0,9 entsprechend der dokumentierten ElevenLabs-Turn-Prediction-Schwelle. Höhere Werte machen das Verfahren geduldiger.\n\nWir verwenden die laufenden Turn-Scores mit unserer gemeinsamen VAD-, Mindestpausen- und Timer-Regel. Der API-Modus ist deshalb „manual“; es gibt keinen zusätzlichen Provider-Stille-Timer. Streaming-Scores treffen im Rhythmus des Anbieters ein, unabhängig vom Prüfintervall der anderen Modelle.\n\nNutzt euren ElevenLabs-Schlüssel und den konfigurierten EU-Endpunkt. Nur Echtzeit; STT wird nach übertragenem Audio abgerechnet. Der Dienst puffert laut Dokumentation anfangs ungefähr zwei Sekunden Audio. Endpointing-Zeiten enthalten diese Verzögerung und das Netzwerk. Die Sitzungsöffnung vor dem Replay wird separat protokolliert.",
    links: [
      {
        url: "https://elevenlabs.io/docs/eleven-api/guides/how-to/speech-to-text/realtime/transcripts-and-commit-strategies",
        label: "Turn Prediction und Commit-Strategien ↗",
      },
    ],
  },
  "model-shared": {
    title: "Gemeinsame Messbedingungen",
    text: "Dieselben VAD- und Replay-Einstellungen gelten für alle ausgewählten Modelle. So bleibt die äußere Entscheidungslogik vergleichbar.\n\nDie Startwerte sind 300 ms Mindestpause und 5000 ms maximale Stille bis zum Timer-Fallback. Der spätere Fallback gibt den semantischen Modellen mehr Zeit für eine eigene Entscheidung. Prüfintervall, Baseline-Zeiten und die gemeinsame VAD-Regel gehören zum Versuchsaufbau; sie sind kein universell bester Betriebspunkt.",
    links: [],
  },
};
const escape = (value) =>
  String(value ?? "").replace(
    /[&<>"']/g,
    (c) =>
      ({ "&": "&amp;", "<": "&lt;", ">": "&gt;", '"': "&quot;", "'": "&#39;" })[
        c
      ],
  );
export function infoButton(topic, extra = "", title = "") {
  const label = title || TOPICS[topic]?.title || "Informationen";
  return `<button type="button" class="info-trigger" data-info-topic="${escape(topic)}" data-info-extra="${escape(extra)}" ${title ? `data-info-title="${escape(title)}"` : ""} aria-label="${escape(label)}: Informationen" title="${escape(label)}"><span aria-hidden="true">i</span></button>`;
}
export function setupInfo() {
  const dialog = document.getElementById("info-dialog");
  document.addEventListener("click", (event) => {
    const button = event.target.closest("[data-info-topic]");
    if (!button) return;
    event.preventDefault();
    const topic = TOPICS[button.dataset.infoTopic] || {
      title: "Informationen",
      text: "",
    };
    document.getElementById("info-dialog-title").textContent =
      button.dataset.infoTitle || topic.title;
    const content = document.getElementById("info-dialog-content");
    content.replaceChildren();
    const text = [topic.text, button.dataset.infoExtra]
      .filter(Boolean)
      .join("\n\n");
    for (const paragraph of text.split(/\n\n+/)) {
      const element = document.createElement("p");
      element.textContent = paragraph;
      content.append(element);
    }
    const links = document.getElementById("info-dialog-links");
    links.replaceChildren();
    for (const source of topic.links || []) {
      const anchor = document.createElement("a");
      anchor.href = source.url;
      anchor.textContent = source.label;
      anchor.target = "_blank";
      anchor.rel = "noreferrer";
      links.append(anchor);
    }
    dialog.showModal();
  });
  document.getElementById("info-dialog-close").onclick = () => dialog.close();
  document.addEventListener(
    "keydown",
    (event) => {
      if (event.key === "Escape" && dialog.open) {
        event.preventDefault();
        event.stopImmediatePropagation();
        dialog.close();
      }
    },
    true,
  );
  dialog.addEventListener("cancel", (event) => {
    event.preventDefault();
    dialog.close();
  });
  dialog.addEventListener("click", (event) => {
    const bounds = dialog.getBoundingClientRect();
    if (
      event.target === dialog &&
      (event.clientX < bounds.left ||
        event.clientX > bounds.right ||
        event.clientY < bounds.top ||
        event.clientY > bounds.bottom)
    )
      dialog.close();
  });
  window.addEventListener("hashchange", () => dialog.close());
}
