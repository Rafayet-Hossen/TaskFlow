/**
 * TaskFlow Authentication Controller
 */

const Auth = {
  currentEmail: "",

  init() {
    this.bindEvents();
    this.checkSession();
  },

  bindEvents() {
    // Navigation / View switchers
    document.querySelectorAll("[data-auth-view]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        e.preventDefault();
        const view = btn.getAttribute("data-auth-view");
        this.showView(view);
      });
    });

    // Form Submissions
    const loginForm = document.getElementById("login-form");
    if (loginForm) {
      loginForm.addEventListener("submit", (e) => this.handleLogin(e));
    }

    const registerForm = document.getElementById("register-form");
    if (registerForm) {
      registerForm.addEventListener("submit", (e) => this.handleRegister(e));
    }

    const verifyForm = document.getElementById("verify-form");
    if (verifyForm) {
      verifyForm.addEventListener("submit", (e) => this.handleVerify(e));
    }

    const resendBtn = document.getElementById("resend-code-btn");
    if (resendBtn) {
      resendBtn.addEventListener("click", (e) => this.handleResendCode(e));
    }

    const forgotForm = document.getElementById("forgot-form");
    if (forgotForm) {
      forgotForm.addEventListener("submit", (e) =>
        this.handleForgotPassword(e),
      );
    }

    const resetForm = document.getElementById("reset-form");
    if (resetForm) {
      resetForm.addEventListener("submit", (e) => this.handleResetPassword(e));
    }

    const logoutBtn = document.getElementById("logout-btn");
    if (logoutBtn) {
      logoutBtn.addEventListener("click", () => this.handleLogout());
    }

    // Auto-advance PIN inputs
    this.setupPinInputAutoAdvance();
  },

  setupPinInputAutoAdvance() {
    const setupPin = (selector) => {
      const inputs = document.querySelectorAll(selector);
      inputs.forEach((input, index) => {
        input.addEventListener("input", (e) => {
          if (e.target.value.length === 1 && index < inputs.length - 1) {
            inputs[index + 1].focus();
          }
        });
        input.addEventListener("keydown", (e) => {
          if (e.key === "Backspace" && !e.target.value && index > 0) {
            inputs[index - 1].focus();
          }
        });
        input.addEventListener("paste", (e) => {
          e.preventDefault();
          const pastedData = (e.clipboardData || window.clipboardData)
            .getData("text")
            .trim();
          if (/^\d+$/.test(pastedData)) {
            for (let i = 0; i < inputs.length; i++) {
              if (i < pastedData.length) {
                inputs[i].value = pastedData[i];
              }
            }
            if (pastedData.length >= inputs.length) {
              inputs[inputs.length - 1].focus();
            } else {
              inputs[pastedData.length]?.focus();
            }
          }
        });
      });
    };

    setupPin(".verify-pin-digit");
    setupPin(".reset-pin-digit");
  },

  getPinValue(selector) {
    const inputs = document.querySelectorAll(selector);
    let pin = "";
    inputs.forEach((input) => {
      pin += input.value.trim();
    });
    return pin;
  },

  setPinValue(selector, code) {
    const inputs = document.querySelectorAll(selector);
    const codeStr = String(code);
    inputs.forEach((input, idx) => {
      input.value = codeStr[idx] || "";
    });
  },

  showView(viewName) {
    // Hide all auth cards
    document.querySelectorAll(".auth-card-view").forEach((card) => {
      card.style.display = "none";
    });

    const target = document.getElementById(`view-${viewName}`);
    if (target) {
      target.style.display = "block";
    }

    // Toggle auth section vs dashboard section
    const authWrapper = document.getElementById("auth-wrapper");
    const dashboard = document.getElementById("dashboard-section");
    const navUserActions = document.getElementById("nav-user-actions");

    if (viewName === "dashboard") {
      if (authWrapper) authWrapper.style.display = "none";
      if (dashboard) dashboard.style.display = "block";
      if (navUserActions) navUserActions.style.display = "flex";
    } else {
      if (authWrapper) authWrapper.style.display = "flex";
      if (dashboard) dashboard.style.display = "none";
      if (navUserActions) navUserActions.style.display = "none";
    }
  },

  async checkSession() {
    const token = API.getToken();
    if (!token) {
      this.showView("login");
      return;
    }

    try {
      const user = await API.request("/api/auth/me");
      API.setUser(user);
      this.renderUserBadge(user);
      this.showView("dashboard");
      Tasks.loadTasks();
    } catch (err) {
      console.warn("Session check failed, navigating to login:", err);
      API.clearToken();
      this.showView("login");
    }
  },

  renderUserBadge(user) {
    const nameEl = document.getElementById("user-display-name");
    const avatarEl = document.getElementById("user-avatar-initial");
    if (nameEl) nameEl.textContent = user.full_name;
    if (avatarEl)
      avatarEl.textContent = (user.full_name || "U")[0].toUpperCase();
  },

  async handleRegister(e) {
    e.preventDefault();
    const name = document.getElementById("reg-name").value.trim();
    const email = document.getElementById("reg-email").value.trim();
    const password = document.getElementById("reg-password").value;

    if (!name || !email || !password) {
      Toast.error("Please fill in all fields.");
      return;
    }

    try {
      const submitBtn = e.target.querySelector("button[type='submit']");
      submitBtn.disabled = true;
      submitBtn.textContent = "Creating Account...";

      const res = await API.request("/api/auth/register", {
        method: "POST",
        body: JSON.stringify({ full_name: name, email, password }),
      });

      this.currentEmail = email;
      const verifyEmailDisplay = document.getElementById(
        "verify-email-display",
      );
      if (verifyEmailDisplay) verifyEmailDisplay.textContent = email;

      Toast.success(
        res.message ||
          "Account created! A verification code has been sent to your email.",
      );
      this.showView("verify");
    } catch (err) {
      Toast.error(err.message);
    } finally {
      const submitBtn = e.target.querySelector("button[type='submit']");
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Sign Up";
      }
    }
  },

  async handleVerify(e) {
    e.preventDefault();
    const code = this.getPinValue(".verify-pin-digit");
    if (code.length < 6) {
      Toast.error("Please enter the complete 6-digit code sent to your email.");
      return;
    }

    try {
      const submitBtn = e.target.querySelector("button[type='submit']");
      submitBtn.disabled = true;
      submitBtn.textContent = "Verifying...";

      const res = await API.request("/api/auth/verify-email", {
        method: "POST",
        body: JSON.stringify({ email: this.currentEmail, code }),
      });

      API.setToken(res.access_token);
      API.setUser(res.user);
      this.renderUserBadge(res.user);

      Toast.success("Email verified successfully! Welcome to TaskFlow.");
      this.showView("dashboard");
      Tasks.loadTasks();
    } catch (err) {
      Toast.error(err.message);
    } finally {
      const submitBtn = e.target.querySelector("button[type='submit']");
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Verify & Continue";
      }
    }
  },

  async handleResendCode(e) {
    e.preventDefault();
    if (!this.currentEmail) {
      Toast.error("Email address missing. Please sign up or log in again.");
      return;
    }

    try {
      const res = await API.request("/api/auth/resend-code", {
        method: "POST",
        body: JSON.stringify({ email: this.currentEmail }),
      });

      Toast.success(
        res.message || "A new 6-digit code has been sent to your email.",
      );
    } catch (err) {
      Toast.error(err.message);
    }
  },

  async handleLogin(e) {
    e.preventDefault();
    const email = document.getElementById("login-email").value.trim();
    const password = document.getElementById("login-password").value;

    if (!email || !password) {
      Toast.error("Please enter both email and password.");
      return;
    }

    try {
      const submitBtn = e.target.querySelector("button[type='submit']");
      submitBtn.disabled = true;
      submitBtn.textContent = "Signing In...";

      const res = await API.request("/api/auth/login", {
        method: "POST",
        body: JSON.stringify({ email, password }),
      });

      API.setToken(res.access_token);
      API.setUser(res.user);
      this.renderUserBadge(res.user);

      Toast.success(`Welcome back, ${res.user.full_name}!`);
      this.showView("dashboard");
      Tasks.loadTasks();
    } catch (err) {
      if (err.message.includes("verified")) {
        this.currentEmail = email;
        const verifyEmailDisplay = document.getElementById(
          "verify-email-display",
        );
        if (verifyEmailDisplay) verifyEmailDisplay.textContent = email;
        this.showView("verify");
      }
      Toast.error(err.message);
    } finally {
      const submitBtn = e.target.querySelector("button[type='submit']");
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Sign In";
      }
    }
  },

  async handleForgotPassword(e) {
    e.preventDefault();
    const email = document.getElementById("forgot-email").value.trim();
    if (!email) {
      Toast.error("Please enter your registered email address.");
      return;
    }

    try {
      const submitBtn = e.target.querySelector("button[type='submit']");
      submitBtn.disabled = true;
      submitBtn.textContent = "Sending Code...";

      const res = await API.request("/api/auth/forgot-password", {
        method: "POST",
        body: JSON.stringify({ email }),
      });

      this.currentEmail = email;
      const resetEmailInput = document.getElementById("reset-email");
      if (resetEmailInput) resetEmailInput.value = email;

      Toast.success(res.message);
      this.showView("reset-password");
    } catch (err) {
      Toast.error(err.message);
    } finally {
      const submitBtn = e.target.querySelector("button[type='submit']");
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Send Reset Code";
      }
    }
  },

  async handleResetPassword(e) {
    e.preventDefault();
    const email =
      document.getElementById("reset-email").value.trim() || this.currentEmail;
    const code = this.getPinValue(".reset-pin-digit");
    const new_password = document.getElementById("reset-new-password").value;

    if (!email || code.length < 6 || !new_password) {
      Toast.error("Please enter email, 6-digit code, and new password.");
      return;
    }

    try {
      const submitBtn = e.target.querySelector("button[type='submit']");
      submitBtn.disabled = true;
      submitBtn.textContent = "Resetting Password...";

      const res = await API.request("/api/auth/reset-password", {
        method: "POST",
        body: JSON.stringify({ email, code, new_password }),
      });

      // Remove dev banner
      document.getElementById("dev-code-banner")?.remove();

      Toast.success(res.message);
      this.showView("login");
    } catch (err) {
      Toast.error(err.message);
    } finally {
      const submitBtn = e.target.querySelector("button[type='submit']");
      if (submitBtn) {
        submitBtn.disabled = false;
        submitBtn.textContent = "Reset Password";
      }
    }
  },

  handleLogout() {
    API.clearToken();
    TimerEngine.stopTicking();
    document.getElementById("dev-code-banner")?.remove();
    Toast.info("You have been logged out.");
    this.showView("login");
  },
};

window.showAuthSection = (view) => Auth.showView(view);
