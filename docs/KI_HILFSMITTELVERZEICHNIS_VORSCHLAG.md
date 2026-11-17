# KI-Hilfsmittelverzeichnis: Vorgaben und Vorschlag

Stand: 17.11.2026. Geprüfte Arbeit: [aktuelle Word-Fassung](./NLP_EOT_Tiemo_Kwiaton_Final.docx). Die Word-Datei wurde nicht verändert. Der Autor hat die Nutzung von „ChatGPT 6.1 sol“ und „ChatGPT Astra“ für die Textarbeit sowie „res sol“ für das Coding angegeben. Diese Bezeichnungen werden als Nutzerangaben übernommen; die genaue Bezeichnung von „res sol“ bleibt offen. Die folgenden Absatzzuordnungen sind eine redaktionelle Auswahl für den Entwurf, keine Rekonstruktion einzelner Dialoge.

## Vorgaben des Leitfadens

Grundlage: „Leitfaden zur formalen Gestaltung von Seminar- und Abschlussarbeiten“, vom Autor bereitgestellte PDF-Datei.

- **Abschnitt 1.6, gedruckte S. 8–9 (PDF-Seiten 16–17):** summarisches KI-Hilfsmittelverzeichnis sowie lokale Nachweise für KI-generierte Inhalte, die unverändert oder überarbeitet übernommen wurden. Genannt werden Textpassagen, Tabellen, Grafiken und weitere Darstellungsformen. Der lokale Nachweis soll System, soweit vorhanden Version, und Kommunikationsdatum enthalten. Bei überarbeiteten Übernahmen steht „Vgl.“ vor der Angabe.
- **Gedruckte S. 9:** KI-Kennzeichnung ersetzt keine Fachquelle. Verwendete Textgenerierung, Paraphrasierung und Übersetzung sind zusätzlich als PDF-Ausdrucke in einem ZIP-Ordner einzureichen.
- **Abschnitt 2.9, gedruckte S. 25 (PDF-Seite 33):** „Alle verwendeten KI-Anwendungen“ sind aufzuführen; Rechtschreibprüfung und Taschenrechner sind ausgenommen. Die Beispiele sind einfache System-/Versionsangaben. Eine Tabelle mit Aufgaben und Fundstellen ist eine hilfreiche Erweiterung, keine ausdrücklich verlangte Tabellenform.
- **Abschnitt 1.6:** Für konzeptionelle Entscheidungen und Recherche ist generell kein Nachweis erforderlich. Zusammen mit der allgemeinen Vorgabe aus Abschnitt 2.9 lässt sich dies so umsetzen: verwendete Anwendungen summarisch aufführen, für reine Konzeption oder Recherche keine einzelnen Textstellen markieren.
- **Abschnitt 1.1, gedruckte S. 1 (PDF-Seite 9):** Das KI-Hilfsmittelverzeichnis steht am Ende der aufgezählten Bestandteile, nach Literatur- und gegebenenfalls weiteren Quellenverzeichnissen. Es heißt im Leitfaden ausdrücklich „KI-Hilfsmittelverzeichnis“.

## Konkrete Kandidaten in dieser Arbeit

