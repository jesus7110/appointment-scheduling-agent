"""
Quick diagnostic script to check appointments table structure and test insertion.
"""
import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import text, inspect
from database.db_service import AsyncSessionLocal, async_engine
from database.models import Appointment

async def check_table_structure():
    """Check if appointments table exists and show its structure."""
    print("=" * 60)
    print("Checking appointments table structure...")
    print("=" * 60)
    
    try:
        async with AsyncSessionLocal() as session:
            # Check if table exists
            result = await session.execute(
                text("""
                    SELECT column_name, data_type, is_nullable, column_default
                    FROM information_schema.columns
                    WHERE table_name = 'appointments'
                    ORDER BY ordinal_position
                """)
            )
            columns = result.fetchall()
            
            if columns:
                print(f"\n✅ Table 'appointments' exists with {len(columns)} columns:\n")
                for col in columns:
                    nullable = "NULL" if col[2] == "YES" else "NOT NULL"
                    default = f" DEFAULT {col[3]}" if col[3] else ""
                    print(f"  - {col[0]}: {col[1]} {nullable}{default}")
            else:
                print("❌ Table 'appointments' does not exist or has no columns")
                return False
                
            # Check current row count
            count_result = await session.execute(text("SELECT COUNT(*) FROM appointments"))
            count = count_result.scalar()
            print(f"\n📊 Current appointments count: {count}")
            
            return True
            
    except Exception as e:
        print(f"❌ Error checking table: {e}")
        import traceback
        traceback.print_exc()
        return False

async def test_direct_insert():
    """Test inserting directly into the table."""
    print("\n" + "=" * 60)
    print("Testing direct SQL insert...")
    print("=" * 60)
    
    try:
        async with AsyncSessionLocal() as session:
            # Try a simple insert
            await session.execute(
                text("""
                    INSERT INTO appointments (
                        appointment_id, doctor_id, doctor_name, specialty,
                        clinic_id, clinic_name, clinic_address,
                        patient_name, patient_phone, patient_email,
                        date, start_time, end_time, duration_minutes,
                        status, confirmation_code, consultation_fee,
                        created_at, updated_at
                    ) VALUES (
                        'APP-TEST-001', 'doctor-001', 'Test Doctor', 'Cardiology',
                        'clinic-001', 'Test Clinic', '123 Test St',
                        'Test Patient', '1234567890', 'test@test.com',
                        '2025-12-25', '14:00:00', '14:30:00', 30,
                        'confirmed', 'TEST01', 1500,
                        CURRENT_TIMESTAMP, CURRENT_TIMESTAMP
                    )
                """)
            )
            await session.commit()
            print("✅ Direct SQL insert successful!")
            
            # Verify it was inserted
            result = await session.execute(
                text("SELECT appointment_id, patient_name FROM appointments WHERE appointment_id = 'APP-TEST-001'")
            )
            row = result.fetchone()
            if row:
                print(f"✅ Verified: Found appointment {row[0]} for {row[1]}")
            else:
                print("⚠️  Insert appeared successful but row not found")
                
            # Clean up
            await session.execute(text("DELETE FROM appointments WHERE appointment_id = 'APP-TEST-001'"))
            await session.commit()
            print("✅ Test row cleaned up")
            
            return True
            
    except Exception as e:
        print(f"❌ Direct SQL insert failed: {e}")
        import traceback
        traceback.print_exc()
        return False

async def check_model_mapping():
    """Check if SQLAlchemy model matches table structure."""
    print("\n" + "=" * 60)
    print("Checking SQLAlchemy model mapping...")
    print("=" * 60)
    
    try:
        inspector = inspect(async_engine.sync_engine)
        table_columns = {col['name']: col for col in inspector.get_columns('appointments')}
        
        print(f"\n📋 Table columns from database: {list(table_columns.keys())}")
        
        # Get model columns
        model_columns = {col.name: col for col in Appointment.__table__.columns}
        print(f"📋 Model columns from SQLAlchemy: {list(model_columns.keys())}")
        
        # Check for mismatches
        table_cols_set = set(table_columns.keys())
        model_cols_set = set(model_columns.keys())
        
        if table_cols_set == model_cols_set:
            print("\n✅ Model and table columns match!")
        else:
            missing_in_table = model_cols_set - table_cols_set
            missing_in_model = table_cols_set - model_cols_set
            
            if missing_in_table:
                print(f"\n⚠️  Columns in model but not in table: {missing_in_table}")
            if missing_in_model:
                print(f"⚠️  Columns in table but not in model: {missing_in_model}")
                
    except Exception as e:
        print(f"❌ Error checking model mapping: {e}")
        import traceback
        traceback.print_exc()

async def main():
    """Run diagnostics."""
    print("\n" + "=" * 60)
    print("APPOINTMENTS TABLE DIAGNOSTICS")
    print("=" * 60 + "\n")
    
    # Check table structure
    table_exists = await check_table_structure()
    
    if not table_exists:
        print("\n❌ Table check failed. Please verify the table exists.")
        return
    
    # Check model mapping
    await check_model_mapping()
    
    # Test direct insert
    await test_direct_insert()
    
    print("\n" + "=" * 60)
    print("DIAGNOSTICS COMPLETE")
    print("=" * 60)
    print("\n💡 Next steps:")
    print("   1. Check backend logs when booking an appointment")
    print("   2. Look for error messages in the logs")
    print("   3. Verify the error message shows what's failing")

if __name__ == "__main__":
    asyncio.run(main())

