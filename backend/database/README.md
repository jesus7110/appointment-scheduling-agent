# Database Module

This module provides PostgreSQL database connectivity using SQLAlchemy for the appointment scheduling system.

## Setup

1. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Set up PostgreSQL database:**
   - Create a PostgreSQL database
   - Set the `DATABASE_URL` environment variable:
     ```bash
     export DATABASE_URL="postgresql://username:password@localhost:5432/appointment_scheduling"
     ```
   - Or create a `.env` file:
     ```
     DATABASE_URL=postgresql://username:password@localhost:5432/appointment_scheduling
     ```

3. **Initialize database tables:**
   - Option 1: Run the DDL script directly:
     ```bash
     psql -U postgres -d appointment_scheduling -f database/ddl.sql
     ```
   - Option 2: Use SQLAlchemy to create tables:
     ```python
     from backend.database import init_db
     init_db()
     ```

## Usage

### Basic Usage

```python
from backend.database import get_db_session, Appointment, ConversationHistory
from datetime import date, time

# Get a database session
db = get_db_session()

try:
    # Create an appointment
    appointment = Appointment(
        appointment_id="apt_12345",
        doctor_id="doctor-001",
        doctor_name="Dr. John Doe",
        specialty="Cardiology",
        clinic_id="clinic-001",
        clinic_name="City Clinic",
        clinic_address="123 Main St, City",
        patient_name="Jane Smith",
        patient_phone="+1234567890",
        patient_email="jane@example.com",
        date=date(2024, 1, 15),
        start_time=time(10, 0),
        end_time=time(10, 30),
        duration_minutes=30,
        confirmation_code="CONF123",
        consultation_fee=500
    )
    db.add(appointment)
    db.commit()
    
    # Create conversation history entry
    conversation = ConversationHistory(
        session_id="session_abc123",
        client_id="client_xyz",
        role="user",
        content="I need to book an appointment",
        message_order=1
    )
    db.add(conversation)
    db.commit()
    
finally:
    db.close()
```

### Using with FastAPI

```python
from fastapi import Depends
from backend.database import get_db, Appointment
from sqlalchemy.orm import Session

@app.get("/appointments/{appointment_id}")
def get_appointment(appointment_id: str, db: Session = Depends(get_db)):
    appointment = db.query(Appointment).filter(
        Appointment.appointment_id == appointment_id
    ).first()
    return appointment
```

### Query Examples

```python
from backend.database import get_db_session, Appointment, ConversationHistory
from datetime import date

db = get_db_session()

# Get all appointments for a specific date
appointments = db.query(Appointment).filter(
    Appointment.date == date(2024, 1, 15)
).all()

# Get all conversations for a session
conversations = db.query(ConversationHistory).filter(
    ConversationHistory.session_id == "session_abc123"
).order_by(ConversationHistory.message_order).all()

# Get appointments by status
confirmed_appointments = db.query(Appointment).filter(
    Appointment.status == "confirmed"
).all()

db.close()
```

## Tables

### `appointments`
Stores all appointment bookings with:
- Appointment details (date, time, duration)
- Doctor and clinic information
- Patient information
- Status tracking
- Timestamps

### `conversation_history`
Stores conversation messages with:
- Session ID and Client ID
- Message role (user/assistant/system)
- Message content
- Message order within session
- Timestamps

## Models

- `Appointment`: SQLAlchemy model for appointments table
- `ConversationHistory`: SQLAlchemy model for conversation_history table

## Functions

- `get_db()`: FastAPI dependency for database sessions
- `get_db_session()`: Get a database session directly
- `init_db()`: Initialize/create all database tables
- `close_db()`: Close database connections