| Tätigkeit / System | Passende Stellen | Befund und Konsequenz |
| --- | --- | --- |
| ElevenLabs Text-to-Speech | Kapitel 3.2; synthetische Hälfte des Datensatzes; Anhang B und digitale Projektbeilage | **In der Arbeit dokumentiert:** 25 Aufnahmen mit synthetischer weiblicher Stimme. Als KI-Hilfsmittel aufnehmen. Tatsächlich verwendetes TTS-Modell und Erzeugungsdaten aus den Metadaten ergänzen. Scribe v3 Live ist das untersuchte Erkennungsmodell und darf nicht als TTS-Modell eingetragen werden. |
| KI-Unterstützung bei Einleitung und Forschungsfrage | Kapitel 1.1–1.3 | Vom Autor angegebene Textassistenz: ChatGPT 6.1 sol und ChatGPT Astra. Konkrete Absatzvorschläge stehen unten. |
| KI-Unterstützung bei der Implementierung | Kapitel 3.1; Prototyp in Anhang A, Aufnahme-/Synthesefunktion, Modelladapter, Evaluation und Diagrammerzeugung | Der Autor nennt für das Coding „res sol“. Für den Entwurf: Unterstützung bei der Implementierung des Evaluationsprototyps. Einzelne zusätzliche Tätigkeiten wie Tests oder Fehlerbehebung sind damit nicht gesondert belegt. Der Leitfaden regelt Code nicht ausdrücklich; eine transparente Beschreibung beim Prototyp ist sinnvoll. |
| KI-gestützte Textüberarbeitung | Insbesondere Kapitel 3.3, 4.2, 4.3 und 5 | **Konkrete Prüfkandidaten:** Die vorhandenen Überarbeitungsvorschläge behandeln Versuchsparameter, unterschiedliche Teilmengen bei Medianen, Limitationen und Fazit. Falls diese Vorschläge mit KI entstanden und übernommen wurden, sind die jeweiligen Absätze lokal nachzuweisen. Aus dem Formulierungsvergleich allein folgt noch keine belegte KI-Nutzung. |
| KI-generierte oder überarbeitete Grundlagenformulierungen | Kapitel 2.1–2.3 | **Zu bestätigen:** Falls aus KI-Entwürfen übernommen, lokale Nachweise zusätzlich zu den wissenschaftlichen bzw. Anbieterquellen. Reine Hilfe beim Auffinden der Literatur löst nach Abschnitt 1.6 keinen lokalen Nachweis aus. |
| KI-Hilfe bei Szenarientexten | Kapitel 3.2; Anhang B, Tabelle B1 und vollständige Sprechtexte in der Projektbeilage | **Zu bestätigen:** Hat KI die gesprochenen Kundennummer-, IBAN-, E-Mail- und Servicebeispiele formuliert, ist das von der anschließenden ElevenLabs-Spracherzeugung getrennt anzugeben. Für übernommene Texte in Tabelle B1 einen Nachweis vorsehen. |
| KI-generierte Abbildung oder übernommener Diagrammentwurf | Insbesondere Abbildung 1; gegebenenfalls Abbildungen 4–6 und Tabellen 1–3 | **Nur bei tatsächlicher Nutzung:** Diagramme aus Messwerten und Screenshots sind nicht allein deshalb KI-generiert, weil der Prototyp KI untersucht. Bei KI-Hilfe nur am Programmcode diesen Umfang beschreiben. Bei übernommenen KI-Inhalten bzw. Darstellungen greift die lokale Nachweispflicht. |
| LiveKit Turn Detector v1 Cloud, ElevenLabs Scribe v3 Live und Silero VAD | Kapitel 2.2–2.3, 3.1, 3.3 und 4; Anhang C | **Als eingesetzte Untersuchungsverfahren dokumentiert.** Wegen „alle verwendeten KI-Anwendungen“ ist eine Aufnahme mit dem Zweck „Untersuchungsgegenstand / automatisierte Verarbeitung der Testaufnahmen“ eine transparente Lösung. Daraus folgt kein KI-Autorschaftsnachweis für die Ergebnisdiskussion. |

Die ausgewählten Stellen für den Entwurf betreffen Kapitel 1.1–1.3, 3.3, 4.2, 4.3 und 5 sowie gegebenenfalls die Sprechtexte in Anhang B. Es sollten tatsächliche Übernahmen dokumentiert werden; Stil oder ein vermeintlich unrealistischer Umfang sind kein Nutzungsbeleg.

## Entwurf für das Verzeichnis

Nur bestätigte Zeilen übernehmen. Eckige Klammern sind offene Angaben und vor Abgabe zu ersetzen. Verschiedene Aufgaben desselben Systems können in einer Zeile zusammengefasst werden.

