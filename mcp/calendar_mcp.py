# mcp/calendar_mcp.py
"""
Simulated Google Calendar Model Context Protocol (MCP) server integration.
Provides tools to check room availability, reserve dates, view events, and cancel reservations.
"""
from shared_state import guest_records

def check_availability(room_type: str, checkin: str, checkout: str) -> bool:
    """
    Checks if the requested room type is available for the check-in/out dates.
    Integrates with the shared guest state to find conflicts dynamically.
    """
    room_lower = room_type.lower().strip()
    print(f"[Calendar MCP Log] Checking availability for '{room_type}' from {checkin} to {checkout}")
    
    # 1. Simulated check against standard cottage reserved block (July 1 to July 7, 2026)
    if "standard" in room_lower and checkin == "2026-07-01" and checkout == "2026-07-07":
        print(f"[Calendar MCP Log] Availability Check Result: Busy (Room Occupied)")
        return False
        
    # 2. Check dynamic reservations in the shared state
    try:
        data = guest_records._load_data()
        for res in data.get("reservations", {}).values():
            if res.get("room_type", "").lower().strip() == room_lower:
                # Overlap check: (start1 < end2) and (start2 < end1)
                res_checkin = res.get("checkin")
                res_checkout = res.get("checkout")
                if checkin < res_checkout and res_checkin < checkout:
                    print(f"[Calendar MCP Log] Availability Check Result: Busy (Overlap with event {res.get('calendar_event_id')})")
                    return False
    except Exception as e:
        print(f"[Calendar MCP Log Warning] Dynamic conflict check failed: {e}")
        
    print(f"[Calendar MCP Log] Availability Check Result: Available")
    return True

def reserve_booking_dates(room_type: str, checkin: str, checkout: str) -> dict:
    """
    Simulates adding an event on the Google Calendar to block room dates.
    Returns calendar confirmation details including a unique event ID.
    """
    room_lower = room_type.lower().strip()
    print(f"[Calendar MCP Log] Blocking calendar dates for '{room_type}' from {checkin} to {checkout}")
    
    try:
        # Generate a unique event ID based on current reservation count
        data = guest_records._load_data()
        count = len(data.get("reservations", {})) + 1
        event_id = f"evt_cal_{room_lower.replace(' ', '_')}_{count}"
    except Exception:
        event_id = f"evt_cal_{room_lower.replace(' ', '_')}_1"
        
    return {
        "status": "confirmed",
        "room_type": room_type,
        "checkin": checkin,
        "checkout": checkout,
        "calendar_event_id": event_id
    }

def view_reservation(event_id: str) -> dict:
    """
    Simulates viewing a calendar event details.
    Queries the shared guest database.
    """
    print(f"[Calendar MCP Log] Viewing reservation event: {event_id}")
    return guest_records.get_reservation(event_id)

def cancel_reservation(event_id: str) -> bool:
    """
    Simulates deleting a calendar event, freeing up the dates.
    Updates the shared guest state database.
    """
    print(f"[Calendar MCP Log] Cancelling reservation event: {event_id}")
    
    try:
        data = guest_records._load_data()
        if event_id in data.get("reservations", {}):
            # Remove from guest links
            for email, guest in list(data.get("guests", {}).items()):
                if event_id in guest.get("reservations", []):
                    guest["reservations"].remove(event_id)
            # Remove from reservations list
            del data["reservations"][event_id]
            guest_records._save_data(data)
            print(f"[Calendar MCP Log] Event {event_id} successfully cancelled.")
            return True
        else:
            print(f"[Calendar MCP Log] Event {event_id} not found.")
            return False
    except Exception as e:
        print(f"[Calendar MCP Log Error] Cancel failed: {e}")
        return False
