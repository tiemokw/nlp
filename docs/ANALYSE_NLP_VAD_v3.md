# Gesamtanalyse der Seminararbeit zur EOT-Erkennung

Geprüfte Fassung: [NLP_VAD_Tiemo_Kwiaton_v3.docx](./NLP_VAD_Tiemo_Kwiaton_v3.docx), Stand 13. November 2026.

Die Prüfung umfasst den gesamten gespeicherten Text, Tabellen, Fußnoten, Literaturverzeichnis, Anhang und die sechs eingebetteten Abbildungen. Die Ergebniszahlen wurden zusätzlich mit den gespeicherten finalen Evaluationsläufen abgeglichen. Die Word-Datei wurde nicht verändert. Dies ist eine inhaltliche und sprachliche Analyse; eine vollständige Prüfung des gerenderten Seitenlayouts ist damit nicht verbunden.

## 1 Gesamturteil

Der rote Faden ist erkennbar: Ein praktisches Endpointing-Problem führt zur Forschungsfrage; darauf folgen Grundlagen, Prototyp und Datensatz, Konfigurationsvergleich sowie eine eingeschränkte Antwort im Fazit. Die Arbeit benötigt keine grundsätzlich neue Gliederung.

Die wesentlichen Ergebniszahlen stimmen miteinander überein. Die ausgewählten Konfigurationen ergeben tatsächlich 29, 19 beziehungsweise zehn vorzeitige Abschlüsse unter jeweils 50 Beiträgen. Auch die genannten medianen Wartezeiten von 1.557, 597 und 911 ms sind durch die gespeicherten Ergebnisse gedeckt.

Die größten Schwächen liegen an drei Stellen:

1. Kapitel 3 beschreibt teilweise einen älteren Stand des Versuchsaufbaus, während Kapitel 4 die spätere Konfigurationsauswahl darstellt.
2. Ziel, Modellvergleich und Messprinzip werden mehrfach angekündigt und erklärt.
3. Einige für die Interpretation wichtige Festlegungen werden zu spät, unvollständig oder mit missverständlichen Begriffen eingeführt.

Die vorhandene Einschränkung zur Auswahl und Bewertung auf demselben Datensatz ist richtig und sollte erhalten bleiben.

## 2 Konkrete Ungereimtheiten und Korrekturen

### 2.1 LiveKit-Voreinstellung und ausgewählte Konfiguration widersprechen sich

**Fundstelle:** Kapitel 3.3, Absatz beginnend mit „Die pausenbasierte Baseline …“, gegenüber Kapitel 4.1 und Abbildung 4.

Kapitel 3.3 nennt die für Deutsch vorgesehene Anbieterschwelle als verwendete Einstellung. Kapitel 4.1 untersucht dagegen vier LiveKit-Schwellen und wählt 0,85 für den abschließenden Vergleich aus. Die deutsche Voreinstellung beträgt laut Tabelle und Laufmetadaten 0,4936.

Das sind unterschiedliche Konfigurationen. Kapitel 3 muss den tatsächlichen Ablauf beschreiben: zunächst mehrere Schwellen untersuchen, anschließend eine Konfiguration für den Modellvergleich auswählen. Die Voreinstellung ist dabei ein Ausgangspunkt.

**Vorschlag:**

> Für LiveKit werden die Deutsch-Voreinstellung von 0,4936 und die Schwellen 0,85, 0,90 und 0,95 untersucht. Die Auswahl für den abschließenden Vergleich erfolgt anhand der Ergebnisse in Kapitel 4.1.

Bei Scribe gilt dieselbe Trennung: 0,95 ist die später ausgewählte Schwelle, nicht die einzige untersuchte Einstellung.

### 2.2 Abbildung 2 zeigt eine andere maximale Stillezeit

**Fundstelle:** Screenshot in Kapitel 3.1 gegenüber Kapitel 3.3 und Kapitel 4.1.

Im Screenshot steht „maximal 2500 ms“. Der Text nennt 5.000 ms. Die vier gespeicherten finalen Läufe bestätigen 5.000 ms.

Außerdem zeigt der Screenshot für LiveKit „Schwelle automatisch · Deutsch“, während der abschließende Modellvergleich 0,85 verwendet.

**Vorschlag:** Den Screenshot mit den finalen Einstellungen aktualisieren. Alternativ deutlich als Beispiel der Oberfläche kennzeichnen und die gültigen Versuchseinstellungen ausschließlich in Kapitel 3.3 festhalten. Ein aktualisierter Screenshot ist eindeutiger.

### 2.3 Aus sechs Inhaltsarten und vier Sprechverläufen entstehen zunächst 24 Szenarien

**Fundstelle:** Kapitel 3.2, „Für beide Varianten werden dieselben 25 Szenarien verwendet. Diese ergeben sich aus sechs Inhaltsarten und vier Sprechverläufen.“

Sechs mal vier ergibt 24. Der zusätzliche IBAN-Fall wird erst in Kapitel 4.3 erklärt. Damit erscheint die Datensatzbeschreibung zunächst rechnerisch unstimmig.

**Vorschlag:**

> Sechs Inhaltsarten und vier Sprechverläufe ergeben 24 Szenarien. Ein zusätzlicher IBAN-Fall mit 3,5 Sekunden Suchpause ergänzt den Datensatz auf 25 Szenarien beziehungsweise 50 Audiodateien aus zwei Stimmquellen.

Das erklärt zugleich die zehn IBAN-Dateien gegenüber jeweils acht Dateien der anderen Inhaltsarten in Abbildung 6.

### 2.4 Die 150 Auswertungen gelten nur für einen Vergleich mit drei Konfigurationen

**Fundstelle:** Kapitel 3.3, erster Absatz.

