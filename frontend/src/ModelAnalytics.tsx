import { useMemo, useState } from "react";

import {
  Bar,
  BarChart,
  CartesianGrid,
  Legend,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

type ComparisonRun = {
  benchmark: string;
  model_label: string;
  tokens_used: number;
  duration_seconds: number;
};

type Props = {
  comparisons: ComparisonRun[];
};

type Metric = "tokens" | "latency";

const COLORS = ["#60a5fa", "#34d399", "#f59e0b", "#c084fc"];

function formatBenchmark(name: string) {
  return name
    .replace(/_case$/, "")
    .replace(/_/g, " ")
    .replace(/\b\w/g, (letter) => letter.toUpperCase());
}

export default function ModelAnalytics({ comparisons }: Props) {
  const [metric, setMetric] = useState<Metric>("tokens");

  const models = useMemo(
    () => Array.from(new Set(comparisons.map((run) => run.model_label))).sort(),
    [comparisons],
  );

  const chartData = useMemo(() => {
    const benchmarks = Array.from(
      new Set(comparisons.map((run) => run.benchmark)),
    ).sort();

    return benchmarks.map((benchmark) => {
      const point: Record<string, string | number | null> = {
        benchmark: formatBenchmark(benchmark),
      };

      for (const model of models) {
        const run = comparisons.find(
          (item) => item.benchmark === benchmark && item.model_label === model,
        );

        point[model] = run
          ? metric === "tokens"
            ? run.tokens_used
            : run.duration_seconds
          : null;
      }

      return point;
    });
  }, [comparisons, metric, models]);

  return (
    <section className="panel analytics-panel">
      <div className="analytics-header">
        <div>
          <h2>Model Performance Analytics</h2>
          <p>Compare model efficiency across coding benchmarks.</p>
        </div>

        <div
          className="metric-toggle"
          role="group"
          aria-label="Choose performance metric"
        >
          <button
            type="button"
            aria-pressed={metric === "tokens"}
            className={metric === "tokens" ? "active" : ""}
            onClick={() => setMetric("tokens")}
          >
            Tokens
          </button>

          <button
            type="button"
            aria-pressed={metric === "latency"}
            className={metric === "latency" ? "active" : ""}
            onClick={() => setMetric("latency")}
          >
            Latency
          </button>
        </div>
      </div>

      <h3>
        {metric === "tokens"
          ? "Token consumption by benchmark"
          : "Execution time by benchmark"}
      </h3>

      {chartData.length === 0 ? (
        <p>No model comparison data available.</p>
      ) : (
        <div className="analytics-chart">
          <ResponsiveContainer width="100%" height="100%">
            <BarChart
              data={chartData}
              margin={{
                top: 16,
                right: 12,
                left: 0,
                bottom: 8,
              }}
            >
              <CartesianGrid
                stroke="#26354c"
                strokeDasharray="3 3"
                vertical={false}
              />

              <XAxis
                dataKey="benchmark"
                stroke="#94a3b8"
                tickLine={false}
                axisLine={false}
              />

              <YAxis
                stroke="#94a3b8"
                tickLine={false}
                axisLine={false}
                width={55}
                tickFormatter={(value: number) =>
                  metric === "tokens" ? value.toLocaleString() : `${value}s`
                }
              />

              <Tooltip
                contentStyle={{
                  background: "#111b2d",
                  border: "1px solid #334155",
                  borderRadius: "10px",
                  color: "#e8eef8",
                }}
                labelStyle={{ color: "#e8eef8" }}
                formatter={(value) =>
                  metric === "tokens"
                    ? `${Number(value).toLocaleString()} tokens`
                    : `${Number(value).toFixed(2)} seconds`
                }
              />

              <Legend verticalAlign="top" height={40} />

              {models.map((model, index) => (
                <Bar
                  key={model}
                  dataKey={model}
                  fill={COLORS[index % COLORS.length]}
                  maxBarSize={44}
                  radius={[6, 6, 0, 0]}
                />
              ))}
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      <p className="analytics-note">
        Showing the latest recorded run per model and benchmark. These are
        individual measurements, not statistical averages.
      </p>
    </section>
  );
}
