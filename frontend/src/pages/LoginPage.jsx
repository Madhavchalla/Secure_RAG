import React, { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import { Shield, Lock, UserCheck, AlertCircle } from "lucide-react";

export default function LoginPage() {
  const [username, setUsername] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState(null);
  const [loading, setLoading] = useState(false);
  const { login } = useAuth();
  const navigate = useNavigate();

  const handleSubmit = async (e) => {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const user = await login(username, password);
      if (user.role === "admin") {
        navigate("/admin/dashboard");
      } else {
        navigate("/chat");
      }
    } catch (err) {
      setError(err.message || "Authentication failed.");
    } finally {
      setLoading(false);
    }
  };

  const handleQuickLogin = (user, pass) => {
    setUsername(user);
    setPassword(pass);
  };

  return (
    <div style={{ display: "flex", minHeight: "100vh", backgroundColor: "#f8fafc" }}>
      {/* Left Feature Showcase */}
      <div style={{ flex: 1, backgroundColor: "#0f172a", color: "#ffffff", padding: "64px", display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
        <div>
          <div style={{ display: "flex", alignItems: "center", gap: "12px", marginBottom: "32px" }}>
            <div style={{ background: "#2563eb", padding: "10px", borderRadius: "10px" }}>
              <Shield size={28} color="#ffffff" />
            </div>
            <div>
              <h1 style={{ fontSize: "1.45rem", fontWeight: 700, letterSpacing: "-0.02em" }}>RAS-RAG</h1>
              <p style={{ fontSize: "0.82rem", color: "#94a3b8" }}>Risk-Aware Secure Retrieval-Augmented Generation</p>
            </div>
          </div>

          <div style={{ maxWidth: "480px" }}>
            <h2 style={{ fontSize: "1.85rem", fontWeight: 700, lineHeight: 1.3, marginBottom: "16px", color: "#f8fafc" }}>
              Privacy-Preserving Document Intelligence with Active Risk Scoring
            </h2>
            <p style={{ fontSize: "0.95rem", color: "#94a3b8", lineHeight: 1.6, marginBottom: "32px" }}>
              A zero-trust AI assistant that enforces pre-retrieval access control, intercepts document-based prompt injections, and dynamically adapts security postures based on composite risk telemetry.
            </p>

            <div style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div style={{ display: "flex", gap: "14px", alignItems: "flex-start" }}>
                <div style={{ background: "rgba(5, 150, 105, 0.15)", padding: "6px", borderRadius: "6px", marginTop: "2px" }}>
                  <Shield size={16} color="#34d399" />
                </div>
                <div>
                  <strong style={{ fontSize: "0.88rem", color: "#e2e8f0" }}>Pre-Retrieval Authorization (MAC)</strong>
                  <p style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Unauthorized document chunks never reach cosine similarity or the LLM context.</p>
                </div>
              </div>

              <div style={{ display: "flex", gap: "14px", alignItems: "flex-start" }}>
                <div style={{ background: "rgba(217, 119, 6, 0.15)", padding: "6px", borderRadius: "6px", marginTop: "2px" }}>
                  <Lock size={16} color="#fbbf24" />
                </div>
                <div>
                  <strong style={{ fontSize: "0.88rem", color: "#e2e8f0" }}>Heuristic Ingestion Quarantine</strong>
                  <p style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Documents containing adversarial jailbreak instructions are automatically quarantined.</p>
                </div>
              </div>

              <div style={{ display: "flex", gap: "14px", alignItems: "flex-start" }}>
                <div style={{ background: "rgba(79, 70, 229, 0.15)", padding: "6px", borderRadius: "6px", marginTop: "2px" }}>
                  <UserCheck size={16} color="#818cf8" />
                </div>
                <div>
                  <strong style={{ fontSize: "0.88rem", color: "#e2e8f0" }}>Adaptive Four-Tier Policy</strong>
                  <p style={{ fontSize: "0.8rem", color: "#94a3b8" }}>Transparent mathematical decisions: ALLOW, RESTRICT, VERIFY, and BLOCK.</p>
                </div>
              </div>
            </div>
          </div>
        </div>

        <div style={{ fontSize: "0.78rem", color: "#64748b" }}>
          Final-Year Engineering Project • Local AI Architecture • Zero Cloud Leakage
        </div>
      </div>

      {/* Right Login Form */}
      <div style={{ width: "480px", display: "flex", alignItems: "center", justifyContent: "center", padding: "48px" }}>
        <div style={{ width: "100%", maxWidth: "360px" }}>
          <h2 style={{ fontSize: "1.45rem", fontWeight: 700, color: "var(--text-main)", marginBottom: "6px" }}>
            Sign In to Console
          </h2>
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", marginBottom: "24px" }}>
            Enter your credentials to access authorized repositories.
          </p>

          {error && (
            <div style={{ background: "#fef2f2", border: "1px solid #fecaca", borderRadius: "8px", padding: "12px", display: "flex", alignItems: "center", gap: "10px", marginBottom: "20px" }}>
              <AlertCircle size={18} color="#dc2626" />
              <span style={{ fontSize: "0.82rem", color: "#b91c1c" }}>{error}</span>
            </div>
          )}

          <form onSubmit={handleSubmit} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
            <div>
              <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "6px" }}>
                Username
              </label>
              <input
                type="text"
                className="input"
                placeholder="e.g. admin or analyst"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
              />
            </div>

            <div>
              <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "6px" }}>
                Password
              </label>
              <input
                type="password"
                className="input"
                placeholder="••••••••••••"
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                required
              />
            </div>

            <button
              type="submit"
              className="btn btn-primary"
              disabled={loading}
              style={{ marginTop: "8px", padding: "10px" }}
            >
              {loading ? "Authenticating..." : "Sign In securely"}
            </button>
          </form>

          {/* Quick Demo Fill Buttons */}
          <div style={{ marginTop: "32px", paddingTop: "20px", borderTop: "1px solid var(--border-light)" }}>
            <span style={{ display: "block", fontSize: "0.75rem", fontWeight: 600, color: "var(--text-muted)", textTransform: "uppercase", letterSpacing: "0.04em", marginBottom: "10px" }}>
              Viva Demonstration Credentials
            </span>
            <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
              <button
                type="button"
                onClick={() => handleQuickLogin("admin", "AdminSecure@2026")}
                className="btn btn-secondary"
                style={{ fontSize: "0.78rem", justifyContent: "flex-start", padding: "8px 12px" }}
              >
                <span className="badge badge-restrict" style={{ fontSize: "0.65rem", padding: "2px 6px" }}>Admin</span>
                <span style={{ color: "var(--text-secondary)" }}>admin / AdminSecure@2026</span>
              </button>
              <button
                type="button"
                onClick={() => handleQuickLogin("analyst", "UserSecure@2026")}
                className="btn btn-secondary"
                style={{ fontSize: "0.78rem", justifyContent: "flex-start", padding: "8px 12px" }}
              >
                <span className="badge badge-low" style={{ fontSize: "0.65rem", padding: "2px 6px" }}>User</span>
                <span style={{ color: "var(--text-secondary)" }}>analyst / UserSecure@2026</span>
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
