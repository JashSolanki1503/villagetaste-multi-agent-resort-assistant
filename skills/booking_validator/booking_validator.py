# skills/booking_validator/booking_validator.py
"""
Booking Validation Skill for checking guest name, check-in/out date formats,
duration correctness, guest counts, and valid resort room types before initiating
booking reservations.
"""

import datetime

def validate_booking(details: dict) -> dict:
    """
    Validates booking parameters.
    Checks:
    - Guest name presence
    - Check-in date format (YYYY-MM-DD)
    - Check-out date format (YYYY-MM-DD)
    - Check-out after check-in
    - Guest count greater than 0
    - Valid room type (Standard Cottage, Deluxe Villa, Luxury Suite)
    
    Output format:
    {
        "valid": bool,
        "message": str
    }
    """
    if not details:
        return {"valid": False, "message": "No booking details provided."}

    guest_name = details.get("guest_name")
    checkin = details.get("checkin")
    checkout = details.get("checkout")
    guests = details.get("guests")
    room_type = details.get("room_type")

    # 1. Guest name check
    if not guest_name:
        return {"valid": False, "message": "Guest name is missing."}

    # 2. Check-in date presence check
    if not checkin:
        return {"valid": False, "message": "Check-in date is missing."}

    # 3. Check-out date presence check
    if not checkout:
        return {"valid": False, "message": "Check-out date is missing."}

    # 4. Guest count presence check
    if guests is None:
        return {"valid": False, "message": "Number of guests is missing."}

    # 5. Room type presence check
    if not room_type:
        return {"valid": False, "message": "Room type is missing."}

    # 6. Check-in date format check
    try:
        if isinstance(checkin, datetime.date):
            checkin_date = checkin
        else:
            checkin_date = datetime.datetime.strptime(str(checkin), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return {"valid": False, "message": "Invalid check-in date format."}

    # 7. Check-out date format check
    try:
        if isinstance(checkout, datetime.date):
            checkout_date = checkout
        else:
            checkout_date = datetime.datetime.strptime(str(checkout), "%Y-%m-%d").date()
    except (ValueError, TypeError):
        return {"valid": False, "message": "Invalid check-out date format."}

    # 8. Check-out after check-in check
    if checkout_date <= checkin_date:
        return {"valid": False, "message": "Check-out date must be after check-in date."}

    # 9. Guest count greater than 0 check
    try:
        guests_val = int(guests)
        if guests_val <= 0:
            return {"valid": False, "message": "Number of guests must be greater than 0."}
    except (ValueError, TypeError):
        return {"valid": False, "message": "Number of guests must be a valid integer."}

    # 10. Valid room type check
    valid_rooms = ["Standard Cottage", "Deluxe Villa", "Luxury Suite"]
    if room_type not in valid_rooms:
        return {"valid": False, "message": "Invalid room type"}

    return {
        "valid": True,
        "message": "Booking validated successfully"
    }
