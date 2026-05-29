// ================================================================
//  pages/Login.tsx — Admin login page
//  Design: glassmorphism dark theme from Stitch
// ================================================================
import { useState, FormEvent } from "react";
import axios from "axios";

const API = "http://localhost:8000";

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
      // For now — accept any login until backend auth is built
      if (email && password) {
        onLogin();
      } else {
        setError("Invalid credentials. Access denied.");
      }
    } finally {
      setLoading(false);
    }
  };

  return (
    <div className="login-root">
      {/* Ambient glow */}
      <div className="login-glow" />

      {/* Card */}
      <main className="login-card-wrap">
        <div className="glass-panel">
          {/* Header */}
          <header className="login-header">
            <div className="login-title-row">
              <span className="live-dot-wrap">
                <span className="live-dot-ping" />
                <span className="live-dot-core" />
              </span>
              <h1 className="login-title">Lab Access Control</h1>
            </div>
            <p className="login-subtitle">Admin Portal</p>
          </header>

          {/* Form */}
          <form className="login-form" onSubmit={handleSubmit}>
            {/* Email */}
            <div className="input-wrap">
              <span className="material-symbols-outlined input-icon">mail</span>
              <input
                className={`input-glass ${error ? "input-error" : ""}`}
                id="email"
                type="email"
                placeholder="Enter admin email"
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                required
              />
            </div>

            {/* Password */}
            <div className="input-wrap">
              <span className="material-symbols-outlined input-icon">lock</span>
              <input
                className={`input-glass ${error ? "input-error" : ""}`}
                id="password"
                type={showPass ? "text" : "password"}
                placeholder="Enter password"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
              <button
                type="button"
                className="input-eye"
                onClick={() => setShowPass((p) => !p)}
              >
                <span className="material-symbols-outlined">
                  {showPass ? "visibility" : "visibility_off"}
                </span>
              </button>
            </div>

            {/* Error message */}
            {error && (
              <div className="login-error">
                <span className="material-symbols-outlined">error</span>
                <span>{error}</span>
              </div>
            )}

            {/* Submit */}
            <button type="submit" className="login-btn" disabled={loading}>
              {loading ? "Signing in..." : "Sign In"}
            </button>
          </form>

          {/* Footer */}
          <footer className="login-footer">
            <span className="material-symbols-outlined">shield</span>
            Secure access — authorized personnel only
          </footer>
        </div>
      </main>
    </div>
  );
}
