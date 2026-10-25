

import ast
import json
import subprocess
import tempfile
from pathlib import Path

from app.evaluator import BENCHMARKS

IMAGE = "agentforge-sandbox:public-v5"

def validate_patch(benchmark_name: str, code: str):
    """Validate the candidate's basic structure."""
    
    if not isinstance(code, str) or not 0 < len(code) <= 6000:
        raise ValueError("Invalid patch size or content.") 
    
    expected_function = BENCHMARKS[benchmark_name]["entry_function"]

    try:
        tree = ast.parse(code)
    except SyntaxError as exc:
        raise ValueError(f"Invalid Python syntax: {exc}") from exc
    
    statements = list(tree.body)

    # Allow one optional module-level docstring
    if (
        statements
        and isinstance(statements[0], ast.Expr)
        and isinstance(statements[0].value, ast.Constant)
        and isinstance(statements[0].value.value, str)
    ):
        statements.pop(0)

    if (
        len(statements) != 1
        or not isinstance(statements[0], ast.FunctionDef)
        or statements[0].name != expected_function
        or statements[0].decorator_list
    ):
        raise ValueError(
            f"Patch must define only {expected_function}."
        )
    
    
    # Defense-in-depth only, not a Python security sandbox.
    forbidden_calls = {
        "eval",
        "exec",
        "compile",
        "open",
        "__import__",
        "globals",
        "locals",
        "vars",
        "getattr",
        "setattr",
        "delattr",
        "breakpoint",
    }

    for node in ast.walk(statements[0]):
        if isinstance(
            node,
            (ast.Import, ast.ImportFrom, ast.Global, ast.Nonlocal),
        ):
            raise ValueError(
                "Imports and global scope modifications are not allowed."
            )

        if (
            isinstance(node, ast.Call)
            and isinstance(node.func, ast.Name)
            and node.func.id in forbidden_calls
        ):
            raise ValueError(
                f"Restricted operation: {node.func.id}"
            )

        if (
            isinstance(node, ast.Attribute)
            and node.attr.startswith("__")
        ):
            raise ValueError(
                "Dunder attribute access is not allowed."
            )

    
def evaluate_patch(benchmark_name: str, code: str):
    """Run a candidate patch inside the Docker benchmark image."""

    validate_patch(benchmark_name, code)

    filename = BENCHMARKS[benchmark_name]["source_file"]

    with tempfile.TemporaryDirectory(
        prefix="agentforge_"
    ) as temp_dir:
        
        candidate = Path(temp_dir) / filename
        candidate.write_text(code, encoding="utf-8")

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
                f"type=bind,source={candidate.resolve()},"
                f"target=/workspace/benchmarks/"
                f"{benchmark_name}/{filename},readonly"
            ),
            IMAGE,
            "python", "-m", "app.evaluator",
            "--benchmark", benchmark_name,
        ]

        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=90,
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"Docker execution failed:\n"
            f"{result.stderr[-2000:]}\n{result.stdout[-2000:]}"
        )
    
    try:
        return json.loads(result.stdout)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "Docker returned an invalid evaluation report."
        ) from exc