
import json

from fastapi import FastAPI, HTTPException, Query

from fastapi.middleware.cors import CORSMiddleware
from app.evaluator import BENCHMARKS, REPORTS

app = FastAPI(
    title="AgentForge API",
    description="AI Agent Simulation & Evaluation Platform",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[
        "http://localhost:5173",
        "http://127.0.0.1:5173",
    ],
    allow_methods=["GET"],
    allow_headers=["*"],
)


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/api/benchmarks")
def list_benchmarks():
    """Return available coding benchmarks."""

    return [
        {
            "name": name,
            "source_file": config["source_file"],
            "entry_function": config["entry_function"],
            "fail_to_pass_tests": len(config["fail_to_pass"]),
            "pass_to_pass_tests": len(config["pass_to_pass"]),
        }
        for name, config in BENCHMARKS.items()
    ]


@app.get("/api/experiments")
def list_experiments(
    limit: int = Query(default=20, ge=1, le=100)
):
    """Return the latest saved agent experiments."""

    history = REPORTS / "history"

    if not history.exists():
        return []

    experiments = []

    for path in history.glob("*.json"):
        try:
            run = json.loads(
                path.read_text(encoding="utf-8")
            )
        except (OSError, json.JSONDecodeError):
            continue

        if not isinstance(run, dict):
            continue

        if (
            not isinstance(run.get("run_id"), str)
            or not isinstance(run.get("evaluation"), dict)
            or not isinstance(run.get("model"), str)
        ):
            continue

        experiments.append(run)

    experiments.sort(
        key=lambda run: run["run_id"],
        reverse=True,
    )

    return experiments[:limit]


@app.get("/api/comparison")
def get_comparison():
    """Return the latest model comparison results."""

    path = REPORTS / "model_comparison_latest.json"

    if not path.exists():
        raise HTTPException(
            status_code=404,
            detail="No comparison report found. Run app.compare.",
        )

    try:
        return json.loads(
            path.read_text(encoding="utf-8")
        )
    except (OSError, json.JSONDecodeError):
        raise HTTPException(
            status_code=500,
            detail="Comparison report could not be read.",
        )


@app.get("/api/reliability")
def get_reliability():
    """Return saved reliability reports for available benchmarks."""

    results = []

    for benchmark_name in BENCHMARKS:
        path = REPORTS / f"{benchmark_name}_reliability_latest.json"

        if not path.exists():
            continue

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            raise HTTPException(
                status_code=500,
                detail=f"Could not read reliability report for {benchmark_name}",
            ) from exc

        if not isinstance(data, list):
            raise HTTPException(
                status_code=500,
                detail=f"Invalid reliability report for {benchmark_name}",
            )

        results.extend(data)

    return results
