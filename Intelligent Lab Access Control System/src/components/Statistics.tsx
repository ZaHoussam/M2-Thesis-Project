// ================================================================
//  Statistics.tsx — charts and summary metrics
// ================================================================
import { useEffect, useState } from "react";
import axios from "axios";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  PieChart,
  Pie,
  Cell,
  Legend,
} from "recharts";
import type { LogEntry, LogStats, ScoreBin } from "../types";

const API = "http://localhost:8000";
const COLORS = ["#1D9E75", "#E24B4A"];

interface StatCardProps {
  value: string | number;
  label: string;
  color?: "green" | "red" | "default";
}

function StatCard({
  value,
  label,
  color = "default",
}: StatCardProps): JSX.Element {
  return (
    <div className={`stat-card ${color !== "default" ? color : ""}`}>
      <div className="stat-val">{value}</div>
      <div className="stat-label">{label}</div>
    </div>
  );
}

export default function Statistics(): JSX.Element {
  const [stats, setStats] = useState<LogStats | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchAll = async (): Promise<void> => {
      try {
        const [s, l] = await Promise.all([
          axios.get<LogStats>(`${API}/logs/stats`),
          axios.get<LogEntry[]>(`${API}/logs?limit=200`),
        ]);
        setStats(s.data);
        setLogs(l.data);
      } catch (e) {
        console.error("Failed to fetch statistics:", e);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  if (loading) return <div className="loading">Loading statistics...</div>;
  if (!stats) return <div className="empty">No data available.</div>;

  const pieData = [
    { name: "ALLOW", value: stats.total_allow },
    { name: "DENY", value: stats.total_deny },
  ];

  // Build score distribution bins
  const binMap: Record<string, number> = {};
  logs.forEach((l: LogEntry) => {
    if (l.similarity_score === null) return;
    const bin = (Math.floor(l.similarity_score * 10) / 10).toFixed(1);
    binMap[bin] = (binMap[bin] ?? 0) + 1;
  });

  const scoreData: ScoreBin[] = Object.entries(binMap)
    .sort((a, b) => parseFloat(a[0]) - parseFloat(b[0]))
    .map(([range, count]) => ({ range, count }));

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>System Statistics</h2>
      </div>

      <div className="stats-grid">
        <StatCard value={stats.total_attempts} label="Total Attempts" />
        <StatCard value={stats.total_allow} label="Allowed" color="green" />
        <StatCard value={stats.total_deny} label="Denied" color="red" />
        <StatCard
          value={`${(stats.allow_rate * 100).toFixed(1)}%`}
          label="Allow Rate"
        />
        <StatCard
          value={stats.avg_latency_ms?.toFixed(2) ?? "—"}
          label="Avg Latency (ms)"
        />
        <StatCard
          value={stats.avg_score_allow?.toFixed(4) ?? "—"}
          label="Avg Score (ALLOW)"
        />
      </div>

      <div className="charts-row">
        <div className="chart-box">
          <h3>ALLOW vs DENY</h3>
          <PieChart width={220} height={220}>
            <Pie
              data={pieData}
              cx={110}
              cy={100}
              outerRadius={80}
              dataKey="value"
              label
            >
              {pieData.map((_entry, i) => (
                <Cell key={`cell-${i}`} fill={COLORS[i % COLORS.length]} />
              ))}
            </Pie>
            <Legend />
          </PieChart>
        </div>

        <div className="chart-box" style={{ flex: 2 }}>
          <h3>Score Distribution</h3>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={scoreData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#333" />
              <XAxis dataKey="range" tick={{ fontSize: 11 }} />
              <YAxis tick={{ fontSize: 11 }} />
              <Tooltip />
              <Bar dataKey="count" fill="#1D9E75" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      </div>
    </div>
  );
}
