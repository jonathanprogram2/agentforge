# AgentForge — Demo Walkthrough

**Suggested demo length:** approximately 2–3 minutes. Record your actual running project; don't substitute mock outputs for experiments.

## Preparation

1. Make sure Docker Desktop is running and the images are built:
   ```powershell
   docker build -f Dockerfile.agent -t agentforge-sandbox:public-v5 .
   docker build -f Dockerfile.sandbox -t agentforge-sandbox:v4 .
   ```
2. Check that `.env` contains a working Groq API key if you plan to run a *new* model experiment. Never show the key on camera.
3. If you already have real saved experiment history, regenerate the comparison with `python -m app.compare`.
4. Start the backend in the root folder: `python -m uvicorn app.main:app --reload`.
5. In another terminal: `cd frontend; npm ci; npm run dev`. Open `http://localhost:5173`.
6. Confirm the dashboard has a comparison report. On fresh clones without local runs, `/api/comparison` returns 404 and the dashboard shows an error until `python -m app.compare` creates a report.

## Recording outline

| Segment | Show | Suggested narration |
|---|---|---|
| **0:00–0:20** | Dashboard overview | “AgentForge is my local platform for running and inspecting AI coding-agent evaluations. It combines a Python agent, containerized tests, and a React analytics dashboard.” |
| **0:20–0:45** | Benchmarks and model comparison | “It includes four synthetic Python bug-fixing challenges and compares GPT-OSS 20B and 120B. These results are observations from saved runs, not a generalized model leaderboard.” |
| **0:45–1:15** | Experiment Explorer tool trajectory | “Agents can read task files, submit a patch, and run tests. Every step is logged, so I can see how a model arrived at a result and where a tool failed.” |
| **1:15–1:40** | Token/latency chart and reliability panel | “I track token usage and elapsed time. Repeated-trial statistics are presented with small-sample caveats.” |
| **1:40–2:00** | Held-out cards | “Saved inventory repairs can be checked against four additional cases withheld from the agent's file-reading tool, though they aren't secret from the public repository.” |
| **2:00–2:20** | GitHub Actions green checks | “GitHub Actions verifies Python tests, frontend lint/build, and the Docker image, plus checks that the agent image excludes the held-out directory.” |
| **2:20–2:40** | Architecture diagram in README | “The goal is a transparent evaluation framework that I can extend with harder tasks, better isolation, and more rigorous benchmarking.” |

## Optional terminal segment

Only if you want to show a **live** agent call and have API quota available:

```powershell
python -m app.multi_agent --benchmark workflow_case --model openai/gpt-oss-20b
python -m app.compare
```

This can encounter rate limits, cost tokens, and produce varying results. Prefer using genuine saved history for a short, reliable portfolio demo. Don't edit or conceal failures; they are a meaningful part of agent evaluation.

## Screenshots to add to README

Capture real screenshots from your local dashboard:

- Whole-dashboard overview with comparison table visible
- One experiment trajectory with `read_file`, `submit_patch`, `run_tests`
- Token/latency chart and reliability analysis
- Held-out inventory results, clearly labeled
- GitHub Actions green checks

Before committing screenshots, inspect for usernames, API keys, private directory paths, or anything you don't want public. Add screenshots under `docs/assets/` and reference the **actual filenames** from the README once uploaded.

## Interview explanation (30 seconds)

> “I built AgentForge, a local AI coding-agent evaluation prototype in Python, FastAPI, Docker, and React. Two GPT-OSS models use structured tools to inspect a buggy benchmark, submit a replacement, and run containerized Pytest checks. I record each execution trace and score the repairs, then compare token usage, latency, and repeated-trial outcomes in a dashboard. I also implemented additional inventory evaluation cases and GitHub Actions checks. The benchmarks are intentionally small, so I present the results as a demonstration of evaluation engineering rather than claims about general model reliability.”
