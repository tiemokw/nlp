# Plan für den Anhang der Seminararbeit

Der Anhang soll den Versuchsaufbau und die Ergebnisse der EOT-Untersuchung nachvollziehbar machen. Dafür bietet sich ein kompakter Dokumentanhang mit einer ergänzenden ZIP-Abgabe an. Im Dokument stehen die lesbaren Übersichten und ausgewählte Belege; die ZIP-Datei enthält das ausführbare Projekt, den verwendeten Datensatz und die vollständigen Messdaten.

Grundlage dieses Plans sind die [aktuelle Seminararbeit](./NLP_VAD_Tiemo_Kwiaton_v3.docx), die [Projektbeschreibung](../README.md), der [Szenarienkatalog](../app/study.py) und die gespeicherten Evaluationsläufe. Der Plan ist ein Vorschlag; die Word-Datei wurde nicht verändert und die ZIP-Datei noch nicht erstellt.

## Vorgeschlagene Gliederung

| Anhang | Inhalt | Nutzen | Richtumfang |
| --- | --- | --- | --- |
| A Digitale Projektbeilage | Name und Inhalt der ZIP-Datei, Projektstand und kurze Nutzungshinweise | Die digitale Abgabe eindeutig zuordnen und öffnen können | ½ Seite |
| B Szenarienkatalog und Sprechvorgaben | Alle 25 Szenarien mit Text, Inhaltsart, Sprechverlauf und geplanter Pause | Die Zusammensetzung des Datensatzes prüfen können | 2–3 Seiten |
| C Regeln zur Referenzannotation | Definition des Beitragsendes, Vorgehen und Umgang mit Nachträgen | Verstehen, woran die Modellentscheidungen gemessen werden | ½–1 Seite |
| D Versuchskonfigurationen und Laufzuordnung | Verwendete Einstellungen und Herkunft der ausgewählten Ergebnisse | Tabellen und Abbildungen eindeutig auf Messläufe zurückführen können | 1 Seite |
| E Ergänzende Ergebnistabellen | Ergebnisse nach Sprechverlauf und Stimmquelle; technische Ausfälle und Fallbacks | Unterschiede hinter den Gesamtwerten nachvollziehen können | 1 Seite |
| F Kommentierte Einzelfälle | Zwei oder drei aussagekräftige Beispiele mit Zeitachse | Typische Fehler und Unterschiede anschaulich belegen | Optional 1–2 Seiten |

Als Arbeitsziel sind etwa fünf bis sieben Seiten für A bis E sinnvoll. Anhang F kommt hinzu, wenn die Beispiele gegenüber den vorhandenen Abbildungen einen erkennbaren Mehrwert haben. Seitenumfang und formale Gestaltung werden vor der Umsetzung mit dem verbindlichen Hochschulleitfaden abgeglichen.

## A Digitale Projektbeilage

Im Dokument genügen der tatsächliche ZIP-Dateiname, der enthaltene Projektstand, eine kurze Inhaltsübersicht und ein Verweis auf die Startanleitung. Eine kleine Zuordnung von Ablageorten zu Quellcode, Audiodaten und Ergebnissen erleichtert die Orientierung.

Für die ZIP-Abgabe sollten vorgesehen werden:

- Quellcode, [Startskript](../run.sh), [Projektbeschreibung](../README.md), [Paketdefinition](../pyproject.toml), [Lockdatei](../uv.lock) und eine Konfigurationsvorlage ohne Zugangsdaten.
- Der tatsächlich ausgewertete, festgeschriebene Datensatz mit 50 Audiodateien, Szenarien, Transkripten, Referenzenden und eindeutigen Kennungen.
- Die zu den Tabellen und Abbildungen gehörenden Messläufe einschließlich Konfigurationen, Einzelmessungen und benötigter Ereignisprotokolle.
- Der verwendete kombinierte Ergebnisexport mit Zuordnung der Verfahren zu ihren Ursprungsläufen sowie den finalen Abbildungen.

Die [Datenablage](../data/) wird durch die [Git-Ausschlussregeln](../.gitignore) nicht versioniert. Beim späteren Packen müssen die benötigten Audio- und Messdaten deshalb ausdrücklich aufgenommen werden. Ein reiner Export der versionierten Projektdateien deckt die wissenschaftliche Beilage nicht ab.

Die Kurzanleitung sollte zwei Nutzungswege beschreiben: vorhandene Ergebnisse prüfen und neue Modellläufe ausführen. Für neue Cloud-Abfragen werden eigene Anbieterzugänge benötigt; die gespeicherten Ergebnisse sollten ohne erneute Abfragen zugänglich sein. Lokale Zugangsdaten, virtuelle Umgebungen und entbehrliche Caches gehören nicht in die Abgabe.

