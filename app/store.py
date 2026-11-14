import json
import random
import sqlite3
import uuid
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from app.audio import RATE, decode, digest
from app.scenarios import cards
from app.study import AUTHOR_ID, STUDY_ID, protocol, study_cards


def now():
    return datetime.now(timezone.utc).isoformat()


def dumps(value):
    return json.dumps(value, ensure_ascii=False, sort_keys=True, allow_nan=False)


class Conflict(ValueError):
    pass


class Store:
    def __init__(self, root: Path):
        self.root = Path(root).resolve()
        for name in ("originals", "canonical", "releases", "runs", "models"):
            (self.root / name).mkdir(parents=True, exist_ok=True)
        self.db_path = self.root / "lab.sqlite3"
        with self.connect() as db:
            db.executescript("""
            CREATE TABLE IF NOT EXISTS participants(id TEXT PRIMARY KEY, split TEXT NOT NULL, metadata TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS scenarios(id TEXT PRIMARY KEY, participant_id TEXT NOT NULL REFERENCES participants(id), payload TEXT NOT NULL, position INTEGER NOT NULL);
            CREATE TABLE IF NOT EXISTS attempts(id TEXT PRIMARY KEY, scenario_id TEXT NOT NULL REFERENCES scenarios(id), payload TEXT NOT NULL, selected INTEGER NOT NULL DEFAULT 0, rejected TEXT, created_at TEXT NOT NULL);
            CREATE UNIQUE INDEX IF NOT EXISTS one_selected ON attempts(scenario_id) WHERE selected=1;
            CREATE TABLE IF NOT EXISTS annotations(id INTEGER PRIMARY KEY AUTOINCREMENT, attempt_id TEXT NOT NULL REFERENCES attempts(id), payload TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS releases(id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS configurations(id TEXT PRIMARY KEY, payload TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, status TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS run_labels(id TEXT PRIMARY KEY REFERENCES runs(id), name TEXT NOT NULL, updated_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS audit(id INTEGER PRIMARY KEY AUTOINCREMENT, action TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS syntheses(id TEXT PRIMARY KEY, status TEXT NOT NULL, payload TEXT NOT NULL, created_at TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS synthetic_records(id TEXT PRIMARY KEY, payload TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS clip_annotations(id INTEGER PRIMARY KEY AUTOINCREMENT, clip_id TEXT NOT NULL REFERENCES synthetic_records(id), payload TEXT NOT NULL, created_at TEXT NOT NULL);
            """)
            for p in range(1, 6):
                db.execute(
                    "INSERT OR IGNORE INTO participants VALUES(?,?,?)",
                    (
                        f"P{p:02}",
                        "dev" if p == 1 else "test",
                        dumps({"label": f"Person {p}", "age_group": "", "notes": ""}),
                    ),
                )
                items = [c for c in cards() if c["participant_id"] == f"P{p:02}"]
                random.Random(4200 + p).shuffle(items)
                for position, item in enumerate(items):
                    db.execute(
                        "INSERT OR IGNORE INTO scenarios VALUES(?,?,?,?)",
                        (item["id"], item["participant_id"], dumps(item), position),
                    )
            db.execute(
                "INSERT OR IGNORE INTO participants VALUES(?,?,?)",
                (AUTHOR_ID, "test", dumps({"label": "Autor · eigene Stimme", "age_group": "", "notes": ""})),
            )
            for position, item in enumerate(study_cards()):
                db.execute(
                    "INSERT OR IGNORE INTO scenarios VALUES(?,?,?,?)",
                    (item["id"], AUTHOR_ID, dumps(item), position),
                )

    def connect(self):
        db = sqlite3.connect(self.db_path, timeout=15)
        db.row_factory = sqlite3.Row
        db.execute("PRAGMA foreign_keys=ON")
        return db

    def audit(self, db, action, payload):
        db.execute(
            "INSERT INTO audit(action,payload,created_at) VALUES(?,?,?)", (action, dumps(payload), now())
        )

    def participants(self):
        with self.connect() as db:
            result = []
            for p in db.execute("SELECT * FROM participants ORDER BY id").fetchall():
                n = db.execute(
                    "SELECT COUNT(*) FROM attempts a JOIN scenarios s ON s.id=a.scenario_id WHERE a.selected=1 AND s.participant_id=?",
                    (p["id"],),
                ).fetchone()[0]
                result.append(
                    {
                        "id": p["id"],
                        "split": p["split"],
                        **json.loads(p["metadata"]),
                        "accepted": n,
                        "total": db.execute(
                            "SELECT COUNT(*) FROM scenarios WHERE participant_id=?", (p["id"],)
                        ).fetchone()[0],
                    }
                )
            return result

    def update_participant(self, ident, metadata):
        with self.connect() as db:
            if not db.execute("SELECT id FROM participants WHERE id=?", (ident,)).fetchone():
                raise ValueError("Unbekannte Person.")
            db.execute("UPDATE participants SET metadata=? WHERE id=?", (dumps(metadata), ident))

    def scenarios(self, participant_id):
        with self.connect() as db:
            return [
                {**json.loads(r["payload"]), "selected_attempt": r["selected_attempt"]}
                for r in db.execute(
                    "SELECT s.*, (SELECT a.id FROM attempts a WHERE a.scenario_id=s.id AND a.selected=1) AS selected_attempt FROM scenarios s WHERE s.participant_id=? ORDER BY position",
                    (participant_id,),
                )
            ]

    def attempt(self, ident):
        with self.connect() as db:
            r = db.execute(
                "SELECT a.*,s.payload AS card,p.split FROM attempts a JOIN scenarios s ON s.id=a.scenario_id JOIN participants p ON p.id=s.participant_id WHERE a.id=?",
                (ident,),
            ).fetchone()
            if not r:
                raise ValueError("Unbekannte Aufnahme.")
            anno = db.execute(
                "SELECT * FROM annotations WHERE attempt_id=? ORDER BY id DESC LIMIT 1", (ident,)
            ).fetchone()
            return {
                "id": r["id"],
                "scenario_id": r["scenario_id"],
                "selected": bool(r["selected"]),
                "rejected": r["rejected"],
                "created_at": r["created_at"],
                "split": r["split"],
                **json.loads(r["payload"]),
                "card": json.loads(r["card"]),
                "annotation": ({**json.loads(anno["payload"]), "revision": anno["id"]} if anno else None),
            }

    def attempts(self, participant=None):
        with self.connect() as db:
            ids = db.execute(
                "SELECT a.id FROM attempts a JOIN scenarios s ON s.id=a.scenario_id WHERE (? IS NULL OR s.participant_id=?) ORDER BY a.created_at DESC",
                (participant, participant),
            ).fetchall()
        return [self.attempt(r["id"]) for r in ids]

    def upload(self, ident, scenario_id, data, metadata):
        try:
            if str(uuid.UUID(ident)) != ident:
                raise ValueError()
        except (ValueError, AttributeError):
            raise ValueError("Die Versuch-ID muss eine UUID sein.") from None
        fingerprint = digest(data + dumps({"scenario": scenario_id, "metadata": metadata}).encode())
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute("SELECT payload FROM attempts WHERE id=?", (ident,)).fetchone()
            if old:
                if json.loads(old["payload"])["upload_fingerprint"] != fingerprint:
                    raise Conflict("Diese Versuch-ID enthält bereits andere Daten.")
                return self.attempt(ident)
            if not db.execute("SELECT id FROM scenarios WHERE id=?", (scenario_id,)).fetchone():
                raise ValueError("Unbekannte Aufnahmekarte.")
            canonical, info = decode(data)
            payload = {**info, "capture": metadata, "upload_fingerprint": fingerprint}
            original_path = self.root / "originals" / f"{ident}.wav"
            canonical_path = self.root / "canonical" / f"{ident}.wav"
            try:
                original_path.write_bytes(data)
                canonical_path.write_bytes(canonical)
                db.execute(
                    "INSERT INTO attempts(id,scenario_id,payload,created_at) VALUES(?,?,?,?)",
                    (ident, scenario_id, dumps(payload), now()),
                )
                self.audit(db, "upload", {"attempt": ident})
            except Exception:
                original_path.unlink(missing_ok=True)
                canonical_path.unlink(missing_ok=True)
                raise
        return self.attempt(ident)

    def select(self, ident, reason=""):
        attempt = self.attempt(ident)
        with self.connect() as db:
            db.execute("BEGIN IMMEDIATE")
            old = db.execute(
                "SELECT id FROM attempts WHERE scenario_id=? AND selected=1", (attempt["scenario_id"],)
            ).fetchone()
            if old and old["id"] != ident and not reason.strip():
                raise ValueError("Zum Ersetzen einer übernommenen Aufnahme bitte einen Grund angeben.")
            db.execute("UPDATE attempts SET selected=0 WHERE scenario_id=?", (attempt["scenario_id"],))
            db.execute("UPDATE attempts SET selected=1,rejected=NULL WHERE id=?", (ident,))
            self.audit(
                db, "select", {"attempt": ident, "previous": old["id"] if old else None, "reason": reason}
            )
        return self.attempt(ident)

    def reject(self, ident, reason):
        self.attempt(ident)
        if not reason.strip():
            raise ValueError("Bitte einen Wiederholungsgrund angeben.")
        with self.connect() as db:
            db.execute("UPDATE attempts SET selected=0,rejected=? WHERE id=?", (reason, ident))
            self.audit(db, "reject", {"attempt": ident, "reason": reason})

    def annotate(self, ident, annotation):
        attempt = self.clip(ident)
        previous = attempt.get("annotation") or {}
        card = attempt.get("card") or attempt.get("scenario") or {}
        previous_annotator = previous.get("annotator", "local")
        annotation = {
            "holds": previous.get("holds", []),
            "transcript": previous.get("transcript", ""),
            "annotator": "local" if previous_annotator == "automatic" else previous_annotator,
            "reviewer": "",
            "status": "annotated",
            "ambiguous_transition": previous.get("ambiguous_transition", card.get("ambiguous", False)),
            "notes": previous.get("notes", ""),
            "listened": False,
            **annotation,
        }
        is_synthetic = attempt.get("source") == "synthetic"
        is_study = attempt.get("study_id") == STUDY_ID or attempt.get("card", {}).get("study_id") == STUDY_ID
        if is_study:
            if not annotation.get("transcript", "").strip():
                raise ValueError("Bitte ein Transkript für den Beitrag angeben.")
            annotation = {**annotation, "reference_method": "human_waveform_annotation"}
        if not annotation["annotator"].strip():
            raise ValueError("Bitte eine Annotatorkennung angeben.")
        end = annotation["gold_eot_sample"]
        if not 0 < end <= attempt["samples"] - 6 * RATE:
            raise ValueError("Nach dem Gold-Ende müssen mindestens sechs Sekunden Audio vorhanden sein.")
        previous_end = 0
        for hold in sorted(annotation["holds"], key=lambda h: h["start_sample"]):
            if not previous_end <= hold["start_sample"] < hold["end_sample"] <= end:
                raise ValueError(
                    "HOLD-Pausen müssen geordnet, überlappungsfrei und vor dem Gold-Ende liegen."
                )
            previous_end = hold["end_sample"]
        if annotation["status"] == "reviewed":
            if (
                not annotation.get("reviewer", "").strip()
                or annotation["reviewer"].strip().casefold() == annotation["annotator"].strip().casefold()
            ):
                raise ValueError("Die Gegenprüfung braucht eine andere Prüferkennung.")
        with self.connect() as db:
            if is_synthetic:
                db.execute(
                    "INSERT INTO clip_annotations(clip_id,payload,created_at) VALUES(?,?,?)",
                    (ident, dumps(annotation), now()),
                )
            else:
                db.execute(
                    "INSERT INTO annotations(attempt_id,payload,created_at) VALUES(?,?,?)",
                    (ident, dumps(annotation), now()),
                )
        return self.clip(ident)

    def release(self, kind):
        attempts = [
            a
            for a in self.attempts()
            if a["selected"]
            and a["card"].get("study_id") != STUDY_ID
            and (kind == "final" or a["split"] == "dev")
        ]
        if not attempts:
            raise ValueError("Keine übernommenen Aufnahmen für diesen Datensatzstand.")
        if any(a["annotation"] is None for a in attempts):
            raise ValueError("Alle ausgewählten Aufnahmen müssen annotiert sein.")
        if kind == "final":
            counts = Counter(a["card"]["participant_id"] for a in attempts)
            if len(attempts) != 100 or counts != Counter({f"P{i:02}": 20 for i in range(1, 6)}):
                raise ValueError("Der finale Stand braucht 100 Beiträge, je 20 pro Person.")
            if sum(a["annotation"]["status"] == "reviewed" for a in attempts) < 20:
                raise ValueError("Mindestens 20 Beiträge müssen gegengeprüft sein.")
        records = []
        for a in sorted(attempts, key=lambda a: a["scenario_id"]):
            path = self.root / "canonical" / f"{a['id']}.wav"
            if digest(path.read_bytes()) != a["canonical_sha256"]:
                raise Conflict("Eine Audiodatei wurde nachträglich verändert.")
            records.append(
                {
                    "id": a["id"],
                    "scenario_id": a["scenario_id"],
                    "participant_id": a["card"]["participant_id"],
                    "content_type": a["card"]["content_type"],
                    "turn_pattern": a["card"]["turn_pattern"],
                    "split": a["split"],
                    "audio_path": f"canonical/{a['id']}.wav",
                    "sha256": a["canonical_sha256"],
                    "samples": a["samples"],
                    "sample_rate": RATE,
                    "annotation": a["annotation"],
                }
            )
        payload = {"schema_version": 1, "kind": kind, "created_at": now(), "records": records}
        ident = digest(dumps(payload).encode())[:20]
        payload["id"] = ident
        (self.root / "releases" / f"{ident}.json").write_text(dumps(payload), encoding="utf-8")
        with self.connect() as db:
            db.execute("INSERT INTO releases VALUES(?,?,?)", (ident, dumps(payload), now()))
        return payload

    def get(self, table, ident):
        if table not in {"releases", "configurations", "runs", "syntheses"}:
            raise ValueError("Unbekannte Tabelle.")
        with self.connect() as db:
            r = db.execute(f"SELECT * FROM {table} WHERE id=?", (ident,)).fetchone()
        if not r:
            raise ValueError("Unbekannte ID.")
        payload = {
            **json.loads(r["payload"]),
            **({"status": r["status"]} if table in {"runs", "syntheses"} else {}),
        }
        if table == "runs":
            with self.connect() as db:
                label = db.execute("SELECT name,updated_at FROM run_labels WHERE id=?", (ident,)).fetchone()
            payload["name"] = label["name"] if label else payload.get("name") or f"Evaluation {ident[:8]}"
            if label:
                payload["name_updated_at"] = label["updated_at"]
        return payload

    def rename_run(self, ident, name):
        self.get("runs", ident)
        name = name.strip()
        if not name or len(name) > 120:
            raise ValueError("Ein Evaluationsname muss zwischen 1 und 120 Zeichen enthalten.")
        # Labels are separate from worker progress, so a concurrent update cannot undo a rename.
        with self.connect() as db:
            db.execute(
                "INSERT INTO run_labels VALUES(?,?,?) ON CONFLICT(id) DO UPDATE SET name=excluded.name,updated_at=excluded.updated_at",
                (ident, name, now()),
            )
            self.audit(db, "rename_run", {"id": ident, "name": name})
        return self.get("runs", ident)

    def listing(self, table):
        if table not in {"releases", "configurations", "runs", "syntheses"}:
            raise ValueError("Unbekannte Tabelle.")
        with self.connect() as db:
            ids = db.execute(f"SELECT id FROM {table} ORDER BY created_at DESC").fetchall()
        return [self.get(table, r["id"]) for r in ids]

    def freeze_config(self, config, model_fingerprints=None):
        payload = {"id": uuid.uuid4().hex, "created_at": now(), "config": config}
        payload["sha256"] = digest(dumps(config).encode())
        payload["model_fingerprints"] = model_fingerprints
        with self.connect() as db:
            db.execute("INSERT INTO configurations VALUES(?,?,?)", (payload["id"], dumps(payload), now()))
        return payload

    def update_run(self, ident, status, **updates):
        payload = self.get("runs", ident)
        payload.pop("status", None)
        payload.update(updates)
        with self.connect() as db:
            db.execute("UPDATE runs SET status=?,payload=? WHERE id=?", (status, dumps(payload), ident))

    def update_synthesis(self, ident, status, **updates):
        payload = self.get("syntheses", ident)
        payload.pop("status", None)
        payload.update(updates)
        with self.connect() as db:
            db.execute("UPDATE syntheses SET status=?,payload=? WHERE id=?", (status, dumps(payload), ident))

    def clip(self, ident):
        with self.connect() as db:
            row = db.execute("SELECT payload FROM synthetic_records WHERE id=?", (ident,)).fetchone()
        if row:
            record = json.loads(row["payload"])
            with self.connect() as db:
                annotation = db.execute(
                    "SELECT id,payload FROM clip_annotations WHERE clip_id=? ORDER BY id DESC LIMIT 1",
                    (ident,),
                ).fetchone()
            if annotation:
                record["annotation"] = {**json.loads(annotation["payload"]), "revision": annotation["id"]}
            return record
        attempt = self.attempt(ident)
        return {**attempt, "audio_path": f"canonical/{ident}.wav", "source": "human"}

    def study_state(self, synthetic_release_id=None):
        releases = [r for r in self.listing("releases") if r.get("kind") == "study_synthetic"]
        synthetic = (
            next((r for r in releases if r["id"] == synthetic_release_id), None)
            if synthetic_release_id
            else next(iter(releases), None)
        )
        if synthetic_release_id and synthetic is None:
            raise ValueError("Bitte einen synthetischen 25-Szenarien-Stand der Studie auswählen.")
        generated = {r["scenario_id"]: self.clip(r["id"]) for r in synthetic["records"]} if synthetic else {}
        humans = {a["scenario_id"]: a for a in self.attempts(AUTHOR_ID) if a["selected"]}
        pairs = []
        for card in study_cards():
            human = humans.get(card["id"])
            pairs.append(
                {
                    "card": card,
                    "human": {**human, "source": "human"} if human else None,
                    "synthetic": generated.get(card["id"]),
                }
            )

        def confirmed(record):
            return bool(
                record
                and record.get("annotation")
                and record["annotation"].get("reference_method") == "human_waveform_annotation"
            )

        counts = {
            "human": len(humans),
            "synthetic": len(generated),
            "human_annotated": sum(confirmed(p["human"]) for p in pairs),
            "synthetic_annotated": sum(confirmed(p["synthetic"]) for p in pairs),
            "complete_pairs": sum(confirmed(p["human"]) and confirmed(p["synthetic"]) for p in pairs),
        }
        return {
            "protocol": protocol(),
            "pairs": pairs,
            "counts": counts,
            "ready": counts["complete_pairs"] == 25,
            "synthetic_release_id": synthetic["id"] if synthetic else None,
            "synthetic_releases": [
                {"id": r["id"], "created_at": r["created_at"], "voice": r["synthesis_config"]["voices"][0]}
                for r in releases
            ],
            "releases": [
                {"id": r["id"], "created_at": r["created_at"], "records": len(r["records"])}
                for r in self.listing("releases")
                if r.get("kind") == "study_paired"
            ],
        }

    def release_study(self, synthetic_release_id):
        state = self.study_state(synthetic_release_id)
        if not state["ready"]:
            c = state["counts"]
            raise ValueError(
                f"Benötigt: 25 eigene und 25 synthetische Aufnahmen mit manuell bestätigtem Referenzende. Aktuell: {c['human']}/25 eigene, {c['synthetic']}/25 synthetische; {c['human_annotated'] + c['synthetic_annotated']}/50 Referenzenden."
            )
        records = []
        for pair in state["pairs"]:
            card = pair["card"]
            for source in ("human", "synthetic"):
                clip = pair[source]
                path = clip.get("audio_path", f"canonical/{clip['id']}.wav")
                sha = clip.get("sha256") or clip["canonical_sha256"]
                if digest((self.root / path).read_bytes()) != sha:
                    raise Conflict("Eine Studienaufnahme wurde verändert; Freigabe abgebrochen.")
                record = {
                    "id": clip["id"],
                    "study_id": STUDY_ID,
                    "pair_id": card["pair_id"],
                    "scenario_id": card["id"],
                    "participant_id": AUTHOR_ID if source == "human" else "ELEVENLABS",
                    "source": source,
                    "content_type": card["content_type"],
                    "turn_pattern": card["turn_pattern"],
                    "split": "test",
                    "audio_path": path,
                    "sha256": sha,
                    "samples": clip["samples"],
                    "sample_rate": RATE,
                    "annotation": clip["annotation"],
                    "scenario": card,
                }
                for key in ("provenance", "base_id", "synthesis_job_id", "generated_reference", "capture"):
                    if key in clip:
                        record[key] = clip[key]
                records.append(record)
        payload = {
            "schema_version": 3,
            "kind": "study_paired",
            "source": "mixed",
            "study_id": STUDY_ID,
            "protocol": protocol(),
            "synthetic_release_id": state["synthetic_release_id"],
            "synthesis_config": self.get("releases", state["synthetic_release_id"])["synthesis_config"],
            "independent_base_files": 25,
            "annotation_method": "human_waveform_annotation",
            "created_at": now(),
            "records": records,
        }
        ident = digest(dumps(payload).encode())[:20]
        payload["id"] = ident
        with self.connect() as db:
            db.execute("INSERT INTO releases VALUES(?,?,?)", (ident, dumps(payload), now()))
        (self.root / "releases" / f"{ident}.json").write_text(dumps(payload), encoding="utf-8")
        return payload

    def save_synthetic_release(self, payload):
        ids = [r["id"] for r in payload["records"]]
        if len(ids) != len(set(ids)) or not ids:
            raise ValueError("Synthetischer Datensatz enthält keine eindeutigen Clips.")
        for record in payload["records"]:
            if (
                record["source"] != "synthetic"
                or digest((self.root / record["audio_path"]).read_bytes()) != record["sha256"]
            ):
                raise ValueError("Synthetischer Clip fehlt oder seine Prüfsumme stimmt nicht.")
        ident = digest(dumps(payload).encode())[:20]
        payload = {**payload, "id": ident}
        with self.connect() as db:
            for record in payload["records"]:
                db.execute("INSERT INTO synthetic_records VALUES(?,?)", (record["id"], dumps(record)))
            db.execute("INSERT INTO releases VALUES(?,?,?)", (ident, dumps(payload), now()))
        (self.root / "releases" / f"{ident}.json").write_text(dumps(payload), encoding="utf-8")
        return payload
