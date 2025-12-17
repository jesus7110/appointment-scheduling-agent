"""
Test script for data loader functions.

Run: python backend/test_data_loader.py
"""
from utils.data_loader import (
    load_clinics,
    load_doctors,
    load_general_info,
    get_clinic_by_id,
    get_doctor_by_id,
    get_doctors_by_specialty,
    search_doctors,
    get_all_specialties,
    get_summary_stats,
)


def test_data_loader():
    """Test all data loader functions."""
    print("=" * 60)
    print("Testing Data Loader")
    print("=" * 60)
    
    # Test 1: Load all data
    print("\n📋 Test 1: Loading all data...")
    try:
        clinics = load_clinics()
        doctors = load_doctors()
        general_info = load_general_info()
        
        print(f"✅ Loaded {len(clinics)} clinics")
        print(f"✅ Loaded {len(doctors)} doctors")
        print(f"✅ Loaded general info (timezone: {general_info.timezone})")
    except Exception as e:
        print(f"❌ Failed: {e}")
        return False
    
    # Test 2: Get clinic by ID
    print("\n📋 Test 2: Getting clinic by ID...")
    try:
        clinic = get_clinic_by_id("clinic-001")
        if clinic:
            print(f"✅ Found clinic: {clinic.name}")
            print(f"   Location: {clinic.address.area}, {clinic.address.city}")
        else:
            print("❌ Clinic not found")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 3: Get doctor by ID
    print("\n📋 Test 3: Getting doctor by ID...")
    try:
        doctor = get_doctor_by_id("doctor-001")
        if doctor:
            print(f"✅ Found doctor: {doctor.name}")
            print(f"   Specialty: {doctor.specialty}")
            print(f"   Fee: ₹{doctor.consultation_fee}")
        else:
            print("❌ Doctor not found")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 4: Search doctors by specialty
    print("\n📋 Test 4: Searching doctors by specialty (Cardiology)...")
    try:
        cardio_doctors = get_doctors_by_specialty("Cardiology")
        print(f"✅ Found {len(cardio_doctors)} cardiologists:")
        for doc in cardio_doctors[:3]:
            print(f"   - {doc.name} at {doc.clinic_name}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 5: Search doctors with multiple filters
    print("\n📋 Test 5: Complex search (Pediatrics, max fee ₹1000)...")
    try:
        results = search_doctors(
            specialty="Pediatrics",
            max_fee=1000
        )
        print(f"✅ Found {len(results)} matching doctors:")
        for doc in results:
            print(f"   - {doc.name} - ₹{doc.consultation_fee}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 6: Get all specialties
    print("\n📋 Test 6: Getting all available specialties...")
    try:
        specialties = get_all_specialties()
        print(f"✅ Found {len(specialties)} specialties:")
        for spec in specialties[:5]:
            print(f"   - {spec}")
        if len(specialties) > 5:
            print(f"   ... and {len(specialties) - 5} more")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    # Test 7: Get summary stats
    print("\n📋 Test 7: Getting summary statistics...")
    try:
        stats = get_summary_stats()
        print(f"✅ Summary:")
        print(f"   Total Clinics: {stats['total_clinics']}")
        print(f"   Total Doctors: {stats['total_doctors']}")
        print(f"   Average Fee: ₹{stats['average_consultation_fee']:.0f}")
        print(f"   Cities: {', '.join(stats['cities'])}")
    except Exception as e:
        print(f"❌ Failed: {e}")
    
    print("\n" + "=" * 60)
    print("✅ All tests completed!")
    print("=" * 60)
    return True


if __name__ == "__main__":
    success = test_data_loader()
    exit(0 if success else 1)

