/**
 * TaskFlow Countdown & Dynamic Urgency Engine
 * 
 * Rules:
 *  - Red:      <= 1 hour remaining
 *  - Yellow:   <= 6 hours remaining (> 1h)
 *  - Green:    <= 24 hours remaining (> 6h)
 *  - Normal:   > 24 hours remaining
 *  - Overdue:  <= 0 seconds remaining
 *  - Sorting:  Ascending order by remaining time (closest deadline first)
 */

const TimerEngine = {
  intervalId: null,

  /**
   * Robustly parses any ISO datetime string from server as UTC
   */
  parseUTCDate(dateInput) {
    if (!dateInput) return new Date();
    if (dateInput instanceof Date) return dateInput;
    let str = String(dateInput).trim();
    str = str.replace(" ", "T");
    // If no timezone specified, append Z so browser treats it as UTC
    if (!str.endsWith("Z") && !/[+-]\d{2}:?\d{2}$/.test(str)) {
      str += "Z";
    }
    return new Date(str);
  },

  /**
   * Calculates remaining time and urgency metadata for a given task.
   */
  calculate(endDateString, status = "pending") {
    const now = new Date();
    const end = this.parseUTCDate(endDateString);
    const diffMs = end.getTime() - now.getTime();
    const remainingSeconds = Math.floor(diffMs / 1000);

    if (status === "completed") {
      return {
        remainingSeconds,
        urgency: "completed",
        cssClass: "status-completed",
        label: "✅ Completed",
        badgeText: "Done",
        isOverdue: false
      };
    }

    if (remainingSeconds <= 0) {
      const overdueSecs = Math.abs(remainingSeconds);
      return {
        remainingSeconds,
        urgency: "overdue",
        cssClass: "urgency-overdue",
        label: `🚨 Overdue: ${this.formatDuration(overdueSecs)}`,
        badgeText: `Overdue -${this.formatDuration(overdueSecs)}`,
        isOverdue: true
      };
    }

    // <= 1 hour (3600 seconds) -> RED
    if (remainingSeconds <= 3600) {
      return {
        remainingSeconds,
        urgency: "red",
        cssClass: "urgency-red",
        label: `🔥 ${this.formatDuration(remainingSeconds)} left`,
        badgeText: `⏳ ${this.formatDuration(remainingSeconds)}`,
        isOverdue: false
      };
    }

    // <= 6 hours (21600 seconds) -> YELLOW
    if (remainingSeconds <= 21600) {
      return {
        remainingSeconds,
        urgency: "yellow",
        cssClass: "urgency-yellow",
        label: `⚡ ${this.formatDuration(remainingSeconds)} left`,
        badgeText: `⏳ ${this.formatDuration(remainingSeconds)}`,
        isOverdue: false
      };
    }

    // <= 24 hours (86400 seconds) -> GREEN
    if (remainingSeconds <= 86400) {
      return {
        remainingSeconds,
        urgency: "green",
        cssClass: "urgency-green",
        label: `🟢 ${this.formatDuration(remainingSeconds)} left`,
        badgeText: `⏳ ${this.formatDuration(remainingSeconds)}`,
        isOverdue: false
      };
    }

    // > 24 hours -> NORMAL
    return {
      remainingSeconds,
      urgency: "normal",
      cssClass: "urgency-normal",
      label: `⏱️ ${this.formatDuration(remainingSeconds)} left`,
      badgeText: `⏳ ${this.formatDuration(remainingSeconds)}`,
      isOverdue: false
    };
  },

  /**
   * Formats seconds into human-readable countdown string (e.g. 2d 4h 12m or 45m 12s)
   */
  formatDuration(seconds) {
    const d = Math.floor(seconds / 86400);
    const h = Math.floor((seconds % 86400) / 3600);
    const m = Math.floor((seconds % 3600) / 60);
    const s = Math.floor(seconds % 60);

    const pad = (n) => String(n).padStart(2, '0');

    if (d > 0) {
      return `${d}d ${pad(h)}h ${pad(m)}m`;
    }
    if (h > 0) {
      return `${pad(h)}h ${pad(m)}m ${pad(s)}s`;
    }
    return `${pad(m)}m ${pad(s)}s`;
  },

  /**
   * Sorts a list of tasks in ascending order by remaining deadline time.
   * Tasks with closest deadline appear first.
   */
  sortTasksByRemainingTime(tasks) {
    return [...tasks].sort((a, b) => {
      // Completed tasks appear at the end
      if (a.status === "completed" && b.status !== "completed") return 1;
      if (b.status === "completed" && a.status !== "completed") return -1;

      const dateA = this.parseUTCDate(a.end_date).getTime();
      const dateB = this.parseUTCDate(b.end_date).getTime();
      return dateA - dateB; // Ascending order
    });
  },

  /**
   * Starts a 1-second ticking loop to update countdowns smoothly
   */
  startTicking(updateCallback) {
    if (this.intervalId) {
      clearInterval(this.intervalId);
    }
    this.intervalId = setInterval(() => {
      if (typeof updateCallback === "function") {
        updateCallback();
      }
    }, 1000);
  },

  stopTicking() {
    if (this.intervalId) {
      clearInterval(this.intervalId);
      this.intervalId = null;
    }
  }
};
