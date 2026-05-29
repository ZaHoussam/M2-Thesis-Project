// ================================================================
//  Sidebar.tsx — left navigation panel
// ================================================================
import type { Tab } from "../types";
import type { JSX, ReactNode } from "react";
import { LuUsers, LuShieldAlert } from "react-icons/lu";
import { GoDeviceCameraVideo } from "react-icons/go";
import { RiLogoutCircleLine } from "react-icons/ri";
import { RiBarChartFill } from "react-icons/ri";

interface SidebarProps {
  tab: Tab;
  setTab: (t: Tab) => void;
  onLogout: () => void;
}

interface NavItem {
  id: Tab;
  icon: ReactNode;
  label: string;
}

const NAV_ITEMS: NavItem[] = [
  { id: "users", icon: <LuUsers />, label: "Users" },
  { id: "live", icon: <GoDeviceCameraVideo />, label: "Live Feed" },
  { id: "stats", icon: <RiBarChartFill />, label: "Statistics" },
  { id: "alerts", icon: <LuShieldAlert />, label: "Security Alerts" },
];

export default function Sidebar({
  tab,
  setTab,
  onLogout,
}: SidebarProps): JSX.Element {
  return (
    <nav
      className="
      fixed h-full left-0 w-64
      bg-[#111828]/60 backdrop-blur-2xl
      text-primary font-body
      border-r border-primary/10 shadow-2xl
      flex flex-col p-4 gap-2 z-40
      hidden md:flex
    "
    >
      {/* Brand */}
      <div className="mb-8 mt-2 px-2">
        <div className="flex items-center gap-3 mb-1">
          <span className="relative flex h-3 w-3">
            <span className="animate-ping absolute inline-flex h-full w-full rounded-full bg-primary opacity-75" />
            <span className="relative inline-flex rounded-full h-3 w-3 bg-primary" />
          </span>
          <h1 className="text-xl font-bold text-primary tracking-tight">
            Glacier Lab
          </h1>
        </div>
        <p className="text-sm text-[#a0b4c4] font-normal pl-6">System v2.0</p>
      </div>

      {/* Nav items */}
      <div className="flex-1 flex flex-col gap-2">
        {NAV_ITEMS.map((item) => (
          <button
            key={item.id}
            onClick={() => setTab(item.id)}
            className={`
              flex items-center gap-3 rounded-lg px-4 py-3
              transition-all active:translate-x-1 duration-150
              text-sm font-medium w-full text-left cursor-pointer
              ${
                tab === item.id
                  ? "bg-primary/15 text-primary border border-primary/20"
                  : "text-[#a0b4c4] hover:text-[#e0e8f0] hover:bg-[#202c42]/50"
              }
            `}
          >
            <span
              className="material-symbols-outlined text-[20px]"
              style={{
                fontVariationSettings:
                  tab === item.id ? "'FILL' 1" : "'FILL' 0",
              }}
            >
              {item.icon}
            </span>
            {item.label}
          </button>
        ))}
      </div>

      {/* Bottom — logout */}
      <div className="mt-auto flex flex-col gap-3">
        <div className="px-2 py-3 rounded-lg border border-[#2a3a48] bg-[#0f1524]/50">
          <p className="text-xs text-[#a0b4c4] mb-1">Logged in as</p>
          <p className="text-sm font-semibold text-[#e0e8f0]">Admin</p>
        </div>
        <button
          onClick={onLogout}
          className="
            w-full py-3 px-4 rounded-lg
            border border-[#ff6b6b]/30 text-[#ff6b6b]
            hover:bg-[#ff6b6b]/10 transition-colors
            flex justify-center items-center gap-2
            text-sm font-semibold
            cursor-pointer
          "
        >
          <RiLogoutCircleLine className="text-[18px]" />
          Sign Out
        </button>
      </div>
    </nav>
  );
}