50 Dateien mal drei Vergleichsbedingungen ergeben 150 Einzelbewertungen. Kapitel 4 untersucht aber mehrere Konfigurationen je Modell. Für die gesamte Untersuchung wurden deshalb mehr als 150 Einzelbewertungen durchgeführt.

**Vorschlag:**

> Jede Konfiguration wird an allen 50 Audiodateien ausgewertet. Der abschließende Vergleich der zwei ausgewählten Modellkonfigurationen mit der Baseline umfasst 150 Einzelbewertungen.

Die 150 Bewertungen sind keine 150 unterschiedlichen oder unabhängigen Eingaben.

### 2.5 Fallback-Ergebnisse werden angekündigt, aber nicht berichtet

**Fundstelle:** Ende von Kapitel 3.3 gegenüber Kapitel 4.

Die Methodik kündigt an, Abschlüsse durch den maximalen Stille-Timeout gesondert auszuweisen. In den Ergebnissen fehlen diese Angaben.

Für die ausgewählten Konfigurationen enthalten die gespeicherten Daten:

| Vergleichsbedingung | Abschlüsse durch den Fallback |
| --- | ---: |
| LiveKit 0,85 | 2 von 50 |
| Scribe 0,95 | 1 von 50 |

Alle drei Fälle liegen nach dem Referenzende und außerhalb des Bewertungsfensters. Die 1.500-ms-Regel der Baseline ist deren reguläre Entscheidungsregel und wird hier nicht als Fallback gezählt.

**Vorschlag für Kapitel 4.2:**

> Zwei LiveKit-Abschlüsse und ein Scribe-Abschluss entstehen erst durch den Fallback.

Diese kurze Ergänzung ist besser, als die Ankündigung vollständig zu streichen: Sie macht sichtbar, dass nicht jede Endentscheidung auf einem ausreichenden Modellscore beruht.

### 2.6 Die Beschreibung von Scribe muss Herstellerfunktion und konkrete Integration unterscheiden

**Fundstelle:** Kapitel 2.3 gegenüber Kapitel 3.3 und der Implementierung.

Kapitel 2.3 erklärt die Finalisierung von Transkriptsegmenten im Modus Turn Prediction. Das kann als allgemeine Beschreibung der Herstellerfunktion stehen bleiben. Die tatsächliche Evaluation nutzt jedoch die Commit-Strategie „manual“, empfängt Abschlusswahrscheinlichkeiten und trifft die Endentscheidung über die Regeln des Prototyps.

Das ist kein Beleg dafür, dass die Modellbezeichnung falsch ist. Es fehlt die Verbindung zwischen allgemeiner Funktionsbeschreibung und dem tatsächlich gemessenen Aufbau.

**Vorschlag für Kapitel 3.3:**

> Scribe liefert im Modus „manual“ Abschlusswahrscheinlichkeiten; die Endentscheidung trifft der Prototyp anhand der gemeinsamen Stillegrenzen und der gewählten Schwelle.

Damit werden Transkriptfinalisierung, Modellscore und wirksame Endentscheidung sauber auseinandergehalten.

### 2.7 Der Anhang passt in seiner gegenwärtigen Form nicht zur Arbeit

**Fundstelle:** gesamter Anhang.

Der Anhang nennt Experteninterviews zu LMOS und CALM, Antwortqualität, Automatisierungsgrad, NPS sowie Risiken und Zukunftspotenziale. Diese Inhalte werden im Haupttext weder eingeführt noch für die EOT-Evaluation verwendet. Der Anhang wirkt daher wie ein übernommener Bestand aus einer anderen Arbeit.

**Vorschlag:** Nicht verwendete Inhalte entfernen. Falls einzelne Interviews tatsächlich die Auswahl oder Problemstellung belegen, müssen sie im Haupttext konkret zitiert und ihre Rolle erläutert werden.

Für diese Arbeit wären stattdessen passende Anhänge:

- Szenarien und Sprechvorgaben;
- verwendete Konfigurationen und eindeutige Laufzuordnung;
- Erläuterung der Referenzannotation;
- Verzeichnis der Audio- und Ergebnisdateien.

Dafür müssen keine zusätzlichen Interviews oder Untersuchungen erfunden oder durchgeführt werden.

### 2.8 Quellen und Deckblatt enthalten prüfbedürftige Stellen

- **Abbildung 1:** „In Anlehnung an Hall (2026)“ steht im Quellenhinweis, aber Hall fehlt im Literaturverzeichnis. Quelle vervollständigen oder die Zuschreibung anhand der tatsächlichen Herkunft korrigieren.
- **Fußnote 5:** LiveKit wird mit „o. J.“ zitiert, der Eintrag „Pipeline nodes and hooks“ im Literaturverzeichnis mit 2026. Einheitlich nach der tatsächlichen Quelle angeben.
- **Literaturverzeichnis:** Die ElevenLabs-Webdokumentation „Transcripts and commit strategies“ steht unter „Bücher und Zeitschriften“. Bei Beibehaltung dieser Aufteilung gehört sie zu den Internetquellen.
- **Telekom-Bezug:** Die öffentliche Übersichtsarbeit in Fußnote 2 kann das allgemeine Problem belegen, aber nicht ohne Weiteres dessen konkretes Auftreten im Telekom-Kundenservice. Auch Angaben zu eingesetzten Timeouts, Erprobungen und Vertragsbeziehungen in Kapitel 3.1 brauchen eine nachvollziehbare Grundlage.
- **Deckblatt:** Als Autor und als Dozent steht jeweils „Tiemo Kwiaton“. Prüfen, ob der Dozenteneintrag ein Platzhalter ist.

Die Telekom-internen Angaben wurden nicht unabhängig bestätigt. Der Telekom-MCP war in dieser Sitzung nicht verfügbar; interne Begriffe, Rollen oder Unternehmensbeziehungen wurden deshalb nicht aus allgemeinem Wissen ergänzt.