| KI-Anwendung / Version | Verwendungszweck | Bereich der Arbeit |
| --- | --- | --- |
| ElevenLabs Text-to-Speech, [tatsächlich verwendetes Modell] | Erzeugung von 25 synthetischen Sprachaufnahmen mit einer weiblichen Stimme | Kapitel 3.2; Testdatensatz in der digitalen Projektbeilage |
| „res sol“ [genaue System-/Modellbezeichnung ergänzen] | Unterstützung bei der Implementierung des Evaluationsprototyps | Kapitel 3.1; Anhang A |
| ChatGPT, Modelle „6.1 sol“ und „Astra“ (Bezeichnungen laut Autor) | Unterstützung bei Formulierung und Überarbeitung ausgewählter Textabschnitte | Kapitel 1.1–1.3, 3.3, 4.2, 4.3 und 5; Absatzabgrenzung siehe unten |
| [tatsächlich verwendeter KI-Assistent und Version] | [bestätigte Erstellung oder Überarbeitung der Szenarientexte] | Kapitel 3.2; Anhang B, Tabelle B1 |
| LiveKit Turn Detector v1 Cloud | Untersuchung der End-of-Turn-Erkennung anhand der Testaufnahmen | Kapitel 2–4; Anhang C |
| ElevenLabs Scribe v3 Live | Untersuchung der End-of-Turn-Erkennung anhand der Testaufnahmen | Kapitel 2–4; Anhang C |
| Silero VAD, [verwendete Version] | Erkennung von Sprachaktivität als Grundlage der pausenbasierten Baseline und der implementierten Entscheidungsregeln | Kapitel 2–4; Anhang C |

TTS-Nutzung und Untersuchungsverfahren sind durch die Projektunterlagen gestützt. Die verwendeten Text- und Coding-Assistenten wurden vom Autor benannt. Welches der beiden Textmodelle welchen Absatz bearbeitet hat, ist nicht angegeben; deshalb erfolgt keine erfundene Einzelzuordnung. Die Auswahl unten beschreibt geeignete Stellen für den Entwurf. Die Szenarientexte bleiben ein optionaler Eintrag.

## Ausgewählte Absätze für die lokalen Nachweise

Die folgenden Absatzanfänge stammen aus der aktuellen Word-Fassung. Die Kennzeichnung gehört jeweils ans Absatzende. Die Auswahl folgt dem Wunsch des Autors, konkrete Stellen vorzuschlagen; sie besagt nicht, dass andere tatsächlich KI-bearbeitete Stellen von der Kennzeichnung ausgenommen wären.

| Stelle | Eindeutiger Absatzanfang | Für den Entwurf beschriebene Unterstützung |
| --- | --- | --- |
| Kapitel 1.1, zweiter Absatz | „Pausenbasierte Verfahren schließen eine Eingabe ab, sobald eine festgelegte Stille überschritten wird.“ | Formulierung des Zielkonflikts zwischen vorzeitigen Abschlüssen und Wartezeit |
| Kapitel 1.2, erster Absatz | „Ziel dieser Arbeit ist es, zu untersuchen, ob semantische EOT-Verfahren den Abschluss einer Nutzereingabe zuverlässiger erkennen als pausenbasierte Verfahren.“ | Präzisierung von Zielsetzung und Vergleichskriterien |
| Kapitel 1.3, erster Absatz | „Die Untersuchung vergleicht die semantischen EOT-Verfahren von LiveKit und ElevenLabs mit einer klassischen, pausenbasierten EOT-Erkennung.“ | Strukturierung und Formulierung der Beschreibung des methodischen Vorgehens |
| Kapitel 3.3, Absatz zu den Kennzahlen | „Verglichen werden der Anteil vorzeitiger Abschlüsse und die mediane Wartezeit der nicht vorzeitig beendeten Beiträge.“ | Verständliche Darstellung der Auswertungskriterien |
| Kapitel 4.2, Absatz zur Zeitabweichung | „Abbildung 5 zeigt die zeitliche Abweichung der Endentscheidungen vom Referenzende.“ | Formulierung des Ergebnisvergleichs und Einordnung der unterschiedlichen Teilmengen |
| Kapitel 4.3, letzter Absatz | „Die Aussagekraft bleibt auf 50 Eingabebeispiele aus zwei Stimmquellen begrenzt.“ | Sprachliche Verdichtung der methodischen Limitationen |
| Kapitel 5, Absatz zur Forschungsfrage | „Bezogen auf die Forschungsfrage zeigen die ausgewählten semantischen Konfigurationen im untersuchten Datensatz weniger vorzeitige Abschlüsse als die Baseline mit 1.500 ms Stille-Timeout.“ | Präzise und eingeschränkte Formulierung der Antwort auf die Forschungsfrage |

