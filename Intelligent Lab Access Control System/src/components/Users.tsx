import { useEffect, useState, type JSX } from "react";
import axios from "axios";
import type { UserEntry } from "../types";
import { MdOutlinePending } from "react-icons/md";
import { IoIosArrowDropleft } from "react-icons/io";
import { GrGroup } from "react-icons/gr";
import { Trash, Ban, ShieldCheck, Search, CircleCheck } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";

const API = "http://localhost:8000";
const ITEMS_PER_PAGE = 10;

function getInitials(name: string): string {
  return name
    .split(" ")
    .map((n) => n[0])
    .join("")
    .toUpperCase()
    .slice(0, 2);
}

function timeAgo(dateStr: string | null): string {
  if (!dateStr) return "Never";
  const diff = Date.now() - new Date(dateStr).getTime();
  const mins = Math.floor(diff / 60000);
  const hours = Math.floor(mins / 60);
  const days = Math.floor(hours / 24);
  if (days > 0) return `${days}d ago`;
  if (hours > 0) return `${hours}h ago`;
  if (mins > 0) return `${mins}m ago`;
  return "Just now";
}

export default function Users(): JSX.Element {
  const [users, setUsers] = useState<UserEntry[]>([]);
  const [search, setSearch] = useState<string>("");
  const [page, setPage] = useState<number>(1);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchUsers = async (): Promise<void> => {
    try {
      const res = await axios.get<UserEntry[]>(`${API}/users`);
      setUsers(res.data);
    } catch (e) {
      console.error(e);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchUsers();
  }, []);

  const toggleStatus = async (id: number, current: boolean): Promise<void> => {
    try {
      await axios.put(`${API}/users/${id}/status`, { is_active: !current });
      await fetchUsers();
    } catch (e) {
      console.error(e);
    }
  };

  const deleteUser = async (id: number, name: string): Promise<void> => {
    if (!window.confirm(`Delete ${name} permanently?`)) return;
    try {
      await axios.delete(`${API}/users/${id}`);
      await fetchUsers();
    } catch (e) {
      console.error(e);
    }
  };

  // ── Search & Filter Logic ───────────────────────────────────────
  const filtered = users.filter(
    (u) =>
      u.full_name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()),
  );

  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE) || 1;

  // Guard current page from going out of bounds if rows are filtered or deleted
  const currentPage = Math.min(page, totalPages);

  const paginated = filtered.slice(
    (currentPage - 1) * ITEMS_PER_PAGE,
    currentPage * ITEMS_PER_PAGE,
  );

  const activeCount = users.filter((u) => u.is_active).length;
  const inactiveCount = users.filter((u) => !u.is_active).length;

  // ── Smart Truncated Pagination Logic (Max 4 Items) ──────────────
  const getPaginationRange = (): (number | string)[] => {
    if (totalPages <= 4) {
      return Array.from({ length: totalPages }, (_, i) => i + 1);
    }

    // Near the beginning: [1, 2, 3, '...']
    if (currentPage <= 2) {
      return [1, 2, 3, "..."];
    }

    // Near the end: ['...', totalPages - 2, totalPages - 1, totalPages]
    if (currentPage >= totalPages - 1) {
      return ["...", totalPages - 2, totalPages - 1, totalPages];
    }

    // In the middle: ['...', currentPage, currentPage + 1, '...']
    return ["...", currentPage, currentPage + 1, "..."];
  };

  return (
    <div className="flex flex-col gap-6 h-full">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h2 className="text-2xl font-bold text-[#e0e8f0] tracking-tight">
            Registered Users
          </h2>
          <p className="text-sm text-[#a0b4c4] mt-1">
            Manage enrolled lab members and access permissions
          </p>
        </div>
        <div className="relative">
          <Search
            size={18}
            className="absolute left-3 top-1/2 -translate-y-1/2 text-[#a0b4c4]"
          />
          <input
            type="text"
            placeholder="Search users..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1); // Reset to first page on search typing
            }}
            className="
                bg-[#0f1524]/50 border border-[#2a3a48]
                rounded-lg pl-9 pr-4 py-2
                text-sm text-[#e0e8f0]
                placeholder-[#a0b4c4]/50
                focus:outline-none focus:border-primary/40
                transition-colors w-56
              "
          />
        </div>
      </div>

      {/* Stat cards */}
      <div className="grid grid-cols-3 gap-4">
        {[
          {
            label: "Total Users",
            value: users.length,
            icon: <GrGroup className="text-[25px]" />,
            color: "#7dd3fc",
            iconBg: "#7dd3fc1a",
            borderColor: "#7dd3fc14",
          },
          {
            label: "Active",
            value: activeCount,
            icon: <ShieldCheck size={25} />,
            color: "#34d399",
            iconBg: "#34d3991a",
            borderColor: "#34d39926",
          },
          {
            label: "Inactive",
            value: inactiveCount,
            icon: <Ban size={25} />,
            color: "#ff6b6b",
            iconBg: "#ff6b6b1a",
            borderColor: "#ff6b6b26",
          },
        ].map((card) => (
          <div
            key={card.label}
            className="glass-panel rounded-lg p-4 flex items-center gap-4 bg-[#0f152480] border"
            style={{ borderColor: card.borderColor }}
          >
            <div
              className="w-10 h-10 rounded-lg flex items-center justify-center"
              style={{ backgroundColor: card.iconBg }}
            >
              <span className="p-[10px]" style={{ color: card.color }}>
                {card.icon}
              </span>
            </div>
            <div className="flex flex-col gap-3">
              <p
                className="text-5xl font-bold font-mono"
                style={{ color: card.color }}
              >
                {card.value.toString().padStart(2, "0")}
              </p>
              <p className="text-xs text-[#a0b4c4] font-bold uppercase tracking-wider">
                {card.label}
              </p>
            </div>
          </div>
        ))}
      </div>

      {/* Table card */}
      <div className="glass-elevated rounded-xl flex flex-col overflow-hidden bg-[#141c2e99] border border-[#7dd3fc1f]">
        {/* Table Wrapper — No vertical scrollbar */}
        <div className="overflow-x-auto overflow-y-hidden custom-scrollbar">
          {loading ? (
            <div className="flex items-center justify-center h-40 text-[#a0b4c4] text-sm">
              Loading users...
            </div>
          ) : paginated.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 gap-2">
              <p className="text-[#a0b4c4] text-[20px]">No users found</p>
            </div>
          ) : (
            <table className="w-full overflow-hidden">
              <thead>
                <tr className="border-b border-[#2a3a48]/50">
                  {[
                    "UID",
                    "Name",
                    "Email",
                    "Role",
                    "Embedding",
                    "Attempts",
                    "Last Seen",
                    "Status",
                    "Actions",
                  ].map((h) => (
                    <th
                      key={h}
                      className="
                        px-6 py-3 text-left
                        text-xs font-semibold text-[#a0b4c4]
                        uppercase tracking-wider
                      "
                    >
                      {h}
                    </th>
                  ))}
                </tr>
              </thead>
              <AnimatePresence mode="wait">
                <motion.tbody
                  key={currentPage}
                  initial={{ opacity: 0, x: 15 }}
                  animate={{ opacity: 1, x: 0 }}
                  exit={{ opacity: 0, x: -15 }}
                  transition={{ duration: 0.2, ease: "easeInOut" }}
                >
                  {paginated.map((u: UserEntry, index: number) => (
                    <motion.tr
                      key={u.id}
                      initial={{ opacity: 0, y: 6 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.15, delay: index * 0.015 }}
                      className="border-b border-[#2a3a48]/30 hover:bg-[#141c2e] transition-colors"
                    >
                      {/* UID */}
                      <td className="px-6 py-4 font-mono text-xs text-[#7dd3fc]">
                        UID-{String(u.id).padStart(4, "0")}
                      </td>

                      {/* Name + avatar */}
                      <td className="px-6 py-4">
                        <div className="flex items-center gap-3">
                          <div
                            className="
                          w-8 h-8 rounded-full
                          bg-primary/20 border border-primary/30
                          flex items-center justify-center
                          text-xs text-primary font-bold
                          flex-shrink-0
                        "
                          >
                            {getInitials(u.full_name)}
                          </div>
                          <span className="text-sm font-semibold text-[#e0e8f0] whitespace-nowrap">
                            {u.full_name}
                          </span>
                        </div>
                      </td>

                      {/* Email */}
                      <td className="px-6 py-4 text-sm text-[#a0b4c4]">
                        {u.email}
                      </td>

                      {/* Role */}
                      <td className="px-6 py-4">
                        <span
                          className="
                        px-2 py-0.5 rounded-full
                        bg-primary/10 text-primary
                        text-[10px] font-bold uppercase tracking-wider
                        border border-primary/20
                      "
                        >
                          {u.role}
                        </span>
                      </td>

                      {/* Embedding */}
                      <td className="px-6 py-4">
                        {u.embedding_count > 0 ? (
                          <div className="flex items-center gap-1.5 text-[#1D9E75]">
                            <CircleCheck size={16} />
                            <span className="text-xs font-medium">Stored</span>
                          </div>
                        ) : (
                          <div className="flex items-center gap-1.5 text-[#a0b4c4]">
                            <MdOutlinePending className="text-[16px]" />
                            <span className="text-xs font-medium">Pending</span>
                          </div>
                        )}
                      </td>

                      {/* Attempts */}
                      <td className="px-6 py-4 text-sm font-mono text-[#a0b4c4]">
                        {u.total_attempts}
                      </td>

                      {/* Last seen */}
                      <td className="px-6 py-4 text-xs text-[#a0b4c4] whitespace-nowrap">
                        {timeAgo(u.last_seen)}
                      </td>

                      {/* Status */}
                      <td className="px-6 py-4">
                        <span
                          className={`
                        px-2 py-0.5 rounded-full
                        text-[10px] font-bold uppercase tracking-wider
                        border
                        ${
                          u.is_active
                            ? "bg-[#1D9E75]/10 text-[#1D9E75] border-[#1D9E75]/20"
                            : "bg-[#ff6b6b]/10 text-[#ff6b6b]/20 border-[#ff6b6b]/20"
                        }
                      `}
                        >
                          {u.is_active ? "Active" : "Inactive"}
                        </span>
                      </td>

                      {/* Actions */}
                      <td className="px-6 py-4 text-right">
                        <div className="flex items-center justify-end gap-3">
                          {/* Toggle switch */}
                          <label className="relative inline-flex items-center cursor-pointer">
                            <input
                              type="checkbox"
                              className="sr-only peer"
                              checked={u.is_active}
                              onChange={() => toggleStatus(u.id, u.is_active)}
                            />
                            <div
                              className="
                            w-10 h-5 rounded-full
                            bg-[#202c42]
                            peer-focus:outline-none
                            peer-checked:bg-[#1D9E75]
                            after:content-[''] after:absolute
                            after:top-[2px] after:left-[2px]
                            after:bg-[#e0e8f0] after:rounded-full
                            after:h-4 after:w-4 after:transition-all
                            peer-checked:after:translate-x-full
                            relative
                          "
                            />
                          </label>

                          {/* Delete */}
                          <button
                            onClick={() => deleteUser(u.id, u.full_name)}
                            className="text-[#a0b4c4] hover:text-[#ff6b6b] transition-colors cursor-pointer"
                          >
                            <Trash size={18} />
                          </button>
                        </div>
                      </td>
                    </motion.tr>
                  ))}
                </motion.tbody>
              </AnimatePresence>
            </table>
          )}
        </div>

        {/* Pagination Footer */}
        <div
          className="
          px-6 py-4 border-t border-[#2a3a48]/30
          flex items-center justify-between
          bg-[#141c2e]/30
        "
        >
          <span className="text-xs text-[#a0b4c4]">
            Showing{" "}
            {filtered.length === 0 ? 0 : (currentPage - 1) * ITEMS_PER_PAGE + 1}{" "}
            to {Math.min(currentPage * ITEMS_PER_PAGE, filtered.length)} of{" "}
            {filtered.length} users
          </span>

          {totalPages > 1 && (
            <div className="flex items-center gap-2">
              <button
                onClick={() => setPage((p) => Math.max(1, p - 1))}
                disabled={currentPage === 1}
                className="
                  p-1 rounded-lg border border-[#2a3a48]
                  text-[#a0b4c4] hover:enabled:bg-primary/10 hover:enabled:text-primary
                  transition-all disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer
                "
              >
                <IoIosArrowDropleft className="text-[25px]" />
              </button>

              {/* Responsive 4-slot layout with Ellipsis */}
              {getPaginationRange().map((p, idx) => {
                if (p === "...") {
                  return (
                    <span
                      key={`ellipsis-${idx}`}
                      className="text-[#a0b4c4] px-1.5 text-xs font-bold select-none"
                    >
                      ...
                    </span>
                  );
                }

                return (
                  <button
                    key={p}
                    onClick={() => setPage(p as number)}
                    className={`
                      w-8 h-8 rounded-lg text-xs font-bold transition-all cursor-pointer
                      ${
                        currentPage === p
                          ? "bg-primary/10 text-primary border border-primary/30"
                          : "text-[#a0b4c4] hover:bg-primary/5"
                      }
                    `}
                  >
                    {p}
                  </button>
                );
              })}

              <button
                onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
                disabled={currentPage === totalPages}
                className="
                  p-1 rounded-lg border border-[#2a3a48]
                  text-[#a0b4c4] hover:enabled:bg-primary/10 hover:enabled:text-primary
                  transition-all disabled:opacity-30 disabled:cursor-not-allowed cursor-pointer
                "
              >
                <IoIosArrowDropleft className="text-[25px] rotate-180" />
              </button>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
