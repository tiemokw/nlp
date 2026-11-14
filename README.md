# EOT Lab

Lokaler Forschungsprototyp zur Erhebung und Evaluation von **25 Szenarien aus zwei
Stimmquellen**: 25 eigene Aufnahmen des Autors und dieselben 25 Beiträge von einer
weiblichen ElevenLabs-Stimme. Der gemeinsame Datensatz umfasst **50 Samples**.

## Den Studiendatensatz erstellen

1. **Datensatz** zeigt alle 25 Paare und den Fortschritt je Stimmquelle. Sechs
   Inhaltsarten × vier Sprechverläufe ergeben 24 Szenarien. Eine zusätzliche IBAN
   mit 3,5 Sekunden Suchpause ergänzt sie auf 25.
2. Unter **Selbst aufnehmen** jede Karte wortgetreu lesen. Die Karte enthält
   Sprechtext, Tempo, Betonung und Pausenlänge. Regieanweisungen nicht mitsprechen.
   Ein optionaler visueller Pausentimer hilft beim Einhalten der Zielpause.
   Nach dem letzten Laut **Beitrag fertig** wählen und sechs Sekunden ruhig bleiben.
   Aufnahme anhören und **Speichern & übernehmen** wählen; die nächste Karte folgt.
3. Unter **ElevenLabs** die **Stimmen laden**, eine weibliche, deutschsprachig
   geeignete Stimme auswählen und die kostenlose **Vorschau berechnen**. Fehlt das
   Geschlechtslabel beim Anbieter, die weibliche Stimme ausdrücklich bestätigen.
   **25 Beispiele mit ElevenLabs erzeugen** startet die TTS-Anfragen.
4. Unter **Referenzenden** jede eigene und synthetische Datei vollständig anhören.
   Die Abspielposition in der Wellenform setzen und **Abspielposition als Gold-Ende**
   wählen. Anschließend das Transkript prüfen und **Speichern** wählen. **Speichern & nächstes offenes Ende** führt
   durch die noch offenen Dateien. Ein TTS-Endvorschlag zählt noch nicht als
   manuell bestätigtes Referenzende. Bei Nachträgen zählt das Ende des Nachtrags.
5. Unter **Datensatz** den gemeinsamen Stand abschließen, sobald 25 vollständige
   Paare und 50 bestätigte Referenzenden vorhanden sind. Der ZIP-Export enthält
   50 WAV-Dateien, Manifest, Szenarien, eine Annotationstabelle und TTS-Basisantworten.

Inhaltsarten: Kundennummer, IBAN, E-Mail, Adresse/Termin, technisches Anliegen und
Vertrag/Rechnung. Sprechverläufe: flüssig, offene Denkpause, Selbstkorrektur und
vollständiger Satz mit Nachtrag. Beide Quellen erhalten dieselben Texte und
Sprechvorgaben. Die menschlichen Pausendauern sind Zielwerte; die synthetischen
Pausen werden anhand von Anbieter-Zeitmarken in leise Zwischenbereiche eingefügt.
Sprachanteile bleiben erhalten. Tempo und Ausdruck werden per TTS-Einstellungen
angenähert; die tatsächliche Sprechweise muss beim Anhören geprüft werden.

Der Bezugstimeout der Aufnahmeplanung beträgt **1000 ms**. Pausen von 1800, 2200
und 3500 ms überschreiten ihn. Die Evaluation speichert ihre tatsächlich gewählten
Timeouts separat. Neue Evaluationen verarbeiten pro Modell bis zu sechs Aufnahmen
gleichzeitig, jede weiterhin in Echtzeit. VAD und Modellzustand sind je Worker
getrennt. Die Parallelität wird mitgespeichert; zusätzliche Rechner- und Dienstlast
kann die gemessenen Latenzen beeinflussen. Über die API lässt sich mit
`config.parallelism=1` weiterhin seriell messen (zulässig: 1–6). Jede Evaluation verwendet den gesamten gewählten Datensatz
und läuft in Echtzeit. Modelle und Einstellungen werden beim Start automatisch
mit dem Lauf gespeichert; eine manuelle Konfigurationsfreigabe ist nicht erforderlich. Der Aufbau koppelt Stimmidentität und natürliche bzw.
synthetische Entstehung; die 50 Dateien bilden 25 Szenarienpaare.

