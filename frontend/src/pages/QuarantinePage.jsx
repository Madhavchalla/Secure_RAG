import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import {
  AlertOctagon,
  CheckCircle,
  Trash2,
  FileText,
  AlertTriangle,
  Info,
} from "lucide-react";

export default function QuarantinePage() {
  const [quarantinedDocs, setQuarantinedDocs] = useState([]);
  const [loading, setLoading] = useState(true);
  const [feedback, setFeedback] = useState(null);
  const [processingId, setProcessingId] = useState(null);

  const fetchQuarantine = async () => {
    try {
      const data = await api.admin.getQuarantine();
      setQuarantinedDocs(data);
    } catch (err) {
      setFeedback({ type: "error", message: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchQuarantine();
  }, []);

  const handleAction = async (docId, actionName) => {
    setProcessingId(docId);
    setFeedback(null);
    try {
      const res = await api.admin.reviewQuarantine(docId, {
        action: actionName,
        sensitivity_level: "LOW",
        notes: `Reviewed by admin via quarantine station. Action: ${actionName}`,
      });
      setFeedback({ type: "success", message: res.message });
      fetchQuarantine();
    } catch (err) {
      setFeedback({ type: "error", message: err.message });
    } finally {
      setProcessingId(null);
    }
  };

  return (
    <div>
      <div style={{ marginBottom: "28px" }}>
        <h1 style={{ fontSize: "1.45rem", fontWeight: 700, color: "var(--text-main)" }}>
          Quarantine Inspection Station
        </h1>
        <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
          Isolated files flagged by pre-ingestion threat scanners for prompt injection and instruction hijacking patterns.
        </p>
      </div>

      {feedback && (
        <div style={{
          padding: "12px 16px",
          borderRadius: "8px",
          marginBottom: "20px",
          fontSize: "0.85rem",
          display: "flex",
          alignItems: "center",
          gap: "10px",
          backgroundColor: feedback.type === "success" ? "#ecfdf5" : "#fef2f2",
          border: `1px solid ${feedback.type === "success" ? "#a7f3d0" : "#fecaca"}`,
          color: feedback.type === "success" ? "#065f46" : "#991b1b",
        }}>
          <CheckCircle size={18} />
          <span>{feedback.message}</span>
        </div>
      )}

      <div style={{ display: "flex", flexDirection: "column", gap: "20px" }}>
        {quarantinedDocs.length === 0 ? (
          <div className="card" style={{ textAlign: "center", padding: "48px" }}>
            <CheckCircle size={40} color="#059669" style={{ margin: "0 auto 16px" }} />
            <h3 style={{ fontSize: "1.1rem", fontWeight: 600, color: "var(--text-main)", marginBottom: "6px" }}>
              Quarantine Queue is Clear
            </h3>
            <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)", maxWidth: "420px", margin: "0 auto" }}>
              No suspicious files are currently awaiting review. All active organizational documents have passed security heuristics.
            </p>
          </div>
        ) : (
          quarantinedDocs.map((doc) => {
            let flags = [];
            try {
              flags = doc.security_flags ? JSON.parse(doc.security_flags) : [];
            } catch {
              flags = [];
            }

            return (
              <div key={doc.id} className="card" style={{ borderLeft: "4px solid #dc2626" }}>
                <div style={{ display: "flex", alignItems: "flex-start", justifyContent: "space-between", marginBottom: "16px" }}>
                  <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
                    <div style={{ background: "#fee2e2", padding: "10px", borderRadius: "8px" }}>
                      <AlertOctagon size={22} color="#dc2626" />
                    </div>
                    <div>
                      <h3 style={{ fontSize: "1.05rem", fontWeight: 700, color: "var(--text-main)" }}>
                        {doc.filename}
                      </h3>
                      <div style={{ display: "flex", gap: "12px", fontSize: "0.78rem", color: "var(--text-muted)", marginTop: "2px" }}>
                        <span>Size: {(doc.file_size / 1024).toFixed(1)} KB</span>
                        <span>•</span>
                        <span>Flagged: {new Date(doc.created_at).toLocaleString()}</span>
                        <span>•</span>
                        <span>Proposed Sensitivity: {doc.sensitivity_level}</span>
                      </div>
                    </div>
                  </div>

                  <div style={{ display: "flex", gap: "10px" }}>
                    <button
                      onClick={() => handleAction(doc.id, "REJECT")}
                      disabled={processingId === doc.id}
                      className="btn btn-danger"
                      style={{ fontSize: "0.82rem", padding: "6px 14px" }}
                    >
                      <Trash2 size={14} />
                      <span>Reject & Purge File</span>
                    </button>
                    <button
                      onClick={() => handleAction(doc.id, "APPROVE")}
                      disabled={processingId === doc.id}
                      className="btn btn-primary"
                      style={{ fontSize: "0.82rem", padding: "6px 14px" }}
                    >
                      <CheckCircle size={14} />
                      <span>Approve & Index Vector</span>
                    </button>
                  </div>
                </div>

                {/* Detected Injection Signatures Breakdown */}
                <div style={{ background: "#f8fafc", border: "1px solid var(--border-light)", borderRadius: "8px", padding: "16px" }}>
                  <div style={{ fontSize: "0.82rem", fontWeight: 700, color: "#991b1b", marginBottom: "10px", display: "flex", alignItems: "center", gap: "6px" }}>
                    <AlertTriangle size={15} color="#dc2626" />
                    <span>Detected Heuristic Threat Triggers ({flags.length}):</span>
                  </div>

                  <div style={{ display: "flex", flexDirection: "column", gap: "8px" }}>
                    {flags.map((flag, fIdx) => (
                      <div key={fIdx} style={{ background: "#ffffff", border: "1px solid var(--border-medium)", borderRadius: "6px", padding: "10px 12px", fontSize: "0.8rem" }}>
                        <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "4px" }}>
                          <span style={{ fontWeight: 600, color: "var(--text-main)" }}>
                            [{flag.id}] {flag.name}
                          </span>
                          <span className={`badge ${flag.severity === "CRITICAL" ? "badge-block" : "badge-high"}`} style={{ fontSize: "0.62rem" }}>
                            {flag.severity} (Score: {flag.weight})
                          </span>
                        </div>
                        <div style={{ fontStyle: "italic", color: "var(--text-secondary)", fontFamily: "var(--font-mono)", fontSize: "0.78rem" }}>
                          Matched phrase: "{flag.matched_snippet}"
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            );
          })
        )}
      </div>
    </div>
  );
}
