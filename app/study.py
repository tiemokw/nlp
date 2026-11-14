"""Shared, immutable recording protocol for 25 paired study scenarios."""

STUDY_ID = "paired-25-v1"
AUTHOR_ID = "AUTHOR"
REFERENCE_TIMEOUT_MS = 1000

CONTENT_LABELS = {
    "K": "Kundennummer",
    "I": "IBAN",
    "E": "E-Mail-Adresse",
    "A": "Adresse / Termin",
    "T": "Technisches Anliegen",
    "V": "Vertrag / Rechnung",
}
PATTERN_LABELS = {
    "F": "Flüssig",
    "U": "Denkpause im offenen Satz",
    "R": "Selbstkorrektur",
    "N": "Vollständiger Satz mit Nachtrag",
}

# All identifiers, addresses and situations are fictitious. Number words ensure
# that both sources receive the same spoken wording rather than TTS normalization.
SCRIPTS = {
    "K": [
        ["Meine Kundennummer ist sieben drei neun eins sechs vier zwei acht."],
        ["Meine Kundennummer ist sieben drei neun eins", "sechs vier zwei acht."],
        [
            "Meine Kundennummer ist sieben drei neun zwei,",
            "Entschuldigung, sieben drei neun eins sechs vier zwei acht.",
        ],
        [
            "Ich möchte meine Kundennummer durchgeben.",
            "Sie lautet sieben drei neun eins sechs vier zwei acht.",
        ],
    ],
    "I": [
        [
            "Meine IBAN lautet DE acht neun drei sieben null vier null null vier vier null fünf drei zwei null eins drei null null null."
        ],
        [
            "Meine IBAN lautet DE acht neun drei sieben null vier null null vier vier",
            "null fünf drei zwei null eins drei null null null.",
        ],
        [
            "Meine IBAN beginnt mit DE acht acht,",
            "Entschuldigung, DE acht neun. Danach drei sieben null vier null null vier vier null fünf drei zwei null eins drei null null null.",
        ],
        [
            "Bitte ändern Sie meine Bankverbindung.",
            "Die neue IBAN lautet DE acht neun drei sieben null vier null null vier vier null fünf drei zwei null eins drei null null null.",
        ],
    ],
    "E": [
        ["Bitte senden Sie die Bestätigung an lea Punkt peters at example Punkt org."],
        ["Meine E-Mail-Adresse lautet lea Punkt", "peters at example Punkt org."],
        [
            "Meine E-Mail-Adresse ist lea Punkt peter,",
            "ich korrigiere: lea Punkt peters at example Punkt org.",
        ],
        [
            "Bitte schicken Sie mir die Rechnung per E-Mail.",
            "Die Adresse ist lea Punkt peters at example Punkt org.",
        ],
    ],
    "A": [
        ["Bitte liefern Sie an den Lindenweg vierundzwanzig in vier fünf eins zwei sieben Essen."],
        ["Für den Technikertermin passt mir am Dienstag", "zehn Uhr am Vormittag."],
        ["Die neue Hausnummer ist vierzehn,", "nein, vierundzwanzig im Lindenweg in Essen."],
        ["Ich möchte den Termin am Freitag absagen.", "Stattdessen passt mir Montag um elf Uhr."],
    ],
    "T": [
        ["Seit gestern bricht meine Internetverbindung bei jedem Videogespräch ab."],
        ["Ich rufe an, weil meine Internetverbindung", "seit gestern bei jedem Videogespräch abbricht."],
        [
            "Mein Router startet gar nicht mehr,",
            "nein, er startet schon, aber die Verbindung bricht danach sofort ab.",
        ],
        [
            "Meine Internetverbindung fällt immer wieder aus.",
            "Das passiert vor allem abends bei Videogesprächen.",
        ],
    ],
    "V": [
        ["Auf meiner Rechnung stehen zwölf Euro fünfzig für einen Dienst, den ich nicht bestellt habe."],
        [
            "Ich habe eine Rückfrage zu meiner Rechnung, und zwar zu",
            "den zusätzlichen zwölf Euro fünfzig für einen nicht bestellten Dienst.",
        ],
        ["Ich möchte meinen Vertrag sofort kündigen,", "Entschuldigung, erst zum Ende der Laufzeit."],
        [
            "Ich möchte meinen Vertrag kündigen.",
            "Allerdings erst zum Ende der Laufzeit, damit meine Rufnummer erhalten bleibt.",
        ],
    ],
}

