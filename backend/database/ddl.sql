-- ============================================================================
-- DDL Script for Appointment Scheduling Database
-- PostgreSQL Database Schema
-- ============================================================================

-- Create database (run this separately if needed)
-- CREATE DATABASE appointment_scheduling;

-- ============================================================================
-- Table: appointments
-- ============================================================================
-- Stores all appointment bookings

CREATE TABLE IF NOT EXISTS appointments (
    id SERIAL PRIMARY KEY,
    appointment_id VARCHAR(100) UNIQUE NOT NULL,
    
    -- Doctor information
    doctor_id VARCHAR(100) NOT NULL,
    doctor_name VARCHAR(200) NOT NULL,
    specialty VARCHAR(100) NOT NULL,
    
    -- Clinic information
    clinic_id VARCHAR(100) NOT NULL,
    clinic_name VARCHAR(200) NOT NULL,
    clinic_address TEXT NOT NULL,
    
    -- Patient information
    patient_name VARCHAR(200) NOT NULL,
    patient_phone VARCHAR(50) NOT NULL,
    patient_email VARCHAR(200) NOT NULL,
    patient_age INTEGER,
    patient_notes TEXT,
    
    -- Appointment details
    date DATE NOT NULL,
    start_time TIME NOT NULL,
    end_time TIME NOT NULL,
    duration_minutes INTEGER NOT NULL DEFAULT 30,
    
    -- Status and confirmation
    status VARCHAR(20) NOT NULL DEFAULT 'confirmed' 
        CHECK (status IN ('pending', 'confirmed', 'cancelled', 'completed', 'no_show')),
    confirmation_code VARCHAR(50) UNIQUE NOT NULL,
    
    -- Financial
    consultation_fee INTEGER NOT NULL,
    
    -- Additional notes
    notes TEXT,
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    cancelled_at TIMESTAMP,
    
    -- Indexes
    CONSTRAINT appointments_appointment_id_key UNIQUE (appointment_id),
    CONSTRAINT appointments_confirmation_code_key UNIQUE (confirmation_code)
);

-- Indexes for appointments table
CREATE INDEX IF NOT EXISTS idx_appointments_appointment_id ON appointments(appointment_id);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor_id ON appointments(doctor_id);
CREATE INDEX IF NOT EXISTS idx_appointments_clinic_id ON appointments(clinic_id);
CREATE INDEX IF NOT EXISTS idx_appointments_specialty ON appointments(specialty);
CREATE INDEX IF NOT EXISTS idx_appointments_date ON appointments(date);
CREATE INDEX IF NOT EXISTS idx_appointments_status ON appointments(status);
CREATE INDEX IF NOT EXISTS idx_appointments_patient_phone ON appointments(patient_phone);
CREATE INDEX IF NOT EXISTS idx_appointments_patient_email ON appointments(patient_email);
CREATE INDEX IF NOT EXISTS idx_appointments_confirmation_code ON appointments(confirmation_code);
CREATE INDEX IF NOT EXISTS idx_appointments_created_at ON appointments(created_at);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_appointments_date_status ON appointments(date, status);
CREATE INDEX IF NOT EXISTS idx_appointments_doctor_date ON appointments(doctor_id, date);
CREATE INDEX IF NOT EXISTS idx_appointments_patient_email ON appointments(patient_email);


-- ============================================================================
-- Table: conversation_history
-- ============================================================================
-- Stores conversation messages with sessionId and clientId

CREATE TABLE IF NOT EXISTS conversation_history (
    id SERIAL PRIMARY KEY,
    
    -- Session and client identifiers
    session_id VARCHAR(100) NOT NULL,
    client_id VARCHAR(100) NOT NULL,
    
    -- Message details
    role VARCHAR(20) NOT NULL CHECK (role IN ('user', 'assistant', 'system')),
    content TEXT NOT NULL,
    
    -- Metadata
    message_order INTEGER NOT NULL,
    metadata_json TEXT,  -- Additional metadata as JSON string
    
    -- Timestamps
    created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
);

