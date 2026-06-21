# skills/booking_summary/booking_summary.py
"""
Booking Summary Generator Skill.
Generates structured booking summaries from guest and booking details.
Calculates stay duration dynamically in Nights.
"""

import datetime

def generate_booking_summary(guest_info: dict, booking_info: dict) -> str:
    """
    Generates a structured booking summary string.
    Input example:
        guest_info = {"guest_name": "John Doe"}
        booking_info = {"room_type": "Deluxe Villa", "guests": 2, "checkin": "2026-08-01", "checkout": "2026-08-04"}
    Output example:
        Guest Name: John Doe
        Accommodation: Deluxe Villa
        Guests: 2
        Stay Duration: 3 Nights
    """
    guest_name = guest_info.get("guest_name") or booking_info.get("guest_name") or "Valued Guest"
    accommodation = booking_info.get("room_type") or booking_info.get("accommodation") or "Standard Cottage"
    guests = booking_info.get("guests") or 2
    
    checkin = booking_info.get("checkin")
    checkout = booking_info.get("checkout")
    
    nights_str = "N/A"
    if checkin and checkout:
        try:
            if isinstance(checkin, datetime.date):
                checkin_date = checkin
            else:
                checkin_date = datetime.datetime.strptime(str(checkin), "%Y-%m-%d").date()
                
            if isinstance(checkout, datetime.date):
                checkout_date = checkout
            else:
                checkout_date = datetime.datetime.strptime(str(checkout), "%Y-%m-%d").date()
                
            nights = (checkout_date - checkin_date).days
            if nights > 0:
                nights_str = f"{nights} Night" + ("s" if nights > 1 else "")
        except Exception:
            pass
            
    summary = (
        f"Guest Name: {guest_name}\n"
        f"Accommodation: {accommodation}\n"
        f"Guests: {guests}\n"
        f"Stay Duration: {nights_str}"
    )
    return summary
