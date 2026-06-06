// ================================================================
//  Statistics.tsx — system performance statistics
//  Design: Stitch glassmorphism — CSS donut + custom bar chart
// ================================================================
import { useEffect, useState, type JSX } from "react";
import axios from "axios";
import type { LogEntry, LogStats } from "../types";
import { IoFingerPrintSharp } from "react-icons/io5";
import {
  CircleCheck,
  ChartPie,
  Timer,
  CircleX,
  UserCheck,
  SquareDashedKanban,
} from "lucide-react";
import {
  Chart as ChartJS,
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
} from "chart.js";

import { Doughnut, Bar } from "react-chartjs-2";

ChartJS.register(
  ArcElement,
  Tooltip,
  Legend,
  CategoryScale,
  LinearScale,
  BarElement,
);

const API = "http://localhost:8000";

// ── Metric card ───────────────────────────────────────────────────
interface MetricCardProps {
  icon: JSX.Element;
  label: string;
  value: string | number;
  sub?: string;
  iconColor?: string;
  glowColor?: string;
  borderColor?: string;
}

function MetricCard({
  icon,
  label,
  value,
  sub,
  iconColor,
  borderColor,
}: MetricCardProps): JSX.Element {
  return (
    <div
      className="glass-panel glass-panel-hover rounded-xl p-6 flex flex-col bg-[#0f152480] gap-3 transition-all cursor-default relative select-none overflow-hidden border"
      style={{
        borderColor: borderColor,
      }}
    >
      {/* Background glow */}
      <div className="absolute inset-0 opacity-30 pointer-events-none" />
      <div className="flex items-center gap-3 text-[#a0b4c4] relative z-10">
        <span
          className="material-symbols-outlined text-primary/70 text-[20px]"
          style={{ color: iconColor }}
        >
          {icon}
        </span>
        <h3 className="text-xs uppercase tracking-wider font-semibold">
          {label}
        </h3>
      </div>
      <div className="relative z-10 flex items-baseline gap-2">
        <span
          className="text-4xl font-bold tracking-tight"
          style={{ color: iconColor }}
        >
          {value}
        </span>
        {sub && <span className="text-sm text-[#a0b4c4]">{sub}</span>}
      </div>
    </div>
  );
}