## 3 Einheitliche Bezeichnungen

„Modell“ kann der bevorzugte Begriff bleiben. Er sollte sich bei den EOT-Modellen auf LiveKit und Scribe beziehen. Die pausenbasierte Vergleichsbedingung besteht aus einem VAD-Modell plus einer Zeitregel.

Eine passende Grundformulierung ist:

> Verglichen werden zwei semantisch unterstützte EOT-Modelle und eine pausenbasierte Baseline aus Silero VAD und Stille-Timeout.

| Gegenstand | Empfohlene Bezeichnung | Zu vermeidende Unschärfe |
| --- | --- | --- |
| Aufgabe | EOT-Erkennung | Wechsel zwischen EOT Detection, EOT-Verfahren und Turnende-Erkennung ohne erkennbaren Zweck |
| LiveKit | Erst „LiveKit Turn Detector v1 Cloud“, danach „LiveKit“ | Anbieter, Produktfamilie und konkrete Modellversion austauschbar verwenden |
| ElevenLabs-Modell | Erst „ElevenLabs Scribe v3 Live“, danach „Scribe“ | „ElevenLabs“ für Modell und gleichzeitig für die synthetische Stimmquelle |
| Vergleichsbasis | Erst „Silero-VAD-Baseline mit 1.500 ms Stille-Timeout“, danach „Baseline“ | Silero allein als EOT-Modell darstellen |
| Oberbegriff für LiveKit und Scribe | semantisch unterstützte EOT-Modelle | Den Beitrag akustischer Merkmale und zeitbasierter Regeln sprachlich ausblenden |
| Gesprochene Einheit | Nutzerbeitrag oder kurz Beitrag | Ständiger Wechsel zwischen Turn, Eingabe, Nutzereingabe und Gesprächsbeitrag |
| Datei im Datensatz | Audiodatei oder Aufnahme | Samples, Testeingaben und Szenarien gleichsetzen |
| Geplanter Fall | Szenario | 50 Dateien als 50 unterschiedliche Szenarien darstellen |
| Manuelle Zeitmarke | Referenzende | Referenzende, Gold-Ende und tatsächliches Turnende ohne Definition wechseln |
| Entscheidung vor dem Referenzende | vorzeitiger Abschluss | Ein tatsächlich gemessenes Abschneiden durch einen live antwortenden Bot suggerieren |
| Entscheidung von 0 bis einschließlich 1.600 ms | rechtzeitiger Abschluss oder „im Bewertungsfenster“ | „Korrekt“ einmal als rechtzeitig und einmal nur als nicht vorzeitig verstehen |
| Wartezeitstatistik | Wartezeit der nicht vorzeitig beendeten Beiträge | „Korrekt abgeschlossene Turns“, wenn verzögerte Abschlüsse mitgerechnet werden |
| Sechs fachliche Gruppen | Inhaltsarten | Falltypen mit den vier Sprechverläufen vermischen |
| Vier Arten des Sprechens | Sprechverläufe | Inhaltsart und Sprechverlauf synonym verwenden |

**EOT oder EUT:** In der geprüften Fassung kommt „EUT“ nicht vor. „EOT“ ist durchgehend die verwendete Abkürzung. Das Abkürzungsverzeichnis löst sie zutreffend als „End of Turn“ auf.

Für Kapitel 4.2 passt beispielsweise die Überschrift **„Vergleich der Modelle mit der Baseline“**. Der gegenwärtige Schrägstrich in „Verfahren/ Modelle“ sollte entfallen.

## 4 Präzisierungen für Methodik und Interpretation

### 4.1 Bewertungsfenster und Auswahlkriterium gehören in Kapitel 3

Die Grenze von 1.600 ms wird erst in Kapitel 4.1 definiert. Sie bestimmt aber sowohl die Ergebniskategorien als auch die Wahl der „besten“ Konfiguration.

Kapitel 3.3 sollte deshalb festhalten:

- vorzeitig: Entscheidung vor dem Referenzende;
- rechtzeitig: 0 bis einschließlich 1.600 ms danach;
- verzögert: mehr als 1.600 ms danach;
- Ausfall: technische Fehler oder fehlende gültige Entscheidung.

Zusätzlich braucht die konkrete Grenze eine kurze Begründung. Sie ist zunächst eine Festlegung dieser Untersuchung. Aus dem Text ergibt sich keine allgemeine wissenschaftliche oder betriebliche Gültigkeit von 1.600 ms.

Auch „beste Konfiguration“ braucht ein benanntes Kriterium. Die tatsächliche Auswahl passt zu „die ausfallfreie Konfiguration mit den meisten rechtzeitigen Abschlüssen“. Dieses Kriterium sollte nur dann als vorab festgelegt bezeichnet werden, wenn es tatsächlich vorab feststand.

### 4.2 Die medianen Wartezeiten beruhen auf unterschiedlichen Beiträgen

Die Zahlen sind richtig. Ihre Grundgesamtheiten unterscheiden sich aber:

| Vergleichsbedingung | Median | Berücksichtigte nicht vorzeitig beendete Beiträge |
| --- | ---: | ---: |
| Baseline | 1.557 ms | 21 |
| LiveKit 0,85 | 597 ms | 31 |
| Scribe 0,95 | 911 ms | 40 |

„Jeweils vollständig abgewartete Eingaben“ in Kapitel 4.2 deutet das bereits an. Ein kurzer Hinweis mit den Fallzahlen würde die Interpretation deutlich verbessern.

Die Aussage „LiveKit ermöglicht kürzere Wartezeiten“ sollte dabei auf diese Auswertung begrenzt werden. Die drei Mediane allein sind kein Vergleich identischer Teilmengen.

