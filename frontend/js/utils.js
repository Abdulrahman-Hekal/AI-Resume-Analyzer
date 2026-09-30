/**
 * AI Resume Analyzer - Frontend Utilities
 */

const Utils = {
  /**
   * Display a clean toast message with auto-dismiss.
   * @param {string} message
   * @param {'success'|'error'|'info'} type
   * @param {number} durationMs
   */
  showToast(message, type = "info", durationMs = 4000) {
    let container = document.getElementById("toastContainer");
    if (!container) {
      container = document.createElement("div");
      container.id = "toastContainer";
      container.className = "toast-container";
      document.body.appendChild(container);
    }

    const toast = document.createElement("div");
    toast.className = `toast toast-${type}`;
    
    let icon = "ℹ";
    if (type === "success") icon = "✓";
    if (type === "error") icon = "⚠";

    toast.innerHTML = `
      <span style="font-weight:bold;">${icon}</span>
      <span style="flex:1;">${Utils.escapeHtml(message)}</span>
    `;

    container.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = "0";
      toast.style.transform = "translateY(10px)";
      toast.style.transition = "all 0.3s ease-out";
      setTimeout(() => toast.remove(), 300);
    }, durationMs);
  },

  /**
   * Safely escape HTML to prevent XSS.
   */
  escapeHtml(str) {
    if (!str) return "";
    const div = document.createElement("div");
    div.textContent = str;
    return div.innerHTML;
  },

  /**
   * Format human-readable date.
   */
  formatDate(dateStr) {
    if (!dateStr) return "N/A";
    const d = new Date(dateStr);
    return d.toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      year: "numeric"
    });
  },

  /**
   * Format file size in KB or MB.
   */
  formatFileSize(bytes) {
    if (!bytes || bytes === 0) return "0 Bytes";
    const k = 1024;
    const sizes = ["Bytes", "KB", "MB", "GB"];
    const i = Math.floor(Math.log(bytes) / Math.log(k));
    return parseFloat((bytes / Math.pow(k, i)).toFixed(1)) + " " + sizes[i];
  },

  /**
   * Returns HTML for colored score indicator.
   */
  renderScoreBadge(score) {
    const s = Math.round(score || 0);
    let cls = "low";
    if (s >= 75) cls = "high";
    else if (s >= 50) cls = "medium";
    return `<span class="score-badge ${cls}">${s}% Match</span>`;
  },

  /**
   * Open modal by ID.
   */
  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add("show");
      document.body.style.overflow = "hidden";
    }
  },

  /**
   * Close modal by ID.
   */
  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove("show");
      document.body.style.overflow = "";
    }
  },

  /**
   * Set active state on current navigation link.
   */
  highlightActiveNav() {
    const current = window.location.pathname.split("/").pop() || "index.html";
    document.querySelectorAll(".nav-link").forEach(link => {
      const href = link.getAttribute("href");
      if (href === current || (current === "" && href === "index.html")) {
        link.classList.add("active");
      } else {
        link.classList.remove("active");
      }
    });
  }
};

window.Utils = Utils;
