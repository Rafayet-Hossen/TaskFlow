# ⚡ TaskFlow - Smart Task Manager

TaskFlow is a modern, high-performance task management web application built with **FastAPI**, **PostgreSQL / SQLite**, and a responsive **HTML5/CSS3/JavaScript** frontend designed exclusively with the **Quicksand** typography.

---

## ✨ Features

1. **🔐 Authentication & User Accounts**:
   - Secure account registration with Full Name, Email, and Bcrypt password hashing.
   - **Email Verification**: After signing up, users receive a 6-digit PIN to verify their email address before accessing the system.
   - **Password Recovery**: Dedicated "Forgot Password" and "Reset Password" workflow with 6-digit one-time PINs.
   - Stateless **JWT (JSON Web Token)** authentication session management.

2. **📋 Full Task CRUD & User Relations**:
   - Every task is strictly isolated and foreign-keyed to the authenticated user's account (`user_id` $\rightarrow$ `users.id`).
   - Fields: Title, Description, Priority (`low`, `medium`, `high`), Status (`pending`, `in_progress`, `completed`), Start Date & Time, Deadline (End Date & Time).
   - Fast one-click status toggle directly from the card.
   - Edit modal and Delete confirmation modal.

3. **⏱️ Real-Time Countdown & Dynamic Urgency Color Coding**:
   - Live 1-second interval ticking countdown showing remaining time (`2d 4h 12m`, `04h 32m 10s`, `45m 12s`).
   - **Dynamic Urgency Color Coding**:
     - 🔴 **Red**: $\le 1$ hour remaining (Urgent / Imminent deadline).
     - 🟡 **Yellow**: $\le 6$ hours remaining (Due soon warning).
     - 🟢 **Green**: $\le 24$ hours remaining (Due today).
     - ⚪ **Normal / Slate**: $> 24$ hours remaining.
     - 🚨 **Overdue**: Past deadline indicator.
     - ✅ **Completed**: Muted status with strike-through.

4. **⚡ Ascending Deadline Sorting**:
   - Tasks are automatically ordered by **ascending remaining time** (the closest deadline always appears first).

5. **🎨 Modern UI & Quicksand Typography**:
   - Google Fonts **Quicksand** applied globally.
   - Live search bar and filter pills (All, Urgent $\le 1$h, Soon $\le 6$h, Today $\le 24$h, Pending, In Progress, Completed).
   - Real-time statistics overview cards.

---

## 🛠️ Tech Stack

- **Backend**: FastAPI (Python 3.13+)
- **ORM & Database**: SQLAlchemy with PostgreSQL (`psycopg2-binary`) & automatic SQLite fallback for zero-friction local development
- **Security**: Direct Bcrypt password hashing + PyJWT token issuance
- **Email Service**: Asynchronous SMTP dispatch via `aiosmtplib` with Developer Console & Banner logging
- **Frontend**: Vanilla HTML5, Modern CSS3, Modular JavaScript (ES6+)
- **Typography**: Quicksand (Google Fonts)

---

## 🚀 Getting Started

### 1. Prerequisites

- Python 3.10+
- PostgreSQL (Optional for local testing; SQLite fallback is built-in)

### 2. Setup Virtual Environment

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
```

### 3. Environment Variables

Copy `.env.example` to `.env`:

```bash
cp .env.example .env
```

Configure your PostgreSQL database and SMTP credentials (optional):

```env
DATABASE_URL=postgresql://postgres:postgres@localhost:5432/taskflow_db
SECRET_KEY=your-secure-secret-key-at-least-64-characters-long
DEV_MODE=True

# (Optional) Real SMTP for Gmail / Mailtrap
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your_email@gmail.com
SMTP_PASSWORD=your_app_password
```

> **Note on Dev Mode**: When `DEV_MODE=True`, verification codes and password reset PINs are displayed on the screen banner and printed directly to the terminal for instant zero-configuration testing.

### 4. Run the Application

```bash
./scripts/run.sh
# or
uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
```

Open your browser at:
👉 **[http://localhost:8000](http://localhost:8000)**

---

## 🧪 Automated Testing

Run the automated end-to-end API test suite:

```bash
.venv/bin/python scripts/test_app.py
```

This verifies:

- User registration & verification code generation
- Email verification & token issuance
- Login authentication & profile access
- Password reset PIN validation & password updating
- Task CRUD operations
- Dynamic countdown categorization (Red, Yellow, Green, Normal)
- Ascending deadline sorting
