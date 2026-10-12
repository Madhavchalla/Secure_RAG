import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from app.main import app, init_database_seeds
from app.core.config import settings

def run_seed():
    print("=" * 60)
    print("SEEDING SYNTHETIC ENTERPRISE DATASET INTO RAS-RAG")
    print("=" * 60)

    # 1. Initialize tables and seed users (admin and analyst)
    init_database_seeds()
    client = TestClient(app)

    # 2. Login as admin
    login_res = client.post("/api/auth/login", json={
        "username": settings.DEFAULT_ADMIN_USERNAME,
        "password": settings.DEFAULT_ADMIN_PASSWORD,
    })
    admin_token = login_res.json()["access_token"]
    admin_headers = {"Authorization": f"Bearer {admin_token}"}

    docs_dir = os.path.join(os.path.dirname(__file__), "..", "data", "synthetic_docs")

    # 3. Upload clean leave policy (LOW Sensitivity, assigned to user)
    leave_path = os.path.join(docs_dir, "01_leave_and_attendance_policy.txt")
    with open(leave_path, "rb") as f:
        res = client.post(
            "/api/documents/upload",
            headers=admin_headers,
            files={"file": ("01_leave_and_attendance_policy.txt", f, "text/plain")},
            data={"sensitivity_level": "LOW", "assign_role": "user"}
        )
    print("  [+] Uploaded Leave Policy (LOW Sensitivity, Accessible to Users):", res.status_code)

    # 4. Upload IT security policy (MEDIUM Sensitivity, assigned to user)
    it_path = os.path.join(docs_dir, "02_it_security_and_password_policy.txt")
    with open(it_path, "rb") as f:
        res = client.post(
            "/api/documents/upload",
            headers=admin_headers,
            files={"file": ("02_it_security_and_password_policy.txt", f, "text/plain")},
            data={"sensitivity_level": "MEDIUM", "assign_role": "user"}
        )
    print("  [+] Uploaded IT Security Policy (MEDIUM Sensitivity, Accessible to Users):", res.status_code)

    # 5. Upload Executive Salary (HIGH Sensitivity, Admin Only - assign_role is empty)
    salary_path = os.path.join(docs_dir, "04_executive_payroll_and_salary_structure.txt")
    with open(salary_path, "rb") as f:
        res = client.post(
            "/api/documents/upload",
            headers=admin_headers,
            files={"file": ("04_executive_payroll_and_salary_structure.txt", f, "text/plain")},
            data={"sensitivity_level": "HIGH", "assign_role": ""}
        )
    print("  [+] Uploaded Executive Salary (HIGH Sensitivity, Admin Only):", res.status_code)

    # 6. Upload Malicious Prompt Injection Test File (Quarantine Test)
    malicious_path = os.path.join(docs_dir, "06_malicious_prompt_injection_test.txt")
    with open(malicious_path, "rb") as f:
        res = client.post(
            "/api/documents/upload",
            headers=admin_headers,
            files={"file": ("06_malicious_prompt_injection_test.txt", f, "text/plain")},
            data={"sensitivity_level": "HIGH", "assign_role": "user"}
        )
    print("  [+] Uploaded Injection Test File (Held in Quarantine Queue):", res.status_code)

    print("\n[SUCCESS] SYNTHETIC DATASET SEEDED SUCCESSFULLY!")

if __name__ == "__main__":
    run_seed()
