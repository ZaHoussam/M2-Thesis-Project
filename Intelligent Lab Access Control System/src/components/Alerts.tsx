// ================================================================
//  Alerts.tsx — security alerts tab
//  Shows historical alerts + live feed via WebSocket
// ================================================================
import { useEffect, useRef, useState } from "react";
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

  // Load existing alerts from DB
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

  // Resolve an alert
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

  useEffect(() => {
    fetchAlerts();

    // Connect to live alert WebSocket
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

      ws.onerror = (): void => ws.close();
    };

    connect();
    return (): void => {
      wsRef.current?.close();
    };
  }, []);

  const activeCount = alerts.filter((a) => !a.is_resolved).length;

  if (loading) return <div className="loading">Loading alerts...</div>;

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>
          Security Alerts
          {activeCount > 0 && (
            <span className="alert-count">{activeCount} active</span>
          )}
        </h2>
        <span
          className={`ws-status ${connected ? "connected" : "disconnected"}`}
        >
          {connected ? "● Live" : "○ Reconnecting..."}
        </span>
      </div>

      {alerts.length === 0 ? (
        <div className="empty">No security alerts recorded.</div>
      ) : (
        <div className="alerts-list">
          {alerts.map((a: AlertEntry) => (
            <div
              key={a.id}
              className={`alert-card ${a.is_resolved ? "resolved" : ""}`}
              style={{
                borderLeftColor: a.is_resolved
                  ? "#444"
                  : SEVERITY_COLORS[a.severity],
              }}
            >
              <div className="alert-header">
                <div className="alert-left">
                  <span
                    className="severity-badge"
                    style={{
                      background: a.is_resolved
                        ? "#333"
                        : SEVERITY_COLORS[a.severity] + "22",
                      color: a.is_resolved
                        ? "#666"
                        : SEVERITY_COLORS[a.severity],
                      border: `1px solid ${a.is_resolved ? "#444" : SEVERITY_COLORS[a.severity]}`,
                    }}
                  >
                    {a.severity}
                  </span>
                  <span className="alert-type">
                    {TYPE_LABELS[a.alert_type] ?? a.alert_type}
                  </span>
                  <span className="alert-lab">Lab #{a.lab_id}</span>
                </div>
                <div className="alert-right">
                  <span className="alert-time">
                    {new Date(a.created_at).toLocaleString()}
                  </span>
                  {!a.is_resolved && (
                    <button
                      className="btn-sm btn-ok"
                      onClick={() => resolveAlert(a.id)}
                    >
                      Resolve
                    </button>
                  )}
                  {a.is_resolved && (
                    <span className="resolved-label">✓ Resolved</span>
                  )}
                </div>
              </div>
              <div className="alert-description">{a.description}</div>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
