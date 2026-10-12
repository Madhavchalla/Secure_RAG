import React from "react";
import { Outlet, NavLink, useNavigate } from "react-router-dom";
import { useAuth } from "../context/AuthContext";
import {
  Shield,
  MessageSquare,
  FileText,
  LayoutDashboard,
  AlertOctagon,
  FileSearch,
  LogOut,
  User as UserIcon,
} from "lucide-react";

export default function Layout() {
  const { user, isAdmin, logout } = useAuth();
  const navigate = useNavigate();

  const handleLogout = () => {
    logout();
    navigate("/login");
  };

  return (
    <div className="app-container">
      {/* Sidebar */}
      <aside className="sidebar">
        <div className="sidebar-header">
          <div style={{ background: "rgba(37, 99, 235, 0.2)", padding: "8px", borderRadius: "8px" }}>
            <Shield size={22} color="#60a5fa" />
          </div>
          <div>
            <div className="sidebar-brand">RAS-RAG</div>
            <span className="sidebar-sub">Secure Document AI</span>
          </div>
        </div>

        <nav className="sidebar-nav">
          <NavLink
            to="/chat"
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            <MessageSquare size={18} />
            <span>AI Assistant</span>
          </NavLink>

          <NavLink
            to="/documents"
            className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
          >
            <FileText size={18} />
            <span>Document Library</span>
          </NavLink>

          {isAdmin && (
            <>
              <div style={{ margin: "16px 12px 6px", fontSize: "0.72rem", color: "#64748b", textTransform: "uppercase", fontWeight: 700, letterSpacing: "0.06em" }}>
                Administration
              </div>

              <NavLink
                to="/admin/dashboard"
                className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
              >
                <LayoutDashboard size={18} />
                <span>Dashboard</span>
              </NavLink>

              <NavLink
                to="/admin/quarantine"
                className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
              >
                <AlertOctagon size={18} />
                <span>Quarantine Queue</span>
              </NavLink>

              <NavLink
                to="/admin/audit-logs"
                className={({ isActive }) => `nav-item ${isActive ? "active" : ""}`}
              >
                <FileSearch size={18} />
                <span>Audit Trail</span>
              </NavLink>
            </>
          )}
        </nav>

        <div className="sidebar-footer">
          <div style={{ display: "flex", alignItems: "center", gap: "10px", minWidth: 0 }}>
            <div style={{ background: "#334155", width: "32px", height: "32px", borderRadius: "50%", display: "flex", alignItems: "center", justifyContent: "center" }}>
              <UserIcon size={16} color="#cbd5e1" />
            </div>
            <div style={{ minWidth: 0 }}>
              <div style={{ fontSize: "0.82rem", fontWeight: 600, color: "#f8fafc", whiteSpace: "nowrap", overflow: "hidden", textOverflow: "ellipsis" }}>
                {user?.username}
              </div>
              <span className={`badge ${user?.role === "admin" ? "badge-restrict" : "badge-low"}`} style={{ fontSize: "0.65rem", padding: "1px 6px" }}>
                {user?.role}
              </span>
            </div>
          </div>
          <button
            onClick={handleLogout}
            style={{ background: "none", border: "none", color: "#94a3b8", cursor: "pointer", padding: "6px" }}
            title="Sign out"
          >
            <LogOut size={16} />
          </button>
        </div>
      </aside>

      {/* Main Content Area */}
      <div className="main-content">
        <header className="top-navbar">
          <div style={{ display: "flex", alignItems: "center", gap: "12px" }}>
            <span style={{ fontSize: "0.85rem", color: "var(--text-secondary)", fontWeight: 500 }}>
              Privacy-Preserving Document Retrieval System
            </span>
          </div>

          <div style={{ display: "flex", alignItems: "center", gap: "16px" }}>
            <div style={{ display: "flex", alignItems: "center", gap: "6px", fontSize: "0.78rem", color: "#059669", background: "#ecfdf5", border: "1px solid #a7f3d0", padding: "4px 10px", borderRadius: "9999px", fontWeight: 600 }}>
              <span style={{ width: "6px", height: "6px", borderRadius: "50%", background: "#059669", display: "inline-block" }}></span>
              Zero-Trust Enforcement Active
            </div>
          </div>
        </header>

        <main className="page-body">
          <Outlet />
        </main>
      </div>
    </div>
  );
}
