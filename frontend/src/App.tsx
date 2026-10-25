import { useEffect, useState } from "react";
import "./App.css";
import ExperimentExplorer from "./ExperimentExplorer";
import ModelAnalytics from "./ModelAnalytics";
import ModelReliability from "./ModelReliability";
import HeldoutResults from "./HeldoutResults";

const API_URL = "http://127.0.0.1:8000";

type Benchmark = {
  name: string;
  source_file: string;
  entry_function: string;
  fail_to_pass_tests: number;
  pass_to_pass_tests: number;
};

type Comparison = {
  run_id: string;
  benchmark: string;
  model_label: string;
  success: boolean;
  tokens_used: number;
  duration_seconds: number;
  tool_errors: number;
};

function App() {
  const [benchmarks, setBenchmarks] = useState<Benchmark[]>([]);
  const [comparisons, setComparisons] = useState<Comparison[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadDashboard() {
      try {
        const [benchmarkResponse, comparisonResponse] = await Promise.all([
          fetch(`${API_URL}/api/benchmarks`, {
            signal: controller.signal,
          }),
          fetch(`${API_URL}/api/comparison`, {
            signal: controller.signal,
          }),
        ]);

        if (!benchmarkResponse.ok || !comparisonResponse.ok) {
          throw new Error("Failed to load evaluation data.");
        }

        const benchmarkData: Benchmark[] = await benchmarkResponse.json();

        const comparisonData: Comparison[] = await comparisonResponse.json();

        if (!controller.signal.aborted) {
          setBenchmarks(benchmarkData);
          setComparisons(comparisonData);
        }
      } catch (err) {
        if (!controller.signal.aborted) {
          setError(err instanceof Error ? err.message : "Unknown error");
        }
      } finally {
        if (!controller.signal.aborted) {
          setLoading(false);
        }
      }
    }

    loadDashboard();

    return () => controller.abort();
  }, []);

  const successfulRuns = comparisons.filter((run) => run.success).length;

  const totalTokens = comparisons.reduce(
    (total, run) => total + run.tokens_used,
    0,
  );

  return (
    <main className="dashboard">
      <header className="hero">
        <p className="eyebrow">AI AGENT EVALUATION PLATFORM</p>
        <h1>AgentForge</h1>
        <p>
          Benchmark AI coding agents, inspect results, and compare model
          performance.
        </p>
      </header>

      {loading && <p role="status">Loading evaluation data...</p>}

      {error && <p role="alert">Error: {error}</p>}

      {!loading && !error && (
        <>
          <section className="stats" aria-label="Evaluation summary">
            <article className="stat-card">
              <span>Benchmarks</span>
              <strong>{benchmarks.length}</strong>
            </article>

            <article className="stat-card">
              <span>Recorded comparisons</span>
              <strong>{comparisons.length}</strong>
            </article>

            <article className="stat-card">
              <span>Successful runs</span>
              <strong>
                {successfulRuns}/{comparisons.length}
              </strong>
            </article>

            <article className="stat-card">
              <span>Tokens consumed</span>
              <strong>{totalTokens.toLocaleString()}</strong>
            </article>
          </section>

          <section className="panel">
            <h2>Model comparison</h2>
            <p>Latest recorded run for each model and benchmark.</p>

            <div className="table-wrap">
              <table>
                <thead>
                  <tr>
                    <th>Benchmark</th>
                    <th>Model</th>
                    <th>Status</th>
                    <th>Tokens</th>
                    <th>Time</th>
                  </tr>
                </thead>
                <tbody>
                  {comparisons.map((run) => (
                    <tr key={run.run_id}>
                      <td>{run.benchmark}</td>
                      <td>{run.model_label}</td>
                      <td>
                        <span className={run.success ? "passed" : "failed"}>
                          {run.success ? "Passed" : "Failed"}
                        </span>
                      </td>
                      <td>{run.tokens_used.toLocaleString()}</td>
                      <td>{run.duration_seconds.toFixed(2)}s</td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </section>
          <ModelAnalytics comparisons={comparisons} />
          <ModelReliability />
          <HeldoutResults />
          <ExperimentExplorer />
        </>
      )}
    </main>
  );
}

export default App;
