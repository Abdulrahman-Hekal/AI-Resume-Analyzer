/**
 * AI Resume Analyzer - Authentication & Session Manager
 */

const Auth = {
  async init() {
    Utils.highlightActiveNav();
    await Auth.renderNavUserSection();
  },

  /**
   * Enforce page protection for authenticated routes.
   */
  requireAuth() {
    const token = API.getToken();
    if (!token) {
      window.location.href = "login.html";
      return false;
    }
    return true;
  },

  /**
   * Render dynamic user section in navbar.
   */
  async renderNavUserSection() {
    const container = document.getElementById("navUserArea");
    if (!container) return;

    const token = API.getToken();
    let user = API.getUser();

    if (!token) {
      container.innerHTML = `
        <a href="login.html" class="btn btn-outline btn-sm">Log In</a>
        <a href="register.html" class="btn btn-primary btn-sm">Get Started</a>
      `;
      return;
    }

    // If token exists, refresh profile if needed
    if (!user) {
      try {
        user = await API.getMe();
        API.setUser(user);
      } catch (e) {
        API.clearToken();
        container.innerHTML = `
          <a href="login.html" class="btn btn-outline btn-sm">Log In</a>
          <a href="register.html" class="btn btn-primary btn-sm">Get Started</a>
        `;
        return;
      }
    }

    container.innerHTML = `
      <div class="user-badge">
        <span>👤 ${Utils.escapeHtml(user.full_name || user.email)}</span>
        <span class="user-badge-role">${Utils.escapeHtml(user.role || "user")}</span>
      </div>
      <button id="logoutBtn" class="btn btn-outline btn-sm" title="Log Out">Log Out</button>
    `;

    document
      .getElementById("logoutBtn")
      ?.addEventListener("click", Auth.handleLogout);
  },

  /**
   * Handle Login submission.
   */
  async handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById("loginEmail").value.trim();
    const password = document.getElementById("loginPassword").value;
    const submitBtn = document.getElementById("loginSubmitBtn");
    const errorBox = document.getElementById("authErrorBox");

    if (!email || !password) {
      errorBox.textContent = "Please provide both email and password.";
      errorBox.style.display = "block";
      return;
    }

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span class="spinner"></span> Signing In...`;
      errorBox.style.display = "none";

      const res = await API.login({ email, password });
      API.setToken(res.access_token);
      API.setUser(res.user);

      window.location.href = "dashboard.html";
    } catch (err) {
      errorBox.textContent =
        err.message || "Failed to sign in. Please check your credentials.";
      errorBox.style.display = "block";
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Sign In";
    }
  },

  /**
   * Handle Registration submission.
   */
  async handleRegister(e) {
    e.preventDefault();
    const full_name = document.getElementById("regFullName").value.trim();
    const email = document.getElementById("regEmail").value.trim();
    const password = document.getElementById("regPassword").value;
    const submitBtn = document.getElementById("regSubmitBtn");
    const errorBox = document.getElementById("authErrorBox");

    if (!full_name || !email || !password) {
      errorBox.textContent = "All fields are required.";
      errorBox.style.display = "block";
      return;
    }

    try {
      submitBtn.disabled = true;
      submitBtn.innerHTML = `<span class="spinner"></span> Creating Account...`;
      errorBox.style.display = "none";

      const res = await API.register({ email, password, full_name, role: "user" });
      API.setToken(res.access_token);
      API.setUser(res.user);

      window.location.href = "dashboard.html";
    } catch (err) {
      errorBox.textContent =
        err.message || "Registration failed. Please try again.";
      errorBox.style.display = "block";
    } finally {
      submitBtn.disabled = false;
      submitBtn.textContent = "Create Account";
    }
  },

  /**
   * Log out user.
   */
  async handleLogout() {
    try {
      await API.logout();
    } catch (e) {
      // Ignore network errors on logout
    }
    API.clearToken();
    window.location.href = "index.html";
  },
};

window.Auth = Auth;
document.addEventListener("DOMContentLoaded", Auth.init);
