import React from "react";
import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./context/AuthContext";
import Layout from "./components/Layout";
import LoginPage from "./pages/LoginPage";
import ChatAssistantPage from "./pages/ChatAssistantPage";
import DocumentLibraryPage from "./pages/DocumentLibraryPage";
import AdminDashboardPage from "./pages/AdminDashboardPage";
import QuarantinePage from "./pages/QuarantinePage";
import AuditLogsPage from "./pages/AuditLogsPage";

function ProtectedRoute({ children, adminOnly = false }) {
  const { user, isAdmin, loading } = useAuth();

  if (loading) {
    return <div style={{ padding: "48px", textAlign: "center", color: "var(--text-secondary)" }}>Verifying security credentials...</div>;
  }

  if (!user) {
    return <Navigate to="/login" replace />;
  }

  if (adminOnly && !isAdmin) {
    return <Navigate to="/chat" replace />;
  }

  return children;
}

export default function App() {
  return (
    <AuthProvider>
      <BrowserRouter>
        <Routes>
          <Route path="/login" element={<LoginPage />} />

          <Route
            path="/"
            element={
              <ProtectedRoute>
                <Layout />
              </ProtectedRoute>
            }
          >
            <Route index element={<Navigate to="/chat" replace />} />
            <Route path="chat" element={<ChatAssistantPage />} />
            <Route path="documents" element={<DocumentLibraryPage />} />

            {/* Admin Routes */}
            <Route
              path="admin/dashboard"
              element={
                <ProtectedRoute adminOnly>
                  <AdminDashboardPage />
                </ProtectedRoute>
              }
            />
            <Route
              path="admin/quarantine"
              element={
                <ProtectedRoute adminOnly>
                  <QuarantinePage />
                </ProtectedRoute>
              }
            />
            <Route
              path="admin/audit-logs"
              element={
                <ProtectedRoute adminOnly>
                  <AuditLogsPage />
                </ProtectedRoute>
              }
            />
          </Route>

          <Route path="*" element={<Navigate to="/chat" replace />} />
        </Routes>
      </BrowserRouter>
    </AuthProvider>
  );
}
