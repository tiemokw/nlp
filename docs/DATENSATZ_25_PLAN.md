# Umsetzung: 25 Szenarien, zwei Stimmquellen

## Versuchsaufbau

Die Studie enthält 25 Szenarien, jeweils einmal vom Autor und einmal von einer
ausgewählten weiblichen ElevenLabs-Stimme gesprochen: insgesamt 50 Audiodateien.
Sechs Inhaltsarten × vier Sprechverläufe ergeben 24 Szenarien. Ein zusätzlicher
IBAN-Fall mit 3,5 Sekunden Denkpause ergänzt den Plan auf 25. Die Inhaltsarten
sind Kundennummer, IBAN, E-Mail, Adresse/Termin, Technik und Vertrag/Rechnung.

Beide Quellen verwenden dieselben ausgeschriebenen Texte, Abschnittsgrenzen und
Sprechvorgaben. Der Bezugstimeout für die Aufnahmeplanung beträgt 1000 ms;
Pausen von 1800, 2200 und 3500 ms überschreiten ihn. Die Evaluation darf mehrere
Timeouts vergleichen; ihre tatsächlich gewählten Werte werden automatisch mit jedem Lauf gespeichert.
Die menschlichen Pausen sind Zielwerte und werden in der Wellenform nachgemessen.
Stimmquelle und natürliche/synthetische Entstehung sind im Design gekoppelt.
Die 50 Dateien sind 25 Szenarienpaare, keine 50 unabhängigen Szenarien.

## Arbeitsschritte

1. Zentralen, versionierten Katalog anlegen; vorhandene Altaufnahmen erhalten.
2. Datensatzübersicht mit 25 Paaren, Quellenfortschritt und offenen Referenzenden.
3. Aufnahmeansicht auf den Autor beschränken, mit genauem Text, Tempo,
   Betonung, Pausenanweisung und sechs Sekunden Nachlauf.
4. ElevenLabs-Ansicht auf eine Stimme und genau 25 Generierungen umstellen.
   Weibliche Stimmen filtern; unbekannte Geschlechtslabels ausdrücklich bestätigen.
   Vorschau, Cache, Abbruch und nachvollziehbare Herkunft beibehalten.
5. Synthetische Referenzenden zunächst als Vorschlag behandeln. Für beide Quellen
   Anhören und manuelle Markierung in derselben Wellenform ermöglichen.
6. Gemeinsamen unveränderlichen Stand erst bei 25 vollständigen Paaren und 50
   manuell bestätigten Referenzenden freigeben. Manifest und WAV-Dateien exportieren.
7. Katalog, Paarbildung, Annotation, eingefrorene Stände, Generierung und
   Fehlerfälle automatisiert prüfen; UI im Browser kontrollieren.

## Bedienung

Unter „Datensatz“ findest du alle 25 Paare. Unter „Selbst aufnehmen“ liest du pro
Karte ausschließlich den hervorgehobenen Sprechtext. Die Pausenhinweise werden
nicht mitgesprochen. Klicke nach dem letzten Laut auf „Beitrag fertig“ und bleibe
sechs Sekunden still. Höre den Versuch an und übernimm ihn.

Unter „ElevenLabs“ lädst du die verfügbaren Stimmen, wählst eine weibliche Stimme,
prüfst die kostenlose Vorschau und startest die 25 Generierungen. Ein Fehler
löst keine automatische kostenpflichtige Wiederholung aus. Erfolgreiche
Basisantworten werden bei einem erneuten Start aus dem Cache geladen.

Unter „Referenzenden“ hörst du jede Datei an, markierst das Ende des letzten
Lauts mit „Abspielposition als Gold-Ende“ und speicherst die Annotation. Bei
Selbstkorrekturen und Nachträgen gilt das Ende des gesamten Beitrags. Eine
zusätzliche Bestätigung oder Prüferkennung ist nicht erforderlich. Erst danach erstellst du unter „Datensatz“ den gemeinsamen
50-Dateien-Stand und lädst ihn als ZIP herunter.

Jede Evaluation verwendet den gesamten gewählten Datensatz und läuft in Echtzeit.
Die Oberfläche bietet Silero VAD, LiveKit und Scribe v3 Live. Modelle und Parameter
werden beim Start automatisch gespeichert; Split-, Modus- und Konfigurationsauswahl
entfallen. Ältere Pilot-/Benchmark-Datensätze und Ergebnisse bleiben verfügbar.
