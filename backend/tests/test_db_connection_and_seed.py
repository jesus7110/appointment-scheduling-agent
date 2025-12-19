"""
Utility script to:
- Load DATABASE_URL from .env (expected in backend/.env)
- Test PostgreSQL connection via SQLAlchemy
- Run the DDL file to create/update tables
- Insert a few sample rows into the tables

Usage (from project root):
    python -m backend.tests.test_db_connection_and_seed
or:
    python backend/tests/test_db_connection_and_seed.py
"""

import os
from pathlib import Path

from dotenv import load_dotenv
from sqlalchemy import create_engine, text
from sqlalchemy.exc import SQLAlchemyError


def load_database_url() -> str:
    """
    Load DATABASE_URL from .env.

    Priority:
    1. backend/.env                  (your current setup)
    2. Any default .env in project root
    3. Existing environment variable
    """
    project_root = Path(__file__).resolve().parents[2]

    # 1) Try backend/.env explicitly
    backend_env_path = project_root / ".env"
    if backend_env_path.exists():
        load_dotenv(backend_env_path)
    else:
        # 2) Fallback: standard .env discovery (project root, etc.)
        load_dotenv()

    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        raise RuntimeError(
            "DATABASE_URL is not set. "
            "Make sure it is defined in backend/.env or your environment."
        )
    return db_url


def test_connection(db_url: str) -> None:
    """
    Test that we can connect to PostgreSQL using SQLAlchemy.
    """
    print(f"Using DATABASE_URL: {db_url}")

    engine = create_engine(db_url, future=True)

    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1"))
            value = result.scalar_one()
            print(f"Connection OK, test query returned: {value}")
    except SQLAlchemyError as e:
        print("Failed to connect to the database:")
        print(e)
        raise
    finally:
        engine.dispose()


def run_ddl_and_seed(db_url: str) -> None:
    """
    Run ddl.sql to create tables and insert a bit of sample data.
    """
    project_root = Path(__file__).resolve().parents[1]
    ddl_path = project_root / "database" / "ddl.sql"

    if not ddl_path.exists():
        raise FileNotFoundError(f"DDL file not found at {ddl_path}")

    ddl_sql = ddl_path.read_text(encoding="utf-8")

    engine = create_engine(db_url, future=True)

    try:
        # 1) Run DDL (can contain multiple statements)
        print(f"Running DDL from: {ddl_path}")
        with engine.begin() as conn:
            conn.exec_driver_sql(ddl_sql)
        print("DDL executed successfully (tables should now exist).")

        # 2) Insert some sample data
        print("Inserting sample rows into appointments and conversation_history...")
        with engine.begin() as conn:
            # Sample appointment
            conn.execute(
                text(
                    """
                    INSERT INTO appointments (
                        appointment_id,
                        doctor_id,
                        doctor_name,
                        specialty,
                        clinic_id,
                        clinic_name,
                        clinic_address,
                        patient_name,
                        patient_phone,
                        patient_email,
                        patient_age,
                        patient_notes,
                        date,
                        start_time,
                        end_time,
                        duration_minutes,
                        status,
                        confirmation_code,
                        consultation_fee,
                        notes
                    ) VALUES (
                        :appointment_id,
                        :doctor_id,
                        :doctor_name,
                        :specialty,
                        :clinic_id,
                        :clinic_name,
                        :clinic_address,
                        :patient_name,
                        :patient_phone,
                        :patient_email,
                        :patient_age,
                        :patient_notes,
                        CURRENT_DATE,
                        '10:00',
                        '10:30',
                        30,
                        'confirmed',
                        :confirmation_code,
                        500,
                        'Test appointment created by seed script'
                    )
                    ON CONFLICT (appointment_id) DO NOTHING;
                    """
                ),
                {
                    "appointment_id": "apt_seed_001",
                    "doctor_id": "doctor-seed-001",
                    "doctor_name": "Dr. Seed Example",
                    "specialty": "General Medicine",
                    "clinic_id": "clinic-seed-001",
                    "clinic_name": "Seed Clinic",
                    "clinic_address": "123 Seed Street, Test City",
                    "patient_name": "Test Patient",
                    "patient_phone": "+910000000000",
                    "patient_email": "test.patient@example.com",
                    "patient_age": 30,
                    "patient_notes": "Initial test patient",
                    "confirmation_code": "SEEDCONF001",
                },
            )

            # Sample conversation history (two messages in same session)
            conn.execute(
                text(
                    """
                    INSERT INTO conversation_history (
                        session_id,
                        client_id,
                        role,
                        content,
                        message_order,
                        metadata_json
                    ) VALUES
                        ('session_seed_001', 'client_seed_001', 'user',
                         'Hi, I want to book an appointment.', 1, NULL),
                        ('session_seed_001', 'client_seed_001', 'assistant',
                         'Sure, I can help you with that!', 2, NULL)
                    ON CONFLICT DO NOTHING;
                    """
                )
            )

        print("Sample data inserted successfully.")
    except SQLAlchemyError as e:
        print("Error while running DDL or inserting seed data:")
        print(e)
        raise
    finally:
        engine.dispose()


def main() -> None:
    db_url = load_database_url()

    print("=== Step 1: Testing database connection ===")
    test_connection(db_url)

    print("\n=== Step 2: Running DDL and seeding sample data ===")
    run_ddl_and_seed(db_url)

    print("\nAll done. You can now inspect the tables:")
    print("- appointments")
    print("- conversation_history")


if __name__ == "__main__":
    main()


