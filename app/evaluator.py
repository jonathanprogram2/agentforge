
import argparse
import json
import subprocess
import sys
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
REPORTS = ROOT / "reports"


# Benchmark dictionary
BENCHMARKS = {
    "pricing_case": {
        "fail_to_pass": [
            "test_ten_percent_discount",
            "test_fifty_percent_discount",
        ],
        "pass_to_pass": [
            "test_zero_discount",
            "test_zero_price",
        ],
        "source_file": "pricing.py",
        "entry_function": "discounted_price",
    },
    "pagination_case": {
        "fail_to_pass": [
            "test_last_page",
            "test_single_page",
        ],
        "pass_to_pass": [
            "test_first_page",
            "test_empty_items",
        ],
        "source_file": "pagination.py",
        "entry_function": "paginate",
    },
    
    "inventory_case": {
        "source_file": "inventory.py",
        "entry_function": "reconcile_inventory",
        "fail_to_pass": [
            "test_repeated_deductions",
            "test_repeated_additions_new_sku",
        ],
        "pass_to_pass": [
            "test_single_adjustment",
            "test_floor_zero",
            "test_original_unchanged",
        ],
    },
    
    "workflow_case": {
        "source_file": "workflow.py",
        "entry_function": "resolve_workflow",
        "fail_to_pass": [
            "test_diamond_workflow",
            "test_shared_dependency_three_branches",
        ],
        "pass_to_pass": [
            "test_linear_workflow",
            "test_independent_tasks",
            "test_cycle_rejected",
            "test_unknown_dependency_rejected",
        ],
    },
}

def run_evaluation(benchmark_name="pricing_case"):
    """Execute and score a selected benchmark."""

    if benchmark_name not in BENCHMARKS:
        raise ValueError(f"Unknown benchmark: {benchmark_name}")
    
    config = BENCHMARKS[benchmark_name]
    REPORTS.mkdir(exist_ok=True)

    xml_path = REPORTS / f"{benchmark_name}.xml"

    if xml_path.exists():
        xml_path.unlink()

    command = [
        sys.executable,
        "-m",
        "pytest",
        f"benchmarks/{benchmark_name}",
        "-q",
        f"--junitxml={xml_path}",
    ]

    result = subprocess.run(
        command,
        cwd=ROOT,
        capture_output=True,
        text=True,
        timeout=30,
    )

    if result.returncode not in (0, 1) or not xml_path.exists():
        raise RuntimeError(
            f"Benchmark execution error:\n{result.stdout}\n{result.stderr}"
        )
    
    tree = ET.parse(xml_path)
    tests = {}

    for case in tree.findall(".//testcase"):
        name = case.get("name")

        if case.find("failure") is not None:
            status = "failed"
        elif case.find("error") is not None:
            status = "error"
        elif case.find("skipped") is not None:
            status = "skipped"
        else:
            status = "passed"

        tests[name] = status

    fail_to_pass = config["fail_to_pass"]
    pass_to_pass = config["pass_to_pass"]

    expected = fail_to_pass + pass_to_pass
    missing = set(expected) - set(tests)

    if missing:
        raise RuntimeError(f"Missing tests: {sorted(missing)}")
    
    summary = {
        "benchmark": benchmark_name,
        "total": len(tests),
        "passed": sum(s == "passed" for s in tests.values()),
        "failed": sum(s == "failed" for s in tests.values()),
        "fail_to_pass": {
            "passed": sum(tests[t] == "passed" for t in fail_to_pass),
            "total": len(fail_to_pass),
        },
        "pass_to_pass": {
            "passed": sum(tests[t] == "passed" for t in pass_to_pass),
            "total": len(pass_to_pass),
        },
        "test_results": tests,
    }

    output_path = REPORTS / f"{benchmark_name}_latest.json"
    output_path.write_text(
        json.dumps(summary, indent=2),
        encoding="utf-8",
    )

    print(json.dumps(summary, indent=2))
    return summary

if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description="AgentForge Benchmark Evaluator"
    )

    parser.add_argument(
        "--benchmark",
        choices=BENCHMARKS.keys(),
        default="pricing_case",
        help="Select the coding benchmark to evaluate",
    )

    args = parser.parse_args()

    run_evaluation(args.benchmark)
    


