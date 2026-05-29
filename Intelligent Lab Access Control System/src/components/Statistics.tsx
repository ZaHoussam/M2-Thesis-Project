// ================================================================
//  Statistics.tsx — system performance statistics
//  Design: Stitch glassmorphism — CSS donut + custom bar chart
// ================================================================
import { useEffect, useState, type JSX } from "react";
import axios from "axios";
import type { LogEntry, LogStats } from "../types";
import { FaRegCheckCircle } from "react-icons/fa";
import { TbCancel } from "react-icons/tb";
import { MdOutlineTimer, MdDonutLarge } from "react-icons/md";
import { BsPersonFillCheck } from "react-icons/bs";
import { IoAnalyticsSharp, IoFingerPrintSharp } from "react-icons/io5";

const API = "http://localhost:8000";

// ── Metric card ───────────────────────────────────────────────────
interface MetricCardProps {
  icon: JSX.Element;
  label: string;
  value: string | number;
  sub?: string;
  glowColor?: string;
}

function MetricCard({
  icon,
  label,
  value,
  sub,
  glowColor = "rgba(125,211,252,0.1)",
}: MetricCardProps): JSX.Element {
  return (
    <div className="glass-panel glass-panel-hover rounded-xl p-6 flex flex-col gap-3 transition-all cursor-default relative overflow-hidden">
      {/* Background glow */}
      <div
        className="absolute inset-0 opacity-30 pointer-events-none"
        style={{
          background: `radial-gradient(circle at 0% 100%, ${glowColor} 0%, transparent 60%)`,
        }}
      />
      <div className="flex items-center gap-3 text-[#a0b4c4] relative z-10">
        <span className="material-symbols-outlined text-primary/70 text-[20px]">
          {icon}
        </span>
        <h3 className="text-xs uppercase tracking-wider font-semibold">
          {label}
        </h3>
      </div>
      <div className="relative z-10 flex items-baseline gap-2">
        <span className="text-3xl font-bold text-[#e0e8f0] tracking-tight">
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
  allowRate,
}: {
  total: number;
  allow: number;
  deny: number;
  allowRate: number;
}): JSX.Element {
  const allowPct = Math.round(allowRate * 100);
  const denyPct = 100 - allowPct;

  return (
    <div className="glass-panel rounded-xl p-6 flex flex-col">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-bold text-[#e0e8f0]">Distribution</h3>
        <span className="material-symbols-outlined text-[#a0b4c4]">
          {<MdDonutLarge size={30} />}
        </span>
      </div>

      <div className="flex-1 flex flex-col items-center justify-center relative min-h-[250px]">
        {/* CSS donut */}
        <div
          className="w-48 h-48 rounded-full relative flex items-center justify-center"
          style={{
            background: `conic-gradient(
              from 0deg,
              #34d399 0% ${allowPct}%,
              #ff6b6b ${allowPct}% 100%
            )`,
            padding: "20px",
          }}
        >
          {/* Inner hole */}
          <div
            className="
              w-full h-full rounded-full
              flex flex-col items-center justify-center
              backdrop-blur-sm border border-primary/10
            "
            style={{
              background: "rgba(17, 24, 40, 0.8)",
              boxShadow: "inset 0 2px 8px rgba(0,0,0,0.4)",
            }}
          >
            <span className="text-2xl font-bold text-[#e0e8f0]">{total}</span>
            <span className="text-xs text-[#a0b4c4]">Total</span>
          </div>
        </div>
      </div>

      {/* Legend */}
      <div className="mt-6 flex justify-center gap-6 text-sm">
        <div className="flex items-center gap-2">
          <span
            className="w-3 h-3 rounded-full bg-emerald-400"
            style={{ boxShadow: "0 0 10px rgba(52,211,153,0.5)" }}
          />
          <span className="text-[#a0b4c4]">Allow ({allowPct}%)</span>
        </div>
        <div className="flex items-center gap-2">
          <span
            className="w-3 h-3 rounded-full bg-[#ff6b6b]"
            style={{ boxShadow: "0 0 10px rgba(255,107,107,0.5)" }}
          />
          <span className="text-[#a0b4c4]">Deny ({denyPct}%)</span>
        </div>
      </div>
    </div>
  );
}

// ── Bar chart ─────────────────────────────────────────────────────
function ScoreBarChart({ logs }: { logs: LogEntry[] }): JSX.Element {
  // Build bins 0.0–1.0 in 0.1 steps
  const bins = Array.from({ length: 10 }, (_, i) => {
    const lo = i / 10;
    const hi = (i + 1) / 10;
    const count = logs.filter((l) => {
      const s = l.similarity_score;
      return s !== null && s >= lo && (i === 9 ? s <= hi : s < hi);
    }).length;
    return { lo: lo.toFixed(1), hi: hi.toFixed(1), count };
  });

  const maxCount = Math.max(...bins.map((b) => b.count), 1);

  // Color by range
  const barColor = (lo: string): string => {
    const v = parseFloat(lo);
    if (v < 0.4) return "bg-[#ff6b6b]/80 hover:bg-[#ff6b6b]";
    if (v < 0.55) return "bg-primary/40  hover:bg-primary/60";
    return "bg-emerald-400/80 hover:bg-emerald-400";
  };

  return (
    <div className="glass-panel rounded-xl p-6 flex flex-col lg:col-span-2">
      <div className="flex justify-between items-center mb-6">
        <h3 className="text-lg font-bold text-[#e0e8f0]">
          Score Distribution (0.0 – 1.0)
        </h3>
        <div className="flex gap-2">
          <button
            className="
            px-3 py-1 rounded
            bg-primary/10 text-primary
            text-xs font-semibold border border-primary/20
          "
          >
            All
          </button>
        </div>
      </div>

      <div
        className="
          flex-1 flex items-end justify-between
          gap-1 mt-4 pt-4
          border-t border-primary/5
          relative min-h-[250px]
        "
      >
        {/* Y-axis grid lines */}
        <div className="absolute inset-0 flex flex-col justify-between pointer-events-none pb-8">
          {[100, 75, 50, 25].map((v) => (
            <div key={v} className="w-full border-t border-primary/5" />
          ))}
        </div>

        {/* Y-axis labels */}
        <div
          className="
          absolute left-0 top-0 bottom-8
          flex flex-col justify-between
          text-[10px] text-[#a0b4c4]/50 -ml-1
        "
        >
          {[
            maxCount,
            Math.round(maxCount * 0.75),
            Math.round(maxCount * 0.5),
            Math.round(maxCount * 0.25),
          ].map((v) => (
            <span key={v}>{v}</span>
          ))}
        </div>

        {/* Bars */}
        <div
          className="
          w-full h-full flex items-end justify-between
          px-4 pb-8 relative z-10 gap-1 sm:gap-2
        "
        >
          {bins.map((bin) => {
            const heightPct =
              maxCount > 0
                ? Math.max((bin.count / maxCount) * 100, bin.count > 0 ? 4 : 0)
                : 0;
            return (
              <div
                key={bin.lo}
                className="w-full flex flex-col items-center gap-1"
                title={`${bin.lo}–${bin.hi}: ${bin.count} events`}
              >
                <div
                  className={`
                    w-full rounded-t-sm transition-all
                    ${barColor(bin.lo)}
                  `}
                  style={{ height: `${heightPct}%` }}
                />
              </div>
            );
          })}
        </div>

        {/* X-axis labels */}
        <div
          className="
          absolute bottom-0 left-4 right-4
          flex justify-between
          text-[10px] text-[#a0b4c4] font-mono
          mt-2 pt-2 border-t border-primary/20
        "
        >
          {[
            "0.0",
            "0.1",
            "0.2",
            "0.3",
            "0.4",
            "0.5",
            "0.6",
            "0.7",
            "0.8",
            "0.9",
            "1.0",
          ].map((v) => (
            <span key={v}>{v}</span>
          ))}
        </div>
      </div>
    </div>
  );
}

// ── Performance table ─────────────────────────────────────────────
// function PerfTable({ stats }: { stats: LogStats }): JSX.Element {
//   const rows = [
//     {
//       label: "Average Latency",
//       value: `${stats.avg_latency_ms?.toFixed(2) ?? "—"} ms`,
//     },
//     {
//       label: "Min Latency",
//       value: `${stats.min_latency_ms?.toFixed(2) ?? "—"} ms`,
//     },
//     {
//       label: "Max Latency",
//       value: `${stats.max_latency_ms?.toFixed(2) ?? "—"} ms`,
//     },
//     {
//       label: "Avg Score (ALLOW)",
//       value: stats.avg_score_allow?.toFixed(4) ?? "—",
//     },
//     {
//       label: "Avg Score (DENY)",
//       value: stats.avg_score_deny?.toFixed(4) ?? "—",
//     },
//     {
//       label: "Allow Rate",
//       value: `${((stats.allow_rate ?? 0) * 100).toFixed(1)}%`,
//     },
//   ];

//   return (
//     <div className="glass-panel rounded-xl p-6">
//       <div className="flex items-center gap-3 mb-6">
//         <span className="material-symbols-outlined text-primary/70">speed</span>
//         <h3 className="text-lg font-bold text-[#e0e8f0]">
//           Performance Metrics
//         </h3>
//       </div>
//       <div className="flex flex-col divide-y divide-[#2a3a48]/50">
//         {rows.map((r) => (
//           <div
//             key={r.label}
//             className="flex justify-between items-center py-3 text-sm"
//           >
//             <span className="text-[#a0b4c4]">{r.label}</span>
//             <span className="font-mono font-semibold text-[#e0e8f0]">
//               {r.value}
//             </span>
//           </div>
//         ))}
//       </div>
//     </div>
//   );
// }

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
        <span className="material-symbols-outlined text-3xl animate-spin">
          refresh
        </span>
        Loading statistics...
      </div>
    );
  }

  if (!stats) {
    return (
      <div className="flex flex-col items-center justify-center h-full gap-3 text-[#a0b4c4]">
        <span className="material-symbols-outlined text-4xl">
          bar_chart_off
        </span>
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
          icon={<IoFingerPrintSharp size={30} />}
          label="Total Attempts"
          value={stats.total_authentications}
          glowColor="rgba(125,211,252,0.15)"
        />
        <MetricCard
          icon={<FaRegCheckCircle size={30} />}
          label="Granted"
          value={stats.total_allow}
          sub={`${((stats.allow_rate ?? 0) * 100).toFixed(1)}%`}
          glowColor="rgba(52,211,153,0.15)"
        />
        <MetricCard
          icon={<TbCancel size={30} />}
          label="Denied"
          value={stats.total_deny}
          sub={`${((stats.deny_rate ?? 0) * 100).toFixed(1)}%`}
          glowColor="rgba(255,107,107,0.15)"
        />
        <MetricCard
          icon={<MdOutlineTimer size={30} />}
          label="Avg Latency"
          value={`${stats.avg_latency_ms?.toFixed(2) ?? "—"}`}
          sub="ms"
          glowColor="rgba(125,211,252,0.1)"
        />
        <MetricCard
          icon={<BsPersonFillCheck size={30} />}
          label="Avg Score (Allow)"
          value={stats.avg_score_allow?.toFixed(4) ?? "—"}
          glowColor="rgba(52,211,153,0.1)"
        />
        <MetricCard
          icon={<IoAnalyticsSharp size={30} />}
          label="Avg Score"
          value={
            stats.avg_score_allow != null
              ? (
                  (stats.avg_score_allow + (stats.avg_score_deny ?? 0)) /
                  2
                ).toFixed(3)
              : "—"
          }
          glowColor="rgba(125,211,252,0.1)"
        />
      </div>

      {/* Charts row */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        <DonutChart
          total={Number(stats.total_authentications) || 0}
          allow={stats.total_allow}
          deny={stats.total_deny}
          allowRate={stats.allow_rate ?? 0}
        />
        <ScoreBarChart logs={logs} />
      </div>

      {/* Performance table */}
      {/* <PerfTable stats={stats} /> */}
    </div>
  );
}
