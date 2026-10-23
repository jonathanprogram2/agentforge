
import ast
import json
import os
import subprocess
import tempfile
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
BENCHMARK = ROOT / "benchmarks" / "pricing_case"
REPORTS = ROOT / "reports"
MODEL = "openai/gpt-oss-20b"

load_dotenv(ROOT / ".env")

PATCH_SCHEMA = {
    "type": "json_schema",
    "json_schema": {
        "name": "coding_patch",
        "strict": True,
        "schema": {
            "type": "object",
            "properties": {
                "explanation": {"type": "string"},
                "code": {"type": "string"},
            },
            "required": ["explanation", "code"],
            "additionalProperties": False,
        },
    },
}


def generate_patch():
    """LLM to propose a complete replacement file"""

    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError("GROQ_API_KEY is missing.")
    
    client = OpenAI(
        api_key=api_key,
        base_url="https://api.groq.com/openai/v1",
        timeout=60.0,
        max_retries=1,
    )

    files = ["pricing.py", "test_bug.py", "test_regression.py" ]
    context = "\n\n".join(
        f"--- {name} ---\n"
        + (BENCHMARK / name).read_text(encoding="utf-8")
        for name in files
    )

    response = client.chat.completions.create(
        model=MODEL,
        messages=[
            {
                "role": "system",
                "content": (
                    "You are a Python coding agent. Fix the bug "
                    "without changing the function interface. "
                    "Return JSON with a brief explanation and "
                    "the complete corrected pricing.py source code. "
                    "The code must contain only the "
                    "discounted_price function and optional docstrings. "
                    "Do not include Markdown fences. "
                    "Do not change the tests."
                ),
            },
            {"role": "user", "content": context},
        ],
        response_format=PATCH_SCHEMA,
        reasoning_effort="low",
        max_completion_tokens=1800,
    )

    content = response.choices[0].message.content
    if not content:
        raise RuntimeError("Model returned no patch.")
    
    return json.loads(content)

def validate_patch(code):
    if not isinstance(code, str) or len(code) > 6000:
        raise ValueError("Invalid patch content or size.")
    
    tree = ast.parse(code)

    functions = [
        node for node in tree.body
        if isinstance(node, ast.FunctionDef)
        and node.name == "discounted_price"
    ]

    if len(functions) != 1:
        raise ValueError("Expected one discounted_price function.")
    
    for node in tree.body:
        if isinstance(node, ast.FunctionDef):
            if node.name == "discounted_price":
                continue
            
        if isinstance(node, ast.Expr):
            if isinstance(node.value, ast.Constant):
                if isinstance(node.value.value, str):
                    continue

        raise ValueError("Unexpected top-level statement.")
    
def evaluate_patch(code):
    """Test the proposed patch inside our Docker sandbox."""

    REPORTS.mkdir(exist_ok=True)

    with tempfile.TemporaryDirectory(
        prefix="candidate_", dir=REPORTS
    ) as temp_dir:
        
        candidate = Path(temp_dir) / "pricing.py"
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
                "target=/workspace/benchmarks/pricing_case/pricing.py,"
                "readonly"
            ),
            "agentforge-sandbox:v1",
        ]
        
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=90,
        )

    if result.returncode != 0:
        raise RuntimeError(
            f"Docker evaluation failed:\n{result.stderr}\n"
            f"{result.stdout}"
        )
    
    return json.loads(result.stdout)

def main():
    print("AgentForge: generating an AI patch...")

    proposal = generate_patch()
    code = proposal["code"]

    validate_patch(code)

    print("\nPatch generated. Running Docker evaluation...")
    metrics = evaluate_patch(code)

    fixed = metrics["fail_to_pass"]["passed"] == 2
    preserved = metrics["pass_to_pass"]["passed"] == 2

    success = fixed and preserved and metrics["failed"] == 0

    report = {
        "model": MODEL,
        "benchmark": "pricing_case",
        "explanation": proposal["explanation"],
        "success": success,
        "evaluation": metrics,
    }

    REPORTS.mkdir(exist_ok=True)

    (REPORTS / "auto_fix_candidate.py").write_text(
        code, encoding="utf-8"
    )
    (REPORTS / "auto_fix_latest.py").write_text(
        json.dumps(report, indent=2),
        encoding="utf-8",
    )

    print("\n=== AgentForge Evaluation ===")
    print(json.dumps(report, indent=2))

    print(
        "\nRESULT:",
        "SUCCESS - ALL TESTS PASSED" if success
        else "PATCH DID NOT PASS ALL TESTS"
    )

if __name__ == "__main__":
    main()
