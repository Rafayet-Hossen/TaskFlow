"""
Comprehensive automated test suite for TaskFlow API.
Tests Authentication, Verification, Password Reset, and Task CRUD with Deadline Sorting.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta, timezone

# Add project root to path
ROOT_DIR = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT_DIR))

from fastapi.testclient import TestClient
from backend.main import app
from backend.database import Base, engine, SessionLocal
from backend.models import User, VerificationCode, Task

client = TestClient(app)

def run_tests():
    print("🚀 Starting TaskFlow Automated Verification Tests...")
    
    # 1. Reset database tables for clean test
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)
    print("✅ Database initialized successfully.")

    # 2. Health check
    res = client.get("/api/health")
    assert res.status_code == 200, f"Health check failed: {res.text}"
    print("✅ /api/health passed.")

    # 3. User Registration
    test_email = "alex.developer@example.com"
    reg_payload = {
        "full_name": "Alex Developer",
        "email": test_email,
        "password": "Password123!"
    }
    res = client.post("/api/auth/register", json=reg_payload)
    assert res.status_code == 201, f"Registration failed: {res.text}"
    
    # Retrieve verification code from DB (sent to user email)
    db = SessionLocal()
    user_entry = db.query(User).filter(User.email == test_email).first()
    assert user_entry is not None
    code_entry = db.query(VerificationCode).filter(
        VerificationCode.user_id == user_entry.id,
        VerificationCode.purpose == "email_verification",
        VerificationCode.is_used == False
    ).first()
    assert code_entry is not None, "Verification code not created in DB."
    verification_code = code_entry.code
    db.close()
    print(f"✅ User registered. Verification Code sent to email (retrieved from DB for test: {verification_code})")

    # 4. Attempt login before verification (should fail with 403)
    login_payload = {
        "email": test_email,
        "password": "Password123!"
    }
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 403, f"Expected 403 for unverified user, got: {res.status_code}"
    print("✅ Login blocked before verification (403 as expected).")

    # 5. Email Verification
    verify_payload = {
        "email": test_email,
        "code": verification_code
    }
    res = client.post("/api/auth/verify-email", json=verify_payload)
    assert res.status_code == 200, f"Verification failed: {res.text}"
    token_data = res.json()
    access_token = token_data["access_token"]
    assert access_token, "No access token returned after verification"
    print("✅ Email verified successfully & token received.")

    # 6. Login after verification
    res = client.post("/api/auth/login", json=login_payload)
    assert res.status_code == 200, f"Login failed: {res.text}"
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Login after verification successful.")

    # 7. Get user profile
    res = client.get("/api/auth/me", headers=headers)
    assert res.status_code == 200 and res.json()["email"] == test_email
    print(f"✅ Profile fetched for: {res.json()['full_name']}")

    # 8. Test Forgot & Reset Password
    res = client.post("/api/auth/forgot-password", json={"email": test_email})
    assert res.status_code == 200
    
    db = SessionLocal()
    reset_entry = db.query(VerificationCode).filter(
        VerificationCode.user_id == user_entry.id,
        VerificationCode.purpose == "password_reset",
        VerificationCode.is_used == False
    ).first()
    assert reset_entry is not None, "Reset code not generated in DB."
    reset_code = reset_entry.code
    db.close()
    print(f"✅ Password reset requested. Reset PIN sent to email (retrieved from DB for test: {reset_code})")

    res = client.post("/api/auth/reset-password", json={
        "email": test_email,
        "code": reset_code,
        "new_password": "NewSecretPassword456!"
    })
    assert res.status_code == 200
    print("✅ Password successfully reset.")

    # Verify new password login
    res = client.post("/api/auth/login", json={"email": test_email, "password": "NewSecretPassword456!"})
    assert res.status_code == 200
    token = res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}
    print("✅ Logged in with new password.")

    # 9. Create Tasks with different deadlines
    now = datetime.now(timezone.utc)
    
    # Task 1: Due in 30 minutes (Urgent Red)
    task1_payload = {
        "title": "Fix critical production bug",
        "description": "Resolve memory leak in worker pool",
        "priority": "high",
        "status": "pending",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(minutes=30)).isoformat()
    }
    res = client.post("/api/tasks", json=task1_payload, headers=headers)
    assert res.status_code == 201
    task1 = res.json()
    assert task1["urgency_category"] == "urgent_red", f"Expected urgent_red, got {task1['urgency_category']}"
    print("✅ Created Task 1 (Due in 30m -> Red).")

    # Task 2: Due in 4 hours (Warning Yellow)
    task2_payload = {
        "title": "Review team pull requests",
        "description": "Review auth flow PR and task CRUD PR",
        "priority": "medium",
        "status": "in_progress",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(hours=4)).isoformat()
    }
    res = client.post("/api/tasks", json=task2_payload, headers=headers)
    assert res.status_code == 201
    task2 = res.json()
    assert task2["urgency_category"] == "warning_yellow", f"Expected warning_yellow, got {task2['urgency_category']}"
    print("✅ Created Task 2 (Due in 4h -> Yellow).")

    # Task 3: Due in 16 hours (Today Green)
    task3_payload = {
        "title": "Deploy staging build",
        "description": "Run smoke tests on staging environment",
        "priority": "medium",
        "status": "pending",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(hours=16)).isoformat()
    }
    res = client.post("/api/tasks", json=task3_payload, headers=headers)
    assert res.status_code == 201
    task3 = res.json()
    assert task3["urgency_category"] == "today_green", f"Expected today_green, got {task3['urgency_category']}"
    print("✅ Created Task 3 (Due in 16h -> Green).")

    # Task 4: Due in 3 days (Normal)
    task4_payload = {
        "title": "Prepare sprint roadmap",
        "description": "Draft upcoming sprint milestones and deliverables",
        "priority": "low",
        "status": "pending",
        "start_date": now.isoformat(),
        "end_date": (now + timedelta(days=3)).isoformat()
    }
    res = client.post("/api/tasks", json=task4_payload, headers=headers)
    assert res.status_code == 201
    task4 = res.json()
    assert task4["urgency_category"] == "normal", f"Expected normal, got {task4['urgency_category']}"
    print("✅ Created Task 4 (Due in 3d -> Normal).")

    # 10. List Tasks and Verify Ascending Deadline Ordering
    res = client.get("/api/tasks", headers=headers)
    assert res.status_code == 200
    tasks = res.json()
    assert len(tasks) == 4, f"Expected 4 tasks, got {len(tasks)}"

    # Ascending check: task1 (30m) < task2 (4h) < task3 (16h) < task4 (3d)
    assert tasks[0]["id"] == task1["id"], "Task 1 (closest deadline) should be first."
    assert tasks[1]["id"] == task2["id"], "Task 2 should be second."
    assert tasks[2]["id"] == task3["id"], "Task 3 should be third."
    assert tasks[3]["id"] == task4["id"], "Task 4 should be fourth."
    print("✅ Tasks sorted in ascending order of deadline (closest first).")

    # 11. Update Task status
    res = client.patch(f"/api/tasks/{task1['id']}/status", json={"status": "completed"}, headers=headers)
    assert res.status_code == 200 and res.json()["status"] == "completed"
    print("✅ Task status updated to completed.")

    # 12. Delete Task
    res = client.delete(f"/api/tasks/{task4['id']}", headers=headers)
    assert res.status_code == 200
    print("✅ Task deleted successfully.")

    # Verify task count is now 3
    res = client.get("/api/tasks", headers=headers)
    assert len(res.json()) == 3
    print("✅ Final task count verified.")

    print("\n🎉 ALL 12 AUTOMATED TESTS PASSED SUCCESSFULLY! 🚀")

if __name__ == "__main__":
    run_tests()

