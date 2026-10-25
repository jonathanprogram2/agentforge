import { useEffect, useState } from "react";

type HeldoutResult = {
  run_id: string;
  benchmark: string;
  model: string;
  public_success: boolean;
  heldout_success: boolean;
  passed: number;
  total: number;
  failed: number;
};

export default function HeldoutResults() {
  const [results, setResults] = useState<HeldoutResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function loadResults() {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/heldout", {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error("Unable to load held-out results.");
        }

        const data = await response.json();

        if (!Array.isArray(data)) {
          throw new Error("Unexpected API response.");
        }

        if (!controller.signal.aborted) {
          setResults(data);
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

    loadResults();
    return () => controller.abort();
  }, []);

  return (
    <section className="panel heldout-panel">
      <h2>Held-Out Evaluation</h2>
      <p>
        Validate AI-generated repairs against additional test cases not exposed
        through the agent tools.
      </p>

      {loading && <p role="status">Loading results...</p>}
      {error && <p role="alert">{error}</p>}

      {!loading && !error && results.length === 0 && (
        <p>No held-out evaluations recorded yet.</p>
      )}

      {!loading && !error && (
        <div className="heldout-grid">
          {results.map((result) => (
            <article className="heldout-card" key={result.run_id}>
              <h3>
                {result.model
                  .replace("openai/gpt-oss-", "GPT-OSS ")
                  .toUpperCase()}
              </h3>

              <p>{result.benchmark}</p>

              <strong className={result.heldout_success ? "passed" : "failed"}>
                {result.passed}/{result.total} passed
              </strong>

              <div className="heldout-status">
                Public tests:
                <span className={result.public_success ? "passed" : "failed"}>
                  {result.public_success ? " Passed" : " Failed"}
                </span>
              </div>

              <div className="heldout-status">
                Held-out tests:
                <span className={result.heldout_success ? "passed" : "failed"}>
                  {result.heldout_success ? " Passed" : " Failed"}
                </span>
              </div>
            </article>
          ))}
        </div>
      )}
    </section>
  );
}
