
import argparse
import json
from collections import defaultdict
from statistics import mean, stdev

from app.evaluator import BENCHMARKS, REPORTS

HISTORY = REPORTS / "history"


def load_experiments(benchmark_name):
    """Load valid saved experiments for a benchmark."""

    experiments = []

    if not HISTORY.exists():
        return experiments

    for path in HISTORY.glob("*.json"):
        try:
            run = json.loads(
                path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            continue

        if not isinstance(run, dict):
            continue

        if run.get("benchmark") != benchmark_name:
            continue

        required = {
            "run_id": str,
            "model": str,
            "success": bool,
            "tokens_used": int,
        }

        if not all(
            isinstance(run.get(key), expected_type)
            for key, expected_type in required.items()
        ):
            continue

        if not isinstance(
            run.get("duration_seconds"), (int, float)
        ):
            continue

        experiments.append(run)

    return experiments


def analyze_reliability(benchmark_name, recent=2):
    """Compare the newest N trials for each model."""

    experiments = load_experiments(benchmark_name)

    groups = defaultdict(list)

    for run in experiments:
        groups[run["model"]].append(run)

    results = []

    for model, runs in sorted(groups.items()):
        runs.sort(key=lambda run: run["run_id"])

        selected = runs[-recent:]

        durations = [
            run["duration_seconds"]
            for run in selected
        ]

        tokens = [
            run["tokens_used"]
            for run in selected
        ]

        successful = sum(
            run["success"] for run in selected
        )

        tool_errors = 0

        for run in selected:
            for event in run.get("trajectory", []):
                result = event.get("result", {})

                if isinstance(result, dict) and "error" in result:
                    tool_errors += 1

        summary = {
            "benchmark": benchmark_name,
            "model": model,
            "trials": len(selected),
            "successful_trials": successful,
            "success_rate_percent": round(
                successful / len(selected) * 100, 2
            ),
            "average_tokens": round(mean(tokens), 2),
            "average_duration_seconds": round(
                mean(durations), 3
            ),
            "duration_stddev_seconds": (
                round(stdev(durations), 3)
                if len(durations) > 1
                else None
            ),
            "tool_errors": tool_errors,
            "run_ids": [
                run["run_id"] for run in selected
            ],
        }

        results.append(summary)

    REPORTS.mkdir(exist_ok=True)

    output = (
        REPORTS /
        f"{benchmark_name}_reliability_latest.json"
    )

    output.write_text(
        json.dumps(results, indent=2),
        encoding="utf-8",
    )

    print("\n=== AgentForge Reliability Analysis ===\n")

    for result in results:
        print(f"Model: {result['model']}")
        print(
            f"Success: {result['successful_trials']}/"
            f"{result['trials']} "
            f"({result['success_rate_percent']}%)"
        )
        print(
            f"Average tokens: {result['average_tokens']}"
        )
        print(
            "Average duration: "
            f"{result['average_duration_seconds']}s"
        )
        print(
            f"Tool errors: {result['tool_errors']}"
        )
        print("-" * 45)

    print(f"\nReliability report saved to {output}")

    return results


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AgentForge Reliability Analyzer"
    )

    parser.add_argument(
        "--benchmark",
        choices=BENCHMARKS.keys(),
        default="inventory_case",
    )

    parser.add_argument(
        "--recent",
        type=int,
        choices=range(1, 101),
        default=2,
        help="Number of newest trials per model",
    )

    args = parser.parse_args()

    analyze_reliability(args.benchmark, args.recent)