Eine ergänzende Paarprüfung der ausgewählten Läufe zeigt bei den 30 von beiden EOT-Modellen nicht vorzeitig beendeten Dateien ebenfalls einen niedrigeren LiveKit-Median. Diese Zusatzanalyse ist bei engem Wortbudget optional; die Klarstellung der verschiedenen Fallzahlen genügt für eine ehrliche Darstellung der vorhandenen Kennzahl.

### 4.3 Eine kurze Aufschlüsselung nach Stimmquelle fehlt

Die zwei Stimmquellen sind ein ausdrücklich beschriebenes Merkmal des Datensatzes. In den Ergebnissen werden sie vollständig zusammengefasst. Dabei verdeckt die Zusammenfassung einen deutlichen Unterschied:

| Stimmquelle | Baseline zu früh | LiveKit 0,85 zu früh | Scribe 0,95 zu früh |
| --- | ---: | ---: | ---: |
| Eigenaufnahmen | 16 von 25 | 2 von 25 | 2 von 25 |
| Synthetische Stimme | 13 von 25 | 17 von 25 | 8 von 25 |
| Gesamt | 29 von 50 | 19 von 50 | 10 von 50 |

Diese Aufteilung wurde für die Analyse aus den gespeicherten Einzelwerten berechnet. Sie ist im gegenwärtigen Manuskript noch nicht enthalten.

**Mögliche Ergänzung in Kapitel 4.3:**

> Die Ergebnisse unterscheiden sich nach Stimmquelle: Bei Eigenaufnahmen schließen LiveKit und Scribe jeweils zwei von 25 Beiträgen vorzeitig ab, bei der synthetischen Stimme 17 beziehungsweise acht. Stimme und synthetische Entstehung lassen sich im vorliegenden Aufbau nicht getrennt bewerten.

Das ist inhaltlich ergiebiger als eine weitere Wiederholung des Gesamtvergleichs.

### 4.4 Lange Suchpause und vollständiger Satz mit Nachtrag sind unterschiedliche Schwierigkeiten

Kapitel 4.3 betrachtet bisher vor allem Inhaltsarten und den langen IBAN-Fall. Die vier Sprechverläufe werden zwar angekündigt, später aber kaum aufgegriffen.

In den ausgewählten Konfigurationen enden alle zwölf Beiträge mit vollständigem Satz und Nachtrag bei der Baseline vorzeitig; bei LiveKit und Scribe sind es jeweils sieben. Bei den zwölf flüssigen Beiträgen hat keine der drei ausgewählten Konfigurationen einen vorzeitigen Abschluss.

Diese Zahlen wären eine optionale Ergänzung oder könnten einen Teil der bloßen Wiederholung aus Abbildung 6 ersetzen. Sie verbinden die Problemstellung besonders direkt mit dem Versuchsdesign.

Dabei muss die Referenzdefinition klar sein: Als Ende gilt der letzte Laut des gesamten geplanten Beitrags einschließlich Nachtrag. Ein Abschluss nach einem bereits vollständigen Satz wird somit als Fehler gewertet. Das ist für dieses Experiment nachvollziehbar, aber keine allgemeingültige Festlegung, wann ein menschlicher Gesprächspartner das Rederecht übernehmen dürfte.

### 4.5 Es wird ein konfigurierter Gesamtaufbau verglichen

LiveKit und Scribe werden über mehrere Schwellen ausgewählt; die Baseline bleibt bei 1.500 ms. Die beiden Modelle verwenden außerdem eine Mindeststille und einen maximalen Stille-Timeout.

Das ist als anwendungsbezogener Vergleich zulässig, sollte aber entsprechend beschrieben werden. Die Ergebnisse erlauben keine isolierte Aussage darüber, welcher Anteil des Unterschieds allein durch semantisches Verständnis verursacht wird.

**Kurze Formulierung:**

> Verglichen werden konkrete Modellkonfigurationen mit einer fest eingestellten Baseline; der isolierte Beitrag semantischer Information wird nicht bestimmt.

Die Begrenzung auf denselben Datensatz ist bereits in Kapitel 4.3 vorhanden und muss nicht nochmals ausführlich erklärt werden.

### 4.6 Zeitmessung und technische Ausfälle knapp erläutern

Die Audiodaten werden tatsächlich in Echtzeit bereitgestellt. Die Zeit bis zur wirksamen Entscheidung enthält damit auch Verarbeitung und Kommunikation mit den Diensten. Verbindungsaufbau vor dem Replay ist hingegen nicht enthalten. Die finalen Läufe verwenden bis zu sechs parallele Aufnahmen je Modell.

Ein knapper Hinweis in der Methodik oder den Limitationen ist sinnvoll:

> Gemessen wird die im Echtzeit-Replay verfügbare Endentscheidung einschließlich Verarbeitung und Dienstkommunikation. Parallele Verarbeitung und schwankende Dienstlaufzeiten können die Messwerte beeinflussen.

Die zehn Ausfälle des LiveKit-Laufs mit Schwelle 0,95 sind als Dienst- beziehungsweise Verbindungsfehler protokolliert. Ihre Ursache ist damit nicht als Wirkung einer hohen Abschlussschwelle nachgewiesen. Die vorhandene Formulierung „Bei der Schwelle 0,95 …“ ist vorsichtiger als eine kausale Aussage und sollte so vorsichtig bleiben.

Auch „nach spätestens 5.000 ms“ ist zu absolut: Die Einstellung beträgt 5.000 ms erkannte Stille, reale Entscheidungen enthalten zusätzliche Laufzeit. Besser: „Fallback nach 5.000 ms erkannter Stille“.

### 4.7 Der Datensatz ist gezielt gestaltet und begrenzt

Die Arbeit benennt bereits die geringe Fallzahl und die fehlende unabhängige Testmenge. Ergänzend sind zwei kurze Hinweise sinnvoll:

