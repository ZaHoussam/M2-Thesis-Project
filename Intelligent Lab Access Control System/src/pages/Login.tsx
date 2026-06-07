// ================================================================
//  pages/Login.tsx — Admin login page
//  Design: matches Login-Screen.html exactly
// ================================================================
import { useState, type FormEvent, type JSX } from "react";
import axios from "axios";
import {
  Mail,
  LockKeyhole,
  EyeOff,
  Eye,
  Shield,
  LoaderCircle,
} from "lucide-react";

const API = "http://localhost:8000";

// ── Credentials — update here if needed ──────────────────────────
const ADMIN_EMAIL = "mrlhou62@gmail.com";
const ADMIN_PASSWORD = "mrlhou2001";

interface LoginProps {
  onLogin: () => void;
}

export default function Login({ onLogin }: LoginProps): JSX.Element {
  const [email, setEmail] = useState<string>("");
  const [password, setPassword] = useState<string>("");
  const [showPass, setShowPass] = useState<boolean>(false);
  const [error, setError] = useState<string>("");
  const [loading, setLoading] = useState<boolean>(false);

  const handleSubmit = async (e: FormEvent): Promise<void> => {
    e.preventDefault();
    setError("");
    setLoading(true);

    try {
      const resp = await axios.post(`${API}/admin/login`, { email, password });
      if (resp.data.success) {
        localStorage.setItem("admin_token", resp.data.token);
        onLogin();
      } else {
        setError("Invalid credentials. Access denied.");
      }
    } catch {
      if (email === ADMIN_EMAIL && password === ADMIN_PASSWORD) {
        onLogin();
      } else {
        setError("Invalid credentials. Access denied.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div
      className="min-h-screen flex items-center justify-center p-10 font-body"
      style={{
        background: "#0f0f0f",
        backgroundImage:
          "radial-gradient(circle at 50% 0%, rgba(125,211,252,0.06) 0%, transparent 50%)",
      }}
    >
      {/* Card */}
      <div
        className="w-full flex flex-col justify-center"
        style={{
          maxWidth: "550px",
          height: "500px",
          background: "rgba(26,26,26,0.6)",
          backdropFilter: "blur(24px)",
          WebkitBackdropFilter: "blur(24px)",
          border: "1px solid rgba(125,211,252,0.2)",
          boxShadow: "0 0 40px rgba(125,211,252,0.1)",
          borderRadius: "16px",
          padding: "40px",
        }}
      >
        {/* ── Header ─────────────────────────────────────────── */}
        <div className="flex flex-col items-center text-center mb-7">
          <div className="flex items-center justify-center gap-3 mb-1.5">
            {/* Pulsing live dot */}
            <span className="relative inline-flex w-3.5 h-3.5">
              <span
                className="absolute inset-0 rounded-full bg-primary opacity-70"
                style={{
                  animation: "ping 1.5s cubic-bezier(0,0,0.2,1) infinite",
                }}
              />
              <span className="relative inline-block w-3.5 h-3.5 rounded-full bg-primary" />
            </span>
            <h1 className="text-[22px] font-bold text-[#e0e8f0] tracking-tight">
              Lab Access Control
            </h1>
          </div>
          <p className="text-[13px] text-[#a0b4c4]">Admin Portal</p>
        </div>

        {/* ── Form ───────────────────────────────────────────── */}
        <form onSubmit={handleSubmit} className="flex flex-col gap-3.5 mb-5">
          {/* Email */}
          <div className="relative">
            <Mail
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[#a0b4c4]"
            />
            <input
              type="email"
              placeholder="Enter admin email"
              value={email}
              onChange={(e) => setEmail(e.target.value)}
              required
              className={`w-full rounded-[10px] py-[13px] pl-[44px] pr-4 text-[14px] text-[${error ? "#ff6b6b" : "#7dd3fc"}] placeholder-[#a0b4c4]/50 outline-none transition-all`}
              style={{
                background: "rgba(10,14,26,0.5)",
                border: error
                  ? "1px solid rgba(255,107,107,0.5)"
                  : "1px solid rgba(125,211,252,0.15)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.border =
                  "1px solid rgba(125,211,252,0.5)";
                e.currentTarget.style.boxShadow =
                  "0 0 15px rgba(125,211,252,0.1)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.border = error
                  ? "1px solid rgba(255,107,107,0.5)"
                  : "1px solid rgba(125,211,252,0.15)";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
          </div>

          {/* Password */}
          <div className="relative">
            <LockKeyhole
              size={18}
              className="absolute left-3 top-1/2 -translate-y-1/2 text-[#a0b4c4]"
            />
            <input
              type={showPass ? "text" : "password"}
              placeholder="Enter password"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
              className={`w-full rounded-[10px] py-[13px] pl-[44px] pr-11 text-[14px] text-[${error ? "#ff6b6b" : "#7dd3fc"}] placeholder-[#a0b4c4]/50 outline-none transition-all`}
              style={{
                background: "rgba(10,14,26,0.5)",
                border: error
                  ? "1px solid rgba(255,107,107,0.5)"
                  : "1px solid rgba(125,211,252,0.15)",
              }}
              onFocus={(e) => {
                e.currentTarget.style.border =
                  "1px solid rgba(125,211,252,0.5)";
                e.currentTarget.style.boxShadow =
                  "0 0 15px rgba(125,211,252,0.1)";
              }}
              onBlur={(e) => {
                e.currentTarget.style.border = error
                  ? "1px solid rgba(255,107,107,0.5)"
                  : "1px solid rgba(125,211,252,0.15)";
                e.currentTarget.style.boxShadow = "none";
              }}
            />
            {/* Show/hide toggle */}
            <button
              type="button"
              onClick={() => setShowPass((p) => !p)}
              className="absolute right-3 top-1/2 -translate-y-1/2 text-[#a0b4c4] hover:text-[#e0e8f0] transition-colors cursor-pointer"
            >
              {showPass ? (
                <Eye size={18} className="text-[#a0b4c4]" />
              ) : (
                <EyeOff size={18} className="text-[#a0b4c4]" />
              )}
            </button>
          </div>

          {/* Error message */}
          {error && (
            <div className="flex items-center justify-center gap-1.5 text-[#ff6b6b] text-[15px] capitalize">
              {error}
            </div>
          )}

          {/* Submit button */}
          <button
            type="submit"
            disabled={loading}
            className="w-full rounded-[10px] py-[13px] text-[18px] font-bold transition-all active:scale-[0.98] disabled:opacity-60 disabled:cursor-not-allowed text-[#7dd3fc] cursor-pointer flex items-center justify-center gap-2 tracking-wide"
            style={{
              background: "rgba(125,211,252,0.15)",
              border: "1px solid rgba(125,211,252,0.3)",
            }}
            onMouseEnter={(e) => {
              if (!loading) {
                (e.currentTarget as HTMLButtonElement).style.background =
                  "rgba(125,211,252,0.25)";
                (e.currentTarget as HTMLButtonElement).style.borderColor =
                  "rgba(125,211,252,0.5)";
              }
            }}
            onMouseLeave={(e) => {
              (e.currentTarget as HTMLButtonElement).style.background =
                "rgba(125,211,252,0.15)";
              (e.currentTarget as HTMLButtonElement).style.borderColor =
                "rgba(125,211,252,0.3)";
            }}
          >
            {loading ? <LoaderCircle className="animate-spin" /> : "Sign In"}
          </button>
        </form>

        {/* ── Footer ─────────────────────────────────────────── */}
        <div className="flex items-center justify-center gap-1.5 text-[11px] text-[#a0b4c4]/80">
          <Shield size={14} />
          Secure access — authorized personnel only
        </div>
      </div>

      {/* Ping keyframe */}
      <style>{`
        @keyframes ping {
          75%, 100% { transform: scale(2); opacity: 0; }
        }
      `}</style>
    </div>
  );
}
