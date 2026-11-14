"""Balanced, versioned scenario assignments; instructions are not read-aloud scripts."""

CONTENTS = {
    "K": (
        "Kundennummer",
        [
            ("Einen neu abgeschlossenen Vertrag zuordnen", "Kundennummer: 73916428"),
            ("Eine fehlende Bestätigung einer Bestellung zuordnen", "Bestandskundennummer: 48273196"),
            ("Nach einem Umzug das richtige Kundenkonto finden", "Konto: 58192473"),
            ("Eine Rücksendung dem Auftrag zuordnen", "Kundennummer: 69134827"),
            ("Eine Rückfrage zur ersten Rechnung stellen", "Kundennummer: 82746135"),
        ],
    ),
    "E": (
        "E-Mail-Adresse",
        [
            ("Eine Bestätigung an eine neue Adresse senden lassen", "lea.peters@example.org"),
            ("Den Versand einer Rechnung per E-Mail beantragen", "tom-berger@example.com"),
            ("Die Adresse für eine Rücksendeanleitung nennen", "maria.schulz@example.org"),
            ("Ein Angebot elektronisch erhalten", "hans.keller@example.com"),
            ("Den Zugang zu einem Benutzerkonto wiederherstellen", "alex.winter@example.org"),
        ],
    ),
    "A": (
        "Adresse / Termin",
        [
            ("Die Lieferadresse ändern lassen", "Erfundene Adresse: Lindenweg 24, 45127 Essen"),
            (
                "Einen Technikertermin vereinbaren",
                "Gewünscht: Dienstag um 10 Uhr, alternativ Donnerstag um 14 Uhr",
            ),
            ("Die Adresse für eine Abholung durchgeben", "Erfundene Adresse: Rosenstraße 17, 44135 Dortmund"),
            ("Einen vereinbarten Termin verschieben", "Bisher Freitag 9 Uhr; gewünscht Montag 11 Uhr"),
            (
                "Eine andere Zustelladresse für eine Ersatzlieferung nennen",
                "Erfundene Adresse: Parkallee 8, 48143 Münster",
            ),
        ],
    ),
    "T": (
        "Technisches Anliegen",
        [
            (
                "Ein Problem während Videogesprächen erklären",
                "Das Bild friert ein; andere Anwendungen funktionieren.",
            ),
            (
                "Einen wiederkehrenden Internetausfall melden",
                "Seit gestern fällt die Verbindung mehrmals am Abend aus.",
            ),
            ("Ein Problem mit einem neuen Gerät beschreiben", "Das Gerät startet, zeigt aber kein Bild."),
            ("Eine Störung beim Telefonieren schildern", "Die Gegenstelle ist hörbar, hört dich aber nicht."),
            (
                "Eine Fehlermeldung in einer Anwendung erklären",
                "Die Anmeldung scheitert mit Fehler 42; das Passwort wurde bereits erneuert.",
            ),
        ],
    ),
    "V": (
        "Vertrag / Rechnung",
        [
            (
                "Den Tarif wegen eines geänderten Bedarfs anpassen",
                "Mehr Datenvolumen benötigt; die Rufnummer soll bleiben.",
            ),
            (
                "Eine unbekannte Rechnungsposition klären",
                "Auf der Rechnung stehen zusätzlich 12,50 Euro für einen nicht bestellten Dienst.",
            ),
            (
                "Die Kündigung zu einem bestimmten Zeitpunkt erklären",
                "Vertrag erst zum Laufzeitende beenden, nicht sofort.",
            ),
            (
                "Eine doppelte Abbuchung reklamieren",
                "Der Monatsbetrag wurde zweimal abgebucht; eine Erstattung ist gewünscht.",
            ),
            (
                "Eine Vertragsverlängerung besprechen",
                "Nur verlängern, wenn die monatlichen Kosten gleich bleiben.",
            ),
        ],
    ),
}
PATTERNS = {
    "F": (
        "Flüssig abgeschlossen",
        "Formuliere einen kurzen vollständigen Beitrag. Beende ihn natürlich, ohne absichtliche Denkpause.",
    ),
    "U": (
        "Offen mit Denkpause",
        "Beginne deine Aussage. Halte an einer sprachlich noch offenen Stelle kurz inne, als müsstest du nachdenken oder nachsehen, und führe sie dann zu Ende.",
    ),
    "N": (
        "Vollständiger Satz mit Nachtrag",
        "Sage zunächst einen vollständigen Satz. Ergänze nach einer kurzen natürlichen Pause eine wichtige Information im selben Beitrag.",
    ),
    "R": (
        "Stocken / Korrektur",
        "Formuliere dein Anliegen mit einer natürlichen Unterbrechung oder Selbstkorrektur. Bei Nummern oder Adressen kannst du einen Bestandteil berichtigen.",
    ),
}


def cards():
    result = []
    for person in range(1, 6):
        for content, (label, stories) in CONTENTS.items():
            goal, facts = stories[person - 1]
            for pattern, (pattern_label, instruction) in PATTERNS.items():
                result.append(
                    {
                        "id": f"P{person:02}-{content}-{pattern}",
                        "participant_id": f"P{person:02}",
                        "content_type": content,
                        "content_label": label,
                        "turn_pattern": pattern,
                        "pattern_label": pattern_label,
                        "goal": goal,
                        "facts": facts,
                        "instruction": instruction,
                        "version": 1,
                        "guidance": "Sprich in eigenen Worten. Die Angaben sind erfunden. Regieanweisungen nicht mitsprechen. Denkpausen müssen nicht exakt lang sein.",
                    }
                )
    return result