- Die 50 Dateien bilden 25 Szenarienpaare mit denselben Sprechtexten. Sie sind keine 50 unabhängig entwickelten Gesprächssituationen.
- Vorgelesene beziehungsweise synthetisch erzeugte Beiträge mit geplanten Pausen bilden natürliche Telefonate nur begrenzt ab. Stimme und natürliche beziehungsweise synthetische Entstehung sind gekoppelt.

Die Referenzenden wurden manuell gesetzt. Wer sie gesetzt hat und ob eine Gegenprüfung stattfand, geht aus dem Manuskript nicht klar hervor. Das tatsächliche Vorgehen knapp nennen; eine zweite Annotation darf nicht nachträglich behauptet werden.

### 4.8 Die mittlere vorzeichenbehaftete Abweichung ist kein alleiniger Qualitätswert

Die negativen Mittelwerte in den Tabellen passen zu den Rohdaten. Ein Wert näher an null bedeutet aber nicht automatisch eine insgesamt bessere Enderkennung: Vorzeitige und verspätete Entscheidungen können sich rechnerisch ausgleichen.

Da diese Spalte im Text kaum genutzt wird, ist sie ein Kandidat für eine optionale Vereinfachung der Tabellen. Alternativ genügt eine klare Definition in Kapitel 3.3. Die Hauptargumentation sollte bei vorzeitigen Abschlüssen, Abschlüssen im Bewertungsfenster und der Wartezeit bleiben.

## 5 Wo sich Kapitel 3 und 4 doppeln

Die sinnvolle Aufgabenteilung lautet: Kapitel 3 erklärt den Versuchsaufbau und die Bewertungsregeln; Kapitel 4 berichtet und interpretiert die Ergebnisse.

| Wiederholter Inhalt | Gegenwärtige Stellen | Empfohlener Ort |
| --- | --- | --- |
| Ziel des Vergleichs semantischer Modelle mit einer Baseline | Einleitung, 1.2, 1.3, Einstieg Kapitel 3, 3.1, Einstieg Kapitel 4, Fazit | Forschungsfrage in 1.2; im Fazit direkt beantworten |
| Identische Audiodateien für alle Vergleichsbedingungen | 3.1, 3.3, 4.1 | 3.3 |
| Messung gegen ein manuelles Referenzende | 3.1, 3.2, 3.3, 4.1 | Annotation in 3.2; Messregel in 3.3 |
| Baseline mit 1.500 ms | 3.1, 3.3, 4.1 und Tabelle 1 | Auswahlbegründung in 3.1; Einstellung in 3.3; Ergebnis in 4.1 |
| Maximaler Stille-Timeout von 5.000 ms | 3.3 und 4.1 | 3.3 |
| Zweck und Bedeutung der Abschlussschwelle | Grundlagen, 3.3 und 4.1 | Kurze Definition in 3.3; in 4.1 nur beobachtete Wirkung |
| Weniger vorzeitige Abschlüsse bedeuten nicht automatisch weniger Wartezeit | Problemstellung, 2.2, 4.2 mehrfach, Fazit | Problem in 1.1; Ergebnisinterpretation einmal in 4.2 |
| Geringe Übertragbarkeit | 4.3 und ausführlich im Fazit | Begründung in 4.3; ein kurzer Satz im Fazit |

Nicht jede Wiederaufnahme ist überflüssig. Ein Ergebnis muss im Fazit nochmals als Antwort auf die Forschungsfrage erscheinen. Die wiederholte Beschreibung des Untersuchungsziels und des Werkzeugs bringt dagegen kaum zusätzlichen Nutzen.

## 6 Wortbudget und Kürzungspotenzial

### 6.1 Näherungszählung

Die folgende Zählung trennt Wörter anhand von Leerraum. Sie ersetzt die verbindliche Word- beziehungsweise Hochschulzählung nicht; insbesondere Bindestriche, Felder und Zahlen können anders gezählt werden.

| Kapitel | Reiner Fließtext ohne Überschriften, Tabellen, Beschriftungen und Quellenzeilen |
| --- | ---: |
| 1 Einleitung | ca. 285 |
| 2 Theoretische Grundlagen | ca. 336 |
| 3 Prototyp und Methodik | ca. 641 |
| 4 Evaluation und Diskussion | ca. 613 |
| 5 Zusammenfassung und Fazit | ca. 206 |
| Gesamt | ca. 2.081 |

Mit Überschriften, Tabelleninhalten, Beschriftungen und Quellenzeilen des Hauptteils ergeben sich ungefähr 2.330 Wörter; einschließlich der zehn inhaltlich belegten Fußnoten ungefähr 2.443. Deckblatt, Verzeichnisse, Literaturverzeichnis und Anhang sind darin nicht enthalten.

Die in der Datei gespeicherte Gesamtstatistik nennt 3.004 Wörter. Diese Gesamtzahl ist keine verlässliche Angabe für den allein bewerteten Haupttext.

Der [Projektplan](../PROJEKTPLAN_TURN_END_ERKENNUNG.md) nennt 2.000 Wörter mit höchstens zehn Prozent Überschreitung. Welche Bestandteile verbindlich mitzählen, muss sich nach der konkreten Hochschulvorgabe richten.

### 6.2 Konkrete Kürzungsoptionen

Die Einsparungen beziehen sich auf die unten vorgeschlagenen Ersatzfassungen beziehungsweise vollständige Streichung der genannten Einstiege. Sie enthalten noch nicht alle zusätzlichen Begründungen und Limitationen.

