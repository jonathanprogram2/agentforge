
import json
from pathlib import Path

from app.evaluator import REPORTS

HISTORY = REPORTS / "history"

MODELS = {
    "openai/gpt-oss-20b": "GPT-OSS 20B",
    "openai/gpt-oss-120b": "GPT-OSS 120B",
}

BENCHMARKS = [
    "pricing_case", 
    "pagination_case", 
    "inventory_case",
    ]


def load_latest_runs():
    """Find the newest completed run for each model and benchmark."""

    latest = {}

    for path in HISTORY.glob("*.json"):
        try:
            run = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError):
            continue

        if not isinstance(run, dict):
            continue

        model = run.get("model")
        benchmark = run.get("benchmark")
        run_id = run.get("run_id")

        if (
            model not in MODELS
            or benchmark not in BENCHMARKS
            or not isinstance(run_id, str)
            or not isinstance(run.get("evaluation"), dict)
            or "duration_seconds" not in run
        ):
            continue

        key = (benchmark, model)

        if key not in latest or run_id > latest[key]["run_id"]:
            latest[key] = run

    return latest


def main():
    if not HISTORY.exists():
        raise RuntimeError("No experiment history found.")

    runs = load_latest_runs()
    comparison = []

    for benchmark in BENCHMARKS:
        for model, model_label in MODELS.items():
            run = runs.get((benchmark, model))

            if run is None:
                print(f"Missing experiment: {benchmark} / {model_label}")
                continue

            evaluation = run["evaluation"]
            trajectory = run.get("trajectory", [])

            tool_errors = sum(
                isinstance(event.get("result"), dict)
                and "error" in event["result"]
                for event in trajectory
            )

            comparison.append({
                "run_id": run["run_id"],
                "benchmark": benchmark,
                "model": model,
                "model_label": model_label,
                "success": run["success"],
                "tokens_used": run["tokens_used"],
                "duration_seconds": run["duration_seconds"],
                "evaluations_used": run["evaluations_used"],
                "tool_calls": len(trajectory),
                "tool_errors": tool_errors,
                "fail_to_pass": evaluation["fail_to_pass"],
                "pass_to_pass": evaluation["pass_to_pass"],
            })

    REPORTS.mkdir(exist_ok=True)

    output = REPORTS / "model_comparison_latest.json"
    output.write_text(
        json.dumps(comparison, indent=2),
        encoding="utf-8",
    )

    print("\n=== AgentForge Model Comparison ===\n")

    header = (
        f"{'Benchmark':<18} {'Model':<14} "
        f"{'Success':<9} {'Tokens':>8} "
        f"{'Seconds':>9} {'Tool errors':>12}"
    )

    print(header)
    print("-" * len(header))

    for row in comparison:
        print(
            f"{row['benchmark']:<18} "
            f"{row['model_label']:<14} "
            f"{str(row['success']):<9} "
            f"{row['tokens_used']:>8} "
            f"{row['duration_seconds']:>9.2f} "
            f"{row['tool_errors']:>12}"
        )

    print(f"\nComparison saved to {output}")


if __name__ == "__main__":
    main()
