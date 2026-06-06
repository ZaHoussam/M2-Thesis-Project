import { useState, type JSX } from "react";
import Login from "./pages/Login";
import Sidebar from "./components/Sidebar";
import Users from "./components/Users";
import LiveFeed from "./components/LiveFeed";
import Statistics from "./components/Statistics";
import Alerts from "./components/Alerts";
import type { Tab } from "./types";

export default function App(): JSX.Element {
  const [tab, setTab] = useState<Tab>("users");
  const [loggedIn, setLoggedIn] = useState<boolean>(
    !!localStorage.getItem("admin_token"),
  );

  const handleLogout = (): void => {
    localStorage.removeItem("admin_token");
    setLoggedIn(false);
  };

  if (!loggedIn) {
    // return <Login onLogin={() => setLoggedIn(true)} />;
  }

  return (
    <div className="bg-[#0a0e1a] text-[#e0e8f0] h-screen overflow-hidden flex font-body dark">
      {/* Sidebar */}
      <Sidebar tab={tab} setTab={setTab} onLogout={handleLogout} />

      {/* Main content */}
      <main
        className="
        flex-1 md:ml-64
        overflow-auto custom-scrollbar
        p-6
      "
      >
        {tab === "users" && <Users />}
        {tab === "live" && <LiveFeed />}
        {tab === "stats" && <Statistics />}
        {tab === "alerts" && <Alerts />}
      </main>
    </div>
  );
}
