// ================================================================
//  LiveFeed.tsx — real-time access event feed
//  Design: Stitch glassmorphism dark theme
// ================================================================
import { useEffect, useRef, useState, type JSX } from "react";
import type { LiveEvent } from "../types";
import {
  TriangleAlert,
  ReceiptText,
  CircleCheck,
  Play,
  Pause,
  CircleX,
  BrushCleaning,
} from "lucide-react";
import { MdOutlineSensorsOff } from "react-icons/md";

const WS_URL = "ws://localhost:8000/logs/ws";

// Score thresholds for event type
const SCORE_REVIEW_THRESHOLD = 0.7; // below this → amber "Review"

function getEventStyle(e: LiveEvent): {
  bg: string;
  border: string;
  accentBar: string;
  hoverBg: string;
  hoverBorder: string;
} {
  if (e.outcome === "DENY")
    return {
      bg: "bg-[#3d1414]/10",
      border: "border-[#ff6b6b]/10",
      accentBar: "bg-[#ff6b6b]/60",
      hoverBg: "hover:bg-[#3d1414]/20",
      hoverBorder: "hover:border-[#ff6b6b]/30",
    };
  const score = e.similarity_score ?? 0;
  if (score < SCORE_REVIEW_THRESHOLD)
    return {
      bg: "bg-amber-900/10",
      border: "border-amber-500/10",
      accentBar: "bg-amber-500/60",
      hoverBg: "hover:bg-amber-900/20",
      hoverBorder: "hover:border-amber-500/30",
    };
  return {
    bg: "bg-[#111828]/40",
    border: "border-primary/5",
    accentBar: "bg-emerald-500/50",
    hoverBg: "hover:bg-[#141c2e]/60",
    hoverBorder: "hover:border-primary/20",
  };
}

function getScoreColor(e: LiveEvent): string {
  if (e.outcome === "DENY") return "text-[#ff6b6b]";
  const score = e.similarity_score ?? 0;
  if (score < SCORE_REVIEW_THRESHOLD) return "text-amber-300";
  return "text-emerald-300";
}

function getOutcomeBadge(e: LiveEvent): { label: string; cls: string } {
  if (e.outcome === "DENY")
    return {
      label: "Denied",
      cls: "bg-[#ff6b6b]/10 text-[#ff6b6b] border-[#ff6b6b]/20",
    };
  const score = e.similarity_score ?? 0;
  if (score < SCORE_REVIEW_THRESHOLD)
    return {
      label: "Review",
      cls: "bg-amber-500/10 text-amber-400 border-amber-500/20",
    };
  return {
    label: "Granted",
    cls: "bg-emerald-500/10 text-emerald-400 border-emerald-500/20",
  };
}

function getIcon(e: LiveEvent): { icon: JSX.Element; color: string } {
  if (e.outcome === "DENY")
    return { icon: <CircleX size={16} />, color: "text-[#ff6b6b]" };
  const score = e.similarity_score ?? 0;
  if (score < SCORE_REVIEW_THRESHOLD)
    return { icon: <TriangleAlert size={16} />, color: "text-amber-400" };
  return { icon: <CircleCheck size={16} />, color: "text-emerald-400" };
}

function formatTime(iso: string): string {
  return new Date(iso).toLocaleTimeString("en-US", {
    hour: "2-digit",
    minute: "2-digit",
    second: "2-digit",
    hour12: false,
  });
}

function Avatar({ userId }: { userId: number | null }): JSX.Element {
  if (!userId)
    return (
      <div className="w-8 h-8 rounded-full border border-[#ff6b6b]/30 bg-[#141c2e] flex items-center justify-center text-[#ff6b6b]">
        <span className="material-symbols-outlined text-sm">person_off</span>
      </div>
    );
  return (
    <div className="w-8 h-8 rounded-full bg-primary/20 border border-primary/30 flex items-center justify-center text-xs text-primary font-bold">
      {String(userId).slice(-2)}
    </div>
  );
}

