// ================================================================
//  Alerts.tsx — Security Alerts page
//  Updated to match sidebar layout + glassmorphism design system
// ================================================================
import { useEffect, useRef, useState, type JSX } from "react";
import axios from "axios";
import type { AlertEntry } from "../types";
import { MdOutlineLockPerson, MdOutlineVisibility } from "react-icons/md";
import { TbShieldBolt } from "react-icons/tb";
import { IoShieldCheckmarkOutline } from "react-icons/io5";
import { exportAlertsCSV, exportAlertsPDF } from "../utils/exportAlerts";
import { CiViewTable } from "react-icons/ci";
import { PiFilePdfDuotone } from "react-icons/pi";

const API = "http://localhost:8000";
const WS_URL = "ws://localhost:8000/alerts/ws";

type FilterTab = "all" | "active" | "resolved";

// ── Severity config ───────────────────────────────────────────────
const SEVERITY_CONFIG: Record<
  string,
  { color: string; bg: string; border: string }
> = {
  LOW: {
    color: "#7dd3fc",
    bg: "rgba(125,211,252,0.1)",
    border: "rgba(125,211,252,0.25)",
  },
  MEDIUM: {
    color: "#EF9F27",
    bg: "rgba(239,159,39,0.1)",
    border: "rgba(239,159,39,0.25)",
  },
  HIGH: {
    color: "#ff6b6b",
    bg: "rgba(255,107,107,0.1)",
    border: "rgba(255,107,107,0.25)",
  },
  CRITICAL: {
    color: "#9b59b6",
    bg: "rgba(155,89,182,0.15)",
    border: "rgba(155,89,182,0.3)",
  },
};

// ── Alert type config ─────────────────────────────────────────────
const TYPE_CONFIG: Record<
  string,
  { icon: JSX.Element; label: string; iconColor: string }
> = {
  CONSECUTIVE_DENY: {
    icon: <MdOutlineLockPerson size={24} />,
    label: "Consecutive Denials",
    iconColor: "#ff6b6b",
  },
  HIGH_VOLUME: {
    icon: <TbShieldBolt size={24} />,
    label: "High Volume",
    iconColor: "#EF9F27",
  },
  SUSPICIOUS_MOVEMENT: {
    icon: <MdOutlineVisibility size={24} />,
    label: "Suspicious Movement",
    iconColor: "#EF9F27",
  },
};

// ── Time ago helper ───────────────────────────────────────────────
function timeAgo(iso: string): string {
  const diff = Date.now() - new Date(iso).getTime();
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(mins / 60);
  const days = Math.floor(hours / 24);
  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (mins > 0) return `${mins}m ago`;
  return "Just now";
}