Der [Umsetzungsplan und die Bedienanleitung](docs/DATENSATZ_25_PLAN.md) beschreiben
das Vorgehen. Der versionierte gemeinsame Katalog steht in [app/study.py](app/study.py).
Vorhandene Altaufnahmen, Pilotdatensätze und Evaluationen bleiben erhalten.
Die früheren Pilot-/Benchmark-Varianten sind weiterhin über die API verfügbar.

**ElevenLabs-Zugang:** `ELEVENLABS_API_KEY` lokal in der ignorierten `.env`
hinterlegen. Für EU Data Residency zusätzlich
`ELEVENLABS_BASE_URL=https://api.eu.residency.elevenlabs.io` setzen. Die API benötigt
TTS- und Stimmen-Leserechte. Der Schlüssel wird nicht im Browser gespeichert.
Die Oberfläche zeigt den aktiven Endpunkt. Erfolgreiche Basisantworten werden
gecacht; nach Fehlern erfolgt kein automatischer kostenpflichtiger Neuversuch.
Ein erneuter Start mit denselben Parametern nutzt den Cache. Ein anderer Seed
führt zu neuen Anfragen. Der Seed garantiert beim Anbieter keine identische
Neugenerierung. Die Vorschau nennt Textzeichen, keine verbindliche Credit-Abrechnung.

## Starten

Die projektinterne Python-Umgebung und die Modelle wurden in dieser Arbeitsumgebung bereits vorbereitet:

```sh
./run.sh
```

Danach **http://127.0.0.1:8765** im Browser öffnen. Die Anwendung bindet ausschließlich an die Loopback-Adresse. Ein anderer Port lässt sich beispielsweise mit `PORT=8766 ./run.sh` wählen.