// ── Donut chart ───────────────────────────────────────────────────
function DonutChart({
  total,
  allow,
  deny,
}: {
  total: number;
  allow: number;
  deny: number;
}): JSX.Element {
  const data = {
    labels: ["Allow", "Deny"],
    datasets: [
      {
        data: [allow, deny],
        backgroundColor: ["#34d399", "#ff6b6b"],
        borderWidth: 0,
      },
    ],
  };

  const options = {
    responsive: true,
    cutout: "70%",
    maintainAspectRatio: false,
    plugins: {
      legend: {
        labels: {
          color: "#a0b4c4",
        },
      },
    },
  };

  return (
    <div className="glass-panel rounded-xl p-6">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-bold text-[#e0e8f0]">Distribution</h3>
        <span className="text-[#a0b4c4]">
          <ChartPie size={30} />
        </span>
      </div>

      <div className="relative h-[300px]">
        <Doughnut data={data} options={options} width={300} height={300} />

        <div
          className="absolute left-1/2 transform -translate-x-1/2 -translate-y-1/2 flex flex-col items-center justify-center pointer-events-none"
          style={{ top: "53%" }}
        >
          <span className="text-4xl font-bold text-[#e0e8f0]">{total}</span>
          <span className="text-xl text-[#a0b4c4]">Total</span>
        </div>
      </div>
    </div>
  );
}

// ── Bar chart ─────────────────────────────────────────────────────
function ScoreBarChart({ logs }: { logs: LogEntry[] }): JSX.Element {
  const bins = Array.from({ length: 10 }, (_, i) => {
    const lo = i / 10;
    const hi = (i + 1) / 10;

    const count = logs.filter((l) => {
      const s = l.similarity_score;
      return s !== null && s >= lo && (i === 9 ? s <= hi : s < hi);
    }).length;

    return {
      label: `${lo.toFixed(1)}-${hi.toFixed(1)}`,
      count,
    };
  });

  const data = {
    labels: bins.map((b) => b.label),
    datasets: [
      {
        label: "Events",
        data: bins.map((b) => b.count),
        backgroundColor: bins.map((_, idx) => {
          const v = idx / 10;

          if (v < 0.4) return "#ff6b6b";
          if (v < 0.55) return "#60a5fa";
          return "#34d399";
        }),
        borderRadius: 6,
      },
    ],
  };

  const options = {
    responsive: true,
    maintainAspectRatio: false,

    plugins: {
      legend: {
        labels: {
          color: "#e0e8f0",
        },
      },
    },

    scales: {
      x: {
        ticks: {
          color: "#a0b4c4",
        },
        grid: {
          color: "rgba(255,255,255,0.05)",
        },
      },

      y: {
        beginAtZero: true,

        ticks: {
          color: "#a0b4c4",
        },

        grid: {
          color: "rgba(255,255,255,0.05)",
        },
      },
    },
  };

  return (
    <div className="glass-panel rounded-xl p-6 lg:col-span-2">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-bold text-[#e0e8f0]">
          Score Distribution (0.0 - 1.0)
        </h3>
      </div>

      <div className="h-[320px]">
        <Bar data={data} options={options} />
      </div>
    </div>
  );
}

// ── Main component ────────────────────────────────────────────────
export default function Statistics(): JSX.Element {
  const [stats, setStats] = useState<LogStats | null>(null);
  const [logs, setLogs] = useState<LogEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const fetchAll = async (): Promise<void> => {
      try {
        const [s, l] = await Promise.all([
          axios.get<LogStats>(`${API}/logs/stats`),
          axios.get<LogEntry[]>(`${API}/logs?limit=500`),
        ]);

        setStats(s.data);
        setLogs(l.data);
      } catch (e) {
        console.error(e);
      } finally {
        setLoading(false);
      }
    };
    fetchAll();
  }, []);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-full gap-3 text-[#a0b4c4]">
        <span className="text-3xl animate-spin">refresh</span>
        Loading statistics...
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-[#a0b4c4]">
        <span className="text-4xl">bar_chart_off</span>
        <p className="text-sm">No data available yet.</p>
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* Header */}
      <div>
        <h2 className="text-2xl font-bold text-[#e0e8f0] tracking-tight">
          Statistics
        </h2>
        <p className="text-sm text-[#a0b4c4] mt-1">
          System performance and access analytics
        </p>
      </div>

      {/* Metric cards — 3 columns */}
      <div className="grid grid-cols-2 lg:grid-cols-3 gap-4">
        <MetricCard
          icon={<IoFingerPrintSharp size={20} />}
          label="Total Attempts"
          value={stats.total_attempts}
          iconColor="#7dd3fc"
          borderColor="#7dd3fc14"
        />
        <MetricCard
          icon={<CircleCheck size={20} />}
          label="Granted"
          value={stats.total_allow}
          sub={`${((stats.allow_rate ?? 0) * 100).toFixed(1)}%`}
          iconColor="#34d399"
          borderColor="#34d39926"
        />
        <MetricCard
          icon={<CircleX size={20} />}
          label="Denied"
          value={stats.total_deny}
          iconColor="#ff6b6b"
          borderColor="#ff6b6b26"
          sub={`${(
            (stats.total_attempts > 0
              ? stats.total_deny / stats.total_attempts
              : 0) * 100
          ).toFixed(1)}%`}
        />
        <MetricCard
          icon={<Timer size={20} />}
          label="Avg Latency"
          value={`${stats.avg_latency_ms?.toFixed(2) ?? "—"}`}
          sub="ms"
          iconColor="#7dd3fc"
          borderColor="#7dd3fc14"
        />
        <MetricCard
          icon={<UserCheck size={20} />}
          label="Avg Score (Allow)"
          value={stats.avg_score_allow?.toFixed(4) ?? "—"}
          iconColor="#34d399"
          borderColor="#34d39926"
        />
        <MetricCard
          icon={<SquareDashedKanban size={20} className="scale-y-[-1]" />}
          label="Avg Score"
          iconColor="#7dd3fc"
          borderColor="#7dd3fc14"
          value={
            stats.avg_score_allow != null
              ? (
                  (stats.avg_score_allow + (stats.avg_score_deny ?? 0)) /
                  2
                ).toFixed(3)
              : "—"
          }
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <DonutChart
          total={stats.total_attempts}
          allow={stats.total_allow}
          deny={stats.total_deny}
        />
        <ScoreBarChart logs={logs} />
      </div>
    </div>
  );
}
