# shared_state/guest_records.py
"""
Shared Guest State layer for the VillageTaste Resort multi-agent system.
Stores and persists guest profiles, reservation details, check-in status, complaints, and service requests.
Uses a local JSON file for data persistence.
"""

import json
import os
from pathlib import Path

# Path to the persisted database file
DATA_FILE = Path(__file__).resolve().parent / "guest_data.json"

# In-memory backup database
_MEMORY_DB = {"guests": {}, "reservations": {}}

def _load_data() -> dict:
    """
    Loads database from JSON file, falling back to in-memory store.
    """
    global _MEMORY_DB
    if not DATA_FILE.exists():
        return _MEMORY_DB
    try:
        with open(DATA_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
            # Ensure correct format
            if "guests" not in data:
                data["guests"] = {}
            if "reservations" not in data:
                data["reservations"] = {}
            _MEMORY_DB = data
            return data
    except Exception as e:
        print(f"[Shared State Warning] Failed to load data file: {e}. Using in-memory database.")
        return _MEMORY_DB

def _save_data(data: dict):
    """
    Saves database to JSON file and updates in-memory backup.
    """
    global _MEMORY_DB
    _MEMORY_DB = data
    try:
        # Create directory if it doesn't exist
        DATA_FILE.parent.mkdir(parents=True, exist_ok=True)
        with open(DATA_FILE, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
    except Exception as e:
        print(f"[Shared State Warning] Failed to write data file: {e}. State remains in-memory.")

def create_or_update_guest(email: str, profile_details: dict) -> dict:
    """
    Registers a new guest or updates an existing guest profile.
    """
    email_lower = email.lower().strip()
    data = _load_data()
    
    if email_lower not in data["guests"]:
        data["guests"][email_lower] = {
            "email": email_lower,
            "profile": {
                "guest_name": "Valued Guest"
            },
            "reservations": [],
            "complaints": [],
            "service_requests": [],
            "checkin_status": "Not Checked In"
        }
        
    data["guests"][email_lower]["profile"].update(profile_details)
    _save_data(data)
    return data["guests"][email_lower]

def add_reservation(email: str, reservation_id: str, reservation_details: dict):
    """
    Adds a reservation to the global database and links it to the guest's profile.
    """
    email_lower = email.lower().strip()
    data = _load_data()
    
    # Ensure the guest profile exists first
    if email_lower not in data["guests"]:
        create_or_update_guest(email_lower, {"guest_name": reservation_details.get("guest_name", "Valued Guest")})
        data = _load_data()
        
    data["reservations"][reservation_id] = reservation_details
    if reservation_id not in data["guests"][email_lower]["reservations"]:
        data["guests"][email_lower]["reservations"].append(reservation_id)
        
    _save_data(data)

def get_guest_by_email(email: str) -> dict:
    """
    Retrieves a guest record by their email address.
    """
    email_lower = email.lower().strip()
    data = _load_data()
    return data["guests"].get(email_lower)

def get_reservation(reservation_id: str) -> dict:
    """
    Retrieves a reservation details by calendar event ID.
    """
    data = _load_data()
    return data["reservations"].get(reservation_id)

def add_complaint(email: str, complaint_details: dict):
    """
    Appends a guest complaint record.
    """
    email_lower = email.lower().strip()
    data = _load_data()
    if email_lower in data["guests"]:
        data["guests"][email_lower]["complaints"].append(complaint_details)
        _save_data(data)
    else:
        # Create profile and append
        create_or_update_guest(email_lower, {})
        data = _load_data()
        data["guests"][email_lower]["complaints"].append(complaint_details)
        _save_data(data)

def add_service_request(email: str, request_details: dict):
    """
    Appends a guest service request record.
    """
    email_lower = email.lower().strip()
    data = _load_data()
    if email_lower in data["guests"]:
        data["guests"][email_lower]["service_requests"].append(request_details)
        _save_data(data)
    else:
        # Create profile and append
        create_or_update_guest(email_lower, {})
        data = _load_data()
        data["guests"][email_lower]["service_requests"].append(request_details)
        _save_data(data)

def update_checkin_status(email: str, status: str):
    """
    Updates the guest's check-in/out status.
    """
    email_lower = email.lower().strip()
    data = _load_data()
    if email_lower in data["guests"]:
        data["guests"][email_lower]["checkin_status"] = status
        _save_data(data)

def clear_records():
    """
    Resets the database. Useful for clearing state before test execution.
    """
    global _MEMORY_DB
    _MEMORY_DB = {"guests": {}, "reservations": {}}
    if DATA_FILE.exists():
        try:
            os.remove(DATA_FILE)
        except Exception:
            pass
    _save_data(_MEMORY_DB)