DELIVERIES = [
    (
        "Ruhig und sachlich",
        "Normale Stimmlage, gleichmäßiges Tempo. Den letzten Satz hörbar abschließen.",
        1.0,
        0.0,
    ),
    (
        "Suchend und nachdenklich",
        "Etwas langsamer sprechen. Vor der Pause offen bleiben, danach den Gedanken fortsetzen.",
        0.9,
        0.15,
    ),
    (
        "Bestimmt und korrigierend",
        "Zunächst sicher beginnen. Die Korrektur deutlich betonen, anschließend natürlich abschließen.",
        1.0,
        0.35,
    ),
    (
        "Lebhaft mit Nachtrag",
        "Etwas zügiger sprechen. Den ersten Satz abschließen; den Nachtrag wie einen nachträglichen Einfall ergänzen.",
        1.1,
        0.4,
    ),
]


def study_cards():
    cards = []
    for content_index, (content, scripts) in enumerate(SCRIPTS.items()):
        for pattern_index, (pattern, segments) in enumerate(zip(PATTERN_LABELS, scripts)):
            delivery, direction, speed, style = DELIVERIES[pattern_index]
            pause = {
                "F": [],
                "U": [400 if content_index % 2 == 0 else 1800],
                "R": [700 if content_index % 2 == 0 else 1800],
                "N": [2200],
            }[pattern]
            number = len(cards) + 1
            cards.append(
                {
                    "id": f"ST25-{number:02}",
                    "pair_id": f"S{number:02}",
                    "study_id": STUDY_ID,
                    "participant_id": AUTHOR_ID,
                    "number": number,
                    "content_type": content,
                    "content_label": CONTENT_LABELS[content],
                    "turn_pattern": pattern,
                    "pattern_label": PATTERN_LABELS[pattern],
                    "title": f"{CONTENT_LABELS[content]} · {PATTERN_LABELS[pattern]}",
                    "goal": f"{CONTENT_LABELS[content]} · {PATTERN_LABELS[pattern]}",
                    "segments": segments,
                    "transcript": " ".join(segments),
                    "pauses_ms": pause,
                    "facts": "Alle Angaben sind erfundene Beispieldaten.",
                    "instruction": direction,
                    "delivery": delivery,
                    "speed": speed,
                    "style": style,
                    "reference_timeout_ms": REFERENCE_TIMEOUT_MS,
                    "ambiguous": pattern == "N",
                    "version": 1,
                    "guidance": "Lies den Sprechtext wortgetreu. Regieanweisungen und Pausenmarken nicht mitsprechen. Nach dem letzten Laut auf ‚Beitrag fertig‘ klicken und sechs Sekunden still bleiben.",
                }
            )
    extra = {
        **cards[5],
        "id": "ST25-25",
        "pair_id": "S25",
        "number": 25,
        "title": "IBAN · Lange Suchpause",
        "goal": "IBAN · Lange Suchpause",
        "pauses_ms": [3500],
        "segments": [
            "Ich lese meine IBAN ab. Sie lautet DE acht neun drei sieben null vier null null vier vier",
            "null fünf drei zwei null eins drei null null null.",
        ],
        "instruction": "Lies die erste Hälfte langsam ab. Schaue dann 3,5 Sekunden still nach und sprich die restlichen Ziffern. Während der Pause keine Füllwörter sprechen.",
    }
    extra["transcript"] = " ".join(extra["segments"])
    cards.append(extra)
    return cards


def protocol():
    return {
        "id": STUDY_ID,
        "scenarios_per_source": 25,
        "sources": ["human", "synthetic"],
        "total_files": 50,
        "reference_timeout_ms": REFERENCE_TIMEOUT_MS,
        "design": "6 Inhaltsarten × 4 Sprechverläufe + 1 IBAN mit 3500 ms Suchpause",
        "split": "test",
        "tail_seconds": 6,
    }
