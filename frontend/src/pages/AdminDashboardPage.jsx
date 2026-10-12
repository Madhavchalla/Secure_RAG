import React, { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import { api } from "../services/api";
import {
  FileText,
  AlertOctagon,
  MessageSquare,
  Lock,
  Shield,
  ArrowRight,
  AlertTriangle,
} from "lucide-react";
import {
  BarChart,
  Bar,
  XAxis,
  YAxis,
  Tooltip,
  ResponsiveContainer,
  Cell,
} from "recharts";

export default function AdminDashboardPage() {
  const [metrics, setMetrics] = useState(null);
  const [securityEvents, setSecurityEvents] = useState([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function loadData() {
      try {
        const [m, ev] = await Promise.all([
          api.admin.getMetrics(),
          api.audit.getSecurityEvents("?limit=6"),
        ]);
        setMetrics(m);
        setSecurityEvents(ev);
      } catch (err) {
        console.error("Dashboard error:", err);
      } finally {
        setLoading(false);
      }
    }
    loadData();
  }, []);

  if (loading) {
    return <div style={{ color: "var(--text-secondary)", padding: "24px" }}>Loading security telemetry...</div>;
  }

  const chartData = [
    { name: "ALLOW", count: metrics?.risk_distribution?.ALLOW || 0, color: "#059669" },
    { name: "RESTRICT", count: metrics?.risk_distribution?.RESTRICT || 0, color: "#d97706" },
    { name: "VERIFY", count: metrics?.risk_distribution?.VERIFY || 0, color: "#4f46e5" },
    { name: "BLOCK", count: metrics?.risk_distribution?.BLOCK || 0, color: "#dc2626" },
  ];

  return (
    <div>
      {/* Page Title */}
      <div style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "1.45rem", fontWeight: 700, color: "var(--text-main)" }}>
          Security Operations & Governance Console
        </h1>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
          System-wide risk telemetry, policy decision distributions, and quarantine management.
        </p>
      </div>

      {/* Metrics Row */}
      <div className="metrics-grid">
        <div className="metric-card">
          <div className="metric-icon-wrap" style={{ background: "#eff6ff", color: "#2563eb" }}>
            <FileText size={24} />
          </div>
          <div>
            <div className="metric-value">{metrics?.active_documents || 0}</div>
            <div className="metric-label">Active Documents</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-wrap" style={{ background: "#fffbeb", color: "#d97706" }}>
            <AlertOctagon size={24} />
          </div>
          <div>
            <div className="metric-value">{metrics?.quarantined_documents || 0}</div>
            <div className="metric-label">Quarantined Files</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-wrap" style={{ background: "#ecfdf5", color: "#059669" }}>
            <MessageSquare size={24} />
          </div>
          <div>
            <div className="metric-value">{metrics?.total_queries || 0}</div>
            <div className="metric-label">Total Evaluated Queries</div>
          </div>
        </div>

        <div className="metric-card">
          <div className="metric-icon-wrap" style={{ background: "#fef2f2", color: "#dc2626" }}>
            <Lock size={24} />
          </div>
          <div>
            <div className="metric-value">{metrics?.blocked_queries || 0}</div>
            <div className="metric-label">Threats Blocked</div>
          </div>
        </div>
      </div>

      {/* Main Grid: Telemetry Chart & Quarantine Alert */}
      <div style={{ display: "grid", gridTemplateColumns: "1.6fr 1fr", gap: "24px", marginBottom: "28px" }}>
        {/* Risk Distribution Chart */}
        <div className="card">
          <div className="card-header">
            <div>
              <h2 className="card-title">Policy Decision Breakdown</h2>
              <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
                Distribution of requests categorized by composite risk scores
              </span>
            </div>
          </div>

          <div style={{ height: "260px", width: "100%" }}>
            <ResponsiveContainer width="100%" height="100%">
              <BarChart data={chartData} margin={{ top: 10, right: 10, left: -20, bottom: 0 }}>
                <XAxis dataKey="name" tick={{ fontSize: 12, fill: "#64748b" }} />
                <YAxis allowDecimals={false} tick={{ fontSize: 12, fill: "#64748b" }} />
                <Tooltip
                  contentStyle={{ backgroundColor: "#0f172a", color: "#ffffff", borderRadius: "8px", fontSize: "0.8rem", border: "none" }}
                  itemStyle={{ color: "#ffffff" }}
                />
                <Bar dataKey="count" radius={[4, 4, 0, 0]}>
                  {chartData.map((entry, index) => (
                    <Cell key={`cell-${index}`} fill={entry.color} />
                  ))}
                </Bar>
              </BarChart>
            </ResponsiveContainer>
          </div>
        </div>

        {/* Quarantine Action Card */}
        <div className="card" style={{ display: "flex", flexDirection: "column", justifyContent: "space-between" }}>
          <div>
            <div style={{ display: "flex", alignItems: "center", gap: "10px", marginBottom: "16px" }}>
              <div style={{ background: "#fee2e2", padding: "8px", borderRadius: "8px" }}>
                <AlertOctagon size={20} color="#dc2626" />
              </div>
              <div>
                <h3 style={{ fontSize: "1.05rem", fontWeight: 600 }}>Quarantine Station</h3>
                <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>Suspicious file isolation</span>
              </div>
            </div>

            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", lineHeight: 1.6, marginBottom: "20px" }}>
              <b>{metrics?.quarantined_documents || 0} document(s)</b> are currently flagged for prompt injection patterns and excluded from the ChromaDB vector index.
            </p>

            <div style={{ background: "#f8fafc", border: "1px solid var(--border-light)", borderRadius: "8px", padding: "12px", fontSize: "0.78rem", color: "var(--text-secondary)", marginBottom: "20px" }}>
              Inspecting quarantined uploads allows you to approve false positives or permanently purge adversarial files before vectors are generated.
            </div>
          </div>

          <Link
            to="/admin/quarantine"
            className="btn btn-secondary"
            style={{ width: "100%", justifyContent: "space-between" }}
          >
            <span>Review Flagged Uploads</span>
            <ArrowRight size={16} />
          </Link>
        </div>
      </div>

      {/* Security Incidents Feed */}
      <div className="card" style={{ padding: 0 }}>
        <div style={{ padding: "20px 24px", borderBottom: "1px solid var(--border-light)", display: "flex", alignItems: "center", justifyContent: "space-between" }}>
          <div>
            <h2 className="card-title">Recent Security Threat Incidents</h2>
            <span style={{ fontSize: "0.78rem", color: "var(--text-muted)" }}>
              Recorded injection attempts, quarantine triggers, and permission violations
            </span>
          </div>

          <Link to="/admin/audit-logs" className="btn btn-secondary" style={{ fontSize: "0.78rem", padding: "6px 12px" }}>
            View Full Audit Trail
          </Link>
        </div>

        <div className="table-container" style={{ border: "none", borderRadius: 0 }}>
          <table className="table">
            <thead>
              <tr>
                <th>Severity</th>
                <th>Incident Type</th>
                <th>Description</th>
                <th>Timestamp</th>
              </tr>
            </thead>
            <tbody>
              {securityEvents.length === 0 ? (
                <tr>
                  <td colSpan={4} style={{ textAlign: "center", padding: "24px", color: "var(--text-muted)" }}>
                    No security incidents recorded. System running normally.
                  </td>
                </tr>
              ) : (
                securityEvents.map((ev) => (
                  <tr key={ev.id}>
                    <td>
                      <span className={`badge ${ev.severity === "CRITICAL" ? "badge-block" : ev.severity === "HIGH" ? "badge-high" : "badge-medium"}`}>
                        {ev.severity}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600, fontSize: "0.82rem" }}>
                      {ev.event_type}
                    </td>
                    <td style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>
                      {ev.description}
                    </td>
                    <td style={{ color: "var(--text-muted)", fontSize: "0.8rem", whiteSpace: "nowrap" }}>
                      {new Date(ev.created_at).toLocaleString()}
                    </td>
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>
    </div>
  );
}
