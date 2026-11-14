# Projektplan zur Seminararbeit

## End-of-Turn Detection in deutschsprachigen Voicebots: Ein empirischer Vergleich semantischer und pausenbasierter Verfahren

**Stand:** 25. Oktober 2026  
**Status:** Ausgearbeiteter Untersuchungsplan. Der Prototyp ist seit dem 12. November 2026 implementiert und technisch geprüft; Hauptdatensatz und wissenschaftliche Messungen stehen noch aus. Bedienung und tatsächliche Modellgrenzen sind in der [README](./README.md) dokumentiert.  
**Umfang der Seminararbeit:** 2.000 Wörter, laut Modulpräsentation maximal 10 % Überschreitung; zusätzlich etwa zehn Minuten Präsentation.  
**Aktueller Kernvergleich:** Silero VAD mit festem Stille-Timeout, LiveKit Turn Detector **v1 Cloud** und Pipecat Smart Turn v3.2. LiveKit mini bleibt eine zusätzliche lokale Option.

**Aktualisierung der Modellwahl (12. November 2026):** Auf Nutzerwunsch ersetzt Cloud v1 die ursprünglich vorgesehene lokale mini-Variante als Standard. Die folgenden Detailabschnitte zur mini-Auswahl dokumentieren den ursprünglichen Plan. Maßgeblich ist die [umgesetzte Modellanbindung](./README.md#modelle-und-zugänge): Cloud nur in Echtzeit, ohne automatischen Modell-Fallback, mit Projektzugang und einschließlich Netzwerk-/Dienstlaufzeit. Die Anbieterbenchmarks motivieren diese Auswahl, ersetzen aber keine eigene Evaluation. Entfernte Gewichte können nicht vollständig versioniert werden.

**Aktualisierung des Erhebungswegs (12. November 2026):** Der Hauptdatensatz soll auf Nutzerwunsch vollständig synthetisch mit ElevenLabs entstehen. Erzeugung, Pausenvariation, Referenzmarken und Import erfolgen automatisch. Die folgenden menschlichen Aufnahme- und Gegenprüfungspläne dokumentieren den ursprünglichen Ansatz und sind für den aktuellen Hauptworkflow nicht erforderlich. Maßgeblich sind die [aktuelle Bedienung und Grenzen der synthetischen Pipeline](./README.md#synthetischen-pilotdatensatz-erzeugen). Der synthetische Benchmark umfasst 100 Varianten aus 25 Basisgenerierungen und wird entsprechend gruppiert ausgewertet.

## 1. Ziel und Gegenstand der Arbeit

Die Arbeit untersucht, wann ein Voicebot einen Nutzerbeitrag als beendet behandeln sollte. Zu frühe Entscheidungen schneiden Äußerungen ab; zu späte Entscheidungen erzeugen Wartezeit. Ein typischer Problemfall ist:

> Meine Kundennummer ist … [Denkpause] … 12345678.

Ein anderer, anspruchsvollerer Fall ist ein bereits vollständiger Satz mit anschließendem Nachtrag:

> Ich möchte meinen Vertrag ändern. [Pause] Und zwar ab nächsten Monat.

Ein semantischer Detektor kann sprachliche und prosodische Hinweise verwenden. Auch er kann die tatsächliche Fortsetzung nicht sicher vorhersagen. Untersucht wird daher ein messbarer Zielkonflikt, keine vorab feststehende Überlegenheit einer Modellklasse.

Die Eigenleistung besteht aus einer reproduzierbaren Evaluationspipeline, einem kleinen annotierten deutschen Audiokorpus und einer begründeten Auswertung. Die Verwendung vortrainierter Modelle genügt dafür; ein eigenes Modelltraining gehört nicht zum Kernumfang.

Die Anforderungen und Themenbeispiele stehen in der [Modulpräsentation](./NLP,%20Textalgorithmen%20und%20Sprachmodelle_WS2026.pdf), insbesondere auf den PDF-Seiten 14–16. Hinweise zur Eingrenzung und wissenschaftlichen Arbeitsweise enthält die [zweite Präsentation](./wissenschaftliche_Recherche_und_Arbeitsweise.pdf), insbesondere die PDF-Seiten 26–30.

### 1.1 Forschungsfrage

**Wie unterscheiden sich semantische und pausenbasierte Verfahren zur End-of-Turn Detection in deutschsprachigen Voicebot-Dialogen hinsichtlich vorzeitiger Turn-Abschlüsse und Erkennungsverzögerung?**

Zwei konkretisierende Auswertungsfragen:

1. Welche Unterschiede zeigen sich bei unvollständigen Äußerungen, vollständigen Sätzen mit Nachtrag und stockenden Zahlenfolgen?
2. Welche Latenz erreichen die Verfahren bei vergleichbarer Rate vorzeitiger Abschlüsse, und welche Rechenzeit benötigen die beiden semantischen Modelle?

### 1.2 Arbeitshypothesen

Die folgenden Erwartungen sind zu prüfen und dürfen durch die Daten widerlegt werden:

- **H1:** Bei gleichem Wartezeitbudget vermeiden semantische Modelle mehr vorzeitige Abschlüsse als eine ausschließlich auf Stilledauer beruhende Entscheidungsregel.
- **H2:** Der mögliche Vorteil hängt vom Falltyp ab. Eine grammatisch vollständige Äußerung mit späterem Nachtrag bleibt auch für semantische Modelle schwierig.
- **H3:** Eine geringere vorzeitige Abbruchrate kann mit höherer Endpointing-Latenz einhergehen. Ein einzelner Accuracy-Wert beschreibt diesen Zielkonflikt unzureichend.

H1 ist eine Arbeitshypothese und kein aus den Herstellerangaben übernommenes Ergebnis. Bei dem kleinen Korpus stehen deskriptive Vergleiche im Vordergrund.

### 1.3 Kurzbeschreibung für Anmeldung oder Exposé

Die Arbeit untersucht die Erkennung abgeschlossener Nutzerbeiträge in deutschsprachigen Voicebot-Dialogen. Ein prototypischer Versuchsaufbau vergleicht zwei vortrainierte semantische Turn-Detektoren mit einer Baseline aus Voice Activity Detection und festen Stille-Timeouts. Die Untersuchung basiert auf ungefähr 100 annotierten Audiobeiträgen mit abgeschlossenen Äußerungen und unterschiedlichen Arten interner Pausen. Bewertet werden vorzeitige Turn-Abschlüsse, Endpointing-Latenz, die Nutzung eines maximalen Wartezeit-Fallbacks und die Inferenzzeit. Ziel ist es, den Zielkonflikt zwischen schnellen Entscheidungen und dem Vermeiden vorzeitiger Unterbrechungen unter kontrollierten Bedingungen zu beschreiben.

## 2. Begriffe und fachliche Abgrenzung

| Begriff | Bedeutung in dieser Arbeit |
|---|---|
| Voice Activity Detection, VAD | Erkennung von Sprachaktivität gegenüber Nicht-Sprache im Audiosignal. |
| End-of-Speech | Ende eines akustischen Sprachsegments; kann lediglich eine Pause innerhalb eines Beitrags sein. |
| End-of-Turn, EOT | Ende des Nutzerbeitrags, nach dem der Bot das Rederecht übernehmen kann. |
| Endpointing | Praktische Entscheidung, zu welchem Zeitpunkt ein System einen Beitrag abschließt. |
| Semantic VAD | In der Praxis verwendete Bezeichnung für inhaltlich beziehungsweise prosodisch informierte Turn-End-Erkennung. Im Text wird der präzisere Begriff End-of-Turn Detection bevorzugt. |
| Prosodie | Unter anderem Intonation, Rhythmus, Betonung und zeitliche Struktur der Sprache. |
| HOLD | An einer Pause soll das System weiter zuhören. |
| Premature cutoff | Das System erklärt den Beitrag vor dessen tatsächlichem Ende für abgeschlossen. |
| Endpointing latency | Zeit vom annotierten tatsächlichen Beitragsende bis zur wirksamen Endentscheidung. |
| Inference time | Reine Dauer eines Modellaufrufs; von Endpointing-Latenz zu unterscheiden. |

Die Baseline verwendet ebenfalls ein trainiertes Modell, nämlich Silero VAD. Der Unterschied liegt in der anschließenden Entscheidungsregel: Die Baseline bewertet die Dauer der Nicht-Sprache, die semantischen Verfahren nutzen zusätzlich ein gelerntes Turn-End-Signal.

Semantische Modelle können mehrere Signale gemeinsam nutzen. Aus einem besseren Ergebnis lässt sich deshalb nicht isoliert ableiten, wie viel der Verbesserung durch Semantik, Syntax oder Prosodie entsteht. Dafür wäre eine zusätzliche Ablationsstudie nötig. Der vorliegende Vergleich bewertet die vollständigen Verfahren.

Ebenso bedeutet „semantisch“ nicht automatisch Zugriff auf frühere Dialogbeiträge. Der Kernversuch bewertet den aktuellen Nutzerbeitrag. Ein Modell, das vorherige Bot-Texte oder den gesamten Dialog benötigt, würde eine andere Eingabebedingung schaffen. Wissenschaftliche Ausgangspunkte für diese Unterscheidungen sind [S1], [S2], [S3] und [S4].

## 3. Modell- und Plattformauswahl

### 3.1 Festlegung des Kernvergleichs

| ID | Verfahren | Ausführung | Rolle |
|---|---|---|---|
| B0 | Silero VAD plus fester Stille-Timeout | Lokal, CPU | Pausenbasierte Baseline; verschiedene Timeout-Einstellungen. |
| M1 | LiveKit Audio Turn Detector **v1-mini** | Lokal, CPU | Semantischer und akustischer Turn-Detektor. |
| M2 | Pipecat **Smart Turn v3.2**, CPU-ONNX-Modell | Lokal, CPU | Weiterer semantischer Turn-Detektor mit offenem Code und Gewichten. |

**Empfehlung:** Diese drei Verfahren bilden den Kernumfang. Der lokale Vergleich vereinfacht die Reproduzierbarkeit und vermeidet Netzwerklatenz als zusätzlichen Einflussfaktor.

Dies ist die Planungsempfehlung; die konkrete Laufzeitkompatibilität muss zuerst mit wenigen Beispielaufnahmen geprüft werden. Modellrevisionen, Bibliotheksversionen und Konfigurationen werden nach diesem Pilot festgeschrieben.

### 3.2 Baseline B0: Silero VAD plus Stille-Timeout

Silero stellt ein akustisches VAD mit Unterstützung für 16-kHz-Audio bereit und steht unter MIT-Lizenz [S10]. Die geplante Baseline beendet einen Beitrag, sobald seit der letzten detektierten Sprachaktivität eine definierte Dauer Nicht-Sprache vergangen ist.

Vorgesehene Timeout-Werte:

- 300 ms;
- 500 ms;
- 800 ms;
- 1.000 ms;
- 1.500 ms;
- 2.000 ms;
- 3.000 ms als besonders geduldiger Referenzpunkt.

Der Timeout läuft ab dem geschätzten Ende der Sprachaktivität. Eine bereits im VAD enthaltene Bestätigungszeit wird nicht versehentlich nochmals addiert. Beide Zeiten müssen im Ereignisprotokoll nachvollziehbar sein.

Die Baseline bekommt dieselben Audioframes und dieselbe gemeinsame VAD-Vorverarbeitung wie M1 und M2. Das Experiment vergleicht damit primär die Entscheidung über das Turn-Ende.

### 3.3 M1: LiveKit Audio Turn Detector v1-mini

Die aktuelle Dokumentation unterscheidet den gehosteten Audio-Detektor `v1`, den lokal auf CPU ausführbaren `v1-mini` und den älteren, inzwischen als veraltet markierten Text-Turn-Detektor. Für M1 wird ausdrücklich **v1-mini** gewählt. Deutsch wird unterstützt [S8].

Für die wissenschaftliche Implementierung ist die lokale Score-Schnittstelle beziehungsweise der bestehende Mini-Adapter aus eot-bench ein Ausgangspunkt. Erst der technische Pilot bestätigt, ob sich die gemeinsame Entscheidungsregel darüber vollständig steuern lässt [S12].

Zu protokollieren sind Modellversion, Revision beziehungsweise Gewichte-Hash und tatsächlich verwendete Spracheinstellung. Ohne STT kann die SDK-Integration englische Standardschwellen verwenden; die deutsche Schwelle muss deshalb ausdrücklich geprüft oder am Entwicklungssatz eingestellt werden [S8].

Die Modellgewichte stehen unter der eigenen LiveKit Model License. Lokale Nutzbarkeit und verfügbare Gewichte sind von einer uneingeschränkten Open-Source-Lizenz zu unterscheiden [S9].

### 3.4 M2: Pipecat Smart Turn v3.2

Smart Turn v3.2 arbeitet direkt auf Audio und unterstützt Deutsch. Das Projekt veröffentlicht Code und Gewichte unter BSD-2-Clause. Die Architektur verwendet einen Whisper-Tiny-Encoder und einen Klassifikationskopf [S11].

Geplantes Artefakt: **`smart-turn-v3.2-cpu.onnx`** aus dem Hugging-Face-Repository `pipecat-ai/smart-turn-v3`. Die Dateiliste enthält verschiedene Versionen; der Repositoryname allein legt die verwendete Version nicht fest [S11b].

Das Modell erwartet 16-kHz-Mono-Audio und verarbeitet bis zu etwa acht Sekunden Kontext. Kürzere Eingaben werden nach der Referenzimplementierung links aufgefüllt, längere von vorne gekürzt. Es erhält nur bereits eingetroffenes Audio. Die native Vorverarbeitung wird dokumentiert [S11].

### 3.5 Rolle des vorhandenen LiveKit-Zugangs

Der vorhandene LiveKit-Zugang ist für eine spätere Demo und eine optionale gehostete Vergleichsmessung nützlich.

**Optionale Erweiterung M3:** LiveKit Audio Turn Detector `v1` über die gehostete Inferenz. Diese Messung wird getrennt vom lokalen Kernvergleich ausgewiesen, weil Dienst- und Netzwerklaufzeiten hinzukommen. Ein Anbieter-Roundtrip ist keine reine Modell-Inferenzzeit.

Automatische Wechsel zwischen `v1` und `v1-mini` dürfen nicht unbemerkt in eine Ergebniszeile eingehen. Ein Fallback oder Providerfehler wird mit dem tatsächlich aktiven Modell protokolliert. Die gehostete Erweiterung ist für die Beantwortung der Kernfrage nicht erforderlich.

### 3.6 Rolle von ElevenLabs

Der vorhandene ElevenLabs-Zugang wird sinnvoll verwendet, ohne den Kernversuch zu vergrößern:

| Einsatz | Entscheidung |
|---|---|
| Bot-Sprachausgabe für die Präsentationsdemo | Sinnvoll; eine vorbereitete Antwort kann nach der EOT-Entscheidung abgespielt werden. |
| Zusätzliche synthetische Testaufnahmen | Optionaler, separat ausgewerteter Zusatzsatz; keine Vermischung mit dem menschlich eingesprochenen Hauptkorpus. |
| Transkription zur Unterstützung der Annotation | Optional; Transkripte und Zeitmarken müssen manuell geprüft werden. |
| ElevenAgents als weiterer Turn-Detektor | Nur optionale Systemmessung, wenn ein verlässlich zeitgestempeltes Turn-End-Ereignis zugänglich ist. |

Für synthetische deutsche Beispiele ist beispielsweise `eleven_multilingual_v2` dokumentiert [S16]. Die primäre Datenerhebung bleibt menschliche Sprache: TTS kann die für Turn-taking relevanten prosodischen Hinweise anders realisieren. Das ist auch Gegenstand einer wissenschaftlichen Untersuchung zu Sprachsynthese [S6].

ElevenAgents bietet Einstellungen wie `eager`, `normal` und `patient`. Der dortige **Soft timeout** überbrückt dagegen Wartezeit bei der Antwortgenerierung nach dem Nutzerbeitrag und ist kein EOT-Detektor [S14].

Die Realtime-STT-API dokumentiert außerdem unterschiedliche Commit-Strategien, darunter `turn_prediction` für dafür geeignete Modelle. Daraus folgt noch nicht, dass das vorhandene Konto oder jedes Scribe-Modell diese Funktion unterstützt. Auch ein finalisiertes Transkript ist nicht ohne Weiteres mit einer eigenständigen EOT-Entscheidung gleichzusetzen [S15].

**Praktische Festlegung:** ElevenLabs wird zunächst für die Demo eingeplant. Ein vierter proprietärer Endpointer ist keine Voraussetzung der Arbeit.

### 3.7 Bewusste Begrenzung

Zum Kernversuch gehören die drei Verfahren B0, M1 und M2. Weitere VADs, LLMs, ASR-Anbieter, Modelltraining, RAG, Telefonie, Mehrpersonengespräche und eine Nutzerstudie würden zusätzliche Fragestellungen eröffnen. Sie bleiben mögliche Ausblicke.

Insbesondere wird keine vollständige Chatbot-Antwortqualität bewertet. Die Untersuchung endet an der Turn-End-Entscheidung. Der NLP-Bezug liegt in der sprachlich informierten Interpretation eines noch nicht sicher abgeschlossenen Beitrags.

## 4. Datensatz und Annotation

### 4.1 Empfohlener Hauptkorpus

Geplant sind **100 unterschiedliche, menschlich eingesprochene deutsche Nutzerbeiträge**. Ein Beispiel ist ein vollständiger beabsichtigter Turn mit möglichen internen Pausen; es ist nicht nur ein isolierter Satz oder ein vollständig abgeschnittener Audioclip.

| Fallgruppe | Anzahl insgesamt | Entwicklung | Test |
|---|---:|---:|---:|
| A: Eindeutig abgeschlossene kurze Beiträge | 25 | 5 | 20 |
| B: Unvollständige Äußerungen mit Denkpause | 25 | 5 | 20 |
| C: Vollständiger Satz mit anschließendem Nachtrag | 25 | 5 | 20 |
| D: Zahlenfolgen, Aufzählungen und Selbstkorrekturen | 25 | 5 | 20 |
| **Gesamt** | **100** | **20** | **80** |

Mögliche Aufnahmeorganisation: fünf Personen mit jeweils 20 Beiträgen, davon fünf je Fallgruppe. Eine Person bildet mit ihren 20 eigenständigen Szenarien den Entwicklungssatz, die anderen vier Personen den Testsatz. Dadurch sind Sprecher und konkrete Inhalte zwischen Entwicklung und Test getrennt. Die geringe Sprecherzahl und der nur von einer Person stammende Entwicklungssatz werden als Einschränkung benannt.

Auch andere Sprecherzahlen sind möglich. Die Trennung wird vor der Parameterauswahl festgelegt. Dieselbe Aufnahme, deren Pausenvarianten und nahezu identische Szenariotexte dürfen nicht auf beide Teilmengen verteilt werden.

Die künstlich ausgeglichene Verteilung ist ein kontrollierter Belastungstest. Ihre Gesamtabbruchrate darf nicht als erwartete Abbruchrate eines produktiven Kundendienstes interpretiert werden.

### 4.2 Aufnahmegestaltung

- Kurze Rollenspiel-Szenarien mit einem erkennbaren Kommunikationsziel; möglichst natürliche Realisierung statt monotonen Vorlesens.
- Typische Dauer ungefähr drei bis acht Sekunden, einzelne längere Beiträge ausdrücklich dokumentieren.
- Interne Pausen möglichst natürlich variieren, beispielsweise zwischen etwa 0,4 und 2,2 Sekunden.
- Gleiche grundlegende Aufnahmebedingungen; kein zusätzlicher systematischer Lärmvergleich im Kernversuch.
- Fiktive Namen und Nummern verwenden. Die Teilnehmenden stimmen der Aufnahme und der geplanten Verwendung zu.
- Rohaufnahmen erhalten; Arbeitskopien einheitlich in Mono-PCM mit 16 kHz bereitstellen.
- Nach dem letzten gesprochenen Laut mindestens sechs Sekunden Nicht-Sprache bereitstellen, damit auch späte Entscheidungen beobachtbar bleiben.

Die abschließende Beobachtungszeit wird bei allen Verfahren gleich gehandhabt. Dateilänge und Dateiende dürfen dem Modell keine künstliche Information über das Turn-Ende liefern.

### 4.3 Beispielszenarien

| Fallgruppe | Beispiel | Gewünschte Annotation |
|---|---|---|
| A | „Ich möchte meine Adresse ändern.“ | EOT nach dem letzten Laut. |
| B | „Meine Kundennummer ist … [Pause] … 12345678.“ | HOLD während der Pause; EOT nach der Nummer. |
| B | „Ich rufe an, weil … [Pause] … mein Anschluss nicht funktioniert.“ | HOLD nach „weil“. |
| C | „Ich möchte kündigen. [Pause] Allerdings erst zum Jahresende.“ | HOLD nach dem ersten Satz. |
| C | „Das war alles. [Pause] Ach, eine Frage habe ich noch.“ | Schwieriger Nachtrag; HOLD vor der Fortsetzung. |
| D | „Die Nummer ist 1234 … [Pause] … nein, 1235.“ | HOLD vor der Korrektur. |

Bei Gruppe C ist der erste Satz ohne Kenntnis der Fortsetzung teilweise ein plausibler Übergabepunkt. Diese Fälle werden als mehrdeutig markiert und zusätzlich separat betrachtet. Das System soll nicht dafür kritisiert werden, dass es die Zukunft nicht sicher kennt.

### 4.4 Annotierungsregeln

Für jede Aufnahme werden festgehalten:

1. Anfang und Ende der tatsächlichen Sprachaktivität sowie interne Pausen.
2. Das **Gold-Turn-Ende** als Ende des letzten gesprochenen Lauts im beabsichtigten Beitrag.
3. Für interne Pausen das Label `HOLD`; für die abschließende Nicht-Sprache `EOT`.
4. Fallgruppe, Sprecherkennung, Transkript und Kennzeichnung mehrdeutiger Übergabepunkte.

Die Annotation darf die gesamte Aufnahme verwenden; das laufende Erkennungssystem darf das nicht. Die Gold-Annotation entsteht durch Anhören und gegebenenfalls Wellenform- beziehungsweise Spektrogrammansicht. Automatische VAD- oder ASR-Zeitmarken sind Hilfsmittel und werden nicht ungeprüft zur Wahrheit erklärt.

Mindestens 20–25 % der Aufnahmen, einschließlich schwieriger Beispiele, werden durch eine zweite Person geprüft. Zu berichten sind die absolute Abweichung der Endzeitpunkte und die Übereinstimmung bei HOLD/EOT beziehungsweise Mehrdeutigkeit. Uneinigkeiten werden vor dem finalen Test geklärt. Falls keine zweite Person verfügbar ist, wird dieser Umstand dokumentiert und die Annotation zeitversetzt erneut geprüft.

### 4.5 Datenformat

Vorgesehen ist ein JSONL-Manifest. Das folgende Objekt illustriert die Struktur; Zeitwerte und Kennungen sind ausdrücklich Beispieldaten:

```json
{
  "id": "de_001",
  "audio_path": "audio/de_001.wav",
  "speaker_id": "spk_01",
  "scenario_id": "customer_number_01",
  "split": "dev",
  "category": "incomplete_with_pause",
  "source": "human",
  "sample_rate_hz": 16000,
  "transcript": "Meine Kundennummer ist 12345678.",
  "speech_start_ms": 300,
  "gold_eot_ms": 5200,
  "annotation_uncertainty_ms": 50,
  "ambiguous_transition": false,
  "pauses": [
    {"start_ms": 1800, "end_ms": 3300, "label": "HOLD"},
    {"start_ms": 5200, "end_ms": 11200, "label": "EOT"}
  ]
}
```

Die Gold-Zeitpunkte und Labels bleiben im Evaluator. Adapter erhalten nur Audio und erlaubte Metadaten, beispielsweise die fest vorgegebene Sprache Deutsch.

### 4.6 Öffentliche Daten als Alternative

Der öffentliche Datensatz `livekit/eot-bench-data` bietet eine mögliche deutsche Datenbasis; das zugehörige Repository beschreibt die Spracheinteilung und das Annotationsschema [S12], [S13]. Vor einer Übernahme müssen die tatsächlichen deutschen Beispiele und Labels stichprobenartig geprüft werden.

Ein kleiner öffentlicher Zusatzsatz kann die Übertragbarkeit ergänzen. Eigene und öffentliche Daten werden getrennt berichtet. Eine Unabhängigkeit von Modelltraining oder Modellauswahl darf ohne Nachweis nicht behauptet werden. Smart-Turn-Trainingsdaten werden nicht als eigener neutraler Testkorpus ausgegeben.

Falls eigene Aufnahmen organisatorisch nicht möglich sind, kann ein dokumentierter deutscher öffentlicher Teilkorpus den Hauptkorpus ersetzen. Diese Entscheidung fällt vor dem finalen Experiment.

## 5. Prototyp und gemeinsame Versuchspipeline

### 5.1 Architektur

```text
Annotierte WAV-Aufnahmen und Manifest
                |
                v
Chronologischer Audio-Replay, nur bereits verfügbare Frames
                |
                v
Gemeinsames akustisches VAD / Pausenkandidaten
                |
       +--------+---------+
       |        |         |
       v        v         v
      B0       M1        M2
  Stillezeit  LiveKit   Smart Turn
       |        |         |
       +--------+---------+
                |
                v
Gemeinsames Entscheidungs- und Ereignisprotokoll
                |
                v
Abgleich mit Gold-Annotation, Tabellen und Diagramme
```

Ein vollständiger Voicebot ist für diese Pipeline nicht nötig. Eine kleine LiveKit-Demo wird erst nach funktionierender Evaluation ergänzt.

### 5.2 Technischer Pilot vor der eigentlichen Datenerhebung

Zuerst werden fünf bis zehn separate Probeaufnahmen verwendet. Diese gehören nicht zum späteren Testkorpus.

Der Pilot muss folgende Fragen beantworten:

- Lassen sich M1 und M2 auf der verfügbaren Hardware laden und ausführen?
- Sind End-of-Turn-Scores beziehungsweise eindeutig zeitgestempelte Entscheidungen zugänglich?
- Was bedeutet ein hoher Score tatsächlich? Eine Richtung oder Kalibrierung wird nicht aus einem Parameternamen geraten.
- Lassen sich Sprache und Entscheidungsschwellen kontrollieren?
- Welche Pausenbestätigung und Vorverarbeitung erfolgen bereits im jeweiligen SDK?
- Kann bei beiden Modellen dieselbe äußere Entscheidungsregel verwendet werden?
- Wie lange dauert die Inferenz, und reicht die Echtzeitfähigkeit für die geplante Abfragerate?

Der vorhandene eot-bench-Code ist ein Ausgangspunkt für Adapter und Methodik [S12]. Übernommen wird nur, was verstanden, passend lizenziert und mit festgehaltener Revision reproduzierbar ist.

Falls ein Adapter ausschließlich vollständige SDK-Entscheidungen zugänglich macht, wird der Versuch als **Vergleich konfigurierter Systeme** ausgewiesen. Unterschiedliche versteckte Wartezeiten dürfen dann nicht als isolierter Modellunterschied interpretiert werden. Das wird im Pilot entschieden und vor dem Test festgehalten.

### 5.3 Gemeinsame Entscheidungsregel

Geplante Startkonfiguration, noch am Entwicklungssatz zu prüfen:

| Parameter | Planung |
|---|---|
| Audio | 16 kHz, Mono; intern einheitliche numerische Darstellung. |
| Replay | Chronologisch; für die finalen Zeitmessungen in Echtzeit, also 1×. |
| VAD | Dieselbe Silero-Version und dieselbe Konfiguration für alle Verfahren. |
| Frühester semantischer Prüfzeitpunkt | Nach etwa 300 ms bestätigter Nicht-Sprache, gemessen ab geschätztem Sprachende. |
| Weitere Prüfzeitpunkte | Beispielsweise alle 100 ms während derselben Pause, soweit die Inferenz dies zulässt. |
| Maximale Wartezeit | 3.000 ms ununterbrochene Nicht-Sprache seit dem letzten detektierten Sprachende. |
| Semantische Entscheidung | EOT-Score oberhalb der am Entwicklungssatz festgelegten Schwelle. |
| Wiederbeginn der Sprache | Pausenwartezeit zurücksetzen; veraltete ausstehende Entscheidungen verwerfen. |

Die Werte sind eigene Versuchsparameter und keine behaupteten optimalen Herstellerwerte. Gemeinsame Parameter und modellabhängige Grenzen werden in der Konfiguration getrennt dokumentiert.

Die aktuelle LiveKit-Integration verlangt mindestens 250 ms VAD-Pausenbestätigung [S8]. Der Pilot muss verhindern, dass zusätzlich dazu nochmals unabsichtlich 300 ms gewartet werden. Wenn sich die gesamte Bestätigungszeit nur als Systemverhalten messen lässt, wird sie vollständig mitgemessen.

Ein maximaler Timeout kann auch einen tatsächlich noch unvollständigen Beitrag vorzeitig abschließen. In diesem Fall zählt die Entscheidung als vorzeitiger Abschluss und erhält zusätzlich den Trigger `fallback_timeout`.

### 5.4 Kausalität und Zeitmessung

Es gibt zwei ausdrücklich unterschiedliche Zeitachsen:

- **Audiozeit:** Position des Audios relativ zum Beginn des Streams.
- **Laufzeit:** Monotone Uhr zur Messung von Verarbeitung und tatsächlich verfügbar gewordenen Entscheidungen.

Für einen Score zum Audiozeitpunkt `t` darf nur Audio bis `t` verwendet werden. Die Entscheidung gilt erst dann als verfügbar, wenn der Modellaufruf beendet ist. Ein bereits zurückliegender Audiozeitpunkt darf nicht als Entscheidungszeit protokolliert werden, wenn das Ergebnis erst später vorlag.

Bei einer neuen Sprachphase während der laufenden Inferenz darf ein veraltetes EOT-Ergebnis die neue Sprache nicht nachträglich abschneiden. Überlastung, übersprungene Abfragen und verworfene Ergebnisse werden protokolliert. Modelle laufen im Zeitvergleich einzeln auf derselben Maschine; gleichzeitige Konkurrenzlast wird vermieden.

Der **erste tatsächlich wirksame Turn-Abschluss** entscheidet über das Ergebnis einer Aufnahme. Nach einem vorzeitigen Abschluss darf das System nicht die restliche Aufnahme anhören und den Fehler rückwirkend korrigieren. Vollständige Score-Verläufe können zusätzlich für die Fehleranalyse gespeichert werden.

Ein schneller Offline-Replay ist zum Entwickeln oder zum Untersuchen von Entscheidungsregeln zulässig. Seine simulierte Wartezeit wird jedoch als solche beschriftet. Die im Hauptergebnis berichtete beobachtete Endpointing-Latenz stammt aus dem 1×-Replay und enthält die tatsächlich wirksame Verarbeitung.

### 5.5 Geplante Softwarebausteine

Der folgende Verzeichnisbaum beschreibt zukünftige Dateien; er ist noch keine vorhandene Implementierung:

```text
data/
  audio/                 # menschliche Arbeitsaufnahmen
  manifest.jsonl         # Metadaten und Annotationen
configs/
  experiment.yaml        # Verfahren, Schwellen und Replay-Einstellungen
src/
  replay.py              # kausaler Audio-Replay
  vad.py                 # gemeinsame VAD-Einbindung
  adapters/              # Baseline, LiveKit mini und Smart Turn
  endpointing.py         # Entscheidungsregel und Timeout
  evaluate.py            # Metriken aus Ereignissen und Gold-Labels
  report.py              # Tabellen und Diagramme
results/
  events.jsonl           # einzelne Messereignisse
  per_turn.csv           # ein Ergebnis je Turn und Konfiguration
  summary.csv            # aggregierte Ergebnisse
  figures/               # Abbildungen
```

Voraussichtliche Werkzeuge: Python, NumPy, SoundFile, ONNX Runtime, Silero VAD, die benötigten LiveKit-Pakete sowie Pandas und Matplotlib. Abhängigkeiten werden im Pilot auf der Zielhardware geprüft und anschließend festgeschrieben. Eine Streamlit-Oberfläche ist optional.

Das Ereignisprotokoll enthält mindestens: Aufnahme-ID, Verfahren, Konfigurations-ID, Modellrevision, Anfrage-Audiozeit, Ergebnisverfügbarkeit, Score, Inferenzdauer, aktiven Modellnamen, Entscheidung, Trigger und technischen Fehlerstatus.

## 6. Evaluationsmetriken

### 6.1 Hauptmetrik: Premature Cutoff Rate

Für Aufnahme `i` seien `g_i` das annotierte tatsächliche Turn-Ende und `c_i` der erste wirksame Turn-Abschluss, jeweils auf dieselbe Stream-Zeitachse bezogen.

```text
Vorzeitiger Abschluss, wenn c_i < g_i

Premature Cutoff Rate =
  Anzahl der Test-Turns mit vorzeitigem Abschluss / Anzahl aller Test-Turns
```

Berichtet werden Prozentwert und absolute Anzahl, beispielsweise „6/80“. Eine Aufnahme zählt höchstens einmal, auch wenn mehrere interne Pausen existieren.

Die Hauptauswertung verwendet die festgeschriebenen Gold-Zeiten. Eine zusätzliche Sensitivitätsanalyse mit beispielsweise 100 ms Annotationstoleranz zeigt, ob zeitliche Grenzfälle das Ergebnis verändern. Diese Toleranz wird vor Sichtung der Testergebnisse festgelegt.

Diese Rate ist nicht identisch mit einer pausebezogenen False Positive Rate. Für eine ergänzende Pause-FPR wäre der Nenner die Anzahl der HOLD-Pausen. Beide Nenner werden ausdrücklich unterschieden.

### 6.2 Hauptmetrik: Endpointing-Latenz

Für korrekt bis zum tatsächlichen Ende abgewartete Turns:

```text
Endpointing-Latenz_i = c_i - g_i
```

Berichtet werden:

- Median;
- 95. Perzentil;
- optional Interquartilsabstand;
- die Anzahl der dafür auswertbaren Turns.

Vorzeitige Abschlüsse werden nicht als negative und damit scheinbar gute Latenzen aufgenommen. Entscheidungen durch den maximalen Wartezeit-Fallback bleiben enthalten, sofern sie nach dem tatsächlichen Ende liegen. Für vollständig fehlende Entscheidungen wird keine günstige Ersatzlatenz erfunden.

Die Latenz ist immer gemeinsam mit Abbruch- und Ausfallrate zu lesen. Wenn ein Verfahren andere Beispiele korrekt beendet, ist der Median über seine erfolgreichen Beispiele nur bedingt direkt vergleichbar. Ergänzend wird deshalb die gepaarte Latenzdifferenz auf den von beiden verglichenen Verfahren korrekt beendeten Turns berichtet; deren Anzahl wird angegeben.

Das 95. Perzentil aus höchstens 80 Testbeiträgen ist empfindlich gegenüber einzelnen Fällen. Es wird als deskriptiver Wert interpretiert.

### 6.3 Ergänzende Metrik: Timeout Fallback Rate

```text
Timeout Fallback Rate =
  Anzahl der Turns mit maximalem Wartezeit-Fallback / Anzahl aller Test-Turns
```

Diese Kennzahl ist für M1 und M2 sinnvoll. Bei B0 ist eine Zeitregel das beabsichtigte Verfahren; sie wird nicht als 100-prozentige Fehlerrate ausgegeben. In der Tabelle erhält B0 in dieser Spalte „nicht anwendbar“.

Der Fallback wird am ersten Commit-Trigger gezählt und zusätzlich in vorzeitige und rechtzeitige Fallbacks aufgeschlüsselt. Ein Provider- oder Laufzeitfehler ist ein gesonderter technischer Trigger.

### 6.4 Ergänzende Metrik: Inferenzzeit und technische Ausfälle

Für lokale Modelle wird die Zeit zwischen Aufrufbeginn und Score-Rückgabe gemessen. Dazu gehören klar definierte Schritte der modellbezogenen Verarbeitung; ihre Abgrenzung wird dokumentiert.

Berichtet werden Median und 95. Perzentil je Aufruf sowie möglichst die aufsummierte Modellrechenzeit pro Turn. Ein schneller Einzelaufruf bei sehr vielen Abfragen kann insgesamt mehr Rechenzeit benötigen.

Kaltstart und Modellladen werden separat erfasst; die Laufzeitmessung nutzt vorgewärmte Modelle. Zumindest ein Wiederholungslauf pro festgelegter Konfiguration prüft die Stabilität der lokalen Laufzeitwerte. Wiederholungen erhöhen nicht die Anzahl unabhängiger Sprachbeispiele.

Zusätzlich werden fehlende Entscheidungen, Exceptions und gegebenenfalls Cloudfehler als Anzahl und Rate protokolliert. Bei einer Cloud-Erweiterung wird der Roundtrip als Dienstlaufzeit ausgewiesen.

### 6.5 Precision, Recall und F1

Optional können HOLD/EOT-Pausen als Klassifikationsaufgabe ausgewertet werden. Dazu werden gemeinsame, im Voraus definierte Entscheidungszeitpunkte verwendet, nicht beliebig viele eng benachbarte Audioframes als unabhängige Fälle.

Precision, Recall, F1 und Konfusionsmatrix erklären dann die Art der Fehler. Sie ersetzen die Kombination aus vorzeitiger Abbruchrate und zeitlicher Verzögerung nicht.

### 6.6 Hauptdarstellung des Zielkonflikts

Die wichtigste Abbildung zeigt:

- **x-Achse:** Endpointing-Latenz;
- **y-Achse:** Premature Cutoff Rate;
- **Punkte beziehungsweise Linien:** vorab festgelegte Einstellungen je Verfahren.

Ein Punkt weiter links unten bedeutet unter diesen Messbedingungen weniger Wartezeit und weniger vorzeitige Abschlüsse. Eine Dominanz wird nur behauptet, wenn beide Größen entsprechend ausfallen; ansonsten wird der Zielkonflikt beschrieben.

Die Kombination von Latenz und Abbruchrate wird auch im offenen eot-bench verwendet. Die konkrete Konfiguration und Auswertung dieses Projekts sind dennoch eigenständig zu dokumentieren [S12].

## 7. Parameterauswahl und Ablauf der Experimente

### 7.1 Entwicklung und Festlegung

1. Gemeinsame VAD- und Replay-Einstellungen mit den Pilotaufnahmen prüfen.
2. Die 20 Entwicklungsbeiträge für die Auswahl von Schwellen und eines primären Betriebspunkts verwenden.
3. Für jedes semantische Modell höchstens drei sinnvoll verteilte Schwellen prüfen. Die Score-Semantik wird vorher verifiziert; numerisch gleiche Schwellen müssen nicht gleichbedeutend sein.
4. Die Baseline über die genannten Stillezeiten auswerten.
5. Vor dem Test Konfigurationen, Auswertungsregeln und Ergebnisdarstellungen einfrieren.

Als einfache vorab definierte Auswahlregel kann gelten: Unter den Einstellungen mit höchstens einem vorzeitigen Abschluss auf den 20 Entwicklungsbeiträgen diejenige mit geringster medianer Latenz wählen; fehlende Entscheidungen dürfen diese Wahl nicht begünstigen. Falls kein Betriebspunkt dieses Kriterium erfüllt, wird zuerst die Anzahl vorzeitiger Abschlüsse und danach die Latenz minimiert, jeweils unter vollständiger Angabe technischer Ausfälle.

Diese kleine Entwicklungsmenge erlaubt nur grobe Entscheidungen. „Ein Fehler von 20“ ist keine belastbare Schätzung einer produktiven Fünf-Prozent-Grenze. Die Regel dient der reproduzierbaren Auswahl, nicht dem Nachweis einer garantierten Fehlerrate.

Die maximal drei semantischen Schwellen sowie die Baseline-Timeouts können zusätzlich als vorab definierte Sensitivitätsreihe auf dem Testsatz laufen. Die Testkurve wird deskriptiv dargestellt. Es wird danach kein neuer „optimaler“ Betriebspunkt ausgewählt und als unvoreingenommenes Hauptergebnis ausgegeben.

### 7.2 Finaler Test

- Alle festgelegten Verfahren auf denselben 80 Testaufnahmen ausführen.
- Parameter und Fallgruppen nach Beginn des finalen Tests unverändert lassen.
- Modelle einzeln und auf derselben Hardware betreiben; Reihenfolge und Warm-up dokumentieren.
- Ereignisse und Laufzeitmetadaten speichern; technische Fehler nicht stillschweigend aus dem Nenner entfernen.
- Das primäre Betriebspunkt-Ergebnis und die vorab geplante Sensitivitätsreihe getrennt ausweisen.

Ein Softwarefehler darf korrigiert werden. Danach muss die betroffene Messung vollständig und mit neuer Laufkennung wiederholt werden. Eine Modellschwelle wegen unerwünschter Testergebnisse zu ändern, wäre dagegen eine neue explorative Untersuchung.

### 7.3 Unsicherheit und Interpretationsgrenzen

Ergebnisse werden mit absoluten Fallzahlen und Fallgruppen berichtet. Optional werden gepaarte Bootstrap-Intervalle für Unterschiede ergänzt. Sprecherabhängigkeit ist dabei zu beachten; bei nur vier Testsprechern bleiben auch sprecherweise resampelte Intervalle sehr unsicher.

Die Arbeit beansprucht eine explorative Fallstudie. Sie erstellt keine allgemeingültige Rangliste und leitet keine produktiven Service-Level-Zusagen ab. Aufwendige Signifikanztests sind bei dieser Datenbasis kein Pflichtbestandteil.

## 8. Erwartete Ergebnisartefakte

Die Untersuchung soll liefern:

1. Ein dokumentiertes Manifest mit 100 Aufnahmen und überprüften Annotationen.
2. Einen kausalen Replay-Prototyp mit drei funktionsfähigen Adaptern.
3. Eine reproduzierbare Konfiguration mit festgehaltenen Modellrevisionen.
4. Eine Haupttabelle mit Abbruchrate, Latenz, Fallbacks, Inferenzzeit und technischen Ausfällen.
5. Eine Abbildung zum Zielkonflikt und eine kompakte Auswertung nach Fallgruppen.
6. Drei bis fünf konkrete Fehlerfälle mit Audiozeitachse und kurzer Interpretation.
7. Eine kleine Präsentationsdemo, beispielsweise mit einer vorbereiteten ElevenLabs-Antwort nach dem erkannten Turn-Ende.

Die folgende Tabelle ist eine Vorlage und enthält bewusst noch keine Messergebnisse:

| Verfahren / Konfiguration | Vorzeitige Abschlüsse | Latenz Median / p95 | Auswertbare Latenzfälle | Fallbacks | Inferenz Median / p95 | Technische Ausfälle |
|---|---|---|---|---|---|---|
| B0: gewählter Stille-Timeout | noch zu messen | noch zu messen | noch zu messen | nicht anwendbar | nur VAD separat | noch zu messen |
| M1: LiveKit v1-mini | noch zu messen | noch zu messen | noch zu messen | noch zu messen | noch zu messen | noch zu messen |
| M2: Smart Turn v3.2 CPU | noch zu messen | noch zu messen | noch zu messen | noch zu messen | noch zu messen | noch zu messen |

Bei der Demo wird eine künstliche feste Antwort verwendet oder die Generierung separat protokolliert. Die Zeit bis zum ersten Bot-Audio wird nicht als EOT-Latenz bezeichnet.

## 9. Gliederung und Wortbudget der Seminararbeit

| Kapitel | Inhalt | Zielumfang |
|---|---|---:|
| 1. Einleitung | Problem, praktische Relevanz und Forschungsfrage | 230 Wörter |
| 2. Grundlagen und Forschungsstand | VAD, EOT, sprachliche und prosodische Hinweise | 350 Wörter |
| 3. Methodik und Prototyp | Verfahren, Korpus, Split, kausaler Replay und Metriken | 600 Wörter |
| 4. Ergebnisse | Haupttabelle, Zielkonflikt und Fallgruppen | 350 Wörter |
| 5. Diskussion | Interpretation, Fehlerfälle und Einschränkungen | 350 Wörter |
| 6. Fazit | Antwort auf die Forschungsfrage und kurzer Ausblick | 120 Wörter |
| **Summe** | | **2.000 Wörter** |

Modellkonfigurationen, längere Datensatzbeschreibungen und technische Einzelheiten können in einen Anhang, sofern die geltenden Hochschulvorgaben dies erlauben. Wie Tabellen, Beschriftungen und Anhänge zur Wortzahl zählen, wird anhand des verbindlichen Leitfadens geprüft.

Der Text konzentriert sich auf den eigenen Versuch. Ein historischer Überblick aller Anbieter und Turn-taking-Modelle ist für diesen Umfang nicht vorgesehen.

## 10. Arbeitsplan für etwa acht Wochen

| Woche | Arbeitsschritt | Abgeschlossen, wenn … |
|---|---|---|
| 1 | Literatur, Begriffsklärung und technischer Pilot | Modellzugriff, Score-Verfügbarkeit und deutsche Konfiguration sind geklärt. |
| 2 | Gemeinsame Replay-Pipeline, Baseline und Modelladapter | Probeaufnahmen liefern nachvollziehbare kausale Ereignisprotokolle. |
| 3 | Szenarien, Aufnahmen und erster Annotationsdurchlauf | 100 geeignete Aufnahmen liegen mit festgelegtem Split vor. |
| 4 | Annotationsprüfung und Pipeline-Verifikation | Gold-Labels sind geprüft; Zeitmessung und Fehlerszenarien funktionieren. |
| 5 | Entwicklungssatz und Festlegung der Konfiguration | Schwellen, Betriebspunkt und Auswertungsregeln sind eingefroren. |
| 6 | Finaler Test | Vollständige Rohprotokolle, Tabellen und erste Abbildungen liegen vor. |
| 7 | Fehleranalyse und Schreiben | Eine vollständige erste Fassung mit belegten Aussagen liegt vor. |
| 8 | Überarbeitung und zehnminütige Präsentation | Wortbudget, Zitate, Reproduzierbarkeit und Demo sind geprüft. |

Wenn weniger Zeit bleibt, entfallen zuerst die gehostete LiveKit-Erweiterung, synthetische Zusatzdaten und die ElevenAgents-Systemmessung. Kernkorpus, drei Verfahren und die zwei Hauptmetriken bleiben erhalten.

## 11. Risiken und konkrete Gegenmaßnahmen

| Risiko | Gegenmaßnahme |
|---|---|
| LiveKit mini ist auf der Zielhardware nicht nutzbar | Bereits in Woche 1 prüfen. Bei Bedarf gehostetes `v1` als geplante Ersatzbedingung festlegen und Dienstlaufzeit getrennt interpretieren. |
| SDKs enthalten unterschiedliche versteckte Wartezeiten | Möglichst rohe Scores und gemeinsame äußere Entscheidungsregel verwenden; andernfalls ausdrücklich Systemvergleich durchführen. |
| Gewichte oder Anbieterstand ändern sich | Versionen, Revisionen und Hashes sichern; gehostete Messungen datieren. |
| Schwellen passen zufällig zum Testsatz | Entwicklung und Test vorab trennen; Parameter vor dem Test festschreiben. |
| TTS erzeugt unnatürliche Turn-taking-Signale | Menschliches Audio als Hauptkorpus; Synthese nur als gekennzeichnete Zusatzbedingung. |
| Vollständige Sätze mit Nachtrag sind objektiv mehrdeutig | Mehrdeutigkeit annotieren, Gruppe C separat berichten und Fehler nicht pauschal als fehlendes Sprachverständnis deuten. |
| Sehr lange interne Pausen überschreiten den maximalen Timeout | Solche Fälle separat als Stressfälle ausweisen; ein erzwungener Abschluss bleibt ein Fehler des konfigurierten Systems. |
| Gute Latenz entsteht durch viele abgeschnittene schwierige Beispiele | Abbruchrate und Latenz gemeinsam berichten; ergänzend gepaarte Latenzanalyse. |
| Die Arbeit wird zu umfangreich | Keine zusätzlichen Modelle, Trainingspipeline oder Antwortqualitätsbewertung im Kernumfang. |

Für den Forschungsdatensatz sind fiktive Kundendaten ausreichend. Betriebliche Audioaufnahmen oder interne Systeme sind für diesen Plan nicht erforderlich. Eine öffentliche Weitergabe menschlicher Aufnahmen wird gesondert mit den Beteiligten vereinbart.

## 12. Literaturrecherche und Quellenstrategie

### 12.1 Suchbegriffe

Die Recherche verwendet mehrere Begriffe, weil „Semantic VAD“ nicht das einzige wissenschaftliche Suchwort ist:

```text
"end-of-turn detection"
"semantic voice activity detection"
"semantic VAD"
"speech endpointing" AND latency
"turn-taking prediction" AND dialogue
"turn-taking" AND prosody
"voice activity projection"
"premature cutoff" AND endpointing
```

Geeignete Einstiege sind ACL Anthology, ISCA Archive, Google Scholar und die Hochschulzugänge zu Verlagsdatenbanken. arXiv dient für aktuelle Vorabveröffentlichungen. Publikationsstatus und finale Fassungen werden vor der Abgabe nochmals geprüft.

### 12.2 Priorisierung

Für die theoretische Argumentation stehen wissenschaftliche Fach- und Konferenzbeiträge im Vordergrund. Anbieterunterlagen belegen Schnittstellen, unterstützte Sprachen und konkrete Implementierungsdetails. Anbieter-Benchmarks werden als solche gekennzeichnet; deren Ranglisten werden nicht als unabhängiger Beweis übernommen.

Für die knappe Hausarbeit sollten zuerst S1, S2 und S3 gelesen werden, danach S4 oder S5 je nach Schwerpunkt. S6 begründet die Vorsicht bei synthetischem Audio. S7 und S12 helfen bei der Evaluationsgestaltung.

Die folgenden Einträge sind eine kommentierte Arbeitsbibliografie. Die Recherche hat die Quellen, Metadaten und ihre thematische Eignung geprüft; sie ersetzt keine vollständige kritische Lektüre aller Volltexte. Beim Review S1 war der direkte Verlagsabruf technisch blockiert; die DOI und bibliografischen Angaben waren über den indexierten Verlagsdatensatz verifizierbar. Der Volltext ist gegebenenfalls über die Hochschule zu beschaffen.

## 13. Kommentierte Quellenliste

### 13.1 Wissenschaftliche Grundlagen

**S1 – Gabriel Skantze (2021).** *Turn-taking in Conversational Systems and Human-Robot Interaction: A Review.* Computer Speech & Language, 67, 101178.  
[Verlagsseite / DOI](https://doi.org/10.1016/j.csl.2020.101178)  
**Quellentyp:** Wissenschaftlicher Zeitschriften-Review.  
**Nutzen:** Einordnung der Turn-taking-Aufgabe und der unterschiedlichen sprachlichen, zeitlichen und akustischen Hinweise. Ausgangspunkt für die Problemstellung. Direkter Volltextabruf bei der Recherche mit HTTP 403 blockiert; keine Detailergebnisse aus ungelesenen Abschnitten übernehmen.

**S2 – Erik Ekstedt und Gabriel Skantze (2020).** *TurnGPT: a Transformer-based Language Model for Predicting Turn-taking in Spoken Dialog.* Findings of EMNLP 2020, S. 2981–2990. DOI: 10.18653/v1/2020.findings-emnlp.268.  
[ACL Anthology und Volltext](https://aclanthology.org/2020.findings-emnlp.268/)  
**Quellentyp:** Veröffentlichter wissenschaftlicher Konferenzbeitrag.  
**Nutzen:** Sprachmodellbasierte Vorhersage und Rolle des Dialogkontexts sowie syntaktischer und pragmatischer Vollständigkeit. TurnGPT ist Hintergrundliteratur, kein weiterer Pflichtadapter des Versuchs.

**S3 – Galo Castillo-López, Gael de Chalendar und Nasredine Semmar (2025).** *A Survey of Recent Advances on Turn-taking Modeling in Spoken Dialogue Systems.* Proceedings of the 15th International Workshop on Spoken Dialogue Systems Technology, S. 254–271.  
[ACL Anthology und Volltext](https://aclanthology.org/2025.iwsds-1.27/)  
**Quellentyp:** Wissenschaftlicher Workshop-Survey.  
**Nutzen:** Neuerer Überblick über Modelle, Daten und Evaluationsprobleme; geeignet zur Ergänzung des älteren Reviews. Aussagen über den damaligen Benchmarkstand zeitlich einordnen.

**S4 – Erik Ekstedt und Gabriel Skantze (2022).** *Voice Activity Projection: Self-supervised Learning of Turn-taking Events.* Interspeech 2022. DOI: 10.21437/Interspeech.2022-10955.  
[ISCA-Volltext](https://www.isca-archive.org/interspeech_2022/ekstedt22_interspeech.pdf)  
**Quellentyp:** Veröffentlichter wissenschaftlicher Konferenzbeitrag.  
**Nutzen:** Audioorientierte Vorhersage zukünftiger Sprachaktivität und Bezug zu HOLD/SHIFT-Entscheidungen. Hilft, klassische VAD von prädiktiver Turn-Modellierung zu unterscheiden.

**S5 – Erik Ekstedt und Gabriel Skantze (2022).** *How Much Does Prosody Help Turn-taking? Investigations using Voice Activity Projection Models.* Proceedings of SIGDIAL 2022, S. 541–551. DOI: 10.18653/v1/2022.sigdial-1.51.  
[ACL Anthology und Volltext](https://aclanthology.org/2022.sigdial-1.51/)  
**Quellentyp:** Veröffentlichter wissenschaftlicher Konferenzbeitrag.  
**Nutzen:** Untersuchung prosodischer Hinweise. Begründet, warum ein audioorientierter Vergleich nicht als isolierter Test von Textsemantik interpretiert werden darf.

**S6 – Erik Ekstedt, Siyang Wang, Éva Székely, Joakim Gustafson und Gabriel Skantze (2023).** *Automatic Evaluation of Turn-taking Cues in Conversational Speech Synthesis.* Interspeech 2023, S. 5481–5485. DOI: 10.21437/Interspeech.2023-2064.  
[ISCA Archive und Volltext](https://www.isca-archive.org/interspeech_2023/ekstedt23_interspeech.html)  
**Quellentyp:** Veröffentlichter wissenschaftlicher Konferenzbeitrag.  
**Nutzen:** Direkt relevant für den Einsatz von ElevenLabs zur Datensynthese. Die Studie untersucht Turn-taking-Signale in Sprachsynthese; sie ist keine spezifische Bewertung der heute ausgewählten ElevenLabs-Version.

**S7 – Freeman Jiang und weitere Autorinnen und Autoren (2026).** *TurnBench: A Multi-Domain Benchmark for Turn-Taking Dynamics in Spoken Dialogue.* arXiv:2608.25218, recherchierte Fassung v2 vom 16. September 2026.  
[Preprint mit vollständiger Autorenliste](https://arxiv.org/abs/2608.25218) · [Projektseite](https://turnbench.sesame.com/)  
**Quellentyp:** Aktueller Preprint; ein endgültiger begutachteter Publikationsstatus wird hier nicht vorausgesetzt.  
**Nutzen:** Zeitliche und ereignisbezogene Evaluation auf unterschiedlichen Gesprächstypen. Der vorgestellte Korpus ist englisch und dient hier als methodische Referenz, nicht als deutscher Hauptdatensatz. Für das finale Literaturverzeichnis die vollständigen Metadaten importieren.

### 13.2 Modelle, Implementierung und Daten

**S8 – LiveKit.** *LiveKit turn detector.*  
[Offizielle Dokumentation](https://docs.livekit.io/agents/logic/turns/turn-detector/)  
**Quellentyp:** Herstellerdokumentation, abgerufen am 25.10.2026.  
**Nutzen:** Modellvarianten, Sprachen, Konfiguration und aktuelles SDK-Verhalten. Herstellerangaben zur Leistung sind keine eigenen Messergebnisse.

**S9 – Chenghao Mou, Leigh Weston und Jerad Fields / LiveKit (17. Juni 2026).** *Solving end-of-turn detection: LiveKit Turn Detector v1.0.*  
[Produkt- und Architekturbeitrag](https://livekit.com/blog/solving-end-of-turn-detection)  
**Quellentyp:** Herstellerbeitrag, abgerufen am 25.10.2026.  
**Nutzen:** Einordnung der aktuellen Audio-Modelle sowie Unterscheidung zwischen Code- und Modelllizenz. Kein wissenschaftlich unabhängiger Modellvergleich.

**S10 – Silero Team.** *Silero VAD.*  
[Offizielles Repository](https://github.com/snakers4/silero-vad)  
**Quellentyp:** Software- und Modelldokumentation, abgerufen am 25.10.2026.  
**Nutzen:** Akustische Baseline, Audioformate, Implementierung und MIT-Lizenz. Tatsächlich verwendete Version später ergänzen.

**S11 – Pipecat.** *Smart Turn v3.2.*  
[Offizielles Repository](https://github.com/pipecat-ai/smart-turn)  
**Quellentyp:** Software- und Modelldokumentation, abgerufen am 25.10.2026.  
**Nutzen:** Architektur, deutsche Sprachunterstützung, Kontextfenster, Vorverarbeitung und BSD-2-Clause-Lizenz.

**S11b – Pipecat.** *smart-turn-v3: Modellartefakte auf Hugging Face.*  
[Modellkarte](https://huggingface.co/pipecat-ai/smart-turn-v3) · [Dateien und Versionen](https://huggingface.co/pipecat-ai/smart-turn-v3/tree/main)  
**Quellentyp:** Modellveröffentlichung, abgerufen am 25.10.2026.  
**Nutzen:** Auswahl der konkreten v3.2-CPU-Datei und späteres Festhalten der Revision. Die derzeitige Modellkarte verweist teilweise noch auf v3.1-Datensätze; deshalb den konkreten Dateistand dokumentieren.

**S12 – LiveKit.** *eot-bench: End-of-Turn Benchmark.*  
[Offizielles Repository und Methodik](https://github.com/livekit/eot-bench)  
**Quellentyp:** Offener, herstellerinitiierter Benchmark und Evaluationscode, abgerufen am 25.10.2026.  
**Nutzen:** Kausale Auswertung, Adapter, Trennung von Konfidenzschwelle und zeitlicher Entscheidungsregel sowie gemeinsame Betrachtung von Abbrüchen und Latenz. Anbieter-Ranglisten nicht ungeprüft übernehmen.

**S13 – LiveKit.** *eot-bench-data.*  
[Datensatz auf Hugging Face](https://huggingface.co/datasets/livekit/eot-bench-data)  
**Quellentyp:** Öffentlicher Datensatz, abgerufen am 25.10.2026.  
**Nutzen:** Mögliche deutsche Zusatzdaten oder Ersatzbasis. Spracheinteilung und Verwendung sind zusätzlich im Repository S12 beschrieben; Daten vor Übernahme selbst prüfen.

### 13.3 ElevenLabs

**S14 – ElevenLabs.** *Conversation flow.*  
[Offizielle Dokumentation](https://elevenlabs.io/docs/eleven-agents/customization/conversation-flow)  
**Quellentyp:** Herstellerdokumentation, abgerufen am 25.10.2026.  
**Nutzen:** Turn eagerness, Wartezeit- und Unterbrechungseinstellungen sowie Abgrenzung des Soft timeouts von der EOT-Erkennung.

**S15 – ElevenLabs.** *Realtime Speech-to-Text API.*  
[API-Referenz](https://elevenlabs.io/docs/api-reference/speech-to-text/v-1-speech-to-text-realtime)  
**Quellentyp:** Herstellerdokumentation, abgerufen am 25.10.2026.  
**Nutzen:** Commit-Strategien und verfügbare Ereignisse. Modellunterstützung und Kontoberechtigung für optionale Versuche praktisch prüfen.

**S16 – ElevenLabs.** *Models.*  
[Offizielle Modellübersicht](https://elevenlabs.io/docs/overview/models)  
**Quellentyp:** Herstellerdokumentation, abgerufen am 25.10.2026.  
**Nutzen:** Auswahl einer deutschen TTS-Stimme beziehungsweise eines dokumentierten TTS-Modells für die Demo oder einen separat gekennzeichneten synthetischen Zusatzsatz.

## 14. Nächste konkrete Schritte

1. Den gewählten Titel für die Anmeldung verwenden; er bleibt unabhängig von einzelnen Modellnamen.
2. S2 und S3 als erste frei verfügbare wissenschaftliche Texte lesen; S1 über den Hochschulzugang beschaffen.
3. Fünf bis zehn Pilotaufnahmen anfertigen und M1/M2 lokal auf der vorgesehenen Hardware testen.
4. Entscheiden, ob rohe Scores mit gemeinsamer Entscheidungsregel oder vollständige SDK-Systeme vergleichbar sind.
5. Die 100 Szenarien, Sprecherverteilung und Annotationsregeln vorbereiten; Split vor Parametereinstellung festlegen.
6. Erst anschließend Hauptkorpus aufnehmen, Parameter am Entwicklungssatz bestimmen und den eingefrorenen Test durchführen.

**Für die Anmeldung ist der Untersuchungsrahmen festgelegt.** Offen sind technische Pilotentscheidungen wie die tatsächlich installierbaren Paketversionen und die konkrete Score-Anbindung; diese ändern die Forschungsfrage nicht. Der nächste Meilenstein ist ein erfolgreicher technischer Pilot mit den beiden semantischen Modellen und der Baseline.

[S1]: https://doi.org/10.1016/j.csl.2020.101178
[S2]: https://aclanthology.org/2020.findings-emnlp.268/
[S3]: https://aclanthology.org/2025.iwsds-1.27/
[S4]: https://www.isca-archive.org/interspeech_2022/ekstedt22_interspeech.pdf
[S5]: https://aclanthology.org/2022.sigdial-1.51/
[S6]: https://www.isca-archive.org/interspeech_2023/ekstedt23_interspeech.html
[S7]: https://arxiv.org/abs/2608.25218
[S8]: https://docs.livekit.io/agents/logic/turns/turn-detector/
[S9]: https://livekit.com/blog/solving-end-of-turn-detection
[S10]: https://github.com/snakers4/silero-vad
[S11]: https://github.com/pipecat-ai/smart-turn
[S11b]: https://huggingface.co/pipecat-ai/smart-turn-v3/tree/main
[S12]: https://github.com/livekit/eot-bench
[S13]: https://huggingface.co/datasets/livekit/eot-bench-data
[S14]: https://elevenlabs.io/docs/eleven-agents/customization/conversation-flow
[S15]: https://elevenlabs.io/docs/api-reference/speech-to-text/v-1-speech-to-text-realtime
[S16]: https://elevenlabs.io/docs/overview/models
