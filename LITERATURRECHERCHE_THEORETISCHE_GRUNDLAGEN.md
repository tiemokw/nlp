# Literaturrecherche zu den theoretischen Grundlagen

**Recherchestand: 12. November 2026.**

**Seminararbeit:** End-of-Turn Detection in deutschsprachigen Voicebots: Ein empirischer Vergleich semantischer und pausenbasierter Verfahren.

Dies ist eine gezielte Literaturrecherche zur Voicebot-Pipeline, zum pausenbasierten Endpointing und zur semantisch unterstützten Turn-End-Erkennung. Sie ist keine systematische Literaturübersicht. Die drei Fachpublikationen wurden im Volltext an den relevanten Stellen geprüft; Herstellerbeiträge und Dokumentation wurden direkt beim jeweiligen Anbieter gelesen. Literatur- und Modellbeschreibungen ersetzen keine eigenen Messergebnisse.

Die bibliografischen Daten stehen zusätzlich in [einer BibLaTeX-Datei](./literatur_theoretische_grundlagen.bib). Die Kennungen Q1 bis Q8 entsprechen den dortigen Einträgen.

## 1. Empfohlener Aufbau von Kapitel 2

**2 Theoretische Grundlagen: ungefähr 350 Wörter**

| Abschnitt | Inhalt | Richtwert | Quellen |
|---|---|---:|---|
| 2.1 Voicebot-Architektur und Turn-Taking | Modulare Pipeline, Aufgaben von STT/ASR, Dialogverarbeitung und TTS; Einordnung der Endentscheidung | 100 Wörter | Q1, ergänzend Q8 |
| 2.2 Pausenbasierte und semantische End-of-Turn Detection | VAD, Stille-Timeout, Unterschied zwischen Pause und Beitragsende, sprachliche und akustische Hinweise | 140 Wörter | Q2, Q3 |
| 2.3 LiveKit Turn Detector und ElevenLabs Scribe | Funktionsprinzipien der konkret gewählten Verfahren, knappe Abgrenzung | 110 Wörter | Q4 bis Q7 |

Die konkreten Parameter, Testdaten und Messregeln gehören in die Kapitel über Versuchsaufbau und Evaluation. Sie sollten nicht ein zweites Mal in den theoretischen Grundlagen beschrieben werden.

## 2. Fachliche Festlegungen für die Arbeit

### 2.1 Pipeline und Rolle der Turn-End-Erkennung

Eine modulare Sprachverarbeitung umfasst ASR/STT, Sprachverstehen, Dialogsteuerung, Antwortformulierung und TTS. Q1 beschreibt diese klassische Aufteilung; Q8 dokumentiert eine aktuelle STT-LLM-TTS-Pipeline. Ein LLM kann mehrere Aufgaben übernehmen, die in der klassischen Architektur getrennten Modulen zugeordnet sind. Die Pipeline sollte im Text ausdrücklich als betrachtete Architektur bezeichnet werden; sie ist keine Aussage über sämtliche Voicebots.

Für unsere Darstellung bietet sich folgende vereinfachte Abfolge an:

**Audioeingabe → STT/ASR → Dialogverarbeitung und Antwortgenerierung → TTS → Audioausgabe.**

VAD und Turn-End-Erkennung ergänzen diese Verarbeitung um die Entscheidung über Sprachaktivität und den Abschluss des Nutzerbeitrags. Ein separater Turn-Detektor muss kein ausschließlich vor STT geschaltetes Modul sein. Q1, Abschnitt 2.3.1, belegt, dass ASR bereits während der Eingabe Teiltranskripte erzeugen kann. Q8 beschreibt die Verarbeitung nach dem erkannten Turn-Ende und vor der Antwort. Daher sollte die Seminararbeit nicht pauschal behaupten, dass EOT Detection erst den Start der Spracherkennung auslöst.

### 2.2 Begriffe

