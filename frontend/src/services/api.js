const API_BASE = "http://localhost:8000/api";

async function request(endpoint, options = {}) {
  const token = localStorage.getItem("token");
  const headers = {
    ...(options.headers || {}),
  };

  if (token && !headers["Authorization"]) {
    headers["Authorization"] = `Bearer ${token}`;
  }

  // If body is NOT FormData, default to application/json
  if (options.body && !(options.body instanceof FormData)) {
    headers["Content-Type"] = "application/json";
  }

  const config = {
    ...options,
    headers,
  };

  const response = await fetch(`${API_BASE}${endpoint}`, config);

  if (response.status === 401) {
    // Clear stale session on unauthorized
    localStorage.removeItem("token");
    localStorage.removeItem("user");
    if (!window.location.pathname.includes("/login")) {
      window.location.href = "/login";
    }
  }

  if (!response.ok) {
    let errorDetail = "An unexpected error occurred.";
    try {
      const errJson = await response.json();
      errorDetail = errJson.detail || JSON.stringify(errJson);
    } catch {
      errorDetail = response.statusText;
    }
    throw new Error(errorDetail);
  }

  return response.json();
}

export const api = {
  // Authentication
  auth: {
    login: (credentials) =>
      request("/auth/login", {
        method: "POST",
        body: JSON.stringify(credentials),
      }),
    register: (userData) =>
      request("/auth/register", {
        method: "POST",
        body: JSON.stringify(userData),
      }),
    me: () => request("/auth/me"),
    logout: () =>
      request("/auth/logout", {
        method: "POST",
      }),
  },

  // Documents
  documents: {
    list: () => request("/documents/"),
    get: (id) => request(`/documents/${id}`),
    upload: (formData) =>
      request("/documents/upload", {
        method: "POST",
        body: formData,
      }),
    update: (id, data) =>
      request(`/documents/${id}`, {
        method: "PUT",
        body: JSON.stringify(data),
      }),
    delete: (id) =>
      request(`/documents/${id}`, {
        method: "DELETE",
      }),
    addPermission: (id, perm) =>
      request(`/documents/${id}/permissions`, {
        method: "POST",
        body: JSON.stringify(perm),
      }),
  },

  // RAG Assistant
  rag: {
    query: (queryText) =>
      request("/rag/query", {
        method: "POST",
        body: JSON.stringify({ query: queryText }),
      }),
  },

  // Admin
  admin: {
    getMetrics: () => request("/admin/metrics"),
    getQuarantine: () => request("/admin/quarantine"),
    reviewQuarantine: (id, reviewData) =>
      request(`/admin/quarantine/${id}/review`, {
        method: "POST",
        body: JSON.stringify(reviewData),
      }),
    getUsers: () => request("/admin/users"),
    updateRole: (userId, newRole) =>
      request(`/admin/users/${userId}/role?new_role=${newRole}`, {
        method: "PUT",
      }),
  },

  // Audit & Telemetry
  audit: {
    getLogs: (params = "") => request(`/audit/logs${params}`),
    getSecurityEvents: (params = "") => request(`/audit/security-events${params}`),
    getRiskAssessments: (params = "") => request(`/audit/risk-assessments${params}`),
  },
};