-- Indexes for conversation_history table
CREATE INDEX IF NOT EXISTS idx_conversation_session_id ON conversation_history(session_id);
CREATE INDEX IF NOT EXISTS idx_conversation_client_id ON conversation_history(client_id);
CREATE INDEX IF NOT EXISTS idx_conversation_created_at ON conversation_history(created_at);
CREATE INDEX IF NOT EXISTS idx_conversation_role ON conversation_history(role);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_conversation_session_order ON conversation_history(session_id, message_order);
CREATE INDEX IF NOT EXISTS idx_conversation_client_created ON conversation_history(client_id, created_at);
CREATE INDEX IF NOT EXISTS idx_conversation_session_created ON conversation_history(session_id, created_at);


-- ============================================================================
-- Table: session_info
-- ============================================================================
-- Stores high-level information about a chat/session:
-- - session_id and client_id
-- - when session started and ended
-- - optional device / browser / IP / user agent / location
-- - generic metadata JSON

CREATE TABLE IF NOT EXISTS session_info (
    id SERIAL PRIMARY KEY,

    -- Identifiers
    session_id VARCHAR(100) UNIQUE NOT NULL,
    client_id VARCHAR(100) NOT NULL,

    -- Timestamps
    started_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    last_activity_at TIMESTAMP,

    -- Optional metadata
    device VARCHAR(200),
    browser VARCHAR(200),
    ip_address VARCHAR(100),
    user_agent TEXT,
    location VARCHAR(200),

    -- Generic metadata JSON (string stored, application parses as needed)
    metadata_json TEXT
);

-- Indexes for session_info table
CREATE INDEX IF NOT EXISTS idx_session_info_session_id ON session_info(session_id);
CREATE INDEX IF NOT EXISTS idx_session_info_client_id ON session_info(client_id);
CREATE INDEX IF NOT EXISTS idx_session_info_started_at ON session_info(started_at);
CREATE INDEX IF NOT EXISTS idx_session_info_ended_at ON session_info(ended_at);
CREATE INDEX IF NOT EXISTS idx_session_info_last_activity_at ON session_info(last_activity_at);

-- Composite indexes for common queries
CREATE INDEX IF NOT EXISTS idx_session_info_client_started
    ON session_info(client_id, started_at);
CREATE INDEX IF NOT EXISTS idx_session_info_client_last_activity
    ON session_info(client_id, last_activity_at);
CREATE INDEX IF NOT EXISTS idx_session_info_started_ended
    ON session_info(started_at, ended_at);


-- ============================================================================
-- Function: Update updated_at timestamp
-- ============================================================================
-- Automatically update the updated_at column when a row is modified

CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = CURRENT_TIMESTAMP;
    RETURN NEW;
END;
$$ language 'plpgsql';

-- Trigger to automatically update updated_at
DROP TRIGGER IF EXISTS update_appointments_updated_at ON appointments;

CREATE TRIGGER update_appointments_updated_at 
BEFORE UPDATE ON appointments
FOR EACH ROW
EXECUTE FUNCTION update_updated_at_column();


-- ============================================================================
-- Sample Queries (for reference)
-- ============================================================================

-- Get all appointments for a specific date
-- SELECT * FROM appointments WHERE date = '2024-01-15' ORDER BY start_time;

-- Get all appointments for a doctor
-- SELECT * FROM appointments WHERE doctor_id = 'doctor-001' ORDER BY date DESC, start_time;

-- Get conversation history for a session
-- SELECT * FROM conversation_history WHERE session_id = 'session_abc123' ORDER BY message_order;

-- Get all conversations for a client
-- SELECT DISTINCT session_id, created_at FROM conversation_history WHERE client_id = 'client_xyz' ORDER BY created_at DESC;

-- Get appointments by status
-- SELECT * FROM appointments WHERE status = 'confirmed' AND date >= CURRENT_DATE ORDER BY date, start_time;

