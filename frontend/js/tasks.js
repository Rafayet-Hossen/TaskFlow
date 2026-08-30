/**
 * TaskFlow Tasks Controller
 */

const Tasks = {
  tasks: [],
  currentFilter: "all",
  currentPriority: "all",
  searchQuery: "",
  editingTaskId: null,
  deletingTaskId: null,

  init() {
    this.bindEvents();
  },

  bindEvents() {
    // New Task Modal Opener
    const newTaskBtn = document.getElementById("new-task-btn");
    if (newTaskBtn) {
      newTaskBtn.addEventListener("click", () => this.openTaskModal());
    }

    // Task Form Submit (Create & Update)
    const taskForm = document.getElementById("task-form");
    if (taskForm) {
      taskForm.addEventListener("submit", (e) => this.handleSaveTask(e));
    }

    // Modal Close buttons
    document.querySelectorAll("[data-close-modal]").forEach((btn) => {
      btn.addEventListener("click", (e) => {
        const modalId = btn.getAttribute("data-close-modal");
        this.closeModal(modalId);
      });
    });

    // Delete Confirmation Button
    const confirmDeleteBtn = document.getElementById("confirm-delete-btn");
    if (confirmDeleteBtn) {
      confirmDeleteBtn.addEventListener("click", () =>
        this.confirmDeleteTask(),
      );
    }

    // Search Input
    const searchInput = document.getElementById("task-search-input");
    if (searchInput) {
      let debounceTimer;
      searchInput.addEventListener("input", (e) => {
        clearTimeout(debounceTimer);
        debounceTimer = setTimeout(() => {
          this.searchQuery = e.target.value.toLowerCase().trim();
          this.renderTasks();
        }, 200);
      });
    }

    // Filter Pills
    document.querySelectorAll(".pill-btn[data-filter]").forEach((pill) => {
      pill.addEventListener("click", (e) => {
        document
          .querySelectorAll(".pill-btn[data-filter]")
          .forEach((p) => p.classList.remove("active"));
        pill.classList.add("active");
        this.currentFilter = pill.getAttribute("data-filter");
        this.renderTasks();
      });
    });

    // Priority Filter
    const prioritySelect = document.getElementById("filter-priority-select");
    if (prioritySelect) {
      prioritySelect.addEventListener("change", (e) => {
        this.currentPriority = e.target.value;
        this.renderTasks();
      });
    }

    // Start Realtime Countdown Engine
    TimerEngine.startTicking(() => this.updateCountdownsAndOrder());
  },

  async loadTasks() {
    try {
      const data = await API.request("/api/tasks");
      this.tasks = data || [];
      this.renderTasks();
      this.updateStats();
    } catch (err) {
      Toast.error(`Failed to load tasks: ${err.message}`);
    }
  },

  updateStats() {
    const stats = {
      total: this.tasks.length,
      urgent: 0,
      soon: 0,
      today: 0,
      completed: 0,
    };

    this.tasks.forEach((task) => {
      if (task.status === "completed") {
        stats.completed++;
      } else {
        const timerData = TimerEngine.calculate(task.end_date, task.status);
        if (timerData.urgency === "red" || timerData.urgency === "overdue") {
          stats.urgent++;
        } else if (timerData.urgency === "yellow") {
          stats.soon++;
        } else if (timerData.urgency === "green") {
          stats.today++;
        }
      }
    });

    const elTotal = document.getElementById("stat-total");
    const elUrgent = document.getElementById("stat-urgent");
    const elSoon = document.getElementById("stat-soon");
    const elToday = document.getElementById("stat-today");
    const elCompleted = document.getElementById("stat-completed");

    if (elTotal) elTotal.textContent = stats.total;
    if (elUrgent) elUrgent.textContent = stats.urgent;
    if (elSoon) elSoon.textContent = stats.soon;
    if (elToday) elToday.textContent = stats.today;
    if (elCompleted) elCompleted.textContent = stats.completed;
  },

  getFilteredTasks() {
    return this.tasks.filter((task) => {
      // Status filter
      if (this.currentFilter !== "all") {
        if (this.currentFilter === "urgent") {
          const timer = TimerEngine.calculate(task.end_date, task.status);
          if (
            task.status === "completed" ||
            (timer.urgency !== "red" && timer.urgency !== "overdue")
          ) {
            return false;
          }
        } else if (this.currentFilter === "soon") {
          const timer = TimerEngine.calculate(task.end_date, task.status);
          if (task.status === "completed" || timer.urgency !== "yellow") {
            return false;
          }
        } else if (this.currentFilter === "today") {
          const timer = TimerEngine.calculate(task.end_date, task.status);
          if (task.status === "completed" || timer.urgency !== "green") {
            return false;
          }
        } else if (task.status !== this.currentFilter) {
          return false;
        }
      }

      // Priority filter
      if (
        this.currentPriority !== "all" &&
        task.priority !== this.currentPriority
      ) {
        return false;
      }

      // Search filter
      if (this.searchQuery) {
        const titleMatch = task.title.toLowerCase().includes(this.searchQuery);
        const descMatch = (task.description || "")
          .toLowerCase()
          .includes(this.searchQuery);
        if (!titleMatch && !descMatch) return false;
      }

      return true;
    });
  },

  renderTasks() {
    const grid = document.getElementById("tasks-grid");
    if (!grid) return;

    let filtered = this.getFilteredTasks();
    // Sort in ascending order by deadline (closest deadline first)
    filtered = TimerEngine.sortTasksByRemainingTime(filtered);

    if (filtered.length === 0) {
      grid.innerHTML = `
        <div class="empty-state">
          <div class="empty-icon">📝</div>
          <h3>No tasks found</h3>
          <p>${this.tasks.length === 0 ? "You haven't created any tasks yet. Click 'New Task' to get started!" : "No tasks match your current filter and search."}</p>
          ${this.tasks.length === 0 ? `<button class="btn btn-primary" onclick="Tasks.openTaskModal()">+ Add Your First Task</button>` : ""}
        </div>
      `;
      this.updateStats();
      return;
    }

    grid.innerHTML = filtered
      .map((task) => this.renderTaskCardHTML(task))
      .join("");
    this.updateStats();
  },

  renderTaskCardHTML(task) {
    const timer = TimerEngine.calculate(task.end_date, task.status);
    const startDateFormatted = this.formatDateTime(task.start_date);
    const endDateFormatted = this.formatDateTime(task.end_date);
    const isChecked = task.status === "completed" ? "checked" : "";

    return `
      <div class="task-card ${timer.cssClass}" id="task-card-${task.id}" data-task-id="${task.id}" data-end-date="${task.end_date}" data-status="${task.status}">
        <div>
          <div class="task-card-top">
            <div class="countdown-badge" id="badge-${task.id}">
              <span class="urgency-indicator-dot" style="width: 8px; height: 8px; border-radius: 50%; display: inline-block;"></span>
              <span class="badge-time-text">${timer.badgeText}</span>
            </div>
            <span class="priority-tag priority-${task.priority}">${task.priority}</span>
          </div>

          <h3 class="task-title" id="title-${task.id}">${this.escapeHtml(task.title)}</h3>
          
          ${task.description ? `<p class="task-description">${this.escapeHtml(task.description)}</p>` : ""}

          <div class="task-dates">
            <div class="date-row">
              <span>Start:</span>
              <strong>${startDateFormatted}</strong>
            </div>
            <div class="date-row">
              <span>Deadline:</span>
              <strong>${endDateFormatted}</strong>
            </div>
          </div>
        </div>

        <div class="task-card-footer">
          <label class="status-checkbox-label">
            <input type="checkbox" ${isChecked} onchange="Tasks.toggleTaskStatus(${task.id}, this.checked)">
            <span>${task.status === "completed" ? "Completed" : "Mark as Done"}</span>
          </label>
          <div class="task-actions">
            <button class="icon-btn" title="Edit Task" onclick="Tasks.openEditModal(${task.id})">✏️</button>
            <button class="icon-btn delete" title="Delete Task" onclick="Tasks.openDeleteModal(${task.id})">🗑️</button>
          </div>
        </div>
      </div>
    `;
  },

  /**
   * Called every 1s by TimerEngine to update countdown badge text and urgency colors seamlessly
   */
  updateCountdownsAndOrder() {
    const cards = document.querySelectorAll(".task-card");
    if (!cards || cards.length === 0) return;

    cards.forEach((card) => {
      const taskId = card.getAttribute("data-task-id");
      const endDate = card.getAttribute("data-end-date");
      const status = card.getAttribute("data-status");

      if (endDate) {
        const timer = TimerEngine.calculate(endDate, status);

        // Update classes
        card.className = `task-card ${timer.cssClass}`;

        const badgeText = card.querySelector(".badge-time-text");
        if (badgeText) {
          badgeText.textContent = timer.badgeText;
        }
      }
    });
  },

  formatDateTime(dateStr) {
    if (!dateStr) return "";
    const d = TimerEngine.parseUTCDate(dateStr);
    return d.toLocaleString([], {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  },

  formatForDatetimeInput(dateInput) {
    if (!dateInput) return "";
    const d = TimerEngine.parseUTCDate(dateInput);
    const pad = (n) => String(n).padStart(2, "0");
    return `${d.getFullYear()}-${pad(d.getMonth() + 1)}-${pad(d.getDate())}T${pad(d.getHours())}:${pad(d.getMinutes())}`;
  },

  openTaskModal() {
    this.editingTaskId = null;
    document.getElementById("modal-task-title").textContent = "Create New Task";
    document.getElementById("task-title-input").value = "";
    document.getElementById("task-desc-input").value = "";
    document.getElementById("task-priority-input").value = "medium";
    document.getElementById("task-status-input").value = "pending";

    // Set smart defaults for dates:
    // Start Date = Now
    // End Date = Now + 6 hours
    const now = new Date();
    const defaultEnd = new Date(now.getTime() + 6 * 60 * 60 * 1000);

    document.getElementById("task-start-input").value =
      this.formatForDatetimeInput(now);
    document.getElementById("task-end-input").value =
      this.formatForDatetimeInput(defaultEnd);

    this.openModal("task-modal");
  },

  openEditModal(taskId) {
    const task = this.tasks.find((t) => t.id === taskId);
    if (!task) return;

    this.editingTaskId = taskId;
    document.getElementById("modal-task-title").textContent = "Edit Task";
    document.getElementById("task-title-input").value = task.title;
    document.getElementById("task-desc-input").value = task.description || "";
    document.getElementById("task-priority-input").value = task.priority;
    document.getElementById("task-status-input").value = task.status;
    document.getElementById("task-start-input").value =
      this.formatForDatetimeInput(task.start_date);
    document.getElementById("task-end-input").value =
      this.formatForDatetimeInput(task.end_date);

    this.openModal("task-modal");
  },

  openDeleteModal(taskId) {
    this.deletingTaskId = taskId;
    const task = this.tasks.find((t) => t.id === taskId);
    const titleEl = document.getElementById("delete-task-name");
    if (titleEl && task) {
      titleEl.textContent = `"${task.title}"`;
    }
    this.openModal("delete-modal");
  },

  async handleSaveTask(e) {
    e.preventDefault();
    const title = document.getElementById("task-title-input").value.trim();
    const description = document.getElementById("task-desc-input").value.trim();
    const priority = document.getElementById("task-priority-input").value;
    const status = document.getElementById("task-status-input").value;
    const start_date_raw = document.getElementById("task-start-input").value;
    const end_date_raw = document.getElementById("task-end-input").value;

    if (!title || !start_date_raw || !end_date_raw) {
      Toast.error("Please fill in the title, start date, and deadline.");
      return;
    }

    const start_date = new Date(start_date_raw).toISOString();
    const end_date = new Date(end_date_raw).toISOString();

    if (new Date(end_date) < new Date(start_date)) {
      Toast.error("Task deadline cannot be earlier than start date.");
      return;
    }

    const payload = {
      title,
      description: description || null,
      priority,
      status,
      start_date,
      end_date,
    };

    try {
      const saveBtn = e.target.querySelector("button[type='submit']");
      saveBtn.disabled = true;
      saveBtn.textContent = "Saving...";

      if (this.editingTaskId) {
        const updated = await API.request(`/api/tasks/${this.editingTaskId}`, {
          method: "PUT",
          body: JSON.stringify(payload),
        });
        const idx = this.tasks.findIndex((t) => t.id === this.editingTaskId);
        if (idx !== -1) this.tasks[idx] = updated;
        Toast.success("Task updated successfully!");
      } else {
        const created = await API.request("/api/tasks", {
          method: "POST",
          body: JSON.stringify(payload),
        });
        this.tasks.push(created);
        Toast.success("Task created successfully!");
      }

      this.closeModal("task-modal");
      this.renderTasks();
    } catch (err) {
      Toast.error(err.message);
    } finally {
      const saveBtn = e.target.querySelector("button[type='submit']");
      if (saveBtn) {
        saveBtn.disabled = false;
        saveBtn.textContent = "Save Task";
      }
    }
  },

  async toggleTaskStatus(taskId, isCompleted) {
    const newStatus = isCompleted ? "completed" : "pending";
    try {
      const updated = await API.request(`/api/tasks/${taskId}/status`, {
        method: "PATCH",
        body: JSON.stringify({ status: newStatus }),
      });

      const idx = this.tasks.findIndex((t) => t.id === taskId);
      if (idx !== -1) {
        this.tasks[idx] = updated;
      }

      Toast.success(
        isCompleted
          ? "Task marked as completed! 🎉"
          : "Task marked as pending.",
      );
      this.renderTasks();
    } catch (err) {
      Toast.error(`Failed to update status: ${err.message}`);
      this.renderTasks(); // Revert checkbox state
    }
  },

  async confirmDeleteTask() {
    if (!this.deletingTaskId) return;

    try {
      const btn = document.getElementById("confirm-delete-btn");
      btn.disabled = true;
      btn.textContent = "Deleting...";

      await API.request(`/api/tasks/${this.deletingTaskId}`, {
        method: "DELETE",
      });

      this.tasks = this.tasks.filter((t) => t.id !== this.deletingTaskId);
      Toast.success("Task deleted successfully.");
      this.closeModal("delete-modal");
      this.renderTasks();
    } catch (err) {
      Toast.error(`Failed to delete task: ${err.message}`);
    } finally {
      const btn = document.getElementById("confirm-delete-btn");
      if (btn) {
        btn.disabled = false;
        btn.textContent = "Delete";
      }
      this.deletingTaskId = null;
    }
  },

  openModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.add("show");
    }
  },

  closeModal(modalId) {
    const modal = document.getElementById(modalId);
    if (modal) {
      modal.classList.remove("show");
    }
  },

  escapeHtml(str) {
    if (!str) return "";
    return str
      .replace(/&/g, "&amp;")
      .replace(/</g, "&lt;")
      .replace(/>/g, "&gt;")
      .replace(/"/g, "&quot;")
      .replace(/'/g, "&#039;");
  },
};
