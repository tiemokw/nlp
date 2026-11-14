import argparse
import json
import os
from pathlib import Path


def main():
    parser = argparse.ArgumentParser(description="EOT Lab: lokale Modelle und reproduzierbare Auswertung")
    parser.add_argument("--data-dir", type=Path, default=Path(os.environ.get("EOT_DATA_DIR", "data")))
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("prepare-models")
    sub.add_parser("doctor")
    command = sub.add_parser("run")
    command.add_argument("run_id")
    synthesis = sub.add_parser("generate")
    synthesis.add_argument("job_id")
    args = parser.parse_args()
    root = args.data_dir.resolve()
    if args.command == "prepare-models":
        from eot_eval.models import prepare

        print(json.dumps(prepare(root), indent=2))
    elif args.command == "doctor":
        from eot_eval.models import inventory

        print(json.dumps(inventory(root), ensure_ascii=False, indent=2))
    elif args.command == "run":
        from eot_eval.runner import run

        run(root, args.run_id)
    else:
        from app.synthesis import generate

        generate(root, args.job_id)


if __name__ == "__main__":
    main()
