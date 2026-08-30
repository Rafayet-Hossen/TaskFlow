/**
 * TaskFlow API & Toast Client
 */

const API_BASE = ""; // Relative path to FastAPI backend

const API = {
  getToken() {
    return localStorage.getItem("taskflow_token");
  },

  setToken(token) {
    localStorage.setItem("taskflow_token", token);
  },

  clearToken() {
    localStorage.removeItem("taskflow_token");
    localStorage.removeItem("taskflow_user");
  },

  getUser() {
    const userStr = localStorage.getItem("taskflow_user");
    try {
      return userStr ? JSON.parse(userStr) : null;
    } catch {
      return null;
    }
  },

  setUser(user) {
    localStorage.setItem("taskflow_user", JSON.stringify(user));
  },

  async request(endpoint, options = {}) {
    const url = `${API_BASE}${endpoint}`;
    const headers = {
      "Content-Type": "application/json",
      ...(options.headers || {}),
    };

    const token = this.getToken();
    if (token) {
      headers["Authorization"] = `Bearer ${token}`;
    }

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      const data = await response.json().catch(() => ({}));

      if (!response.ok) {
        if (response.status === 401) {
          // Token expired or invalid
          this.clearToken();
          if (!window.location.pathname.includes("login")) {
            window.showAuthSection?.("login");
          }
        }

        let errorMsg =
          data.detail || data.message || "An unexpected error occurred.";
        if (Array.isArray(errorMsg)) {
          errorMsg = errorMsg
            .map((err) => err.msg || JSON.stringify(err))
            .join(", ");
        }

        throw new Error(errorMsg);
      }

      return data;
    } catch (err) {
      console.error(
        `API Error on [${options.method || "GET"}] ${endpoint}:`,
        err,
      );
      throw err;
    }
  },
};

// Simple Toast Notification Manager
const Toast = {
  container: null,

  init() {
    if (!this.container) {
      this.container = document.getElementById("toast-container");
      if (!this.container) {
        this.container = document.createElement("div");
        this.container.id = "toast-container";
        this.container.className = "toast-container";
        document.body.appendChild(this.container);
      }
    }
  },

  show(message, type = "info", duration = 4000) {
    this.init();
    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;

    let icon = "ℹ️";
    if (type === "success") icon = "✅";
    if (type === "error") icon = "⚠️";
    if (type === "warning") icon = "⏳";

    toast.innerHTML = `
      <div style="display:flex; align-items:center; gap:8px;">
        <span>${icon}</span>
        <span>${message}</span>
      </div>
      <button style="background:none; border:none; color:#94a3b8; font-size:16px; cursor:pointer;" onclick="this.parentElement.remove()">✕</button>
    `;

    this.container.appendChild(toast);

    setTimeout(() => {
      if (toast.parentElement) {
        toast.style.opacity = "0";
        toast.style.transform = "translateX(50px)";
        toast.style.transition = "all 0.3s ease";
        setTimeout(() => toast.remove(), 300);
      }
    }, duration);
  },

  success(msg) {
    this.show(msg, "success");
  },
  error(msg) {
    this.show(msg, "error");
  },
  warning(msg) {
    this.show(msg, "warning");
  },
  info(msg) {
    this.show(msg, "info");
  },
};
