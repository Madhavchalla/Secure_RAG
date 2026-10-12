import React, { useState, useEffect } from "react";
import { api } from "../services/api";
import { useAuth } from "../context/AuthContext";
import {
  FileText,
  Upload,
  Trash2,
  Search,
  Filter,
  CheckCircle,
  AlertTriangle,
  Lock,
  Plus,
  X,
} from "lucide-react";

export default function DocumentLibraryPage() {
  const { isAdmin } = useAuth();
  const [documents, setDocuments] = useState([]);
  const [loading, setLoading] = useState(true);
  const [search, setSearch] = useState("");
  const [filterSens, setFilterSens] = useState("ALL");
  const [showUploadModal, setShowUploadModal] = useState(false);
  const [uploadFile, setUploadFile] = useState(null);
  const [uploadSens, setUploadSens] = useState("LOW");
  const [uploadRole, setUploadRole] = useState("user");
  const [uploading, setUploading] = useState(false);
  const [feedback, setFeedback] = useState(null);

  const fetchDocs = async () => {
    try {
      const data = await api.documents.list();
      setDocuments(data);
    } catch (err) {
      setFeedback({ type: "error", message: err.message });
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    fetchDocs();
  }, []);

  const handleUpload = async (e) => {
    e.preventDefault();
    if (!uploadFile) return;

    setUploading(true);
    setFeedback(null);
    const formData = new FormData();
    formData.append("file", uploadFile);
    formData.append("sensitivity_level", uploadSens);
    formData.append("assign_role", uploadRole);

    try {
      const res = await api.documents.upload(formData);
      if (res.status === "QUARANTINED") {
        setFeedback({
          type: "warning",
          message: `Document '${res.filename}' was QUARANTINED due to detected security flags. Vectors were not indexed.`,
        });
      } else {
        setFeedback({
          type: "success",
          message: `Document '${res.filename}' indexed successfully into ChromaDB!`,
        });
      }
      setShowUploadModal(false);
      setUploadFile(null);
      fetchDocs();
    } catch (err) {
      setFeedback({ type: "error", message: err.message });
    } finally {
      setUploading(false);
    }
  };

  const handleDelete = async (docId, filename) => {
    if (!window.confirm(`Are you sure you want to purge '${filename}' and its vector embeddings?`)) {
      return;
    }
    try {
      await api.documents.delete(docId);
      setFeedback({ type: "success", message: `Document '${filename}' and vectors purged.` });
      fetchDocs();
    } catch (err) {
      setFeedback({ type: "error", message: err.message });
    }
  };

  const filteredDocs = documents.filter((doc) => {
    const matchesSearch = doc.filename.toLowerCase().includes(search.toLowerCase());
    const matchesSens = filterSens === "ALL" || doc.sensitivity_level === filterSens;
    return matchesSearch && matchesSens;
  });

  return (
    <div>
      {/* Header bar */}
      <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "24px" }}>
        <div>
          <h1 style={{ fontSize: "1.45rem", fontWeight: 700, color: "var(--text-main)" }}>
            Document Repository
          </h1>
          <p style={{ fontSize: "0.85rem", color: "var(--text-secondary)" }}>
            Authorized organizational knowledge bases available for retrieval.
          </p>
        </div>

        {isAdmin && (
          <button
            onClick={() => setShowUploadModal(true)}
            className="btn btn-primary"
          >
            <Plus size={16} />
            <span>Upload Document</span>
          </button>
        )}
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
          backgroundColor: feedback.type === "success" ? "#ecfdf5" : feedback.type === "warning" ? "#fffbeb" : "#fef2f2",
          border: `1px solid ${feedback.type === "success" ? "#a7f3d0" : feedback.type === "warning" ? "#fde68a" : "#fecaca"}`,
          color: feedback.type === "success" ? "#065f46" : feedback.type === "warning" ? "#92400e" : "#991b1b",
        }}>
          {feedback.type === "success" ? <CheckCircle size={18} /> : <AlertTriangle size={18} />}
          <span>{feedback.message}</span>
        </div>
      )}

      {/* Filter and Search Bar */}
      <div className="card" style={{ padding: "16px", marginBottom: "24px", display: "flex", gap: "16px", alignItems: "center" }}>
        <div style={{ display: "flex", alignItems: "center", gap: "8px", flex: 1 }}>
          <Search size={18} color="var(--text-muted)" />
          <input
            type="text"
            className="input"
            placeholder="Search by filename..."
            value={search}
            onChange={(e) => setSearch(e.target.value)}
            style={{ border: "none", boxShadow: "none", padding: "6px" }}
          />
        </div>

        <div style={{ display: "flex", alignItems: "center", gap: "8px" }}>
          <Filter size={16} color="var(--text-muted)" />
          <select
            className="select"
            value={filterSens}
            onChange={(e) => setFilterSens(e.target.value)}
            style={{ width: "auto", padding: "6px 12px" }}
          >
            <option value="ALL">All Sensitivity Levels</option>
            <option value="LOW">Low Sensitivity</option>
            <option value="MEDIUM">Medium Sensitivity</option>
            <option value="HIGH">High Sensitivity</option>
          </select>
        </div>
      </div>

      {/* Documents Table */}
      <div className="card" style={{ padding: 0 }}>
        <div className="table-container">
          <table className="table">
            <thead>
              <tr>
                <th>Document Name</th>
                <th>Sensitivity Tier</th>
                <th>Status</th>
                <th>File Size</th>
                <th>Uploaded Date</th>
                {isAdmin && <th>Actions</th>}
              </tr>
            </thead>
            <tbody>
              {filteredDocs.length === 0 ? (
                <tr>
                  <td colSpan={isAdmin ? 6 : 5} style={{ textAlign: "center", padding: "32px", color: "var(--text-muted)" }}>
                    No authorized documents match the current filter.
                  </td>
                </tr>
              ) : (
                filteredDocs.map((doc) => (
                  <tr key={doc.id}>
                    <td>
                      <div style={{ display: "flex", alignItems: "center", gap: "10px" }}>
                        <div style={{ background: "var(--primary-subtle)", padding: "6px", borderRadius: "6px" }}>
                          <FileText size={16} color="#2563eb" />
                        </div>
                        <span style={{ fontWeight: 600 }}>{doc.filename}</span>
                      </div>
                    </td>
                    <td>
                      <span className={`badge ${doc.sensitivity_level === "HIGH" ? "badge-high" : doc.sensitivity_level === "MEDIUM" ? "badge-medium" : "badge-low"}`}>
                        {doc.sensitivity_level}
                      </span>
                    </td>
                    <td>
                      <span className={`badge ${doc.status === "ACTIVE" ? "badge-allow" : doc.status === "QUARANTINED" ? "badge-block" : "badge-low"}`}>
                        {doc.status}
                      </span>
                    </td>
                    <td style={{ color: "var(--text-secondary)" }}>
                      {(doc.file_size / 1024).toFixed(1)} KB
                    </td>
                    <td style={{ color: "var(--text-secondary)" }}>
                      {new Date(doc.created_at).toLocaleDateString()}
                    </td>
                    {isAdmin && (
                      <td>
                        <button
                          onClick={() => handleDelete(doc.id, doc.filename)}
                          className="btn btn-secondary"
                          style={{ padding: "4px 8px", color: "#b91c1c", borderColor: "#fecaca" }}
                          title="Purge document"
                        >
                          <Trash2 size={14} />
                        </button>
                      </td>
                    )}
                  </tr>
                ))
              )}
            </tbody>
          </table>
        </div>
      </div>

      {/* Upload Modal */}
      {showUploadModal && (
        <div className="modal-overlay">
          <div className="modal-content">
            <div style={{ display: "flex", alignItems: "center", justifyContent: "space-between", marginBottom: "20px" }}>
              <h2 style={{ fontSize: "1.2rem", fontWeight: 700, color: "var(--text-main)" }}>
                Upload & Ingest Document
              </h2>
              <button
                onClick={() => setShowUploadModal(false)}
                style={{ background: "none", border: "none", cursor: "pointer", color: "var(--text-muted)" }}
              >
                <X size={20} />
              </button>
            </div>

            <form onSubmit={handleUpload} style={{ display: "flex", flexDirection: "column", gap: "16px" }}>
              <div>
                <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "6px" }}>
                  Select File (PDF, DOCX, TXT, MD)
                </label>
                <input
                  type="file"
                  accept=".pdf,.docx,.txt,.md"
                  onChange={(e) => setUploadFile(e.target.files[0])}
                  required
                  style={{ fontSize: "0.85rem" }}
                />
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "6px" }}>
                  Sensitivity Level
                </label>
                <select
                  className="select"
                  value={uploadSens}
                  onChange={(e) => setUploadSens(e.target.value)}
                >
                  <option value="LOW">LOW — General Employee Access</option>
                  <option value="MEDIUM">MEDIUM — Internal Departmental Confidential</option>
                  <option value="HIGH">HIGH — Restricted Executive / Payroll</option>
                </select>
              </div>

              <div>
                <label style={{ display: "block", fontSize: "0.82rem", fontWeight: 600, color: "var(--text-secondary)", marginBottom: "6px" }}>
                  Grant Role-Based Read Access
                </label>
                <select
                  className="select"
                  value={uploadRole}
                  onChange={(e) => setUploadRole(e.target.value)}
                >
                  <option value="user">Standard Users & Admins ('user' role)</option>
                  <option value="admin">Administrators Only ('admin' role)</option>
                  <option value="none">No Automatic Role Grant (Unassigned)</option>
                </select>
              </div>

              <div style={{ background: "#f8fafc", border: "1px solid var(--border-light)", borderRadius: "8px", padding: "12px", fontSize: "0.78rem", color: "var(--text-secondary)" }}>
                <strong>Automated Security Inspection:</strong> Every document is scanned for prompt injection vectors. Flagged documents are held in quarantine and will not enter ChromaDB until reviewed.
              </div>

              <div style={{ display: "flex", justifyContent: "flex-end", gap: "10px", marginTop: "12px" }}>
                <button
                  type="button"
                  onClick={() => setShowUploadModal(false)}
                  className="btn btn-secondary"
                  disabled={uploading}
                >
                  Cancel
                </button>
                <button
                  type="submit"
                  className="btn btn-primary"
                  disabled={uploading || !uploadFile}
                >
                  {uploading ? "Ingesting & Scanning..." : "Upload & Index"}
                </button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
}
