// ================================================================
//  LiveFeed.tsx — real-time access event feed via WebSocket
// ================================================================
import { useEffect, useRef, useState } from "react";
import type { LiveEvent } from "../types";

const WS_URL = "ws://localhost:8000/logs/ws";

export default function LiveFeed(): JSX.Element {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [connected, setConnected] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);

  useEffect(() => {
    const connect = (): void => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = (): void => {
        setConnected(true);
        console.log("[DASHBOARD] Connected to live feed");
      };

      ws.onmessage = (msg: MessageEvent): void => {
        try {
          const event = JSON.parse(msg.data as string) as LiveEvent;
          setEvents((prev) => [event, ...prev].slice(0, 100));
        } catch (e) {
          console.error("Failed to parse event:", e);
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

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Live Access Feed</h2>
        <span
          className={`ws-status ${connected ? "connected" : "disconnected"}`}
        >
          {connected ? "● Connected" : "○ Reconnecting..."}
        </span>
      </div>

      {events.length === 0 && (
        <div className="empty">Waiting for access events...</div>
      )}

      <div className="feed">
        {events.map((e: LiveEvent, i: number) => (
          <div
            key={i}
            className={`feed-row ${e.outcome === "ALLOW" ? "feed-allow" : "feed-deny"}`}
          >
            <span
              className={`outcome-badge ${e.outcome === "ALLOW" ? "allow" : "deny"}`}
            >
              {e.outcome}
            </span>
            <span className="feed-score">
              score: {e.similarity_score?.toFixed(4) ?? "—"}
            </span>
            <span className="feed-latency">
              {e.latency_ms?.toFixed(1) ?? "—"}ms
            </span>
            <span className="feed-user">
              {e.user_id !== null ? `User #${e.user_id}` : "Unknown"}
            </span>
            <span className="feed-time">
              {new Date(e.created_at).toLocaleTimeString()}
            </span>
          </div>
        ))}
      </div>
    </div>
  );
}
