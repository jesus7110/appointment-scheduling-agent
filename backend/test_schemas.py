"""
Simple test to verify schemas can load and validate JSON data.

Run: python backend/test_schemas.py
"""
import json
from pathlib import Path
from models.schemas import ClinicData, DoctorData

def test_schemas():
    """Test that schemas can load and validate the JSON data files."""
    print("=" * 60)
    print("Testing Pydantic Schemas with JSON Data")
    print("=" * 60)
    
    # Get paths
    backend_dir = Path(__file__).parent
    clinic_file = backend_dir / "data" / "clinic_info.json"
    doctor_file = backend_dir / "data" / "doctor_schedule.json"
    
    # Test 1: Load and validate clinic data
    print("\n📋 Test 1: Loading clinic_info.json...")
    try:
        with open(clinic_file) as f:
            clinic_json = json.load(f)
        
        clinic_data = ClinicData(**clinic_json)
        print(f"✅ Success! Loaded {len(clinic_data.clinics)} clinics")
        
        # Display first clinic
        first_clinic = clinic_data.clinics[0]
        print(f"\n   Example clinic:")
        print(f"   - Name: {first_clinic.name}")
        print(f"   - Location: {first_clinic.address.area}, {first_clinic.address.city}")
        print(f"   - Specialties: {', '.join(first_clinic.specialties[:3])}...")
        print(f"   - Contact: {first_clinic.contact.phone}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    # Test 2: Load and validate doctor data
    print("\n📋 Test 2: Loading doctor_schedule.json...")
    try:
        with open(doctor_file) as f:
            doctor_json = json.load(f)
        
        doctor_data = DoctorData(**doctor_json)
        print(f"✅ Success! Loaded {len(doctor_data.doctors)} doctors")
        
        # Display first doctor
        first_doctor = doctor_data.doctors[0]
        print(f"\n   Example doctor:")
        print(f"   - Name: {first_doctor.name}")
        print(f"   - Specialty: {first_doctor.specialty}")
        print(f"   - Experience: {first_doctor.experience_years} years")
        print(f"   - Fee: ₹{first_doctor.consultation_fee}")
        print(f"   - Clinic: {first_doctor.clinic_name}")
        print(f"   - Languages: {', '.join(first_doctor.languages)}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    # Test 3: Validate data structure integrity
    print("\n📋 Test 3: Validating data integrity...")
    try:
        # Check that all doctors reference valid clinics
        clinic_ids = {clinic.id for clinic in clinic_data.clinics}
        doctor_clinic_ids = {doctor.clinic_id for doctor in doctor_data.doctors}
        
        invalid_refs = doctor_clinic_ids - clinic_ids
        if invalid_refs:
            print(f"⚠️  Warning: Found doctors referencing non-existent clinics: {invalid_refs}")
        else:
            print(f"✅ All doctor clinic references are valid")
        
        # Count doctors by specialty
        from collections import Counter
        specialty_counts = Counter(doctor.specialty for doctor in doctor_data.doctors)
        print(f"\n   Doctors by specialty:")
        for specialty, count in specialty_counts.most_common():
            print(f"   - {specialty}: {count}")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    # Test 4: Test serialization (convert back to dict)
    print("\n📋 Test 4: Testing serialization...")
    try:
        # Convert a clinic back to dict
        clinic_dict = first_clinic.model_dump()
        print(f"✅ Serialization works")
        print(f"   Clinic as dict has {len(clinic_dict)} keys")
        
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    print("\n" + "=" * 60)
    print("✅ All tests passed! Schemas are working correctly.")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_schemas()
    exit(0 if success else 1)