Die Tätigkeitsbeschreibungen sind Formulierungsvorschläge für die Dokumentation. Originaldialoge bleiben die Grundlage, um Umfang, verwendetes Modell und Datum eines konkreten lokalen Nachweises festzustellen.

## Muster für lokale Nachweise

Bei überarbeiteter Übernahme eines KI-Textes als Fußnote am betroffenen Absatz:

> Vgl. [System], [Version, soweit vorhanden], Kommunikation vom [tatsächliches Datum]; Vorschlag zur Formulierung dieses Absatzes, durch den Autor überarbeitet.

Bei unveränderter Übernahme entfällt gemäß Leitfaden das „Vgl.“; die Übernahme ist entsprechend dessen Zitierbeispiel kenntlich zu machen. Fachquellen bleiben zusätzlich erforderlich. Ein pauschaler Hinweis für ein vollständiges Kapitel sollte nicht die Kennzeichnung einzelner übernommener Absätze ersetzen.

Für die synthetischen Audios bietet sich als ergänzende Herkunftsangabe in Kapitel 3.2 oder bei der Datensatzbeschreibung an:

> Die synthetischen Sprachaufnahmen wurden mit ElevenLabs Text-to-Speech, Modell [Modellkennung], Stimme [Stimmenbezeichnung], am [Datum/Zeitraum] erzeugt.

Dies ist ein Vorschlag zur transparenten Methodendokumentation; der Leitfaden enthält kein ausdrückliches Zitiermuster für synthetische Audiodateien.

## Vor der Übernahme noch zu klären

1. Genaue System-/Modellbezeichnung des als „res sol“ genannten Coding-Assistenten ergänzen. Die Textmodelle sind laut Autor ChatGPT 6.1 sol und ChatGPT Astra.
2. Für die oben ausgewählten Absätze anhand vorhandener Dialoge das jeweilige Textmodell zuordnen. Die Auswahl der Stellen ist erledigt; zusätzliche tatsächlich übernommene KI-Inhalte bleiben ebenfalls kennzeichnungspflichtig.
3. Tatsächliche Kommunikations- und Erzeugungsdaten ermitteln; keine nachträglichen Beispieldaten als echte Nutzungsdaten einsetzen.
4. Verwendete Dialoge zur Textgenerierung, Paraphrasierung und Übersetzung als PDF sichern und gemäß Leitfaden in einer ZIP-Beilage abgeben. Fehlende Originaldialoge nicht durch nachgestellte Prompts ersetzen.

## Lokale Prüfbasis

- [Seminararbeit](./NLP_EOT_Tiemo_Kwiaton_Final.docx): Kapitelbezüge, dokumentierte TTS-Nutzung und aktuelle Verzeichnisse.
- [Konkrete Überarbeitungsvorschläge](./KONKRETE_ERSETZUNGEN_NLP_VAD.md): Kandidaten für einen Abgleich mit verwendeten KI-Dialogen.
- [Analyse der Vorfassung](./ANALYSE_NLP_VAD_v3.md): Hinweise auf Methoden-, Ergebnis- und Formulierungsänderungen.
- [Literaturrecherche](../LITERATURRECHERCHE_THEORETISCHE_GRUNDLAGEN.md): vorhandene Quellenarbeit; allein kein Beleg für KI-generierte Grundlagenabsätze.
- [Datensatzplanung](./DATENSATZ_25_PLAN.md) und [Projektbeschreibung](../README.md): synthetische Stimmquelle und Datensatzumfang.
