"""
Test script to verify appointment creation and database table.
"""
import asyncio
import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text
from database.db_service import AsyncSessionLocal
from database.models import Appointment
from utils.appointment_manager import create_appointment
from datetime import date, time

async def test_table_exists():
    """Check if appointments table exists."""
    print("=" * 60)
    print("Testing if appointments table exists...")
    print("=" * 60)
    
    try:
        async with AsyncSessionLocal() as session:
            # Try to query the table
            result = await session.execute(text("SELECT COUNT(*) FROM appointments"))
            count = result.scalar()
            print(f"✅ Table 'appointments' exists! Current count: {count}")
            return True
    except Exception as e:
        print(f"❌ Error accessing appointments table: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

async def test_appointment_creation():
    """Test creating an appointment."""
    print("\n" + "=" * 60)
    print("Testing appointment creation...")
    print("=" * 60)
    
    try:
        result = await create_appointment(
            doctor_id="doctor-001",
            clinic_id="clinic-001",
            patient_name="Test Patient",
            patient_phone="1234567890",
            patient_email="test@example.com",
            appointment_date=date(2025, 12, 25),
            appointment_time=time(14, 0),
            patient_age=30,
        )
        
        print(f"Result: {result}")
        
        if result.get("success"):
            print(f"✅ Appointment created successfully!")
            print(f"   Appointment ID: {result.get('appointment_id')}")
            print(f"   Confirmation Code: {result.get('confirmation_code')}")
        else:
            print(f"❌ Appointment creation failed!")
            print(f"   Error: {result.get('error')}")
            
        return result.get("success", False)
        
    except Exception as e:
        print(f"❌ Exception during appointment creation: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_query_appointments():
    """Test querying appointments from database."""
    print("\n" + "=" * 60)
    print("Testing querying appointments...")
    print("=" * 60)
    
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(
                text("SELECT appointment_id, patient_name, date, start_time FROM appointments ORDER BY created_at DESC LIMIT 5")
            )
            rows = result.fetchall()
            
            if rows:
                print(f"✅ Found {len(rows)} recent appointments:")
                for row in rows:
                    print(f"   - {row[0]}: {row[1]} on {row[2]} at {row[3]}")
            else:
                print("⚠️  No appointments found in database")
                
    except Exception as e:
        print(f"❌ Error querying appointments: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run all tests."""
    print("\n" + "=" * 60)
    print("APPOINTMENT CREATION TEST")
    print("=" * 60 + "\n")
    
    # Test 1: Check if table exists
    table_exists = await test_table_exists()
    
    if not table_exists:
        print("\n❌ Table doesn't exist. Please run the DDL script to create it.")
        return
    
    # Test 2: Query existing appointments
    await test_query_appointments()
    
    # Test 3: Create a test appointment
    success = await test_appointment_creation()
    
    if success:
        # Test 4: Query again to see if appointment was saved
        await test_query_appointments()
    
    print("\n" + "=" * 60)
    print("TEST COMPLETE")
    print("=" * 60)

if __name__ == "__main__":
    asyncio.run(main())