| Stelle | Bisher | Vorschlag | Einsparung |
| --- | ---: | ---: | ---: |
| Einstieg Kapitel 1 vor 1.1 streichen | 31 | 0 | 31 |
| 1.1 Problemstellung straffen | 112 | 47 | 65 |
| 1.2 Ziel und Forschungsfrage verbinden | 56 | 36 | 20 |
| 1.3 auf Vorgehen und Aufbau begrenzen | 86 | 34 | 52 |
| Einstieg Kapitel 2 streichen | 31 | 0 | 31 |
| 2.1 zweiten Absatz vereinfachen | 50 | 26 | 24 |
| 2.2 ersten Absatz straffen | 59 | 27 | 32 |
| Beide Einstiegsabsätze von Kapitel 3 streichen | 80 | 0 | 80 |
| 3.1 Prototyp und Modellauswahl straffen | 197 | 63 | 134 |
| 3.2 Datensatz präziser zusammenfassen | 141 | 75 | 66 |
| 3.3 Methodik neu bündeln | 223 | 153 | 70 |
| Einstieg Kapitel 4 streichen | 54 | 0 | 54 |
| 4.1 nach Verschieben der Definitionen straffen | 241 | 87 | 154 |
| 4.2 Ergebnisse und Interpretation bündeln | 175 | 104 | 71 |
| Fazit auf Antwort und Grenzen begrenzen | 206 | 93 | 113 |

Die vier Kapitel-Einstiege allein ergeben 196 Wörter. Das ist die einfachste erste Kürzung. Die übrigen Varianten sind ein Auswahlangebot; alle gleichzeitig umzusetzen wäre für eine Arbeit mit ungefähr 2.000 Wörtern voraussichtlich unnötig.

Ein sinnvoller erster Durchgang spart etwa 400 bis 600 Wörter durch Wiederholungen und lange Formulierungen. Nach den notwendigen Präzisierungen bleibt voraussichtlich eine Nettoeinsparung von ungefähr 300 bis 450 Wörtern. Das konkrete Ziel hängt davon ab, was zur verbindlichen Wortzahl gehört.

## 7 Konkrete Formulierungsvorschläge

Die Vorschläge sind zur Auswahl gedacht. Vorhandene Quellenbelege müssen an den sachlich passenden Aussagen erhalten bleiben. Die Abschnitte 3.3 und 4.1 sind aufeinander abgestimmt: Bewertungsdefinitionen werden in die Methodik verschoben.

### 7.1 Einleitung

Den allgemeinen Einstieg vor 1.1 streichen.

**1.1 Problemstellung:**

> Voicebots im telefonischen Kundenservice müssen Sprechpausen von abgeschlossenen Nutzerbeiträgen unterscheiden. Beim Nachschlagen einer Kundennummer oder IBAN können längere Pausen entstehen. Ein kurzer Stille-Timeout kann den Beitrag vorzeitig beenden und Rückfragen oder erneute Eingaben erforderlich machen. Längere Timeouts verringern dieses Risiko, erhöhen aber die Wartezeit nach abgeschlossenen Beiträgen.

Der konkrete Telekom-Bezug kann in 3.1 bei der Auswahlbegründung bleiben. Die öffentliche Fachquelle wird hier auf das allgemeine Problem bezogen.

**1.2 Zielsetzung:**

> Die Arbeit vergleicht zwei semantisch unterstützte EOT-Modelle mit einer pausenbasierten Baseline anhand vorzeitiger Abschlüsse und der Wartezeit nach dem Referenzende. Die Forschungsfrage lautet: Erkennen semantisch unterstützte EOT-Modelle das Ende deutschsprachiger Nutzerbeiträge zuverlässiger als eine pausenbasierte Baseline?

**1.3 Vorgehen und Aufbau:**

> Ein eigens entwickelter Prototyp wertet 50 menschliche und synthetische Sprachaufnahmen aus. Kapitel 2 erläutert die Grundlagen, Kapitel 3 den Versuchsaufbau. Kapitel 4 vergleicht die Ergebnisse und diskutiert ihre Grenzen; Kapitel 5 beantwortet die Forschungsfrage.

Die EOT-Abkürzung beim ersten Auftreten im überarbeiteten Text einmal einführen.

### 7.2 Grundlagen

Den Einstieg „Im folgenden Kapitel werden …“ streichen.

**Zweiter Absatz von 2.1:**

> In der vereinfachten Pipeline folgt auf die Endentscheidung die Dialogverarbeitung, etwa mit einem Large Language Model (LLM). Text-to-Speech (TTS) wandelt die Antwort anschließend in Sprache um.

Das beseitigt zugleich die zu absolute Formulierung „Erst danach kann … beginnen“. Allgemein ist auch eine inkrementelle Verarbeitung während des Sprechens möglich; die Abbildung darf trotzdem eine vereinfachte Pipeline zeigen.

**Erster Absatz von 2.2:**

> Die pausenbasierte EOT-Erkennung beendet einen Beitrag, sobald die von VAD erkannte Stille einen festgelegten Timeout erreicht. Kurze Timeouts erhöhen das Risiko vorzeitiger Abschlüsse; längere verlängern die Wartezeit.

### 7.3 Kapitel 3.1

Die beiden allgemeinen Einstiegsabsätze vor 3.1 streichen. Als passendere Abschnittsüberschrift bietet sich „Prototyp und Modellauswahl“ an, weil der vorhandene Text überwiegend Anwendung und Auswahl erklärt.

> Die browserbasierte Anwendung dient zur Aufnahme, synthetischen Erzeugung und Auswertung der Sprachbeiträge. Sie vergleicht LiveKit Turn Detector v1 Cloud, ElevenLabs Scribe v3 Live und eine Baseline aus Silero VAD mit 1.500 ms Stille-Timeout anhand identischer Audiodateien.
>
> Die Auswahl orientiert sich am beruflichen Umfeld des Autors bei Frag Magenta. Der Baseline-Timeout entspricht einer dort eingesetzten Konfiguration; bestehende Vertragsbeziehungen ermöglichten den Zugang zu beiden Anbietern.