Auf einem neuen Rechner mit [uv](https://docs.astral.sh/uv/) installieren:

```sh
uv sync --extra models --frozen
./run.sh prepare-models
./run.sh doctor
./run.sh
```

Python 3.12 wird benötigt; uv kann eine passende Laufzeit bereitstellen. `uv.lock` hält die aufgelösten Paketversionen fest. Ohne die optionalen `models`-Abhängigkeiten funktionieren Verwaltung, Aufnahme und Annotation, aber keine echten Modellvergleiche. Es gibt keinen automatischen Ersatz durch einen simulierten Detektor.

## Was implementiert ist

- **25 Studienkarten:** sechs Inhaltsarten × vier Sprechverläufe plus ein zusätzlicher IBAN-Fall; derselbe Katalog für beide Quellen.
- **Browseraufnahme:** Mikrofon, Pegelanzeige, WAV, sechs Sekunden samplegezählter Nachlauf und lokale Sicherung bei Uploadfehlern.
- **Versuche:** Original und 16-kHz-Mono-Arbeitskopie, Prüfsummen, begründete Wiederholungen und genau eine ausgewählte Aufnahme je Karte.
- **Annotation:** Audioplayer, Wellenform mit Zoom, Gold-Ende, HOLD-Pausen, Mehrdeutigkeit, Transkript und Gegenprüfung als neue Revision.
- **Datensatzstände:** gemeinsamer Stand mit genau 25 Paaren und 50 manuell bestätigten Referenzenden; unveränderlicher ZIP-Export mit WAV, Manifest und Annotationstabelle. Ältere Pilotstände bleiben verfügbar.
- **Verfahren in der Oberfläche:** Silero VAD mit Stille-Timeouts, LiveKit und ElevenLabs Scribe v3 Live. Drei Modellkarten nebeneinander; Smart Turn wird nur noch für historische Läufe und die CLI unterstützt.
- **Evaluation:** gesamter gewählter Datensatz, immer Echtzeit, kausaler Replay, Umgang mit veralteten Scores und erste wirksame Commit-Entscheidung. Historische Offline-Läufe bleiben lesbar.
- **Auswertung:** Abbruchrate, Median/p95 der Endpointing-Latenz, Fallbacks, Ausfälle, gepaarte Latenzen, Fallansicht, Rohereignisse, CSV und PNG.
- **Reproduzierbarkeit:** versionierte Datenstände sowie automatisch gespeicherte Einstellungen, Paket-, Modell- und Hardwaremetadaten je Lauf.

## Texte, Pausen und Modelleinstellungen

Die Beispielsätze stehen unter **Erzeugen** mit sichtbaren Pausenmarkierungen. Bei **Anhören** zeigt jede erzeugte Datei ihren gesprochenen Text und die Dauer der eingefügten Pausen. Ein Klick auf eine Pausenmarkierung springt im Audioplayer zur zugehörigen Zeit. Diese Markierungen beschreiben die gezielt eingesetzte Stille; zusätzliche natürliche Pausen im TTS-Audio sind möglich. Derselbe Text erscheint in **Evaluation starten** beim ausgewählten Ergebnisbeitrag zusammen mit Audio und Wellenform. Dabei wird der Text aus dem ausgewerteten Datensatzstand verwendet, auch wenn später Annotationen geändert wurden.

Die Vergleichsansicht zeigt Datensatz, Modellkarten und Laufstart. Jede Modellkarte öffnet **Einstellungen** im Dialog. Dort können Parameter geändert, verworfen oder auf Startwerte zurückgesetzt werden. Die beim Start gespeicherten Einstellungen erscheinen im jeweiligen Ergebnis. Gemeinsame VAD- und Replay-Parameter bleiben für die Verfahren identisch.

Neue Vergleiche verwenden bei LiveKit automatisch die vom SDK beziehungsweise Cloud-Dienst bereitgestellte kalibrierte Schwelle für Deutsch; eine numerische Überschreibung ist möglich. Die tatsächliche Schwelle wird je Score in `events.jsonl` protokolliert. Smart Turn startet mit 0,5 entsprechend der Referenzinferenz. Gemeinsame Mindestpause und maximale Stille bis zum Timer-Fallback sind jetzt 300/5000 ms. Der spätere Fallback gibt den semantischen Modellen mehr Zeit für eine eigene Entscheidung; das Prüfintervall bleibt 100 ms und die Silero-Schwelle 0,5. Die drei Baseline-Zeiten 500/1000/1500 ms sind Betriebspunkte des Versuchs. Das sind dokumentierte Startwerte, keine Garantie einer optimalen Einstellung. Bestehende Läufe und gespeicherte Konfigurationen behalten ihre expliziten Werte; für Messungen mit dem neuen Fallback ist ein neuer Lauf erforderlich.

Quellen: [LiveKit-Schwellen und Endpointing](https://docs.livekit.io/agents/logic/turns/turn-detector/), [Smart-Turn-Referenzinferenz](https://github.com/pipecat-ai/smart-turn/blob/main/inference.py).

## Kompakte Oberfläche

Erklärungen, Modellhinweise, Quellen und Messdefinitionen sind über die einheitlichen **i-Schaltflächen** erreichbar. Der Info-Dialog lässt sich über Schließen, Escape oder einen Klick außerhalb schließen; er ist auch aus dem Einstellungsdialog heraus verwendbar. Wichtige Fehler, Datenquelle, Parameterwerte und Messergebnisse bleiben sichtbar. Positive Rückmeldungen verschwinden nach fünf Sekunden, Fehlermeldungen bleiben bis zum Schließen erhalten.

Unter **Erzeugen** liegen TTS-Modell und Seed hinter **Weitere Einstellungen**. In den Ergebnissen ist das **Zeitfenster** einklappbar. Text, Pausen, Wellenform, EOT-Linien und Modellvergleich bleiben direkt zugänglich. Diese Änderungen betreffen ausschließlich die Darstellung; Modellparameter, Daten und wissenschaftliche Exporte werden dadurch nicht verändert.

## Evaluationen verwalten und Ergebnisse verwenden

**Evaluation starten** enthält nur Datensatz, Modellwahl, Einstellungen und Start. Ein optionaler Name (maximal 120 Zeichen) wird mit dem Lauf gespeichert. Die separate Seite **Ergebnisse** listet alle Evaluationen mit Modell-Tags, Datum, Status und Umfang. Suche sowie Status- und Modellfilter erleichtern das Wiederfinden. **Umbenennen** ist auch für bestehende Läufe möglich. Namen werden unabhängig von Worker-Fortschritt gespeichert; eine Umbenennung ändert keine Messwerte oder eingefrorenen Einstellungen.

Unter **Ergebnisse → Läufe kombinieren** lässt sich jede Modellzeile aus einem anderen abgeschlossenen Lauf auswählen. Die Anwendung prüft identische Audiodateien, Referenzenden, vollständige Betriebspunkte und denselben Zeitmodus. Ergebnisse derselben Aufnahme werden je ausgewähltem Betriebspunkt einmal gezählt. So können beispielsweise Silero aus Final 001, LiveKit aus Final 002 und Scribe aus Final 004 gemeinsam dargestellt werden. Die Einzelfallansicht verwendet ebenfalls diese Auswahl. Der Link zur Auswahl und die zuletzt verwendete Auswahl im Browser ermöglichen das Wiederöffnen. Der ZIP-Export enthält Herkunft, Konfigurationen, Kennzahlen, Einzelwerte und PNG-/SVG-Abbildungen.

Das Bewertungsfenster ist standardmäßig **0–1600 ms** ab Referenzende, sowohl für einzelne Läufe als auch für kombinierte Vergleiche und Grafikexporte. Die Grenze ändert keine gespeicherten Endentscheidungen. Die Kennzahlentabelle zeigt alle vier Ergebniskategorien, die mittlere vorzeichenbehaftete Abweichung über gültige Entscheidungen, den mittleren und medianen Vorlauf vorzeitiger Abschlüsse sowie Median/p95 der Wartezeit gültiger Entscheidungen ab dem Referenzende. Technische Ausfälle bleiben im Gesamtumfang, sind aber aus Zeitstatistiken ausgeschlossen.

Jede Evaluation hat eine eigene, direkt verlinkbare Detailansicht mit vier Bereichen:

- **Überblick:** ausschließende Kategorien „zu früh“, „im Zeitfenster“, „verzögert“ und „Ausfall/kein Ende“, Kennzahlentabelle und Fehlerraten nach Falltyp.
- **Zeitverhalten:** vorzeichenbehaftete Einzelentscheidungen relativ zum Referenzende und separate Wartezeitverteilungen ausschließlich korrekt beendeter Beiträge. Der zusätzliche Trade-off-Plot verwendet eine externe Legende statt sich überlappender Datenbeschriftungen.
- **Einzelfälle:** Filter nach Ergebnis und Verfahren, Text mit Pausen, Audio, Wellenform und eine eigene Zeitachsenzeile je Verfahren. Ein negativer Abstand beschreibt die Zeit bis zum tatsächlichen Ende des ganzen Beitrags, nicht die Restdauer einer einzelnen Pause.
- **Versuchsaufbau:** Messdefinitionen, gespeicherte Einstellungen, Datenquelle und Rohkonfiguration.

Das standardmäßige **Zeitfenster 0–500 ms** ist eine ausdrücklich veränderbare Darstellungshilfe, kein behaupteter universeller Qualitätsstandard. Die Einstellung verändert weder Entscheidungen noch Modellparameter. Vorzeitige Abschlüsse bleiben bei jeder Fenstergröße Fehler. Ein technischer Fehler hat bei der Kategorisierung Vorrang vor einem eventuell trotzdem gespeicherten Commit; fehlende Entscheidungen werden ebenfalls als Ausfall gezählt. Nenner sind jeweils alle beobachteten Beiträge des Betriebspunkts. Verzögerungsstatistiken schließen vorzeitige Abschlüsse und technische Ausfälle aus und nennen ihre eigene Fallzahl. Ein Fallfilter „mindestens ein Verfahren“ zeigt Beiträge, bei denen wenigstens ein Verfahren die gewählte Kategorie hat.

Alle Diagramme lassen sich vergrößern und als **PNG (200 dpi) oder SVG** herunterladen. SVG enthält editierbaren Text. Der ZIP-Export enthält zusätzlich die aktuellen Grafiken unter `figures/`, `analysis.json`, `analysis_per_turn.csv` mit `delta_ms` und Ergebnis-Kategorie sowie den aktuellen Anzeigenamen in `display_metadata.json`. Die ursprünglichen Messdateien bleiben zusätzlich erhalten. Das gewählte Zeitfenster wird im Export mitgeführt. Alte Läufe werden aus ihren gespeicherten Einzelmessungen neu visualisiert; es ist keine erneute Modellabfrage nötig.

Die Boxplots der Wartezeit zeigen Quartile, Median und Whisker nach der üblichen 1,5-IQR-Regel; Einzelpunkte zeigen alle gültigen Beobachtungen einschließlich Ausreißern. Die Diagramme sind deskriptiv und enthalten keine behaupteten Konfidenzintervalle. Synthetische Varianten werden im Diagramm als solche mit ihrer Zahl an Basisdateien gekennzeichnet.

## Historischer Pilot mit Mikrofonaufnahme (API / Altbestände)

Die folgenden Abschnitte beschreiben den früheren Fünf-Personen-Pilot. Seine Daten und API-Endpunkte bleiben erhalten; die aktuelle Oberfläche führt durch die 25-Paare-Studie.

1. Über die API die Karten von P01 laden. Eine Karte lesen, ohne die Regieanweisungen mitzusprechen.
2. Aufnahme starten, den Beitrag sprechen und **Beitrag fertig** drücken. Während der sechs Sekunden Nachlauf ruhig bleiben.
3. Anhören und **Speichern & übernehmen** wählen. Der Versuch wird bereits nach Ende der Aufnahme als noch nicht ausgewählter Versuch gespeichert; die Übernahme trifft die Datensatzauswahl.
4. In **Annotieren** die Aufnahme auswählen. Den letzten gesprochenen Laut anhören und seine Position als Gold-Ende markieren. Der Fertig-Klick ist ausdrücklich keine Gold-Marke.
5. Interne Pausen mit HOLD-Anfang und HOLD-Ende markieren, Transkript und Annotatorkennung eintragen und speichern.
6. In **Evaluation starten** einen **Entwicklungsstand erstellen**. Auch ein einzelner Beitrag von P01 genügt für den technischen Pilot.
7. Modelle und Stillezeiten auswählen. Mit **Offline** lässt sich die Pipeline schnell prüfen; für tatsächliche Endpointing-Latenzen **Echtzeit (1×)** verwenden.
8. Den Vergleich starten, den Lauf ansehen und Ergebnisse oder Rohprotokolle exportieren.

Pilotaufnahmen nicht als Hauptkorpus weiterverwenden. Für vollständig getrennte Pilotdaten die Anwendung mit einer anderen Ablage starten:

```sh
EOT_DATA_DIR="$PWD/pilot-data" ./run.sh
```

Die Smart-Turn-Gewichte werden je Ablage mit `EOT_DATA_DIR="$PWD/pilot-data" ./run.sh prepare-models` vorbereitet. Eine andere Ablage hat eine eigene Datenbank.

## Optional: Menschliche Aufnahmen

Die vorbereiteten Kennungen sind P01 bis P05. P01 ist der Entwicklungssprecher mit 20 Beiträgen; P02–P05 bilden 80 Testbeiträge. Dieser Split ist absichtlich nicht nachträglich über die Oberfläche austauschbar.

Inhaltsarten sind Kundennummer, E-Mail, Adresse/Termin, technisches Anliegen und Vertrag/Rechnung. Die vier Sprechverläufe sind flüssig abgeschlossen, sprachlich offen mit Denkpause, vollständiger Satz mit Nachtrag sowie Stocken/Korrektur.

Die Karten liefern personenabhängige Situationen und fiktive Angaben statt einheitlicher Vorlesesätze. Sie teilen bewusst dieselben Aufgabenkategorien. Vor der Hauptaufnahme sollten die Aufgaben mit den Beteiligten durchgesehen werden; sie sollen ihre eigenen Formulierungen verwenden. Die kleine Studie bewertet diese Aufgabenfamilien, keine allgemeine Generalisierung über beliebige Domänen.

Nach einer Gegenprüfung die entsprechende Aufnahme mit einer anderen Prüferkennung erneut als **gegengeprüft** speichern (Schaltfläche: „Als gegengeprüft speichern“). Die aktuelle Revision muss mindestens bei 20 Beiträgen diesen Status haben. Danach kann der finale Stand erstellt werden.

Für den abschließenden Test:

1. Datensatz auswählen.
2. Modelle und Einstellungen festlegen.
3. Optional einen Namen vergeben und **Evaluation starten** wählen.

Der vollständige Datensatz wird in Echtzeit ausgewertet. Die Einstellungen werden automatisch gespeichert.

Technische Prüfung, Gegenprüferkennungen und das Festschreiben werden lokal dokumentiert. Die Anwendung authentifiziert keine verschiedenen Personen; die korrekte unabhängige Gegenprüfung ist Teil der Versuchsdurchführung.

## Modelle und Zugänge

Der Standardvergleich verwendet **LiveKit v1 Cloud**. In der lokalen, ignorierten `.env` folgende Variablen ergänzen:

```dotenv
LIVEKIT_API_KEY=
LIVEKIT_API_SECRET=
```

Hier die Zugangsdaten eines LiveKit-Cloud-Projekts mit Inference-Zugriff eintragen. Danach im Bereich **Evaluation starten** auf **Status aktualisieren** klicken; ein Neustart ist nicht erforderlich. Eine konfigurierte Verbindung wird erst beim Lauf tatsächlich authentifiziert. Die Schlüssel bleiben auf dem lokalen Server und werden nicht in Messkonfigurationen oder Exporte geschrieben. Die Audiodaten werden für diese Vergleichsbedingung an LiveKit übertragen. Die Nutzung kann abhängig von Konto und Kontingent kostenpflichtig sein; mehrere Score-Abfragen innerhalb eines Beitrags sind mehrere Anfragen.

Der Inference-Endpunkt ist standardmäßig `https://agent-gateway.livekit.cloud/v1`. Optional lässt er sich mit `LIVEKIT_INFERENCE_URL` überschreiben. Die Room-URL wird hierfür nicht benötigt. Für einen Vergleich ohne LiveKit-Zugang im Dropdown **LiveKit v1-mini lokal** wählen; diese Variante erlaubt auch den Offline-Modus.

| Verfahren | Ausführung und Herkunft |
|---|---|
| Silero VAD | Paket `silero-vad`, ONNX auf CPU; anschließender Stille-Timer ist eigene Entscheidungsregel. |
| LiveKit v1 Cloud (Standard) | Öffentliche Agents-SDK-Schnittstelle `TurnDetector(version="v1", local_fallback=False)` mit eigenem Inference-Stream und fortlaufenden freigegebenen Audioframes. Nur Echtzeitmodus. |
| LiveKit v1-mini | Öffentliche `livekit.agents.inference.TurnDetector`-Schnittstelle des Agents-Frameworks mit lokalem Backend. Das native Fenster umfasst **1,2 Sekunden** bei 16 kHz. |
| Smart Turn v3.2 CPU | Datei `smart-turn-v3.2-cpu.onnx` von `pipecat-ai/smart-turn-v3`, **8 Sekunden** Kontext. Hugging-Face-Revision und Gewichte-Hash werden beim Vorbereiten gespeichert. |

Die unterschiedlichen nativen Audiofenster gehören zum Systemvergleich. Insbesondere hat LiveKit mini hier keinen vollständigen Dialogverlauf. Aus dem Ergebnis lässt sich deshalb kein isolierter Einfluss von Textsemantik ableiten. Der gemeinsame äußere Replay und die Entscheidungsregeln werden einheitlich verwendet.

Modellgewichte werden nicht in den Quellcode kopiert. Smart Turn ist unter BSD-2-Clause veröffentlicht; LiveKit verwendet eine eigene Modelllizenz. Beim lokalen LiveKit wird der Hash der nativen Bibliothek samt Paketversion protokolliert. Beim Cloud-Modell werden Modellkennung, SDK-Version und Endpunkt gespeichert. Die Revision der entfernten Gewichte legt der Anbieter nicht offen; sie kann deshalb nicht lokal eingefroren werden. Laufdatum und Anbieteränderungen begrenzen die Reproduzierbarkeit.

Cloud v1 und lokales mini werden im Ergebnis ausdrücklich getrennt benannt. Automatischer Modell-Fallback ist für Cloud deaktiviert; Ersatzmodelle und SDK-Standardantworten nach Ausfällen werden als technische Fehler gewertet. Ein maximaler Stille-Timeout bleibt eine getrennte Entscheidungsregel des Versuchs. Alte gespeicherte Konfigurationen ohne Varianteneintrag bleiben mini zugeordnet. Nach Adapteränderungen muss eine zuvor eingefrorene Konfiguration neu festgelegt werden.

ElevenLabs-TTS benötigt für die Datenerzeugung weiterhin seinen eigenen API-Schlüssel. Die frühere direkte native LiveKit-Einbindung wurde durch das Agents-Framework ersetzt; ältere Messungen dieser Integration sind getrennt zu betrachten. Der Adapter berücksichtigt den SDK-Audioeingang mit einer kurzen Scheduling-Pause; diese ist in der gemessenen Verarbeitungszeit enthalten.

## Zeitmessung und Grenzen

### Optional: ElevenLabs Scribe v3 Live

Unter **Evaluation starten** ist Scribe v3 Live als viertes Verfahren verfügbar und zunächst abgewählt. Es verwendet denselben lokalen ElevenLabs-Schlüssel und `ELEVENLABS_BASE_URL` wie die TTS-Erzeugung; der Schlüssel braucht zusätzlich Speech-to-Text-Zugriff. Der bestehende EU-Zugang wurde am 12. November 2026 geprüft: Sitzung mit `scribe_v3_live` bestätigt, anschließend wurden beim ausdrücklich freigegebenen Test von acht Sekunden eines nachweislich synthetischen Pilotclips 25 echte `turn_probability`-Werte empfangen. Das bestätigt die Funktion, keine allgemeine Erkennungsqualität.

Im Einstellungsdialog steht die Turn-Schwelle standardmäßig auf 0,9. Unsere Integration nutzt die **manuelle Commit-Strategie** und wertet ausschließlich die semantischen Scores der partiellen Transkripte aus. Sie sendet selbst keine Commits. Die gemeinsame Silero-VAD-Regel sowie Mindestpause und maximaler Timer bestimmen die wirksame Endentscheidung. Dadurch gibt es keinen zusätzlichen, verdeckten Anbieter-Stille-Timeout. Das ist ein **Systemvergleich mit eigener Endpointing-Regel**, keine Messung des vollständigen ElevenAgents-Verhaltens und auch kein Nachbau der automatischen Anbieterstrategie.

Der Dienst bekommt ausschließlich bereits im Echtzeit-Replay freigegebene Audiosamples, in Paketen von 2048 Samples (128 ms). Vollständige Referenztranskripte, Szenariokarten und zukünftige Samples werden nicht übermittelt. Er empfängt einen neuen Stream pro Aufnahme. Die anfängliche Audiopufferung des Dienstes (laut Dokumentation ungefähr zwei Sekunden), Übertragung und die tatsächliche Verfügbarkeit von Scores sind in der Endpointing-Latenz enthalten. Das vor dem Replay erfolgende Öffnen der Verbindung wird je Sitzung separat gespeichert. Das lokale Prüfintervall anderer Detektoren steuert nicht die Ausgabehäufigkeit des Streaming-Dienstes.

Nur während der aktuellen VAD-Pause eingegangene Scores dürfen eine Entscheidung auslösen; bei neuer Sprache wird der bisherige Score verworfen. `stream_score`-Ereignisse protokollieren empfangenen Text, Score, Schwelle, tatsächliche Verfügbarkeit und den beobachteten Replay-Zeitpunkt. Der Stand gesendeter Samples ist lediglich eine **Obergrenze**, weil die API keinen exakten verarbeiteten Audiocursor zurückgibt. Segment-Commits allein werden nicht als Turn-Ende interpretiert. Fehlende Turn-Scores und Dienstfehler werden als technische Ausfälle erfasst; es gibt keinen automatischen Anbieter- oder Modellwechsel.

Für einen laufenden STT-Stream gibt es keine vergleichbare Inferenzdauer pro Einzelaufruf. In der entsprechenden Ergebnisspalte steht deshalb „–“, nicht 0 ms. Der Dienst läuft ausschließlich im Echtzeitmodus und wird nach übertragenem Audio abgerechnet. Ein Vergleichslauf mit ausgewähltem Scribe überträgt die ausgewählten Audiodateien an den konfigurierten ElevenLabs-Endpunkt. Entfernte Modellrevisionen lassen sich nicht lokal einfrieren.

Quellen: [Realtime API](https://elevenlabs.io/docs/api-reference/speech-to-text/v-1-speech-to-text-realtime), [Turn Prediction und Commit-Strategien](https://elevenlabs.io/docs/eleven-api/guides/how-to/speech-to-text/realtime/transcripts-and-commit-strategies), [EU Data Residency](https://elevenlabs.io/docs/overview/administration/data-residency).

### Gemeinsame Zeitmessung

- Modelle bekommen nur ein bereits verfügbares Audiopräfix, keine Gold-Labels, Szenariotexte oder Dateigesamtdauer.
- Gemeinsames VAD verarbeitet Frames von 512 Samples (32 ms). Entscheidungen haben daher mindestens diese zeitliche Granularität; Scheduler- und Inferenzzeiten kommen hinzu.
- Im Echtzeitmodus wird ein Score erst nach Rückgabe wirksam. Veraltete Scores nach erneut erkannter Sprache werden verworfen. Audiofreigabe und semantische Inferenz laufen getrennt.
- Im Offline-Modus werden Modellberechnungen ausgeführt, aber die Commit-Zeiten auf einer virtuellen Audiozeitachse ausgewertet. Die Ergebnistabelle und die Abbildung kennzeichnen diesen Modus.
- Cloud v1 ist nur in Echtzeit zugelassen. Seine gemessene Aufrufdauer (`service_roundtrip`) umfasst Adapter, Netzwerk und Dienstverarbeitung. Der vom SDK gelieferte Server-E2E-Wert wird zusätzlich exportiert; er ist keine isolierte GPU-Rechenzeit. Lokale Adapterlaufzeiten und Cloud-Aufrufdauern sind entsprechend zu beschriften. Endpointing-Latenz umfasst bei Cloud die tatsächlich wirksame Netzwerkverzögerung.
- Negative Latenzen werden nicht als besonders gute Ergebnisse gewertet. Fehlende Entscheidungen und technische Fehler werden separat gezählt. Die Latenzen erfolgreich beendeter Beiträge sind immer zusammen mit der Abbruchrate zu lesen.
- Die gepaarte Latenzauswertung verwendet nur von beiden Verfahren korrekt abgeschlossene Beiträge und nennt deren Anzahl.
- Der Timer-Fallback ist für semantische Verfahren eine eigene Kennzahl. Bei der pausenbasierten Baseline ist der Timer die vorgesehene Methode und kein Fehlerfallback.
- Das System misst Endpointing auf aufgezeichnetem Audio einschließlich eines gewählten Cloud-EOT-Aufrufs, aber keine vollständige Bot-Latenz mit Mikrofon, LLM und Antwort-TTS.

Echte deutschsprachige Hauptaufnahmen und eine empirische Evaluation müssen noch erhoben werden. Technische Testsignale sind kein Nachweis von Erkennungsqualität. Mit zwei Stimmquellen und 25 Szenarienpaaren bleiben Gruppen- und Signifikanzbehauptungen eingeschränkt.

## Ablage und Wiederholung

Standardmäßig liegt die Arbeitsablage in `data/`:

```text
data/lab.sqlite3        Verwaltung, Zuordnungen und Annotationsrevisionen
data/originals/        Erfasste WAV-Dateien
data/canonical/        Gemeinsame 16-kHz-Mono-Dateien
data/models/           Smart-Turn-Datei und Revisionsmetadaten
data/releases/         Unveränderliche Datensatzmanifeste
data/runs/<id>/        Konfiguration, Metadaten und Messergebnisse
```

Ein abgeschlossener Lauf exportiert `events.jsonl`, `per_turn.csv`, `summary.csv`, die Fallgruppen-Tabellen, `report.json`, `manifest.json` und `tradeoff.png`. Unvollständige Läufe tragen einen entsprechenden Status. Ein laufender Vergleich lässt sich abbrechen; ein Serverneustart gibt einen vorher unterbrochenen Lauf nicht als abgeschlossen aus.

Vor größeren Sitzungen die gesamte Ablage sichern, wenn kein Lauf aktiv ist. Die wissenschaftlichen ZIP-Exporte enthalten Arbeitsaudio und Manifest, aber keine vollständige Datenbanksicherung und keine Rohaufnahme-Originale.

CLI zum Ausführen eines neu eingereihten Laufs (wird normalerweise vom Webserver verwendet):

```sh
./run.sh run LAUF_ID
```

Die Lauf-ID muss zur aktiven Datenablage gehören und den Status `queued` besitzen. Für eine Wiederholung über die Oberfläche einen neuen Lauf mit eigener ID anlegen; abgeschlossene Ergebnisse werden nicht überschrieben. Eingefrorene Konfigurationen enthalten auch Bibliotheksversionen und Modellprüfsummen. Eine nachträgliche Änderung führt vor dem Start zum Abbruch statt zu einem stillen Modellwechsel.

## Verifikation

```sh
./run.sh test
.venv/bin/ruff check app eot_eval tests
```

Die Tests prüfen unter anderem Upload-Idempotenz, Auswahl von Wiederholungen, Sample-Zeitachsen, unveränderliche Freigaben, Trennung der Sprecher, Grenzen der Annotation, erste wirksame Commit-Entscheidung, veraltete Scores, kausale Eingaben und korrekte Metriknenner. Sie ersetzen die Generalprobe mit dem tatsächlich verwendeten Mikrofon nicht.

## Planung und Quellen

- [Wissenschaftlicher Projektplan und Fachliteratur](./PROJEKTPLAN_TURN_END_ERKENNUNG.md)
- [Implementierungs- und Aufnahmeplan](./IMPLEMENTIERUNGSPLAN_PROTOTYP_UND_AUDIOAUFNAHMEN.md)
- [LiveKit-Modellschnittstelle und Referenzadapter](https://github.com/livekit/eot-bench)
- [LiveKit-Turn-Detector-Dokumentation: v1 und mini](https://docs.livekit.io/agents/logic/turns/turn-detector/)
- [LiveKit-Anbieterbenchmark: Solving end-of-turn detection](https://livekit.com/blog/solving-end-of-turn-detection)
- [Smart Turn: Architektur und Inferenz](https://github.com/pipecat-ai/smart-turn)
- [Silero VAD](https://github.com/snakers4/silero-vad)

Die Software dokumentiert den tatsächlich getesteten Implementierungsstand. Abweichungen zu den früheren Planungsannahmen, insbesondere das kurze native LiveKit-mini-Audiofenster, sind oben ausdrücklich benannt.
