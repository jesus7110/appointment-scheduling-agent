# Appointment Manager Guide

## Overview

The `appointment_manager.py` module provides all functions needed for booking and managing appointments. It's designed to be used by tools that the LLM can call.

## Functions Available

### 1. **`generate_appointment_id()` → str**
Generates unique appointment IDs in format `APP-00001`, `APP-00002`, etc.

```python
from utils.appointment_manager import generate_appointment_id

appointment_id = generate_appointment_id()
# Returns: "APP-00001"
```

### 2. **`create_appointment(...)` → Dict**
Creates and stores an appointment in the database.

**Required Parameters:**
- `doctor_id`: str
- `clinic_id`: str
- `patient_name`: str
- `patient_phone`: str
- `patient_email`: str
- `appointment_date`: date
- `appointment_time`: time

**Optional Parameters:**
- `patient_age`: int
- `patient_notes`: str
- `notes`: str

**Returns:**
```python
{
    "success": True,
    "appointment_id": "APP-00001",
    "confirmation_code": "A1B2C3",
    "appointment": {
        "appointment_id": "APP-00001",
        "doctor_name": "Dr. Rajesh Kumar",
        "date": "2025-01-25",
        "start_time": "10:00",
        "confirmation_code": "A1B2C3",
        ...
    }
}
```

### 3. **`get_appointment_by_id(appointment_id: str)` → Dict**
Fetches appointment by appointment ID.

### 4. **`get_appointments_by_patient_name(patient_name: str)` → List[Dict]**
Fetches appointments by patient name (partial match).

### 5. **`get_appointments_by_date(appointment_date: date)` → List[Dict]**
Fetches all appointments for a specific date.

### 6. **`get_appointments_by_patient_phone(patient_phone: str)` → List[Dict]**
Fetches appointments by patient phone number.

### 7. **`validate_booking_data(booking_data: Dict)` → Dict**
Validates that all required fields are present and correctly formatted.

**Returns:**
```python
{
    "valid": True/False,
    "missing_fields": ["patient_email", "appointment_time"],
    "errors": ["patient_email must be a valid email address"]
}
```

### 8. **`check_appointment_conflict(...)` → bool**
Checks if a time slot conflicts with existing appointments.

### 9. **`cancel_appointment(appointment_id: str, reason: str)` → Dict**
Cancels an appointment.

---

## Required Fields for Booking

The following fields are **required** to book an appointment:

1. **`doctor_id`** - Which doctor
2. **`clinic_id`** - Which clinic
3. **`patient_name`** - Patient's full name
4. **`patient_phone`** - Patient's phone number
5. **`patient_email`** - Patient's email address
6. **`appointment_date`** - Date (YYYY-MM-DD format)
7. **`appointment_time`** - Time (HH:MM format)

**Optional but recommended:**
- `patient_age` - Patient's age
- `patient_notes` - Any medical notes
- `notes` - Appointment-specific notes

---

## Improving Agent's Approach

### Current Problem
The agent might not collect all required information before attempting to book, leading to incomplete bookings or multiple back-and-forth messages.

### Solution: Validation Before Booking

**Step 1: Add validation to booking tool**

When the LLM wants to book, first validate:

```python
# In tool_executor.py _book_appointment method:

from utils.appointment_manager import validate_booking_data

# Before creating appointment, validate
validation = validate_booking_data(booking_data)

if not validation["valid"]:
    return {
        "success": False,
        "error": "Missing required information",
        "missing_fields": validation["missing_fields"],
        "errors": validation["errors"],
        "message": f"To complete booking, I need: {', '.join(validation['missing_fields'])}"
    }
```

**Step 2: Add a "check_booking_readiness" tool**

Create a tool that checks if all required info is collected:

```python
CHECK_BOOKING_READINESS_TOOL = {
    "type": "function",
    "function": {
        "name": "check_booking_readiness",
        "description": "Check if all required information is collected to book an appointment. Use this before attempting to book.",
        "parameters": {
            "type": "object",
            "properties": {
                "doctor_id": {"type": "string"},
                "clinic_id": {"type": "string"},
                "patient_name": {"type": "string"},
                "patient_phone": {"type": "string"},
                "patient_email": {"type": "string"},
                "appointment_date": {"type": "string"},
                "appointment_time": {"type": "string"},
            },
            "required": []
        }
    }
}
```

**Step 3: Update system prompt**

Add to system prompt:

```
**Booking Process:**
1. Collect all required information: doctor, clinic, patient name, phone, email, date, time
2. Use check_booking_readiness tool to verify all fields are present
3. Only call book_appointment when all fields are validated
4. If fields are missing, ask the user specifically for those fields
```

---

## Example Usage Flow

### Complete Booking Flow:

```python
# 1. User: "I want to book with Dr. Kumar on Monday at 10 AM"
# LLM collects: doctor_id, date, time

# 2. LLM calls check_booking_readiness
validation = validate_booking_data({
    "doctor_id": "doctor-001",
    "appointment_date": "2025-01-27",
    "appointment_time": "10:00"
})
# Returns: missing_fields = ["clinic_id", "patient_name", "patient_phone", "patient_email"]

# 3. LLM: "I have the doctor and time. I need your name, phone, and email to complete the booking."

# 4. User provides info
# LLM collects: patient_name, patient_phone, patient_email

# 5. LLM calls check_booking_readiness again
validation = validate_booking_data({...all fields...})
# Returns: valid = True

# 6. LLM calls book_appointment
result = await create_appointment(...)
# Returns: success with appointment_id and confirmation_code

# 7. LLM: "Your appointment is confirmed! Appointment ID: APP-00001, Confirmation Code: A1B2C3"
```

---

## Integration with Tools

These functions will be used by booking tools:

1. **`book_appointment` tool** - Uses `create_appointment()`
2. **`check_appointment` tool** - Uses `get_appointment_by_id()`
3. **`find_my_appointments` tool** - Uses `get_appointments_by_patient_name()` or `get_appointments_by_patient_phone()`
4. **`cancel_appointment` tool** - Uses `cancel_appointment()`

---

## Error Handling

All functions return structured responses:

**Success:**
```python
{"success": True, "appointment_id": "...", ...}
```

**Failure:**
```python
{"success": False, "error": "Error message", ...}
```

Always check `success` field before proceeding.

