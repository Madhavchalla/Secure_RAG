import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import {
  FileSearch,
  Filter,
  CheckCircle,
  AlertTriangle,
  XCircle,
  Code,
  Eye,
  Shield,
  Layers,
} from "lucide-react";

export default function AuditLogsPage() {
  const [activeTab, setActiveTab] = useState("logs"); // 'logs', 'events', 'assessments'
  const [logs, setLogs] = useState([]);
  const [events, setEvents] = useState([]);
  const [assessments, setAssessments] = useState([]);
  const [statusFilter, setStatusFilter] = useState("ALL");
  const [selectedDetails, setSelectedDetails] = useState(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      setLoading(true);
      try {
        if (activeTab === "logs") {
          const params = statusFilter !== "ALL" ? `?status_filter=${statusFilter}` : "";
          const data = await api.audit.getLogs(params);
          setLogs(data);
        } else if (activeTab === "events") {
          const data = await api.audit.getSecurityEvents();
          setEvents(data);
        } else if (activeTab === "assessments") {
          const data = await api.audit.getRiskAssessments();
          setAssessments(data);
        }
      } catch (err) {
        console.error("Audit load error:", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
  }, [activeTab, statusFilter]);

  return (
    <div>
      <div style={{ marginBottom: "24px" }}>
        <h1 style={{ fontSize: "1.45rem", fontWeight: 700, color: "var(--text-main)" }}>
          Audit Trail & Security Telemetry
        </h1>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
          Immutable logs documenting every access decision, risk calculation, and security incident.
        </p>
      </div>

      {/* Tabs */}
      <div style={{ display: "flex", gap: "8px", borderBottom: "1px solid var(--border-light)", marginBottom: "20px" }}>
        <button
          onClick={() => setActiveTab("logs")}
          className={`btn ${activeTab === "logs" ? "btn-primary" : "btn-secondary"}`}
          style={{ borderRadius: "8px 8px 0 0", borderBottom: "none", fontSize: "0.82rem" }}
        >
          <FileSearch size={16} />
          <span>System Audit Logs</span>
        </button>
        <button
          onClick={() => setActiveTab("events")}
          className={`btn ${activeTab === "events" ? "btn-primary" : "btn-secondary"}`}
          style={{ borderRadius: "8px 8px 0 0", borderBottom: "none", fontSize: "0.82rem" }}
        >
          <Shield size={16} />
          <span>Security Threats</span>
        </button>
        <button
          onClick={() => setActiveTab("assessments")}
          className={`btn ${activeTab === "assessments" ? "btn-primary" : "btn-secondary"}`}
          style={{ borderRadius: "8px 8px 0 0", borderBottom: "none", fontSize: "0.82rem" }}
        >
          <Layers size={16} />
          <span>Risk Assessments</span>
        </button>
      </div>

      {/* Audit Logs Tab Content */}
      {activeTab === "logs" && (
        <div className="card" style={{ padding: 0 }}>
          <div style={{ padding: "16px 20px", borderBottom: "1px solid var(--border-light)", display: "flex", justifyContent: "space-between", alignItems: "center" }}>
            <span style={{ fontSize: "0.85rem", fontWeight: 600 }}>Recorded Events ({logs.length})</span>
            <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
              <Filter size={15} color="var(--text-muted)" />
              <select
                className="select"
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                style={{ width: "auto", padding: "5px 10px", fontSize: "0.8rem" }}
              >
                <option value="ALL">All Statuses</option>
                <option value="SUCCESS">SUCCESS</option>
                <option value="DENIED">DENIED</option>
                <option value="WARNING">WARNING</option>
              </select>
            </div>
          </div>

          <div className="table-container" style={{ border: "none" }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Status</th>
                  <th>Action</th>
                  <th>User</th>
                  <th>Resource</th>
                  <th>Client IP</th>
                  <th>Timestamp</th>
                  <th>Details</th>
                </tr>
              </thead>
              <tbody>
                {logs.length === 0 ? (
                  <tr>
                    <td colSpan={7} style={{ textAlign: "center", padding: "24px", color: "var(--text-muted)" }}>
                      No audit logs match current filter.
                    </td>
                  </tr>
                ) : (
                  logs.map((log) => (
                    <tr key={log.id}>
                      <td>
                        <span className={`badge ${log.status === "SUCCESS" ? "badge-allow" : log.status === "DENIED" ? "badge-block" : "badge-restrict"}`}>
                          {log.status}
                        </span>
                      </td>
                      <td style={{ fontWeight: 600, fontSize: "0.82rem" }}>
                        {log.action}
                      </td>
                      <td style={{ color: "var(--text-secondary)" }}>
                        {log.username || "System/Anon"}
                      </td>
                      <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                        {log.resource_type}: {log.resource_id}
                      </td>
                      <td style={{ color: "var(--text-muted)", fontSize: "0.8rem", fontFamily: "var(--font-mono)" }}>
                        {log.ip_address}
                      </td>
                      <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>
                        {new Date(log.created_at).toLocaleString()}
                      </td>
                      <td>
                        {log.details_json && (
                          <button
                            onClick={() => setSelectedDetails({ title: log.action, json: log.details_json })}
                            className="btn btn-secondary"
                            style={{ padding: "4px 8px", fontSize: "0.75rem" }}
                          >
                            <Code size={13} />
                            <span>Inspect</span>
                          </button>
                        )}
                      </td>
                    </tr>
                  ))
                )}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Security Threat Events Tab */}
      {activeTab === "events" && (
        <div className="card" style={{ padding: 0 }}>
          <div className="table-container" style={{ border: "none" }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Severity</th>
                  <th>Event Type</th>
                  <th>User</th>
                  <th>Description</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {events.map((ev) => (
                  <tr key={ev.id}>
                    <td>
                      <span className={`badge ${ev.severity === "CRITICAL" ? "badge-block" : ev.severity === "HIGH" ? "badge-high" : "badge-medium"}`}>
                        {ev.severity}
                      </span>
                    </td>
                    <td style={{ fontWeight: 600, fontSize: "0.82rem" }}>{ev.event_type}</td>
                    <td style={{ color: "var(--text-secondary)" }}>{ev.username || "Anonymous"}</td>
                    <td style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>{ev.description}</td>
                    <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{new Date(ev.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* Risk Assessments Telemetry Tab */}
      {activeTab === "assessments" && (
        <div className="card" style={{ padding: 0 }}>
          <div className="table-container" style={{ border: "none" }}>
            <table className="table">
              <thead>
                <tr>
                  <th>Decision</th>
                  <th>Risk Score</th>
                  <th>Query Threat (Sq)</th>
                  <th>Session (Ss)</th>
                  <th>Doc Sens (Sd)</th>
                  <th>User Inquiry Snippet</th>
                  <th>Timestamp</th>
                </tr>
              </thead>
              <tbody>
                {assessments.map((a) => (
                  <tr key={a.id}>
                    <td>
                      <span className={`badge ${a.decision === "ALLOW" ? "badge-allow" : a.decision === "RESTRICT" ? "badge-restrict" : a.decision === "VERIFY" ? "badge-verify" : "badge-block"}`}>
                        {a.decision}
                      </span>
                    </td>
                    <td style={{ fontWeight: 700 }}>{a.final_risk_score}</td>
                    <td>{a.query_risk_score}</td>
                    <td>{a.session_risk_score}</td>
                    <td>{a.doc_sensitivity_score}</td>
                    <td style={{ color: "var(--text-secondary)", fontSize: "0.82rem" }}>"{a.query_text.slice(0, 60)}..."</td>
                    <td style={{ color: "var(--text-muted)", fontSize: "0.8rem" }}>{new Date(a.created_at).toLocaleString()}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        </div>
      )}

      {/* JSON Inspection Modal */}
      {selectedDetails && (
        <div className="modal-overlay">
          <div className="modal-content">
            <h3 style={{ fontSize: "1.1rem", fontWeight: 700, marginBottom: "12px" }}>
              Audit Details: {selectedDetails.title}
            </h3>
            <pre style={{
              background: "#0f172a",
              color: "#38bdf8",
              padding: "16px",
              borderRadius: "8px",
              fontFamily: "var(--font-mono)",
              fontSize: "0.8rem",
              overflowX: "auto",
              maxHeight: "360px",
            }}>
              {JSON.stringify(JSON.parse(selectedDetails.json), null, 2)}
            </pre>
            <div style={{ display: "flex", justifyContent: "flex-end", marginTop: "16px" }}>
              <button onClick={() => setSelectedDetails(null)} className="btn btn-secondary">
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
