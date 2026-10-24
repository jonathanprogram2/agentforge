import { useEffect, useMemo, useState } from "react";

type ToolEvent = {
  round?: number;
  step?: number;
  tool: string;
  filename?: string;
  result?: {
    error?: string;
    success?: boolean;
    accepted?: boolean;
    read?: boolean;
  };
};

type Experiment = {
  run_id: string;
  benchmark: string;
  model: string;
  success: boolean;
  tokens_used?: number;
  duration_seconds?: number;
  evaluations_used?: number;
  trajectory?: ToolEvent[];
};

const API_URL = "http://127.0.0.1:8000";

function formatModel(model: string) {
  const prefix = "openai/gpt-oss-";

  if (model.startsWith(prefix)) {
    return `GPT-OSS ${model.slice(prefix.length).toUpperCase()}`;
  }

  return model;
}

function describeEvent(event: ToolEvent) {
  if (event.result?.error) {
    return `Error: ${event.result.error}`;
  }

  if (event.tool === "read_file") {
    return event.filename
      ? `Inspected ${event.filename}`
      : "Inspected a benchmark file";
  }

  if (event.tool === "submit_patch") {
    return "Submitted a candidate patch";
  }

  if (event.tool === "run_tests") {
    if (event.result?.success === true) {
      return "Docker evaluation passed";
    }

    if (event.result?.success === false) {
      return "Docker evaluation did not pass";
    }

    return "Requested Docker evaluation";
  }

  return "Tool executed";
}

export default function ExperimentExplorer() {
  const [experiments, setExperiments] = useState<Experiment[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState("");

  const [benchmarkFilter, setBenchmarkFilter] = useState("all");
  const [modelFilter, setModelFilter] = useState("all");
  const [selectedRunId, setSelectedRunId] = useState<string | null>(null);

  useEffect(() => {
    const controller = new AbortController();

    async function loadExperiments() {
      try {
        const response = await fetch(`${API_URL}/api/experiments?limit=100`, {
          signal: controller.signal,
        });

        if (!response.ok) {
          throw new Error("Could not load experiment history.");
        }

        const data: unknown = await response.json();

        if (!Array.isArray(data)) {
          throw new Error("Unexpected experiment data.");
        }

        const validRuns = data.filter(
          (item): item is Experiment =>
            item !== null &&
            typeof item === "object" &&
            typeof item.run_id === "string" &&
            typeof item.benchmark === "string" &&
            typeof item.model === "string" &&
            typeof item.success === "boolean",
        );

        if (!controller.signal.aborted) {
          setExperiments(validRuns);
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

    loadExperiments();
    return () => controller.abort();
  }, []);

  const benchmarks = Array.from(
    new Set(experiments.map((run) => run.benchmark)),
  ).sort();

  const models = Array.from(
    new Set(experiments.map((run) => run.model)),
  ).sort();

  const filteredRuns = useMemo(() => {
    return experiments
      .filter(
        (run) =>
          (benchmarkFilter === "all" || run.benchmark === benchmarkFilter) &&
          (modelFilter === "all" || run.model === modelFilter),
      )
      .sort((a, b) => b.run_id.localeCompare(a.run_id));
  }, [experiments, benchmarkFilter, modelFilter]);

  const selectedRun =
    filteredRuns.find((run) => run.run_id === selectedRunId) ?? filteredRuns[0];

  const events = Array.isArray(selectedRun?.trajectory)
    ? selectedRun.trajectory
    : [];

  return (
    <section className="panel explorer">
      <h2>Experiment Explorer</h2>
      <p>Explore recorded AI agent runs and inspect tool execution.</p>

      {loading && <p role="status">Loading experiments...</p>}
      {error && <p role="alert">{error}</p>}

      {!loading && !error && (
        <>
          <div className="explorer-filters">
            <label>
              Benchmark
              <select
                value={benchmarkFilter}
                onChange={(e) => setBenchmarkFilter(e.target.value)}
              >
                <option value="all">All benchmarks</option>
                {benchmarks.map((benchmark) => (
                  <option key={benchmark} value={benchmark}>
                    {benchmark}
                  </option>
                ))}
              </select>
            </label>

            <label>
              Model
              <select
                value={modelFilter}
                onChange={(e) => setModelFilter(e.target.value)}
              >
                <option value="all">All models</option>
                {models.map((model) => (
                  <option key={model} value={model}>
                    {formatModel(model)}
                  </option>
                ))}
              </select>
            </label>
          </div>

          <p className="run-count">
            Showing {filteredRuns.length} experiment runs
          </p>

          <div className="explorer-layout">
            <div className="run-list" aria-label="Experiment runs">
              {filteredRuns.map((run) => (
                <button
                  key={run.run_id}
                  type="button"
                  className={`run-choice ${
                    selectedRun?.run_id === run.run_id ? "selected" : ""
                  }`}
                  aria-pressed={selectedRun?.run_id === run.run_id}
                  onClick={() => setSelectedRunId(run.run_id)}
                >
                  <span className="run-choice-heading">
                    <strong>{formatModel(run.model)}</strong>
                    <span className={run.success ? "passed" : "failed"}>
                      {run.success ? "Passed" : "Failed"}
                    </span>
                  </span>

                  <small>
                    {run.benchmark} · {run.tokens_used?.toLocaleString() ?? "—"}{" "}
                    tokens
                  </small>
                </button>
              ))}
            </div>

            <div className="run-detail">
              {selectedRun ? (
                <>
                  <h3>Selected experiment</h3>

                  <div className="detail-metrics">
                    <div>
                      <span>Model</span>
                      <strong>{formatModel(selectedRun.model)}</strong>
                    </div>
                    <div>
                      <span>Execution time</span>
                      <strong>
                        {selectedRun.duration_seconds != null
                          ? `${selectedRun.duration_seconds.toFixed(2)}s`
                          : "—"}
                      </strong>
                    </div>
                    <div>
                      <span>Evaluations</span>
                      <strong>{selectedRun.evaluations_used ?? "—"}</strong>
                    </div>
                  </div>

                  <h3>Agent tool trajectory</h3>

                  {events.length === 0 ? (
                    <p>No tool trajectory recorded for this run.</p>
                  ) : (
                    <ol className="agent-timeline">
                      {events.map((event, index) => (
                        <li key={`${selectedRun.run_id}-${index}`}>
                          <span className="timeline-step">
                            Step {event.round ?? event.step ?? index + 1}
                          </span>

                          <strong>{event.tool}</strong>

                          <p
                            className={event.result?.error ? "event-error" : ""}
                          >
                            {describeEvent(event)}
                          </p>
                        </li>
                      ))}
                    </ol>
                  )}

                  <p className="run-id">Run ID: {selectedRun.run_id}</p>
                </>
              ) : (
                <p>No experiments match the selected filters.</p>
              )}
            </div>
          </div>
        </>
      )}
    </section>
  );
}