export default function Alerts(): JSX.Element {
  const [alerts, setAlerts] = useState<AlertEntry[]>([]);
  const [connected, setConnected] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);
  const [filter, setFilter] = useState<FilterTab>("all");
  const wsRef = useRef<WebSocket | null>(null);

  // ── Fetch ─────────────────────────────────────────────────────
  const fetchAlerts = async (): Promise<void> => {
    try {
      const res = await axios.get<AlertEntry[]>(`${API}/alerts`);
      setAlerts(res.data);
    } catch (e) {
      console.error("Failed to fetch alerts:", e);
    } finally {
      setLoading(false);
    }
  };

  // ── Resolve ───────────────────────────────────────────────────
  const resolveAlert = async (id: number): Promise<void> => {
    try {
      await axios.put(`${API}/alerts/${id}/resolve`);
      setAlerts((prev) =>
        prev.map((a) => (a.id === id ? { ...a, is_resolved: true } : a)),
      );
    } catch (e) {
      console.error("Failed to resolve alert:", e);
    }
  };

  // ── WebSocket ─────────────────────────────────────────────────
  useEffect(() => {
    fetchAlerts();

    const connect = (): void => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = (): void => setConnected(true);
      ws.onmessage = (msg: MessageEvent): void => {
        try {
          const alert = JSON.parse(msg.data as string) as AlertEntry;
          setAlerts((prev) => [alert, ...prev]);
        } catch (e) {
          console.error(e);
        }
      };
      ws.onclose = (): void => {
        setConnected(false);
        setTimeout(connect, 3000);
      };
      ws.onerror = (): void => ws.close();
    };

    connect();
    return (): void => {
      wsRef.current?.close();
    };
  }, []);

  // ── Derived stats ─────────────────────────────────────────────
  const activeCount = alerts.filter((a) => !a.is_resolved).length;
  const resolvedCount = alerts.filter((a) => a.is_resolved).length;
  const criticalCount = alerts.filter(
    (a) => a.severity === "CRITICAL" && !a.is_resolved,
  ).length;

  const filtered = alerts.filter((a) => {
    if (filter === "active") return !a.is_resolved;
    if (filter === "resolved") return a.is_resolved;
    return true;
  });

  // ── Loading ───────────────────────────────────────────────────
  if (loading) {
    return (
      <div className="flex items-center justify-center h-full gap-3 text-[#a0b4c4]">
        <span className="material-symbols-outlined text-3xl animate-spin">
          refresh
        </span>
        Loading security alerts...
      </div>
    );
  }

  return (
    <div className="flex flex-col gap-6">
      {/* ── Header ─────────────────────────────────────────── */}
      <div className="flex items-start justify-between">
        <div className="relative">
          <h2 className="text-2xl font-bold text-[#e0e8f0] tracking-tight flex items-center gap-3">
            Security Alerts
            {activeCount > 0 && (
              <span
                className="
                px-2.5 py-0.5 rounded-full
                bg-[#ff6b6b] text-white
                text-xs font-bold
              "
              >
                {activeCount}
              </span>
            )}
          </h2>
          <p className="text-sm text-[#a0b4c4] mt-1">
            Threat detection and incident management across all lab entrances
          </p>
          {/* WebSocket status */}
          <div
            className={`
          absolute top-0 right-0
          flex items-center gap-2 px-3 py-1.5 rounded-full
          border text-xs font-semibold
          ${
            connected
              ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
              : "bg-[#ff6b6b]/10 border-[#ff6b6b]/20 text-[#ff6b6b]"
          }
        `}
          >
            <span className="relative flex h-2 w-2">
              {connected && (
                <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-emerald-400 opacity-75" />
              )}
              <span
                className={`
              relative inline-flex rounded-full h-2 w-2
              ${connected ? "bg-emerald-400" : "bg-[#ff6b6b]"}
            `}
              />
            </span>
            {connected ? "Live" : "Reconnecting..."}
          </div>
        </div>
        {/* ── Export buttons — add these ── */}
        <div className="flex gap-2 ml-auto">
          <button
            onClick={() => exportAlertsCSV(filtered)}
            className="
      flex items-center gap-2
      px-3 py-1.5 rounded-lg
      border border-[#2a3a48]
      text-[#a0b4c4] text-xs font-semibold
      hover:text-emerald-400 hover:border-emerald-500/30
      hover:bg-emerald-500/5
      transition-all
      cursor-pointer
    "
            title="Export as CSV — opens in Excel"
          >
            <CiViewTable size={16} />
            CSV
          </button>
          <button
            onClick={() => exportAlertsPDF(filtered)}
            className="
      flex items-center gap-2
      px-3 py-1.5 rounded-lg
      border border-[#2a3a48]
      text-[#a0b4c4] text-xs font-semibold
      hover:text-[#7dd3fc] hover:border-primary/30
      hover:bg-primary/5
      transition-all
      cursor-pointer
    "
            title="Export as PDF — opens print dialog"
          >
            <PiFilePdfDuotone size={16} />
            PDF
          </button>
        </div>
      </div>
      {/* ── Table card ─────────────────────────────────────── */}
      <div className="glass-elevated rounded-xl overflow-hidden flex flex-col">
        {/* Table header + filter tabs */}
        <div
          className="
          px-6 py-4
          border-b border-[#2a3a48]/50
          flex items-center justify-between gap-4
        "
        >
          <h3 className="text-sm font-semibold text-[#e0e8f0] flex-shrink-0">
            Incidents
            <span
              className="
              ml-2 px-2 py-0.5 rounded-full
              bg-primary/10 text-primary
              text-xs border border-primary/20
            "
            >
              {filtered.length}
            </span>
          </h3>

          {/* Filter tabs */}
          <div className="flex gap-2">
            {(["all", "active", "resolved"] as FilterTab[]).map((f) => (
              <button
                key={f}
                onClick={() => setFilter(f)}
                className={`
                  px-4 py-1.5 rounded-lg text-xs font-semibold
                  transition-all capitalize
                  ${
                    filter === f
                      ? "bg-primary/10 text-primary border border-primary/20"
                      : "bg-transparent text-[#a0b4c4] border border-[#2a3a48] hover:text-[#e0e8f0]"
                  }
                `}
              >
                {f}
              </button>
            ))}
          </div>
        </div>

        {/* Table */}
        <div className="overflow-x-auto flex-1 custom-scrollbar">
          {filtered.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-20 gap-3">
              <IoShieldCheckmarkOutline
                size={48}
                className="text-emerald-400"
              />
              <p className="text-sm text-[#a0b4c4]">
                {filter === "active"
                  ? "No active alerts — system is secure"
                  : "No alerts recorded"}
              </p>
            </div>
          ) : (
            <table className="w-full">
              <thead>
                <tr className="border-b border-[#2a3a48]/50">
                  {[
                    "Severity",
                    "Time",
                    "Alert Type",
                    "Lab",
                    "Description",
                    "Status",
                    "Actions",
                  ].map((h) => (
                    <th
                      key={h}
                      className="
                        px-6 py-3 text-left
                        text-xs font-semibold uppercase
                        tracking-wider text-[#4a6070]
                      "
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <tbody>
                {filtered.map((a: AlertEntry) => {
                  const sev =
                    SEVERITY_CONFIG[a.severity] ?? SEVERITY_CONFIG["LOW"];
                  const type = TYPE_CONFIG[a.alert_type] ?? {
                    icon: "notifications",
                    label: a.alert_type,
                    iconColor: "#a0b4c4",
                  };

                  return (
                    <tr
                      key={a.id}
                      className={`
                        border-b border-[#2a3a48]/30
                        transition-colors
                        hover:bg-[#181818]
                        ${a.is_resolved ? "opacity-50" : ""}
                      `}
                    >
                      {/* Severity */}
                      <td className="px-6 py-4">
                        <span
                          className="
                            px-2.5 py-1 rounded-md
                            text-[10px] font-bold
                            uppercase tracking-wider
                            border
                          "
                          style={{
                            background: sev.bg,
                            color: sev.color,
                            borderColor: sev.border,
                          }}
                        >
                          {a.severity}
                        </span>
                      </td>

                      {/* Timestamp */}
                      <td
                        className="
                        px-6 py-4
                        text-xs font-mono text-[#a0b4c4]
                        whitespace-nowrap
                      "
                      >
                        {timeAgo(a.created_at)}
                      </td>

                      {/* Alert type */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span
                            className="material-symbols-outlined text-[18px]"
                            style={{ color: type.iconColor }}
                          >
                            {type.icon}
                          </span>
                          <span className="text-sm font-semibold text-[#e0e8f0] whitespace-nowrap">
                            {type.label}
                          </span>
                        </div>
                      </td>

                      {/* Lab */}
                      <td className="px-6 py-4 text-xs font-mono text-[#a0b4c4]">
                        LAB-{a.lab_id}
                      </td>

                      {/* Description */}
                      <td
                        className="
                        px-6 py-4 text-xs text-[#a0b4c4]
                        max-w-xs
                      "
                      >
                        <span className="line-clamp-2">{a.description}</span>
                      </td>

                      {/* Status */}
                      <td className="px-6 py-4">
                        {a.is_resolved ? (
                          <span
                            className="
                            flex items-center gap-1.5
                            text-[10px] font-bold
                            text-[#a0b4c4]
                            uppercase tracking-wider
                          "
                          >
                            <span className="material-symbols-outlined text-[14px] text-emerald-400">
                              verified
                            </span>
                            Resolved
                          </span>
                        ) : (
                          <span
                            className="
                            flex items-center gap-1.5
                            text-[10px] font-bold
                            text-[#ff6b6b]
                            uppercase tracking-wider
                          "
                          >
                            <span
                              className="w-1.5 h-1.5 rounded-full bg-[#ff6b6b] inline-block"
                              style={{ animation: "pulse 1.5s infinite" }}
                            />
                            Live
                          </span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-6 py-4 text-right">
                        {a.is_resolved ? (
                          <span
                            className="
                            text-[10px] font-bold
                            text-[#4a6070]
                            uppercase italic
                          "
                          >
                            Archived
                          </span>
                        ) : (
                          <div className="flex items-center justify-end gap-2">
                            <button
                              onClick={() => resolveAlert(a.id)}
                              className="
                                px-3 py-1.5 rounded-lg
                                border border-[#2a3a48]
                                text-[#e0e8f0] text-[10px] font-bold
                                uppercase tracking-wider
                                hover:bg-emerald-500/10
                                hover:border-emerald-500/30
                                hover:text-emerald-400
                                transition-all
                              "
                            >
                              Resolve
                            </button>
                          </div>
                        )}
                      </td>
                    </tr>
                  );
                })}
              </tbody>
            </table>
          )}
        </div>

        {/* Footer */}
        <div
          className="
          px-6 py-4
          border-t border-[#2a3a48]/30
          flex items-center justify-between
          bg-[#141c2e]/30
        "
        >
          <span className="text-xs text-[#4a6070] font-semibold uppercase tracking-wider">
            Showing {filtered.length} of {alerts.length} alerts
          </span>
          <span
            className={`
            text-xs font-bold
            ${connected ? "text-emerald-400" : "text-[#ff6b6b]"}
          `}
          >
            {connected ? "● WebSocket Connected" : "○ Reconnecting..."}
          </span>
        </div>
      </div>
    </div>
  );
}