Mögliche Formulierung nach Fertigstellung und Prüfung der ZIP-Datei:

> Der Arbeit ist eine digitale Projektbeilage als ZIP-Datei beigefügt. Sie enthält den Quellcode des Evaluationsprototyps, den verwendeten Datensatz einschließlich Referenzannotationen sowie die Konfigurationen und Ergebnisse der dokumentierten Evaluationsläufe. Hinweise zur Installation und Nutzung enthält die beiliegende Projektbeschreibung. Für erneute Abfragen der Cloud-Modelle sind eigene Anbieterzugänge erforderlich.

## B Szenarienkatalog und Sprechvorgaben

Empfehlung: Alle 25 Szenarien dokumentieren. Bei diesem Umfang ist der vollständige Katalog ein hilfreicher Beleg für die eigene Datensatzerstellung.

Die Darstellung sollte pro Szenario Kennung, Inhaltsart, Sprechverlauf, vollständigen Sprechtext und geplante Pause enthalten. Pausenmarken müssen sich sichtbar vom gesprochenen Text unterscheiden. Allgemeine Vorgaben zu Tempo, Betonung und Nachlauf können einmal vorangestellt werden.

Den Aufbau ausdrücklich als sechs Inhaltsarten mal vier Sprechverläufe plus einen zusätzlichen IBAN-Fall mit 3,5 Sekunden Suchpause erklären. Pro Szenario existieren eine menschliche und eine synthetische Aufnahme; der Sprechtext muss deshalb nur einmal abgedruckt werden. Die Zuordnung zu beiden Audiodateien erfolgt über die Szenarien- beziehungsweise Paarkennung.

Geplante Pausen sind als Zielwerte zu kennzeichnen. Tatsächliche Pausendauern nur dann ergänzen, wenn sie nachgemessen wurden. Die 50 Aufnahmen bilden 25 Szenarienpaare; Stimmidentität und natürliche beziehungsweise synthetische Entstehung sind im Aufbau gekoppelt.

Grundlage: [versionierter Szenarienkatalog](../app/study.py). Für die endgültige Fassung mit dem tatsächlich ausgewerteten Datensatzstand abgleichen.

## C Regeln zur Referenzannotation

Eine kurze, zusammenhängende Beschreibung sollte folgende Fragen beantworten:

- Was gilt als Referenzende? Das Ende des letzten gesprochenen Lauts des gesamten vorgesehenen Beitrags einschließlich einer Selbstkorrektur oder eines Nachtrags.
- Wie wird es bestimmt? Durch vollständiges Anhören und manuelles Setzen der Zeitmarke in der Wellenform.
- Was zählt noch nicht als Beitragsende? Eine interne Denkpause oder ein abgeschlossener erster Satz, auf den ein zum Szenario gehörender Nachtrag folgt.
- Wer hat annotiert und geprüft? Die tatsächlich ausgeführte Annotation und gegebenenfalls Gegenprüfung benennen.

Die vollständigen Zeitmarken aller 50 Dateien gehören in eine maschinenlesbare Tabelle in der ZIP-Beilage. Der Dokumentanhang erklärt die Regeln und zeigt bei Bedarf ein Grenzbeispiel. Die bereits im Haupttext vorhandene Abbildung zur Markierung des Referenzendes muss dafür nicht erneut abgedruckt werden.

## D Versuchskonfigurationen und Laufzuordnung

Zwei kompakte Tabellen bieten sich an: eine für gemeinsame Messbedingungen und eine für die Verfahren mit ihren jeweiligen Läufen.

Aufzunehmen sind die tatsächlich gespeicherten Werte für Baseline-Timeout, VAD-Schwelle, Modellschwellen, Mindeststille, maximalen Stille-Timeout, Prüfintervall, Echtzeitmodus und Parallelität. Hinzu kommen Datensatzkennung, Laufkennung, Datum sowie relevante Paket- und Modellversionen. Die ausgewählten Einstellungen sind Baseline 1.500 ms, LiveKit 0,85 und Scribe 0,95; die übrigen untersuchten Schwellen werden als Konfigurationsübersicht ergänzt.

Die geprüften Läufe speichern sechs parallele Verarbeitungen. Dieser Wert sollte dokumentiert werden, da Rechner- und Dienstlast die gemessenen Zeiten beeinflussen können. Grundlage sind die gespeicherten Laufmetadaten und keine später geänderten Startwerte der Oberfläche.

Besonders wichtig ist die genaue Zuordnung: Der abschließende Vergleich verwendet Ergebnisse aus unterschiedlichen Läufen. Für jede Tabellenzeile beziehungsweise Abbildung muss feststehen, welcher Lauf und welches Verfahren verwendet wurden. Der ausgewählte Vergleich umfasst 50 Aufnahmen mal drei Verfahren, also 150 Einzelbewertungen; die zusätzlichen Schwellenversuche gehen darüber hinaus.