Die internen Angaben im zweiten Absatz sind aus der vorhandenen Fassung übernommen und müssen bei Verwendung belegt werden. Der Absatz lässt sich bei fehlender Beleggrundlage auf den nachweisbaren Auswahlkontext beschränken.

### 7.4 Kapitel 3.2

> Die 25 Szenarien liegen jeweils mit identischem Sprechtext als Eigenaufnahme des Autors und als synthetische Aufnahme einer weiblichen ElevenLabs-Stimme vor, insgesamt 50 Audiodateien. Sechs Inhaltsarten werden mit vier Sprechverläufen kombiniert: Kundennummer, IBAN, E-Mail-Adresse, Adresse beziehungsweise Termin, technisches Anliegen sowie Vertrag beziehungsweise Rechnung; jeweils flüssig, mit Denkpause, Selbstkorrektur oder Nachtrag. Ein zusätzlicher IBAN-Fall mit 3,5 Sekunden Suchpause ergänzt die 24 Kombinationen. Als Referenzende wird manuell das Ende des gesamten Beitrags einschließlich möglicher Nachträge markiert (Abbildung 3).

Die Aufzählung kann für einen natürlicheren Lesefluss auch in zwei Sätze getrennt werden. Die Information zur ausführenden Person der Annotation ist entsprechend dem tatsächlichen Vorgehen zu ergänzen.

### 7.5 Kapitel 3.3

> Alle 50 Audiodateien werden schrittweise in Echtzeit bereitgestellt. Die Endentscheidung beruht ausschließlich auf dem bereits verfügbaren Audio. Der abschließende Vergleich von zwei Modellen und der Baseline umfasst 150 Einzelbewertungen.
>
> Die Baseline verwendet 1.500 ms Stille-Timeout. Untersucht werden für LiveKit die Schwellen 0,4936, 0,85, 0,90 und 0,95, für Scribe 0,80, 0,85, 0,90 und 0,95. Beide Modelle verwenden mindestens 300 ms Stille und einen Fallback nach 5.000 ms. Die Abschlusswahrscheinlichkeiten von Scribe werden im Modus „manual“ empfangen und durch den Prototyp ausgewertet.
>
> Gemessen wird die erste wirksame Endentscheidung relativ zum Referenzende. Negative Abweichungen gelten als vorzeitig, 0 bis einschließlich 1.600 ms als rechtzeitig und größere Abweichungen als verzögert. Technische Ausfälle werden gesondert gezählt und aus Zeitstatistiken ausgeschlossen. Die mediane Wartezeit bezieht sich auf alle nicht vorzeitig beendeten Beiträge ohne technische Fehler; Fallbacks werden zusätzlich gekennzeichnet.
>
> Für den Modellvergleich werden die ausfallfreien Konfigurationen mit den meisten rechtzeitigen Abschlüssen ausgewählt. Auswahl und Bewertung erfolgen auf demselben Datensatz.

Hier noch die tatsächliche Begründung für das Bewertungsfenster ergänzen. Das formulierte Auswahlkriterium beschreibt eine zu den Ergebnissen passende Regel; seine Darstellung muss dem tatsächlichen Auswahlvorgehen entsprechen. Falls die Mittelwertspalte erhalten bleibt, außerdem die mittlere vorzeichenbehaftete Abweichung definieren.

### 7.6 Kapitel 4.1

Den allgemeinen Einstieg vor 4.1 streichen. Nach Verschieben der Methodenregeln nach 3.3 kann der Abschnitt unmittelbar mit den Ergebnissen beginnen. Die Tabellen bleiben erhalten.

> Die Baseline beendet 29 von 50 Beiträgen vorzeitig (Tabelle 1). Bei LiveKit erzielt die Schwelle 0,85 mit 27 rechtzeitigen Abschlüssen und ohne technische Ausfälle das beste Ergebnis nach dem gewählten Kriterium (Tabelle 2). Höhere Schwellen verringern die Zahl vorzeitiger Abschlüsse, gehen in diesen Läufen jedoch mit mehr Verzögerungen und technischen Ausfällen einher.
>
> Bei Scribe erreicht die Schwelle 0,95 mit 30 rechtzeitigen und zehn verzögerten Abschlüssen den höchsten Anteil rechtzeitiger Abschlüsse; zehn Beiträge enden vorzeitig (Tabelle 3). Für den folgenden Vergleich werden LiveKit 0,85 und Scribe 0,95 ausgewählt.

### 7.7 Kapitel 4.2

> Mit den ausgewählten Einstellungen sinkt der Anteil vorzeitiger Abschlüsse von 58 % bei der Baseline auf 38 % bei LiveKit und 20 % bei Scribe; rechtzeitig enden 32 %, 54 % beziehungsweise 60 % der Beiträge (Abbildung 4).
>
> Die mediane Wartezeit beträgt 1.557 ms bei der Baseline, 597 ms bei LiveKit und 911 ms bei Scribe. Sie bezieht sich auf unterschiedliche Teilmengen von 21, 31 beziehungsweise 40 nicht vorzeitig beendeten Beiträgen. Scribe vermeidet mehr vorzeitige Abschlüsse, überschreitet das Bewertungsfenster jedoch häufiger: zehnmal gegenüber viermal bei LiveKit und fünfmal bei der Baseline (Abbildung 5). LiveKit erreicht zwei, Scribe einen dieser Abschlüsse erst durch den Fallback.

Die Fallback-Angabe kann auch als eigener kurzer Satz nach dem Absatz stehen.

### 7.8 Fazit