export default function LiveFeed(): JSX.Element {
  const [events, setEvents] = useState<LiveEvent[]>([]);
  const [connected, setConnected] = useState<boolean>(false);
  const [paused, setPaused] = useState<boolean>(false);
  const wsRef = useRef<WebSocket | null>(null);
  const pauseRef = useRef<boolean>(false);

  useEffect(() => {
    const connect = (): void => {
      const ws = new WebSocket(WS_URL);
      wsRef.current = ws;

      ws.onopen = (): void => setConnected(true);

      ws.onmessage = (msg: MessageEvent): void => {
        if (pauseRef.current) return;
        try {
          const event = JSON.parse(msg.data as string) as LiveEvent;
          setEvents((prev) => [event, ...prev].slice(0, 100));
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

  const togglePause = (): void => {
    pauseRef.current = !pauseRef.current;
    setPaused(pauseRef.current);
  };

  const clearFeed = (): void => setEvents([]);

  // Stats
  const granted = events.filter((e) => e.outcome === "ALLOW").length;
  const denied = events.filter((e) => e.outcome === "DENY").length;
  const review = events.filter(
    (e) =>
      e.outcome === "ALLOW" &&
      (e.similarity_score ?? 0) < SCORE_REVIEW_THRESHOLD,
  ).length;

  return (
    <div className="flex flex-col gap-6 h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-[#e0e8f0] tracking-tight">
            Live Access Feed
          </h2>
          <p className="text-sm text-[#a0b4c4] mt-1">
            Real-time authentication events across all lab entrances
          </p>
        </div>
        <div className="flex items-center gap-3">
          {/* Connection status */}
          <div
            className={`
            flex items-center gap-2 px-3 py-1.5 rounded-full
            border text-xs font-semibold
            ${
              connected
                ? "bg-emerald-500/10 border-emerald-500/20 text-emerald-400"
                : "bg-[#ff6b6b]/10 border-[#ff6b6b]/20 text-[#ff6b6b]"
            }
          `}
          >
            <span
              className={`
              relative flex h-2 w-2
            `}
            >
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
            {connected ? "Connected" : "Reconnecting..."}
          </div>

          {/* Pause button */}
          <button
            onClick={togglePause}
            className={`
              flex items-center gap-2 px-3 py-1.5 rounded-lg
              border text-xs font-semibold transition-all
              cursor-pointer
              ${
                paused
                  ? "bg-amber-500/10 border-amber-500/30 text-amber-400"
                  : "bg-[#141c2e] border-[#2a3a48] text-[#a0b4c4] hover:text-[#e0e8f0]"
              }
            `}
          >
            <span className="material-symbols-outlined text-[16px]">
              {paused ? <Play size={16} /> : <Pause size={16} />}
            </span>
            {paused ? "Resume" : "Pause"}
          </button>

          {/* Clear button */}
          <button
            onClick={clearFeed}
            className="
              flex items-center gap-2 px-3 py-1.5 rounded-lg
              border border-[#2a3a48] text-[#a0b4c4]
              hover:text-[#e0e8f0] text-xs font-semibold
              transition-all
              cursor-pointer
            "
          >
            <BrushCleaning size={16} />
            Clear
          </button>
        </div>
      </div>

      {/* Stats bar */}
      <div className="grid grid-cols-4 gap-4">
        {[
          {
            label: "Total Events",
            value: events.length,
            icon: <ReceiptText size={20} />,
            color: "#7dd3fc",
            borderColor: "#7dd3fc14",
          },
          {
            label: "Granted",
            value: granted,
            icon: <CircleCheck size={20} />,
            color: "#34d399",
            borderColor: "#34d39926",
          },
          {
            label: "Denied",
            value: denied,
            icon: <CircleX size={20} />,
            color: "#ff6b6b",
            borderColor: "#ff6b6b26",
          },
          {
            label: "Review",
            value: review,
            icon: <TriangleAlert size={20} />,
            color: "#fbbf24",
            borderColor: "#fbbf2426",
          },
        ].map((s) => (
          <div
            key={s.label}
            className="glass-panel rounded-lg p-4 flex items-center gap-3 bg-[#0f152480] border "
            style={{
              borderColor: s.borderColor,
            }}
          >
            <span
              className={`text-[22px]`}
              style={{
                color: s.color,
                padding: "4px",
                borderRadius: "8px",
              }}
            >
              {s.icon}
            </span>
            <div className="flex flex-col gap-2">
              <p
                className="text-4xl font-bold text-[#e0e8f0] font-mono"
                style={{ color: s.color }}
              >
                {s.value.toString().padStart(2, "0")}
              </p>
              <p className="text-xs text-[#a0b4c4] uppercase tracking-wider font-semibold">
                {s.label}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Event list */}
      <div className="glass-elevated rounded-xl flex flex-col flex-1 overflow-hidden">
        {/* Column headers */}
        <div
          className="
          grid grid-cols-12 gap-4 px-4 py-3
          border-b border-[#2a3a48]/50
          text-xs font-semibold text-[#a0b4c4] uppercase tracking-wider
        "
        >
          <div className="col-span-2">Timestamp</div>
          <div className="col-span-3">Identity</div>
          <div className="col-span-2">Lab / Door</div>
          <div className="col-span-2">Confidence</div>
          <div className="col-span-2">Decision</div>
          <div className="col-span-1 text-right">Latency</div>
        </div>

        {/* Events */}
        <div
          className="
          flex-1 overflow-auto custom-scrollbar
          flex flex-col gap-2 p-3
          relative
        "
        >
          {events.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full gap-3 text-[#a0b4c4]">
              <MdOutlineSensorsOff className="text-[150px]" />
              <p className="text-sm">
                {paused
                  ? "Feed paused — click Resume to continue"
                  : "Waiting for access events..."}
              </p>
            </div>
          ) : (
            events.map((e: LiveEvent, i: number) => {
              const style = getEventStyle(e);
              const badge = getOutcomeBadge(e);
              const icon = getIcon(e);
              const scoreColor = getScoreColor(e);
              const score =
                e.similarity_score !== null
                  ? `${(e.similarity_score * 100).toFixed(2)}%`
                  : "—";

              return (
                <div
                  key={i}
                  className={`
                    grid grid-cols-12 gap-4 px-4 py-3
                    items-center rounded-lg border
                    relative overflow-hidden
                    transition-colors group
                    ${style.bg} ${style.border}
                    ${style.hoverBg} ${style.hoverBorder}
                    animate-[slide-in-right_0.3s_ease-out_forwards]
                  `}
                  style={{ animationDelay: `${i * 0.02}s` }}
                >
                  {/* Left accent bar */}
                  <div
                    className={`
                    absolute left-0 top-0 bottom-0 w-1
                    ${style.accentBar}
                    group-hover:opacity-100
                    transition-all
                    shadow-[0_0_10px_rgba(125,211,252,0.2)]
                  `}
                  />

                  {/* Timestamp */}
                  <div className="col-span-2 text-sm text-[#a0b4c4] flex items-center gap-2">
                    <span
                      className={`material-symbols-outlined text-[16px] ${icon.color}`}
                    >
                      {icon.icon}
                    </span>
                    <span className="font-mono text-xs">
                      {formatTime(e.created_at)}
                    </span>
                  </div>

                  {/* Identity */}
                  <div className="col-span-3 flex items-center gap-3">
                    <Avatar userId={e.user_id} />
                    <div>
                      <div className="text-sm font-medium text-[#e0e8f0]">
                        {e.user_name ??
                          (e.user_id ? `User #${e.user_id}` : "Unknown Entity")}
                      </div>
                      <div
                        className={`text-xs font-mono ${e.user_id ? "text-[#a0b4c4]" : "text-[#ff6b6b]"}`}
                      >
                        {e.user_id
                          ? `UID-${String(e.user_id).padStart(4, "0")}`
                          : "UID-NULL"}
                      </div>
                    </div>
                  </div>

                  {/* Lab */}
                  <div className="col-span-2 text-sm text-[#a0b4c4]">
                    Lab #{e.lab_id}
                  </div>

                  {/* Confidence */}
                  <div className={`col-span-2 font-mono text-sm ${scoreColor}`}>
                    {score}
                  </div>

                  {/* Decision badge */}
                  <div className="col-span-2">
                    <span
                      className={`
                      px-2.5 py-1 rounded-md border
                      text-xs font-semibold uppercase tracking-wider
                      ${badge.cls}
                    `}
                    >
                      {badge.label}
                    </span>
                  </div>

                  {/* Latency */}
                  <div className="col-span-1 text-right text-xs text-[#a0b4c4] font-mono">
                    {e.latency_ms != null
                      ? `${e.latency_ms.toFixed(1)}ms`
                      : "—"}
                  </div>
                </div>
              );
            })
          )}

          {/* Bottom fade */}
          {events.length > 5 && (
            <div
              className="
              absolute bottom-0 left-0 w-full h-12
              bg-gradient-to-t from-[#0f1524]/80 to-transparent
              pointer-events-none rounded-b-xl z-10
            "
            />
          )}
        </div>
      </div>
    </div>
  );
}
