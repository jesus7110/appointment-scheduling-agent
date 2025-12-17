"""
Data loader utilities for loading and querying clinic and doctor data.

Provides cached access to JSON data with type-safe Pydantic models.
"""
import json
from pathlib import Path
from typing import List, Optional, Dict
from datetime import time as Time
from functools import lru_cache

from models.schemas import (
    Clinic,
    Doctor,
    GeneralInfo,
    ClinicData,
    DoctorData,
)


# Path to data directory
DATA_DIR = Path(__file__).parent.parent / "data"
CLINIC_FILE = DATA_DIR / "clinic_info.json"
DOCTOR_FILE = DATA_DIR / "doctor_schedule.json"


# ============================================================================
# Core Loading Functions (with caching)
# ============================================================================

@lru_cache(maxsize=1)
def load_clinic_data() -> ClinicData:
    """
    Load and validate clinic data from JSON file.
    
    Returns:
        ClinicData: Validated clinic data with all clinics and general info.
    
    Raises:
        FileNotFoundError: If clinic_info.json doesn't exist.
        ValueError: If JSON data is invalid.
    """
    try:
        with open(CLINIC_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return ClinicData(**data)
    except FileNotFoundError:
        raise FileNotFoundError(f"Clinic data file not found: {CLINIC_FILE}")
    except Exception as e:
        raise ValueError(f"Failed to load clinic data: {e}")


@lru_cache(maxsize=1)
def load_doctor_data() -> DoctorData:
    """
    Load and validate doctor data from JSON file.
    
    Returns:
        DoctorData: Validated doctor data with all doctors.
    
    Raises:
        FileNotFoundError: If doctor_schedule.json doesn't exist.
        ValueError: If JSON data is invalid.
    """
    try:
        with open(DOCTOR_FILE, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return DoctorData(**data)
    except FileNotFoundError:
        raise FileNotFoundError(f"Doctor data file not found: {DOCTOR_FILE}")
    except Exception as e:
        raise ValueError(f"Failed to load doctor data: {e}")


def load_clinics() -> List[Clinic]:
    """Get list of all clinics."""
    return load_clinic_data().clinics


def load_doctors() -> List[Doctor]:
    """Get list of all doctors."""
    return load_doctor_data().doctors


def load_general_info() -> GeneralInfo:
    """Get general booking information and policies."""
    return load_clinic_data().general_info


# ============================================================================
# Clinic Query Functions
# ============================================================================

def get_clinic_by_id(clinic_id: str) -> Optional[Clinic]:
    """
    Get a clinic by its ID.
    
    Args:
        clinic_id: The clinic ID to search for.
    
    Returns:
        Clinic object if found, None otherwise.
    """
    clinics = load_clinics()
    return next((c for c in clinics if c.id == clinic_id), None)


def get_clinic_by_name(name: str, exact: bool = False) -> Optional[Clinic]:
    """
    Get a clinic by name.
    
    Args:
        name: Clinic name to search for.
        exact: If True, match exact name. If False, case-insensitive partial match.
    
    Returns:
        First matching clinic, or None if not found.
    """
    clinics = load_clinics()
    if exact:
        return next((c for c in clinics if c.name == name), None)
    else:
        name_lower = name.lower()
        return next((c for c in clinics if name_lower in c.name.lower()), None)


def search_clinics(
    city: Optional[str] = None,
    area: Optional[str] = None,
    specialty: Optional[str] = None
) -> List[Clinic]:
    """
    Search for clinics by various criteria.
    
    Args:
        city: Filter by city name.
        area: Filter by area/locality.
        specialty: Filter by specialty offered.
    
    Returns:
        List of matching clinics.
    """
    clinics = load_clinics()
    results = clinics
    
    if city:
        city_lower = city.lower()
        results = [c for c in results if city_lower in c.address.city.lower()]
    
    if area:
        area_lower = area.lower()
        results = [c for c in results if area_lower in c.address.area.lower()]
    
    if specialty:
        specialty_lower = specialty.lower()
        results = [
            c for c in results
            if any(specialty_lower in s.lower() for s in c.specialties)
        ]
    
    return results


def get_all_specialties() -> List[str]:
    """
    Get a list of all unique specialties across all clinics.
    
    Returns:
        Sorted list of unique specialties.
    """
    clinics = load_clinics()
    specialties = set()
    for clinic in clinics:
        specialties.update(clinic.specialties)
    return sorted(specialties)


# ============================================================================
# Doctor Query Functions
# ============================================================================

def get_doctor_by_id(doctor_id: str) -> Optional[Doctor]:
    """
    Get a doctor by their ID.
    
    Args:
        doctor_id: The doctor ID to search for.
    
    Returns:
        Doctor object if found, None otherwise.
    """
    doctors = load_doctors()
    return next((d for d in doctors if d.id == doctor_id), None)


def get_doctor_by_name(name: str, exact: bool = False) -> Optional[Doctor]:
    """
    Get a doctor by name.
    
    Args:
        name: Doctor name to search for.
        exact: If True, match exact name. If False, case-insensitive partial match.
    
    Returns:
        First matching doctor, or None if not found.
    """
    doctors = load_doctors()
    if exact:
        return next((d for d in doctors if d.name == name), None)
    else:
        name_lower = name.lower()
        return next((d for d in doctors if name_lower in d.name.lower()), None)


def get_doctors_by_clinic(clinic_id: str) -> List[Doctor]:
    """
    Get all doctors at a specific clinic.
    
    Args:
        clinic_id: The clinic ID.
    
    Returns:
        List of doctors at the clinic.
    """
    doctors = load_doctors()
    return [d for d in doctors if d.clinic_id == clinic_id]


def get_doctors_by_specialty(specialty: str, exact: bool = False) -> List[Doctor]:
    """
    Get all doctors with a specific specialty.
    
    Args:
        specialty: The medical specialty to search for.
        exact: If True, exact match. If False, case-insensitive partial match.
    
    Returns:
        List of matching doctors.
    """
    doctors = load_doctors()
    if exact:
        return [d for d in doctors if d.specialty == specialty]
    else:
        specialty_lower = specialty.lower()
        return [d for d in doctors if specialty_lower in d.specialty.lower()]


def search_doctors(
    name: Optional[str] = None,
    specialty: Optional[str] = None,
    clinic_id: Optional[str] = None,
    max_fee: Optional[int] = None,
    language: Optional[str] = None
) -> List[Doctor]:
    """
    Search for doctors by various criteria.
    
    Args:
        name: Filter by doctor name (partial match).
        specialty: Filter by specialty (partial match).
        clinic_id: Filter by clinic ID.
        max_fee: Filter by maximum consultation fee.
        language: Filter by language spoken.
    
    Returns:
        List of matching doctors.
    """
    doctors = load_doctors()
    results = doctors
    
    if name:
        name_lower = name.lower()
        results = [d for d in results if name_lower in d.name.lower()]
    
    if specialty:
        specialty_lower = specialty.lower()
        results = [d for d in results if specialty_lower in d.specialty.lower()]
    
    if clinic_id:
        results = [d for d in results if d.clinic_id == clinic_id]
    
    if max_fee is not None:
        results = [d for d in results if d.consultation_fee <= max_fee]
    
    if language:
        language_lower = language.lower()
        results = [
            d for d in results
            if any(language_lower in lang.lower() for lang in d.languages)
        ]
    
    return results


def get_all_doctor_specialties() -> List[str]:
    """
    Get a list of all unique doctor specialties.
    
    Returns:
        Sorted list of unique specialties.
    """
    doctors = load_doctors()
    specialties = {d.specialty for d in doctors}
    return sorted(specialties)


# ============================================================================
# Combined Query Functions
# ============================================================================

def get_doctors_with_clinic_info(doctor_ids: Optional[List[str]] = None) -> List[Dict]:
    """
    Get doctors with their full clinic information.
    
    Args:
        doctor_ids: Optional list of doctor IDs to filter. If None, returns all.
    
    Returns:
        List of dicts with doctor and clinic info combined.
    """
    doctors = load_doctors()
    if doctor_ids:
        doctors = [d for d in doctors if d.id in doctor_ids]
    
    results = []
    for doctor in doctors:
        clinic = get_clinic_by_id(doctor.clinic_id)
        results.append({
            "doctor": doctor,
            "clinic": clinic,
        })
    
    return results


def get_clinic_with_doctors(clinic_id: str) -> Optional[Dict]:
    """
    Get a clinic with all its doctors.
    
    Args:
        clinic_id: The clinic ID.
    
    Returns:
        Dict with clinic and doctors, or None if clinic not found.
    """
    clinic = get_clinic_by_id(clinic_id)
    if not clinic:
        return None
    
    doctors = get_doctors_by_clinic(clinic_id)
    return {
        "clinic": clinic,
        "doctors": doctors,
        "doctor_count": len(doctors),
    }


# ============================================================================
# Helper Functions
# ============================================================================

def parse_time(time_str: str) -> Time:
    """
    Parse time string in HH:MM format to time object.
    
    Args:
        time_str: Time string in "HH:MM" format.
    
    Returns:
        time object.
    """
    hour, minute = map(int, time_str.split(':'))
    return Time(hour, minute)


def is_clinic_open(clinic: Clinic, day: str, check_time: Optional[str] = None) -> bool:
    """
    Check if a clinic is open on a specific day and time.
    
    Args:
        clinic: The clinic to check.
        day: Day of week (lowercase, e.g., "monday").
        check_time: Optional time to check in HH:MM format. If None, just checks if open.
    
    Returns:
        True if clinic is open, False otherwise.
    """
    day_hours = getattr(clinic.operating_hours, day.lower(), None)
    
    if not day_hours or day_hours == "closed":
        return False
    
    if check_time is None:
        return True
    
    # Check if the time is within operating hours
    try:
        check_time_obj = parse_time(check_time)
        open_time_obj = parse_time(day_hours.open)
        close_time_obj = parse_time(day_hours.close)
        return open_time_obj <= check_time_obj <= close_time_obj
    except (ValueError, AttributeError):
        return False


def get_summary_stats() -> Dict:
    """
    Get summary statistics about the data.
    
    Returns:
        Dict with various stats about clinics and doctors.
    """
    clinics = load_clinics()
    doctors = load_doctors()
    
    # Count doctors by specialty
    from collections import Counter
    specialty_counts = Counter(d.specialty for d in doctors)
    
    # Count doctors by clinic
    doctors_per_clinic = Counter(d.clinic_id for d in doctors)
    
    return {
        "total_clinics": len(clinics),
        "total_doctors": len(doctors),
        "specialties": get_all_doctor_specialties(),
        "specialty_counts": dict(specialty_counts),
        "doctors_per_clinic": dict(doctors_per_clinic),
        "cities": list({c.address.city for c in clinics}),
        "average_consultation_fee": sum(d.consultation_fee for d in doctors) / len(doctors) if doctors else 0,
    }


# ============================================================================
# Cache Management
# ============================================================================

def clear_cache():
    """Clear the cached data (useful for testing or data updates)."""
    load_clinic_data.cache_clear()
    load_doctor_data.cache_clear()


def reload_data():
    """Reload all data from JSON files."""
    clear_cache()
    load_clinic_data()
    load_doctor_data()

