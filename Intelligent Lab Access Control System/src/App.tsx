// ================================================================
//  App.tsx — root component with tab navigation
// ================================================================
import { useState } from "react";
import Users from "./components/Users";
import LiveFeed from "./components/LiveFeed";
import Statistics from "./components/Statistics";
import "./App.css";

type Tab = "users" | "live" | "stats";

interface TabDef {
  id: Tab;
  label: string;
}

const TABS: TabDef[] = [
  { id: "users", label: "👥 Users" },
  { id: "live", label: "📡 Live Feed" },
  { id: "stats", label: "📊 Statistics" },
];

export default function App(): JSX.Element {
  const [tab, setTab] = useState<Tab>("users");

  return (
    <div className="app">
      <header className="header">
        <div className="header-left">
          <div className="logo-dot" />
          <span className="header-title">Lab Access Control</span>
          <span className="header-version">Admin Dashboard</span>
        </div>
        <div className="header-right">
          <span className="live-indicator">● LIVE</span>
        </div>
      </header>

      <nav className="nav">
        {TABS.map((t) => (
          <button
            key={t.id}
            className={`nav-btn ${tab === t.id ? "active" : ""}`}
            onClick={() => setTab(t.id)}
          >
            {t.label}
          </button>
        ))}
      </nav>

      <main className="main">
        {tab === "users" && <Users />}
        {tab === "live" && <LiveFeed />}
        {tab === "stats" && <Statistics />}
      </main>
    </div>
  );
}