- **Voice Activity Detection (VAD):** Erkennung von Sprachaktivität beziehungsweise Nicht-Sprache; kein hinreichender Nachweis dafür, dass eine Person ihren Beitrag abgeschlossen hat. Beleg: Q5, Overview.
- **Pausenbasiertes Endpointing:** Für unsere Baseline die Kombination aus VAD und festgelegtem Stille-Timeout. Beleg: Q2, Abschnitt 4.
- **End-of-Turn Detection (EOT):** Entscheidung, ob der aktuelle Beitrag beendet ist und das System den Turn übernehmen soll. Beleg: Q2, Abschnitt 4.
- **Semantisch unterstützte EOT Detection:** Nutzung zusätzlicher gelernter Hinweise, etwa sprachlicher Vollständigkeit; bei den betrachteten aktuellen Produkten können auch akustische Merkmale einfließen. Belege: Q3, Q4, Q6.

„End-of-Speech Detection“ sollte nicht als fester Name einer ausschließlich klassischen Modellklasse dem Begriff „semantisch“ gegenübergestellt werden. Auch ein pausenbasiertes Verfahren trifft im Gesamtsystem eine Turn-End-Entscheidung. Die Literatur verwendet außerdem EOT und End-of-Utterance teilweise überlappend (Q2). Deshalb werden die Begriffe für diese Arbeit ausdrücklich operationalisiert.

## 3. Wissenschaftliche Quellen

### Q1 — Voicebot-Architektur und Streaming-ASR

