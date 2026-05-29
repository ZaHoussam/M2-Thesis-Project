import { useEffect, useState, type JSX } from "react";
import axios from "axios";
import type { UserEntry } from "../types";
import { FaRegCheckCircle } from "react-icons/fa";
import {
  MdOutlineRemoveCircleOutline,
  MdVerified,
  MdDeleteOutline,
} from "react-icons/md";
import { IoSearchSharp } from "react-icons/io5";
import { GoBlocked } from "react-icons/go";
import { IoIosArrowDropleft } from "react-icons/io";
import { GrGroup } from "react-icons/gr";

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
    await axios.put(`${API}/users/${id}/status`, { is_active: !current });
    fetchUsers();
  };

  const deleteUser = async (id: number, name: string): Promise<void> => {
    if (!window.confirm(`Delete ${name} permanently?`)) return;
    await axios.delete(`${API}/users/${id}`);
    fetchUsers();
  };

  const filtered = users.filter(
    (u) =>
      u.full_name.toLowerCase().includes(search.toLowerCase()) ||
      u.email.toLowerCase().includes(search.toLowerCase()),
  );

  const totalPages = Math.ceil(filtered.length / ITEMS_PER_PAGE);
  const paginated = filtered.slice(
    (page - 1) * ITEMS_PER_PAGE,
    page * ITEMS_PER_PAGE,
  );

  const activeCount = users.filter((u) => u.is_active).length;
  const inactiveCount = users.filter((u) => !u.is_active).length;

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
          <IoSearchSharp className="absolute left-3 top-1/2 -translate-y-1/2 text-[#a0b4c4] text-[18px]" />
          <input
            type="text"
            placeholder="Search users..."
            value={search}
            onChange={(e) => {
              setSearch(e.target.value);
              setPage(1);
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
            icon: <GrGroup className="text-[30px]" />,
            color: "text-primary",
          },
          {
            label: "Active",
            value: activeCount,
            icon: <MdVerified className="text-[30px]" />,
            color: "text-[#1D9E75]",
          },
          {
            label: "Inactive",
            value: inactiveCount,
            icon: <GoBlocked className="text-[30px]" />,
            color: "text-[#ff6b6b]",
          },
        ].map((card) => (
          <div
            key={card.label}
            className="glass-panel rounded-lg p-4 flex items-center gap-4"
          >
            <div className="w-10 h-10 rounded-lg bg-primary/10 flex items-center justify-center">
              <span className={`material-symbols-outlined ${card.color}`}>
                {card.icon}
              </span>
            </div>
            <div className="flex flex-col">
              <p className="text-2xl font-bold text-[#e0e8f0] font-mono">
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
      <div className="glass-elevated rounded-xl flex flex-col flex-1 overflow-hidden">
        {/* Table */}
        <div className="overflow-auto custom-scrollbar flex-1">
          {loading ? (
            <div className="flex items-center justify-center h-40 text-[#a0b4c4] text-sm">
              Loading users...
            </div>
          ) : paginated.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-40 gap-2">
              <p className="text-[#a0b4c4] text-[20px]">No users found</p>
            </div>
          ) : (
            <table className="w-full">
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
              <tbody>
                {paginated.map((u: UserEntry) => (
                  <tr
                    key={u.id}
                    className="border-b border-[#2a3a48]/30 hover:bg-[#181818] transition-colors"
                  >
                    {/* UID */}
                    <td className="px-6 py-4 font-mono text-xs text-primary">
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
                        <span className="text-sm font-semibold text-[#e0e8f0]">
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
                          <FaRegCheckCircle className="text-[16px]" />
                          <span className="text-xs font-medium">Stored</span>
                        </div>
                      ) : (
                        <div className="flex items-center gap-1.5 text-[#a0b4c4]">
                          <MdOutlineRemoveCircleOutline className="text-[16px]" />
                          <span className="text-xs font-medium">Pending</span>
                        </div>
                      )}
                    </td>

                    {/* Attempts */}
                    <td className="px-6 py-4 text-sm font-mono text-[#a0b4c4]">
                      {u.total_attempts}
                    </td>

                    {/* Last seen */}
                    <td className="px-6 py-4 text-xs text-[#a0b4c4]">
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
                            : "bg-[#ff6b6b]/10 text-[#ff6b6b] border-[#ff6b6b]/20"
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
                          <MdDeleteOutline className="text-[18px]" />
                        </button>
                      </div>
                    </td>
                  </tr>
                ))}
              </tbody>
            </table>
          )}
        </div>

        {/* Pagination */}
        <div
          className="
          px-6 py-4 border-t border-[#2a3a48]/30
          flex items-center justify-between
          bg-[#141c2e]/30
        "
        >
          <span className="text-xs text-[#a0b4c4]">
            Showing {Math.min((page - 1) * ITEMS_PER_PAGE + 1, filtered.length)}
            –{Math.min(page * ITEMS_PER_PAGE, filtered.length)} of{" "}
            {filtered.length} users
          </span>
          <div className="flex items-center gap-2">
            <button
              onClick={() => setPage((p) => Math.max(1, p - 1))}
              disabled={page === 1}
              className="
                p-1 rounded-lg border border-[#2a3a48]
                text-[#a0b4c4] hover:bg-primary/10 hover:text-primary
                transition-all disabled:opacity-30 disabled:cursor-not-allowed
              "
            >
              <IoIosArrowDropleft className="text-[25px]" />
            </button>

            {Array.from(
              { length: Math.min(totalPages, 5) },
              (_, i) => i + 1,
            ).map((p) => (
              <button
                key={p}
                onClick={() => setPage(p)}
                className={`
                  w-8 h-8 rounded-lg text-xs font-bold transition-all
                  ${
                    page === p
                      ? "bg-primary/10 text-primary border border-primary/30"
                      : "text-[#a0b4c4] hover:bg-primary/5"
                  }
                `}
              >
                {p}
              </button>
            ))}

            <button
              onClick={() => setPage((p) => Math.min(totalPages, p + 1))}
              disabled={page === totalPages || totalPages === 0}
              className="
                p-1 rounded-lg border border-[#2a3a48]
                text-[#a0b4c4] hover:bg-primary/10 hover:text-primary
                transition-all disabled:opacity-30 disabled:cursor-not-allowed
              "
            >
              <IoIosArrowDropleft className="text-[25px] rotate-180" />
            </button>
          </div>
        </div>
      </div>
    </div>
  );
}
