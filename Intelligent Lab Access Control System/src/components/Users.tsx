// ================================================================
//  Users.tsx — user management tab
// ================================================================
import { useEffect, useState } from "react";
import axios from "axios";
import type { UserEntry } from "../types";

const API = "http://localhost:8000";

export default function Users(): JSX.Element {
  const [users, setUsers] = useState<UserEntry[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  const fetchUsers = async (): Promise<void> => {
    try {
      const res = await axios.get<UserEntry[]>(`${API}/users`);
      setUsers(res.data);
    } catch (e) {
      console.error("Failed to fetch users:", e);
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
      fetchUsers();
    } catch (e) {
      console.error("Failed to update status:", e);
    }
  };

  const deleteUser = async (id: number, name: string): Promise<void> => {
    if (!window.confirm(`Delete ${name} permanently?`)) return;
    try {
      await axios.delete(`${API}/users/${id}`);
      fetchUsers();
    } catch (e) {
      console.error("Failed to delete user:", e);
    }
  };

  if (loading) return <div className="loading">Loading users...</div>;

  return (
    <div className="panel">
      <div className="panel-header">
        <h2>Registered Users</h2>
        <span className="count">{users.length} total</span>
      </div>

      {users.length === 0 ? (
        <div className="empty">No users registered yet.</div>
      ) : (
        <table className="table">
          <thead>
            <tr>
              <th>ID</th>
              <th>Name</th>
              <th>Email</th>
              <th>Role</th>
              <th>Embeddings</th>
              <th>Attempts</th>
              <th>Last Seen</th>
              <th>Status</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody>
            {users.map((u: UserEntry) => (
              <tr key={u.id}>
                <td>{u.id}</td>
                <td>
                  <strong>{u.full_name}</strong>
                </td>
                <td>{u.email}</td>
                <td>
                  <span className="role-badge">{u.role}</span>
                </td>
                <td>{u.embedding_count}</td>
                <td>{u.total_attempts}</td>
                <td>
                  {u.last_seen
                    ? new Date(u.last_seen).toLocaleString()
                    : "Never"}
                </td>
                <td>
                  <span
                    className={`status-badge ${u.is_active ? "active" : "inactive"}`}
                  >
                    {u.is_active ? "Active" : "Inactive"}
                  </span>
                </td>
                <td className="actions">
                  <button
                    className={`btn-sm ${u.is_active ? "btn-warn" : "btn-ok"}`}
                    onClick={() => toggleStatus(u.id, u.is_active)}
                  >
                    {u.is_active ? "Deactivate" : "Activate"}
                  </button>
                  <button
                    className="btn-sm btn-danger"
                    onClick={() => deleteUser(u.id, u.full_name)}
                  >
                    Delete
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      )}
    </div>
  );
}