Das Bewertungsfenster von 0 bis einschließlich 1.600 ms, die Behandlung technischer Fehler und die Berechnungsgrundlage der Wartezeit werden konsistent zur Methodik angegeben. Anbieteränderungen begrenzen die identische Wiederholbarkeit von Cloud-Läufen; die gespeicherten Originalmessungen bleiben die Grundlage der eingereichten Ergebnisse.

## E Ergänzende Ergebnistabellen

Hier lohnen sich Aufschlüsselungen, die im Haupttext bisher fehlen:

1. Ergebnisse nach Sprechverlauf: flüssig, Denkpause, Selbstkorrektur und Nachtrag; den zusätzlichen langen IBAN-Fall kenntlich machen.
2. Ergebnisse nach Stimmquelle: Eigenaufnahmen und synthetische Aufnahmen, jeweils mit Fallzahl.
3. Technische Ausfälle und Fallback-Entscheidungen der ausgewählten Verfahren, sofern sich diese Angaben nicht übersichtlich in die beiden Tabellen integrieren lassen.

Je Gruppe sollten die Anzahl vorzeitiger, rechtzeitiger und verzögerter Abschlüsse sowie technischer Ausfälle nachvollziehbar sein. Bei Wartezeiten den jeweiligen Nenner angeben: Vorzeitige Abschlüsse und technische Fehler gehen nicht in diese Zeitstatistik ein. Ein Fallback ist eine zusätzliche Eigenschaft der Entscheidung und keine fünfte, ausschließende Ergebniskategorie.

Die vollständigen Einzelwerte kommen als CSV in die ZIP-Beilage. Ein Ausdruck aller 150 Einzelbewertungen ist nur bei einer entsprechenden Vorgabe sinnvoll. Die bereits im Haupttext vorhandenen Gesamtvergleiche und Schwellentabellen müssen nicht nochmals erscheinen. Falls die zusätzlichen Aufschlüsselungen die Interpretation wesentlich verändern, gehört die Erkenntnis auch in die Diskussion.

## F Kommentierte Einzelfälle

Optional zwei oder drei Fälle aus den vorhandenen Messungen auswählen:

- Ein Beitrag, bei dem eine semantische Konfiguration die Fortsetzung abwartet, während die Baseline vorzeitig abschließt.
- Der zusätzliche IBAN-Fall mit langer Suchpause als dokumentierte Grenze der Verfahren.
- Falls vorhanden und zusätzlich aufschlussreich: ein Nachtrag oder eine Selbstkorrektur, bei der sich LiveKit und Scribe unterscheiden.

Pro Fall genügen Szenarienkennung, Stimmquelle, Sprechtext, Pausenmarkierung und eine gemeinsame Zeitachse mit Referenzende und den drei Endentscheidungen. Zwei bis vier Sätze erläutern die Beobachtung. Die Erklärung bleibt bei den gemessenen Entscheidungen; aus einem erfolgreichen Abschluss lässt sich beispielsweise nicht ableiten, ob ein Modell eine IBAN inhaltlich geprüft hat.

## Umsetzung und Verweise im Haupttext

1. Den finalen Datensatz, die ausgewählten Verfahren und die Herkunft sämtlicher verwendeter Ergebnisse festlegen.
2. Den Szenarienkatalog sowie die Konfigurations- und Ergebnistabellen aus diesen Daten ableiten.
3. Die tatsächlich angewendeten Annotationsregeln formulieren und gegebenenfalls zwei Einzelfälle ergänzen.
4. Den Dokumentanhang einfügen und gezielt darauf verweisen: Kapitel 3.1 auf A, Kapitel 3.2 auf B und C, Kapitel 3.3 auf D sowie Kapitel 4 auf E und gegebenenfalls F.
5. Die ZIP-Datei zusammenstellen, Dateinamen und Ablageorte im Anhang ergänzen und die Abgabe durch Entpacken und Öffnen der enthaltenen Daten prüfen.

Forschungsfrage, wesentliche Messregeln, zentrale Ergebnisse und Limitationen bleiben im Haupttext verständlich. Der Anhang ergänzt die Nachweise. Zusätzliche Theorie, vollständige Quellcodeausdrucke und weitere Oberflächenbilder ohne Bezug zu einer konkreten Aussage bringen für diese Arbeit wenig Nutzen. Ob Anhänge bei der Wortzahl mitgerechnet werden und wo weitere formale Erklärungen stehen müssen, richtet sich nach dem verbindlichen Hochschulleitfaden.
