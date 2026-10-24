import { useEffect, useState } from "react";

type ReliabilityResult = {
  benchmark: string;
  model: string;
  trials: number;
  successful_trials: number;
  success_rate_percent: number;
  average_tokens: number;
  average_duration_seconds: number;
  duration_stddev_seconds: number | null;
  tool_errors: number;
};

export default function ModelReliability() {
  const [results, setResults] = useState<ReliabilityResult[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  useEffect(() => {
    const controller = new AbortController();

    async function fetchReliability() {
      try {
        const response = await fetch("http://127.0.0.1:8000/api/reliability", {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error("Failed to load reliability results.");
        }

        const data: unknown = await response.json();

        if (!Array.isArray(data)) {
          throw new Error("Invalid reliability data.");
        }

        if (!controller.signal.aborted) {
          setResults(data as ReliabilityResult[]);
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

    fetchReliability();

    return () => controller.abort();
  }, []);

  return (
    <section className="panel reliability-panel">
      <h2>Model Reliability Analysis</h2>
      <p>
        Evaluate repeatability, token efficiency, and execution variability
        across AI agent experiments.
      </p>

      {loading && <p role="status">Loading reliability data...</p>}
      {error && <p role="alert">{error}</p>}

      {!loading && !error && results.length === 0 && (
        <p>No reliability reports available yet.</p>
      )}

      {!loading && !error && results.length > 0 && (
        <div className="reliability-grid">
          {results.map((result) => (
            <article
              key={`${result.benchmark}-${result.model}`}
              className="reliability-card"
            >
              <div className="reliability-heading">
                <div>
                  <h3>
                    {result.model
                      .replace("openai/gpt-oss-", "GPT-OSS ")
                      .toUpperCase()
                      .replace("GPT-OSS", "GPT-OSS")}
                  </h3>
                  <span>{result.benchmark}</span>
                </div>
                <span className="reliability-success">
                  {result.success_rate_percent}% observed
                </span>
              </div>

              <div className="reliability-metrics">
                <div>
                  <span>Successful trials</span>
                  <strong>
                    {result.successful_trials}/{result.trials}
                  </strong>
                </div>

                <div>
                  <span>Avg. tokens</span>
                  <strong>{result.average_tokens.toLocaleString()}</strong>
                </div>

                <div>
                  <span>Avg. latency</span>
                  <strong>{result.average_duration_seconds.toFixed(3)}s</strong>
                </div>

                <div>
                  <span>Latency std. dev.</span>
                  <strong>
                    {result.duration_stddev_seconds === null
                      ? "—"
                      : `${result.duration_stddev_seconds.toFixed(3)}s`}
                  </strong>
                </div>
              </div>

              <p className="reliability-footer">
                {result.tool_errors} tool errors recorded
              </p>
            </article>
          ))}
        </div>
      )}

      <p className="reliability-note">
        Statistics reflect the latest saved reliability analysis for each
        benchmark. Small samples should not be interpreted as proven model
        reliability.
      </p>
    </section>
  );
}
