# Konkrete Ersetzungen und neue Abbildungen

Grundlage ist die zuletzt gespeicherte [Word-Fassung](./NLP_VAD_Tiemo_Kwiaton_v3.docx). Die Word-Datei wurde nicht verändert.

Die folgenden elf Änderungen sparen zusammen ungefähr 95 Wörter nach Leerraumzählung. Die beiden gekürzten Kapitel-Einstiege sparen 104 Wörter; die übrigen Änderungen zusammen benötigen neun zusätzliche Wörter. Die verbindliche Word-Zählung kann abweichen.

## 3.1 Bezeichnungen

**Alte Stelle**

> Verglichen werden eine pausenbasierte Baseline auf Grundlage von Silero VAD und die semantisch Modelle LiveKit Turn Detector v1 Cloud und ElevenLabs Scribe v3 Live.

**Neue Stelle**

> Verglichen werden die semantisch unterstützten EOT-Modelle LiveKit Turn Detector v1 Cloud und ElevenLabs Scribe v3 Live mit einer pausenbasierten Baseline aus Silero VAD und Stille-Timeout.

## 3.2 Szenarien

**Alte Stelle**

> Für beide Varianten werden dieselben 25 Szenarien verwendet. Diese ergeben sich aus sechs Inhaltsarten und vier Sprechverläufen.

**Neue Stelle**

> Sechs Inhaltsarten und vier Sprechverläufe ergeben 24 Szenarien. Ein zusätzlicher IBAN-Fall mit 3,5 Sekunden Suchpause ergänzt den Datensatz auf 25 Szenarien je Stimmquelle.

## 3.3 Durchführung

**Alte Stelle**

> Nachdem alle 50 Testeingaben vorliegen und mit einer Zeitmarke für das tatsächliche Turnende versehen wurden, wird der Evaluationslauf gestartet. Jede Audiodatei wird durch alle drei Verfahren verarbeitet, sodass insgesamt 150 Auswertungen entstehen. Die Audiodaten werden schrittweise bereitgestellt. Dadurch müssen die Verfahren ihre Endentscheidung anhand des jeweils verfügbaren Ausschnitts treffen.

**Neue Stelle**

> Jede Konfiguration wird an allen 50 Audiodateien ausgewertet. Die Audiodaten werden schrittweise in Echtzeit bereitgestellt, sodass nur bereits verfügbares Audio für die Endentscheidung genutzt werden kann. Der abschließende Vergleich der beiden ausgewählten Modellkonfigurationen mit der Baseline umfasst 150 Einzelbewertungen.

## 3.3 Einstellungen

**Alte Stelle**

> Die pausenbasierte Baseline schließt eine Eingabe ab, sobald für 1.500 ms keine Sprachaktivität erkannt wird. Beim LiveKit Turn Detector wird die vom Anbieter für Deutsch vorgesehene Entscheidungsschwelle verwendet. Für ElevenLabs Scribe v3 Live wird eine Schwelle von 0,95 festgelegt. Erreicht die ausgegebene Abschlusswahrscheinlichkeit diesen Wert, liegt ein modellseitiges Endsignal vor. Bei beiden semantischen Verfahren wird eine solche Entscheidung frühestens nach 300 ms Stille übernommen. Nach spätestens 5000 ms Stille wird der Beitrag auch ohne entsprechendes Endsignal abgeschlossen.

**Neue Stelle**

> Die Baseline beendet einen Beitrag nach 1.500 ms ohne erkannte Sprachaktivität. Für LiveKit werden die Deutsch-Voreinstellung von 0,4936 sowie 0,85, 0,90 und 0,95 untersucht; für Scribe 0,80, 0,85, 0,90 und 0,95. Die Auswahl erfolgt anhand der Ergebnisse in Kapitel 4.1. Beide Modelle übernehmen Endsignale frühestens nach 300 ms Stille; nach 5.000 ms erkannter Stille greift ein Fallback. Bei Scribe wertet der Prototyp die im Modus „manual“ empfangenen Abschlusswahrscheinlichkeiten aus.

## 3.3 Kennzahlen

**Alte Stelle**

> Für den Vergleich werden der Anteil vorzeitiger Abschlüsse und die mediane Wartezeit der korrekt abgeschlossenen Turns gegenübergestellt. Fehlende Entscheidungen, technische Fehler und Abschlüsse durch den maximalen Stille-Timeout werden gesondert ausgewiesen. Dadurch lässt sich beurteilen, ob ein Verfahren weniger vorzeitige Abschlüsse erreicht und welche Wartezeit damit verbunden ist.

**Neue Stelle**

> Verglichen werden der Anteil vorzeitiger Abschlüsse und die mediane Wartezeit der nicht vorzeitig beendeten Beiträge. Technische Fehler und fehlende Entscheidungen bilden eine eigene Kategorie und werden aus Zeitstatistiken ausgeschlossen. Fallback-Abschlüsse werden zusätzlich ausgewiesen. Als rechtzeitig gelten hier Abschlüsse von 0 bis einschließlich 1.600 ms nach dem Referenzende; spätere gültige Abschlüsse werden als verzögert gewertet.

## 4.2 Wartezeit

**Alte Stelle**

