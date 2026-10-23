
import os
from pathlib import Path

from dotenv import load_dotenv
from openai import OpenAI

ROOT = Path(__file__).resolve().parents[1]
load_dotenv(ROOT / ".env")

BENCHMARK = ROOT / "benchmarks" / "pricing_case"

files = ["pricing.py", "test_bug.py", "test_regression.py"]

context = "\n\n".join(
    f"--- {filename} ---\n"
    + (BENCHMARK / filename).read_text(encoding="utf-8")
    for filename in files
)

api_key = os.getenv("GROQ_API_KEY")

if not api_key:
    raise RuntimeError("GROQ_API_KEY is missing from .env")

client = OpenAI(
    api_key=api_key,
    base_url="https://api.groq.com/openai/v1",
    timeout=60.0,
    max_retries=1,
)

response = client.chat.completions.create(
    model="openai/gpt-oss-20b",
    messages=[
        {
            "role": "user",
            "content": (
                "You are a Python coding agent. Investigate the " 
                "bug using the provided source code and tests. "
                "Explain the root cause briefly and propose a "
                "complete corrected pricing.py file. "
                "Do not change the tests. "
                "Do not claim you executed any code.\n\n"
                + context
            ),
        }
    ],
    max_completion_tokens=1800,
    reasoning_effort="low",
)

proposal = response.choices[0].message.content or ""

if not proposal:
    raise RuntimeError("The model returned no proposal.")

REPORTS = ROOT / "reports"
REPORTS.mkdir(exist_ok=True)

(REPORTS / "first_agent_proposal.txt").write_text(
    proposal, encoding="utf-8"
)

print(proposal)
print("\nProposal saved to reports/first_agent_proposal.txt")