**Literaturangabe:** Kennington, Casey; Lison, Pierre; Schlangen, David (2025): Prior Lessons of Incremental Dialogue and Robot Action Management for the Age of Language Models. In: *Dialogue & Discourse*, 16(3), S. 96–130. DOI: [10.5210/dad.2025.305](https://doi.org/10.5210/dad.2025.305).

**Typ und Eignung:** Wissenschaftlicher Zeitschriftenbeitrag mit Literaturüberblick; der Anwendungskontext umfasst Robotik. Die allgemeinen Architektur- und ASR-Abschnitte eignen sich für unsere Grundlagen.

**Geprüfte Fundstellen:**

- Abschnitt 2.1, Abbildung 2, **S. 99** (PDF-Seite 4): modulare Architektur.
- Abschnitt 2.1, letzter Absatz auf S. 99 und Fortsetzung auf **S. 100** (PDF-Seiten 4–5): Aufgaben der fünf Komponenten.
- Abschnitt 2.3.1, erster Absatz, **S. 102** (PDF-Seite 7): Streaming-Eingabe und Teiltranskripte.
- Abschnitt 3.1.3, **S. 110** (PDF-Seite 15): zeitliche Steuerung und Turn-End-Vorhersage.

**Nachprüfen:** [Verlagsseite](https://journals.uic.edu/ojs/index.php/dad/article/view/13353), [Volltext](https://journals.uic.edu/ojs/index.php/dad/article/download/13353/12124/93251), [lokale Textauszüge](./.cache/literatur_theoretische_grundlagen/kennington_lison_schlangen_2025_fundstellen.txt), dort Z. 4–8, 35–48, 115–127 und 146–153.

**Muster für eine Fußnote:** Vgl. Kennington, C. et al. (2025), S. 99 f.; zur laufenden Transkription S. 102.

### Q2 — Pausenbasiertes Endpointing und Einordnung der EOT-Aufgabe

**Literaturangabe:** Castillo-López, Galo; de Chalendar, Gaël; Semmar, Nasredine (2025): A Survey of Recent Advances on Turn-taking Modeling in Spoken Dialogue Systems. In: *Proceedings of the 15th International Workshop on Spoken Dialogue Systems Technology*, S. 254–271. Bilbao: Association for Computational Linguistics.

**Typ und Eignung:** Veröffentlichter wissenschaftlicher Workshop-Survey. Direkte Grundlage für unsere Begriffserklärung und den Zielkonflikt zwischen Unterbrechungen und Wartezeit.

**Geprüfte Fundstellen:**

- Abschnitt 1, **S. 254** (PDF-Seite 1), Absatz mit der Einführung von VAD und Stille-Schwellen: kurze und lange Timeouts haben gegenläufige Nachteile.
- Abschnitt 4, erster Absatz, **S. 257** (PDF-Seite 4): Definition der EOT-/EOU-Aufgabe; Einteilung in silence-based, IPU-based und continuous; VAD plus Stille-Schwelle.

**Nachprüfen:** [Publikationsseite](https://aclanthology.org/2025.iwsds-1.27/), [Volltext](https://aclanthology.org/2025.iwsds-1.27.pdf), [lokale Textauszüge](./.cache/literatur_theoretische_grundlagen/castillo_lopez_et_al_2025_fundstellen.txt), Z. 43–58 und 113–137.

**Muster für eine Fußnote:** Vgl. Castillo-López, G. et al. (2025), S. 254, 257.

### Q3 — Sprachliche Vollständigkeit und Dialogkontext

**Literaturangabe:** Ekstedt, Erik; Skantze, Gabriel (2020): TurnGPT: a Transformer-based Language Model for Predicting Turn-taking in Spoken Dialog. In: *Findings of the Association for Computational Linguistics: EMNLP 2020*, S. 2981–2990. DOI: [10.18653/v1/2020.findings-emnlp.268](https://doi.org/10.18653/v1/2020.findings-emnlp.268).

**Typ und Eignung:** Wissenschaftlicher Konferenzbeitrag mit eigener Modellentwicklung und Evaluation. Belegt die Bedeutung sprachlicher und kontextueller Hinweise; er untersucht nicht die aktuellen LiveKit- oder ElevenLabs-Modelle.

**Geprüfte Fundstellen:**

- Abschnitt 1, **S. 2981** (PDF-Seite 1): Problematik festgelegter Stilledauern.
- Abschnitt 2, **S. 2982** (PDF-Seite 2): syntaktische und pragmatische Vollständigkeit, Abbildung 1 und begleitende Erklärung.
- Abschnitt 6.3, **S. 2986** (PDF-Seite 6): Ablation des vorausgehenden Dialogkontexts; Ergebnisse gelten für TurnGPT.

**Nachprüfen:** [Publikationsseite](https://aclanthology.org/2020.findings-emnlp.268/), [Volltext](https://aclanthology.org/2020.findings-emnlp.268.pdf), [lokale Textauszüge](./.cache/literatur_theoretische_grundlagen/ekstedt_skantze_2020_fundstellen.txt), insbesondere Z. 130–176 und 230–247.

**Muster für eine Fußnote:** Vgl. Ekstedt, E.; Skantze, G. (2020), S. 2982; für die Ablation S. 2986.

## 4. Originalquellen der Hersteller

### Q4 — LiveKit: Architekturbeitrag

**Literaturangabe:** Mou, Chenghao; Weston, Leigh; Fields, Jerad (2026): Solving end-of-turn detection: LiveKit Turn Detector v1.0. LiveKit Blog, 17.06.2026, o. S. Zugriff: 12.11.2026.

**Belegbarer Inhalt:** Der Hersteller beschreibt eine direkte Audioverarbeitung und die Zusammenführung eines semantischen und eines akustischen Zweigs. Dieser Beitrag eignet sich für die Architektur von v1, nicht als unabhängiger Nachweis einer Überlegenheit.

**Fundstelle:** Abschnitt **Listening instead of reading**, Absätze 1–3 und zugehörige Architekturgrafik. [Original](https://livekit.com/blog/solving-end-of-turn-detection), [lokale Textfassung](./.cache/literatur_theoretische_grundlagen/livekit_blog_2026_text.txt), Z. 28–32.

**Muster für eine Fußnote:** Vgl. Mou, C. et al. (2026), o. S., Abschnitt Listening instead of reading.

### Q5 — LiveKit: aktuelle technische Dokumentation

**Literaturangabe:** LiveKit (o. J.): LiveKit turn detector. LiveKit Documentation, o. S. Zugriff: 12.11.2026.

**Belegbarer Inhalt:** Ergänzung zu VAD; direktes Audio als Eingabe; Varianten v1 und v1-mini; Zusammenspiel mit Endpointing. Die aktuelle Audio-Variante darf nicht mit dem älteren textbasierten LiveKit-Detektor gleichgesetzt werden.

**Fundstellen:** **Overview**, Absätze 1–2; **Audio turn detector**, erster Absatz und Aufzählung der Varianten; **Endpointing defaults**. [Original](https://docs.livekit.io/agents/logic/turns/turn-detector/), [lokale Textfassung](./.cache/literatur_theoretische_grundlagen/livekit_turn_detector_doku_text.txt), Z. 10–13, 23–25 und 71–80.

**Muster für eine Fußnote:** Vgl. LiveKit (o. J.), LiveKit turn detector, o. S., Abschnitt Audio turn detector.

### Q6 — ElevenLabs: Modellveröffentlichung

**Literaturangabe:** Kim, Min (2026): Introducing Scribe v3 and v3 Live, our most accurate speech to text models. ElevenLabs Blog, 10.11.2026, o. S. Zugriff: 12.11.2026.

**Belegbarer Inhalt:** Der Anbieter beschreibt für Scribe v3 Live die Nutzung von Gesprächskontext und Audio für Turn Detection. Das Zahlenbeispiel passt zum praktischen Ausgangspunkt unserer Arbeit; es ist kein Beleg für eine bestimmte Fehlerhäufigkeit bei der Telekom. Die internen Modellbausteine werden hier nicht mit derselben Detailtiefe wie bei LiveKit offengelegt.

**Fundstelle:** Abschnitt **Turn detection that listens to the conversation**, Absatz 1. [Original](https://elevenlabs.io/blog/scribe-v3), [lokale Textfassung](./.cache/literatur_theoretische_grundlagen/elevenlabs_scribe_v3_blog_2026_text.txt), Z. 45–46; Autor und Datum Z. 24–27.

**Muster für eine Fußnote:** Vgl. Kim, M. (2026), o. S., Abschnitt Turn detection that listens to the conversation.

### Q7 — ElevenLabs: Commit-Strategien

**Literaturangabe:** ElevenLabs (o. J.): Transcripts and commit strategies. ElevenLabs Documentation, o. S. Zugriff: 12.11.2026.

**Belegbarer Inhalt:** Die Dokumentation unterscheidet Teiltranskripte und finalisierte Segmente sowie manuelle, VAD-basierte und Turn-Prediction-Commits. Turn Prediction ist für Scribe v3 Live dokumentiert. Auch dabei bleibt ein Stille-Timeout wirksam. Deshalb muss eine Evaluation den vollständigen Commit-Mechanismus berücksichtigen.

**Fundstellen:** **Overview**, Aufzählung der beiden Transkriptarten; **Voice Activity Detection (VAD)**, erster Absatz; **Turn prediction**, Beschreibung vor und nach dem JSON-Beispiel. [Original](https://elevenlabs.io/docs/eleven-api/guides/how-to/speech-to-text/realtime/transcripts-and-commit-strategies), [lokale Textfassung](./.cache/literatur_theoretische_grundlagen/elevenlabs_commit_strategies_doku_text.txt), Z. 38–40, 75–78 und 91–103. Die kombinierte Commit-Regel steht in Z. 102.

**Muster für eine Fußnote:** Vgl. ElevenLabs (o. J.), Transcripts and commit strategies, o. S., Abschnitt Turn prediction.

### Q8 — Ergänzung: aktuelle STT-LLM-TTS-Pipeline

**Literaturangabe:** LiveKit (o. J.): Pipeline nodes and hooks. LiveKit Documentation, o. S. Zugriff: 12.11.2026.

**Belegbarer Inhalt:** Konkrete Verarbeitungsschritte für STT, LLM und TTS sowie ein Hook nach Abschluss des Nutzerturns und vor der Antwort. Dient als aktuelles Implementierungsbeispiel zur wissenschaftlich beschriebenen modularen Pipeline aus Q1.

**Fundstellen:** **Overview**, Aufzählung der STT-LLM-TTS-Knoten; **On user turn completed**, erster Absatz; **STT node**, erster Absatz. [Original](https://docs.livekit.io/agents/logic/nodes/), [lokale Textfassung](./.cache/literatur_theoretische_grundlagen/livekit_pipeline_nodes_doku_text.txt), Z. 20–25, 104–105 und 309–310.

## 5. Zuordnung von Aussagen und Belegen

| Aussage für die Seminararbeit | Hauptbeleg | Konkrete Fundstelle |
|---|---|---|
| Eine modulare Voicebot-Pipeline enthält Spracherkennung, Dialogverarbeitung und Sprachsynthese. | Q1 | S. 99–100, Abschnitt 2.1, Abbildung 2 |
| Streaming-ASR kann während des Sprechens Teiltranskripte erzeugen. | Q1 | S. 102, Abschnitt 2.3.1, erster Absatz |
| Eine aktuelle Kaskade lässt sich als STT → LLM → TTS darstellen. | Q8 | Overview, Liste der Pipeline-Knoten |
| Der erkannte Abschluss des Nutzerturns liegt vor der Antwort. | Q8 | On user turn completed, erster Absatz |
| VAD allein erkennt Sprachaktivität, nicht zuverlässig den Abschluss eines Beitrags. | Q5 | Overview |
| Kurze Stille-Timeouts können Unterbrechungen, lange Timeouts Wartezeiten verursachen. | Q2 | S. 254, Einleitung |
| Pausenbasiertes Endpointing lässt sich durch VAD plus Stille-Schwelle realisieren. | Q2 | S. 257, Abschnitt 4 |
| Sprachliche Vollständigkeit und Kontext können für die Turn-Vorhersage relevant sein. | Q3 | S. 2982; modellspezifische Ablation S. 2986 |
| LiveKit v1 verarbeitet Audio mit semantischen und akustischen Zweigen. | Q4 | Listening instead of reading, Absätze 1–3 |
| ElevenLabs beschreibt Kontext- und Audiosignale für Scribe v3 Live. | Q6 | Turn detection that listens to the conversation |
| Bei Scribe v3 Live kann zusätzlich zur Turn Prediction ein Stille-Timeout einen Commit auslösen. | Q7 | Turn prediction, Absatz nach dem JSON-Beispiel |

## 6. Zitierweise und Aussagegrenzen

Für die eigentliche Arbeit werden die **gedruckten Seitenzahlen** der Fachartikel verwendet. PDF-Seitenzahlen helfen beim Auffinden, ersetzen die bibliografischen Seitenzahlen aber nicht. Bei Webseiten werden Autor beziehungsweise Organisation, Datum oder o. J., Titel, URL und Zugriffstag angegeben. Eine Abschnittsüberschrift kann in der Fußnote die Fundstelle präzisieren. Die getrennten Angaben für Literaturverzeichnis und Fußnote müssen an den geltenden Hochschulleitfaden angepasst werden.

Die zusätzlich angegebenen **Zeilennummern gehören ausschließlich zu den gespeicherten lokalen Textfassungen** dieser Recherche. Sie sind nachvollziehbare Arbeitshilfen, keine stabilen Zeilennummern der Originalwebseiten. In den PDF-Auszügen sind die ausgewählten Seiten nacheinander extrahiert; Seitenwechsel stehen ausdrücklich im Text. Die Original-PDFs und ein Prüfsummenmanifest liegen im Recherchecache.

Für die Grundlagen sind Q1 und Q2 die tragenden Überblicksquellen; Q3 liefert ein konkretes Forschungsergebnis zur Nutzung sprachlicher Information. Q4 bis Q8 belegen Produktbeschreibungen und Schnittstellen. Anbieterbenchmarks und Formulierungen zur eigenen Marktführerschaft werden nicht als unabhängige Vergleichsergebnisse übernommen. Aus TurnGPT-Ergebnissen folgt keine nachgewiesene Überlegenheit von LiveKit oder ElevenLabs in unserem Versuch.

Die Bezeichnung der Vergleichsbedingungen sollte lauten: **pausenbasiertes Endpointing** und **semantisch unterstützte EOT Detection**. Der Seminartitel bleibt bestehen. Der Begriff semantisch bedeutet hier nicht, dass akustische Merkmale oder Timeout-Regeln ausgeschlossen sind. Für ElevenLabs ist das konkrete Produkt **Scribe v3 Live mit Turn Prediction** zu benennen; ein beliebiges Scribe-Modell oder dessen VAD-Modus ist nicht automatisch dieselbe Vergleichsbedingung. Die Verfügbarkeit im verwendeten Konto und der tatsächlich gemessene Commit-Modus sind Teil der Versuchsdurchführung, nicht durch Literatur allein nachgewiesen.