> Die Zeitabweichung in Abbildung 5 verdeutlicht, wie weit die erkannten Eingabeenden vom tatsächlichen Ende entfernt liegen. Einige Eingaben werden mehrere Sekunden zu früh abgeschlossen. Bei den jeweils vollständig abgewarteten Eingaben beträgt die mediane Wartezeit für Silero 1557 ms, für LiveKit 597 ms und für ElevenLabs 911 ms.

**Neue Stelle**

> Abbildung 5 zeigt die zeitliche Abweichung der Endentscheidungen vom Referenzende. Bei nicht vorzeitig beendeten Beiträgen beträgt die mediane Wartezeit für die Baseline 1.557 ms, für LiveKit 597 ms und für Scribe 911 ms. Diese Mediane beruhen auf unterschiedlichen Teilmengen von 21, 31 beziehungsweise 40 Beiträgen.

## 4.2 Fallbacks

**Alte Stelle**

Keine entsprechende Angabe vorhanden.

**Neue Stelle**

> Zwei LiveKit-Abschlüsse und ein Scribe-Abschluss entstehen erst durch den Fallback.

## 4.1 Einleitung der Tabellen

**Alte Stelle**

> Die Verfahren wurden anhand derselben 50 aufgezeichneten Eingabebeispiele ausgewertet. Als rechtzeitig gelten Abschlüsse bis einschließlich 1600 ms nach dem Referenzende. Spätere Abschlüsse werden als verzögert gewertet. Technische Ausfälle werden gesondert gezählt und aus der durchschnittlichen Zeitabweichung ausgeschlossen.

**Neue Stelle**

> Die Tabellen 1 bis 3 zeigen die Ergebnisse der untersuchten Konfigurationen.

## 4.3 Stimmquelle

**Alte Stelle**

Keine entsprechende Angabe vorhanden.

**Neue Stelle**

> Die Ergebnisse unterscheiden sich nach Stimmquelle: Bei Eigenaufnahmen schließen LiveKit und Scribe jeweils zwei von 25 Beiträgen vorzeitig ab, bei synthetischen Aufnahmen 17 beziehungsweise acht. Stimme und Entstehungsart sind dabei gekoppelt.

## 3 Einstieg

**Alte Stelle**

> In dieser Untersuchung wird ein pausenbasiertes Verfahren zur Erkennung des Gesprächsbeitragsendes mit zwei semantisch unterstützten Verfahren verglichen. Dabei wird untersucht, ob die Berücksichtigung des sprachlichen Inhalts vorzeitige Abschlüsse verringert und welche Wartezeit nach dem tatsächlichen Beitragsende entsteht. Als Grundlage dienen selbst eingesprochene und synthetisch erzeugte Spracheingaben, die mit allen drei Modellen ausgewertet werden. Das folgende Kapitel beschreibt die dafür entwickelte Anwendung, die Auswahl der Modelle, sowie die Erstellung des Testdatensatzes. Anschließend wird erläutert, wie der Vergleich durchgeführt und ausgewertet wird.

**Neue Stelle**

> Dieses Kapitel beschreibt den Evaluationsprototyp, den Datensatz und die Vergleichsmethodik.

## 4 Einstieg

**Alte Stelle**

> Für die Auswertung wurde die in Kapitel 3 beschriebene, eigens entwickelte Webanwendung verwendet. Mit ihr wurden die EOT-Modelle von LiveKit und ElevenLabs mit unterschiedlichen Einstellungen getestet. Ziel war es, Konfigurationen zu finden, die möglichst wenige Eingaben vorzeitig beenden und gleichzeitig kurze Wartezeiten ermöglichen. Anschließend werden die jeweils besten Einstellungen mit der pausenbasierten Baseline verglichen.

**Neue Stelle**

> Zunächst werden die Modellkonfigurationen verglichen und die Einstellungen für den Vergleich mit der Baseline ausgewählt. Anschließend werden die Ergebnisse diskutiert.

## Neue Abbildungen

- [Abbildung 2 Modellauswahl und Messbedingungen](./abbildungen/abbildung_2_modellauswahl_final.png): Baseline 1.500 ms, LiveKit 0,85, Scribe 0,95; Mindeststille 300 ms, Fallback 5.000 ms, Prüfintervall 100 ms, VAD-Schwelle 0,5. Neu aus der laufenden Oberfläche aufgenommen.
- [Abbildung 3 Referenzende](./abbildungen/abbildung_3_referenzende_final.png): vorhandene IBAN-Eigenaufnahme ST25-25 mit gespeichertem Referenzende 22,203 s. Neu aufgenommen; Annotation unverändert.
- [Abbildung 5 Zeitabweichung PNG](./abbildungen/abbildung_5_zeitabweichung_final.png) und [SVG](./abbildungen/abbildung_5_zeitabweichung_final.svg): aus den gespeicherten Einzelwerten neu erzeugt; alle drei Modellzeilen einschließlich LiveKit beschriftet. Je 50 Dateien; Bewertungsfenster 0–1.600 ms.

Empfohlene Beschriftung für Abbildung 2: „Abbildung 2: Modellauswahl und Messbedingungen des abschließenden Vergleichs“. Quellenzeile: „Quelle: Eigene Darstellung.“

Weitere kurze Ersetzungen: „Vergleich der ausgewählten Verfahren/ Modelle“ → „Vergleich der Modelle mit der Baseline“; „Abschlüsse der besten Konfigurationen“ → „Abschlüsse der ausgewählten Konfigurationen“; „1600ms“ → „1.600 ms“; „Stille Timeout“ → „Stille-Timeout“.

