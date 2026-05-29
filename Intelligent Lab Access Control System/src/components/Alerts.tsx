// ================================================================
// Alerts.tsx — Modern Security Alerts Dashboard
// Real-time alerts + glassmorphism UI
// ================================================================

import { useEffect, useRef, useState, type JSX } from "react";
import axios from "axios";
import type { AlertEntry } from "../types";

const API = "http://localhost:8000";
const WS_URL = "ws://localhost:8000/alerts/ws";

const SEVERITY_COLORS: Record<string, string> = {
  LOW: "#378ADD",
  MEDIUM: "#EF9F27",
  HIGH: "#E24B4A",
  CRITICAL: "#7B2FBE",
};

const TYPE_LABELS: Record<string, string> = {
  CONSECUTIVE_DENY: "🔒 Consecutive Denials",
  HIGH_VOLUME: "⚡ High Volume",
  SUSPICIOUS_MOVEMENT: "👁 Suspicious Movement",
};

export default function Alerts(): JSX.Element {
  const [alerts, setAlerts] = useState<AlertEntry[]>([]);
  const [connected, setConnected] = useState<boolean>(false);
  const [loading, setLoading] = useState<boolean>(true);

  const wsRef = useRef<WebSocket | null>(null);

  // ============================================================
  // Fetch alerts from backend
  // ============================================================
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

  // ============================================================
  // Resolve alert
  // ============================================================
  const resolveAlert = async (id: number): Promise<void> => {
    try {
      await axios.put(`${API}/alerts/${id}/resolve`);

      setAlerts((prev) =>
        prev.map((a) =>
          a.id === id
            ? {
                ...a,
                is_resolved: true,
              }
            : a,
        ),
      );
    } catch (e) {
      console.error("Failed to resolve alert:", e);
    }
  };

  // ============================================================
  // WebSocket live alerts
  // ============================================================
  useEffect(() => {
    fetchAlerts();

    const connect = (): void => {
      const ws = new WebSocket(WS_URL);

      wsRef.current = ws;

      ws.onopen = (): void => {
        setConnected(true);
        console.log("[ALERTS] WebSocket connected");
      };

      ws.onmessage = (msg: MessageEvent): void => {
        try {
          const alert = JSON.parse(msg.data as string) as AlertEntry;

          setAlerts((prev) => [alert, ...prev]);
        } catch (e) {
          console.error("Failed to parse alert:", e);
        }
      };

      ws.onclose = (): void => {
        setConnected(false);

        setTimeout(connect, 3000);
      };

      ws.onerror = (): void => {
        ws.close();
      };
    };

    connect();

    return (): void => {
      wsRef.current?.close();
    };
  }, []);

  const activeCount = alerts.filter((a) => !a.is_resolved).length;

  // ============================================================
  // Loading state
  // ============================================================
  if (loading) {
    return (
      <div className="min-h-screen flex items-center justify-center bg-[#0a0e1a] text-white text-lg">
        Loading security alerts...
      </div>
    );
  }

  // ============================================================
  // UI
  // ============================================================
  return (
    <main className="relative min-h-screen overflow-x-hidden bg-[#0a0e1a] text-[#e0e8f0] p-6 md:p-10">
      {/* Background Glow Effects */}
      <div className="absolute top-0 right-0 w-[600px] h-[600px] bg-cyan-400/5 rounded-full blur-[160px] pointer-events-none -z-10 opacity-60" />

      <div className="absolute bottom-0 left-0 w-[500px] h-[500px] bg-red-500/5 rounded-full blur-[140px] pointer-events-none -z-10 opacity-40" />

      {/* ===================================================== */}
      {/* Header */}
      {/* ===================================================== */}
      <div className="flex flex-col lg:flex-row lg:items-end justify-between mb-10 gap-6">
        <div>
          <div className="flex items-center gap-4 mb-2 flex-wrap">
            <h1 className="text-4xl font-extrabold tracking-tight">
              Security Alerts
            </h1>

            {/* Live Badge */}
            <span className="bg-red-500/15 text-red-400 text-[10px] px-3 py-1 rounded-full border border-red-500/20 font-black uppercase tracking-widest flex items-center gap-1.5">
              <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-ping" />
              {connected ? "Live Feed" : "Offline"}
            </span>

            {/* Active Alerts Count */}
            {activeCount > 0 && (
              <span className="bg-cyan-400/10 text-cyan-300 text-xs px-3 py-1 rounded-full border border-cyan-400/20 font-bold">
                {activeCount} Active
              </span>
            )}
          </div>

          <p className="text-slate-400 max-w-2xl">
            Monitoring real-time security violations and suspicious telemetry
            across all connected laboratory sectors.
          </p>
        </div>
      </div>

      {/* ===================================================== */}
      {/* Alerts Table */}
      {/* ===================================================== */}
      <div className="rounded-2xl overflow-hidden border border-white/5 bg-white/[0.04] backdrop-blur-2xl shadow-2xl">
        <div className="overflow-x-auto">
          <table className="w-full border-collapse text-left">
            {/* =============================================== */}
            {/* Table Header */}
            {/* =============================================== */}
            <thead>
              <tr className="bg-white/5 border-b border-white/10">
                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-400">
                  Severity
                </th>

                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-400">
                  Timestamp
                </th>

                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-400">
                  Alert Type
                </th>

                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-400">
                  Lab
                </th>

                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-400">
                  Description
                </th>

                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-400">
                  Status
                </th>

                <th className="px-6 py-4 text-[10px] font-black uppercase tracking-widest text-slate-400 text-right">
                  Actions
                </th>
              </tr>
            </thead>

            {/* =============================================== */}
            {/* Table Body */}
            {/* =============================================== */}
            <tbody className="divide-y divide-white/5">
              {alerts.length === 0 ? (
                <tr>
                  <td colSpan={7} className="text-center py-16 text-slate-500">
                    No security alerts recorded.
                  </td>
                </tr>
              ) : (
                alerts.map((a: AlertEntry) => {
                  const color = SEVERITY_COLORS[a.severity] || "#888888";

                  return (
                    <tr
                      key={a.id}
                      className={`transition-all hover:bg-white/[0.03] ${
                        a.is_resolved ? "opacity-50 grayscale-[0.4]" : ""
                      }`}
                    >
                      {/* Severity */}
                      <td className="px-6 py-4">
                        <span
                          className="text-[10px] font-black px-2.5 py-1 rounded-md border uppercase tracking-widest"
                          style={{
                            background: `${color}22`,
                            color,
                            borderColor: `${color}55`,
                          }}
                        >
                          {a.severity}
                        </span>
                      </td>

                      {/* Timestamp */}
                      <td className="px-6 py-4 text-xs font-mono text-slate-400 uppercase">
                        {new Date(a.created_at).toLocaleString()}
                      </td>

                      {/* Alert Type */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-2">
                          <span className="text-sm font-bold">
                            {TYPE_LABELS[a.alert_type] ?? a.alert_type}
                          </span>
                        </div>
                      </td>

                      {/* Lab */}
                      <td className="px-6 py-4 text-xs font-mono">
                        LAB-{a.lab_id}
                      </td>

                      {/* Description */}
                      <td className="px-6 py-4 text-sm text-slate-300">
                        {a.description}
                      </td>

                      {/* Status */}
                      <td className="px-6 py-4">
                        {!a.is_resolved ? (
                          <span className="flex items-center gap-1.5 text-[10px] font-bold text-red-400 uppercase tracking-wider">
                            <span className="w-1.5 h-1.5 rounded-full bg-red-500 animate-pulse" />
                            Live
                          </span>
                        ) : (
                          <span className="flex items-center gap-1.5 text-[10px] font-bold text-slate-400 uppercase tracking-wider">
                            ✓ Resolved
                          </span>
                        )}
                      </td>

                      {/* Actions */}
                      <td className="px-6 py-4 text-right">
                        {!a.is_resolved ? (
                          <button
                            onClick={() => resolveAlert(a.id)}
                            className="px-3 py-1.5 rounded-lg text-[10px] font-black uppercase border transition-all hover:scale-105"
                            style={{
                              background: `${color}22`,
                              color,
                              borderColor: `${color}55`,
                            }}
                          >
                            Resolve
                          </button>
                        ) : (
                          <span className="text-[10px] font-black text-slate-500 uppercase italic">
                            Archived
                          </span>
                        )}
                      </td>
                    </tr>
                  );
                })
              )}
            </tbody>
          </table>
        </div>

        {/* ================================================= */}
        {/* Footer */}
        {/* ================================================= */}
        <div className="px-6 py-4 bg-white/5 border-t border-white/5 flex items-center justify-between">
          <p className="text-[10px] font-bold text-slate-500 uppercase tracking-widest">
            Showing {alerts.length} alerts
          </p>

          <div
            className={`text-xs font-bold ${
              connected ? "text-green-400" : "text-red-400"
            }`}
          >
            {connected ? "● WebSocket Connected" : "○ Reconnecting..."}
          </div>
        </div>
      </div>
    </main>
  );
}