> Im untersuchten Datensatz beendeten die ausgewählten semantisch unterstützten EOT-Modelle weniger Beiträge vorzeitig als die pausenbasierte Baseline: LiveKit 38 %, Scribe 20 % und die Baseline 58 %. LiveKit erzielte bei den jeweils nicht vorzeitig beendeten Beiträgen die kürzeste mediane Wartezeit, während Scribe häufiger das vollständige Beitragsende abwartete. Lange Sprechpausen blieben problematisch.
>
> Die Forschungsfrage lässt sich damit für diese Konfigurationen und diesen Datensatz zugunsten der semantisch unterstützten Modelle beantworten. Wegen der kleinen, gezielt gestalteten Stichprobe und der Konfigurationsauswahl auf denselben Daten bleibt die Übertragbarkeit begrenzt. Weitere Untersuchungen sollten zusätzliche Stimmen und unabhängige Testdaten einbeziehen.

Der gegenwärtige erste Fazitabsatz wiederholt überwiegend Ziel, Modelle, Werkzeug und Stichprobe. Diese Wiederholung kann zugunsten der direkten Antwort entfallen.

## 8 Kleinere sprachliche und formale Korrekturen

| Fundstelle | Gegenwärtig | Vorschlag |
| --- | --- | --- |
| Einstieg Kapitel 2 | „Voicebot Architektur“ | „Voicebot-Architektur“ |
| 2.2 | „die eigentlich Verarbeitung“ | „die eigentliche Verarbeitung“ oder in der Kurzfassung streichen |
| 2.2 | „wenn Sie gerade die Kundennummer ablesen“ | Bei neutraler Beschreibung „wenn sie …“; besser die entbehrliche Klammer streichen |
| Ende des ersten Absatzes 2.2 | fehlender Schlusspunkt | Punkt ergänzen |
| 2.2 | „längeren Latenzen der Antwortzeit“ | „längerer Wartezeit“ |
| Einstieg Kapitel 3 | „die Auswahl der Modelle, sowie“ | Komma vor „sowie“ streichen |
| 3.1 | „die semantisch Modelle“ | „die semantisch unterstützten Modelle“ |
| 3.2 | „Stille Timeout“ | „Stille-Timeout“ |
| Abbildung 2 | „mit den drei ausgewählten Modellen“ | „zur Auswahl der Modelle und der Baseline“ |
| Abbildung 4 | „besten Konfigurationen“ | „ausgewählten Konfigurationen“ |
| Abbildung 4 | „1600ms“ | „1.600 ms“ |
| Abbildung 5 | mittlere Punktreihe ohne Modellnamen | LiveKit-Beschriftung ergänzen; in der eingebetteten Grafik fehlt sie |
| Abbildung 6 und zugehöriger Text | Grafik „Falltyp“, Bildunterschrift „Inhaltsart“ | einheitlich „Inhaltsart“ |
| 3.2 und 3.3 | Wechsel zwischen Planung und abgeschlossenem Experiment | Tatsächlich durchgeführte Schritte bevorzugt im Präteritum; Definitionen im Präsens |

Auch größere Zahlen und Dezimalwerte sollten einheitlich geschrieben werden, beispielsweise 1.500 ms, 1.600 ms und 5.000 ms sowie 0,85 im deutschen Fließtext.

IBAN wird mehrfach verwendet, steht aber nicht im Abkürzungsverzeichnis. Ergänzen, sofern das Verzeichnis nach der geltenden Vorgabe sämtliche verwendeten Fachabkürzungen enthalten soll. Die fachfremden Abkürzungen aus dem bisherigen Anhang sollten nicht allein wegen dieses Anhangs zusätzlich eingeführt werden.

## 9 Empfohlene Reihenfolge der Überarbeitung

1. Die konkreten Widersprüche beheben: LiveKit-Einstellungen, Screenshot, 24 plus eins, Umfang der 150 Bewertungen und Anhang.
2. Kapitel 3.3 als zentrale Stelle für Einstellungen, Messregeln und Auswahlkriterium überarbeiten.
3. Die vier allgemeinen Kapitel-Einstiege streichen und 1.3 straffen.
4. Kapitel 4 auf Ergebnisse und deren Interpretation konzentrieren; Fallbacks und eine knappe Aufschlüsselung nach Stimmquelle ergänzen.
5. Begriffe vereinheitlichen und das Fazit direkt mit der Antwort auf die Forschungsfrage beginnen.
6. Quellen, Bildbeschriftungen und verbindliche Wortzahl abschließend prüfen.

So wird die Arbeit kürzer und zugleich methodisch vollständiger. Ein Ausbau der allgemeinen Theorie oder neue Hauptkapitel sind dafür nicht erforderlich.

## Prüfgrundlagen

Neben der Word-Fassung wurden vor allem folgende vorhandene Projektdateien verwendet:

- [Studienprotokoll und Szenarien](../app/study.py)
- [Datensatzplan](./DATENSATZ_25_PLAN.md)
- [Konfiguration Final 001](../data/runs/d6db9e1bdb0a4e0caf06d7f23f6ad8db/manifest.json) und [Einzelergebnisse](../data/runs/d6db9e1bdb0a4e0caf06d7f23f6ad8db/report.json)
- [Konfiguration Final 002](../data/runs/5ee33010b2e8433d8695c986cf208a62/manifest.json) und [Einzelergebnisse](../data/runs/5ee33010b2e8433d8695c986cf208a62/report.json)
- [Konfiguration des Laufs mit Schwelle 0,95](../data/runs/ee5979a0406144aaad7234bcd894aaa4/manifest.json) und [Einzelergebnisse](../data/runs/ee5979a0406144aaad7234bcd894aaa4/report.json)
- [Definitionen der Ergebniskategorien und Zeitstatistiken](../eot_eval/analysis.py)
- [Echtzeit-Replay und Entscheidungsregeln](../eot_eval/replay.py)
- [Scribe-Integration](../eot_eval/scribe.py)

