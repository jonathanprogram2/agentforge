
import argparse
import json
import re
import subprocess
from pathlib import Path

from app.evaluator import REPORTS, ROOT

IMAGE = "agentforge-sandbox:v4"


def score_heldout(run_id=None):
    if run_id:
        if not re.fullmatch(r"\d{8}T\d{12}Z", run_id):
            raise ValueError("Invalid run ID.")

        report_path = REPORTS / "history" / f"{run_id}.json"
    else:
        report_path = REPORTS / "multi_agent_latest.json"

    run = json.loads(report_path.read_text(encoding="utf-8"))

    benchmark = run["benchmark"]
    run_id = run["run_id"]

    if benchmark != "inventory_case":
        raise ValueError("Only inventory_case has held-out tests.")

    if not re.fullmatch(r"\d{8}T\d{12}Z", run_id):
        raise ValueError("Invalid stored run ID.")

    candidate = (
        REPORTS / "history" / f"{run_id}_candidate.py"
    ).resolve()

    if not candidate.is_file():
        raise FileNotFoundError(f"Candidate not found: {candidate}")

    command = [
        "docker", "run", "--rm",
        "--network", "none",
        "--read-only",
        "--memory", "256m",
        "--cpus", "1",
        "--pids-limit", "64",
        "--cap-drop", "ALL",
        "--security-opt", "no-new-privileges",
        "--user", "10001:10001",
        "--tmpfs",
        "/workspace/reports:rw,size=16m,uid=10001,gid=10001",
        "--tmpfs",
        "/tmp:rw,size=32m,uid=10001,gid=10001",
        "--mount",
        (
            f"type=bind,source={candidate},"
            "target=/workspace/benchmarks/"
            "inventory_case/inventory.py,readonly"
        ),
        IMAGE,
        "python", "-m", "app.heldout_runner",
        "--benchmark", benchmark,
    ]

    completed = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=90,
    )

    if completed.returncode != 0:
        raise RuntimeError(
            "Docker held-out evaluation failed:\n"
            + completed.stderr[-2000:]
            + completed.stdout[-2000:]
        )

    metrics = json.loads(completed.stdout)

    result = {
        "run_id": run_id,
        "benchmark": benchmark,
        "model": run["model"],
        "public_success": run["success"],
        "heldout_evaluation": metrics,
    }

    output = REPORTS / f"{run_id}_heldout.json"

    output.write_text(
        json.dumps(result, indent=2),
        encoding="utf-8",
    )

    print("\n=== AgentForge Held-Out Scoring ===")
    print(json.dumps(result, indent=2))
    print(f"\nReport saved: {output}")

    return result


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--run-id", default=None)

    args = parser.parse_args()
    score_heldout(args.run_id)
