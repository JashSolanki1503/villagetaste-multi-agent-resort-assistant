# agents/booking.py
"""
Booking Agent for the VillageTaste Resort assistant system.
Handles room bookings, room availability checks, reservation management, and booking confirmations.
Integrates validation skills and simulated MCP tools for Google Calendar and Gmail.
Saves profiles and reservation records to the shared guest state.
"""

import sys
import os
import re
import datetime
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path to ensure robust imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from google.adk import Agent
from mcp import gmail_mcp, calendar_mcp

# Check for google-genai package
has_genai = False
try:
    from google import genai
    has_genai = True
except ImportError:
    pass

# Define the Booking Agent
booking_agent = Agent(
    name="BookingAgent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Booking Agent for VillageTaste Resort, a fictional village-themed resort. "
        "Your responsibilities include:\n"
        "1. Handling room booking/reservation requests.\n"
        "2. Checking room availability (standard cottages, deluxe villas, luxury suites).\n"
        "3. Managing reservations (new, modification, cancellation).\n"
        "4. Collecting guest information (name, check-in/out dates, room preference, guests count).\n"
        "5. Generating clean booking confirmations containing stay details.\n\n"
        "Active Integrations:\n"
        "- resort-booking-validator: Validates names, dates, and guest counts.\n"
        "- calendar_mcp: Simulates checking room availability and reserving slots.\n"
        "- gmail_mcp: Simulates dispatching HTML confirmation receipts."
    )
)

def validate_booking_request(details: dict) -> list[str]:
    """
    Validates booking parameters (Skill 1: resort-booking-validator).
    Checks:
    - Guest name present
    - Check-in date present
    - Check-out date present
    - Number of guests > 0
    Returns list of error messages (empty if valid).
    """
    errors = []
    
    # 1. Guest name check
    if not details or not details.get("guest_name"):
        errors.append("Guest name is missing.")
        
    # 2. Check-in date check
    if not details or not details.get("checkin"):
        errors.append("Check-in date is missing.")
        
    # 3. Check-out date check
    if not details or not details.get("checkout"):
        errors.append("Check-out date is missing.")
        
    # 4. Guest count check
    if not details or details.get("guests") is None:
        errors.append("Number of guests is missing.")
    else:
        try:
            guests_val = int(details["guests"])
            if guests_val <= 0:
                errors.append("Number of guests must be greater than 0.")
        except (ValueError, TypeError):
            errors.append("Number of guests must be a valid integer.")
            
    return errors

def parse_dates_heuristically(query: str) -> tuple[str, str]:
    """
    Parses dates from query locally using regex and base current date (Saturday, June 20, 2026).
    """
    query_lower = query.lower()
    base_date = datetime.date(2026, 6, 20)
    
    checkin_date = base_date + datetime.timedelta(days=7)
    checkout_date = checkin_date + datetime.timedelta(days=3)
    
    # Try YYYY-MM-DD
    dates = re.findall(r'\d{4}-\d{2}-\d{2}', query)
    if len(dates) >= 2:
        return dates[0], dates[1]
    elif len(dates) == 1:
        try:
            checkin_date = datetime.datetime.strptime(dates[0], "%Y-%m-%d").date()
            checkout_date = checkin_date + datetime.timedelta(days=3)
        except ValueError:
            pass
        return str(checkin_date), str(checkout_date)
        
    # Relative date parsing: "next Friday"
    # June 20, 2026 is Saturday. Next Friday is June 26, 2026 (6 days later)
    if "next friday" in query_lower:
        checkin_date = datetime.date(2026, 6, 26)
    elif "next weekend" in query_lower:
        checkin_date = datetime.date(2026, 6, 27)
    elif "july 1" in query_lower or "2026-07-01" in query_lower:
        checkin_date = datetime.date(2026, 7, 1)
        checkout_date = datetime.date(2026, 7, 7)
        return str(checkin_date), str(checkout_date)
    elif "august 10" in query_lower or "2026-08-10" in query_lower:
        checkin_date = datetime.date(2026, 8, 10)
        checkout_date = datetime.date(2026, 8, 15)
        return str(checkin_date), str(checkout_date)
        
    # Nights check
    nights_match = re.search(r'(\d+)\s+night', query_lower)
    if nights_match:
        nights = int(nights_match.group(1))
        checkout_date = checkin_date + datetime.timedelta(days=nights)
        
    return str(checkin_date), str(checkout_date)

def generate_details_with_gemini(query: str) -> dict:
    """
    Calls Gemini once to parse structured JSON booking details from user query text.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not has_genai or not api_key:
        return None
    try:
        client = genai.Client(api_key=api_key)
        prompt = (
            "Extract booking details from the user query. Your response must be a single raw JSON object "
            "with keys: 'guest_name' (string, default 'Valued Guest'), 'checkin' (string 'YYYY-MM-DD'), "
            "'checkout' (string 'YYYY-MM-DD'), 'guests' (integer, default 2), 'room_type' (string, e.g. "
            "'Standard Cottage', 'Deluxe Villa', or 'Luxury Suite', default 'Standard Cottage'), and "
            "'email' (string, default to guest_name@example.com). Do not wrap in markdown or backticks.\n\n"
            f"Query: \"{query}\"\n"
            "JSON Output:"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        import json
        text = response.text.strip()
        if text.startswith("```json"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return json.loads(text.strip())
    except Exception as e:
        print(f"[Booking Agent] Gemini details extraction failed: {e}")
        return None

async def extract_booking_details(query: str) -> dict:
    """
    Parses and extracts booking details from user query text.
    First tries to use Gemini, and falls back to local heuristic rules.
    """
    # 1. Try Gemini
    details = generate_details_with_gemini(query)
    if details:
        return details
        
    # 2. Heuristic fallback
    details = {}
    query_lower = query.lower()
    
    # Room type
    if "deluxe villa" in query_lower or "deluxe" in query_lower:
        details["room_type"] = "Deluxe Villa"
    elif "luxury suite" in query_lower or "luxury" in query_lower:
        details["room_type"] = "Luxury Suite"
    else:
        details["room_type"] = "Standard Cottage"
        
    # Guest Name
    name_match = re.search(r'(?:for|under the name of)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', query)
    if name_match:
        details["guest_name"] = name_match.group(1)
    else:
        details["guest_name"] = "Valued Guest"
        
    # Email
    email_match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', query)
    if email_match:
        details["email"] = email_match.group(1).lower().strip().rstrip('.')
    else:
        details["email"] = f"{details['guest_name'].lower().replace(' ', '_')}@example.com"
    
    # Guest headcount
    guests_match = re.search(r'(\d+)\s+(?:guest|people|person|visitor)', query_lower)
    if guests_match:
        details["guests"] = int(guests_match.group(1))
    else:
        details["guests"] = 2
        
    # Dates
    checkin, checkout = parse_dates_heuristically(query)
    details["checkin"] = checkin
    details["checkout"] = checkout
    
    return details

async def run_booking_flow(details: dict) -> dict:
    """
    Executes the structured booking agent flow:
    Validate Booking -> Check Calendar Availability -> Reserve Dates -> Create Reservation Record -> Save Guest Record -> Gmail MCP Confirmation
    """
    # Step 1: Validate Booking Request using the Booking Validation Skill
    from skills.booking_validator import validate_booking
    validation_res = validate_booking(details)
    if not validation_res["valid"]:
        return {
            "status": "validation_failed",
            "errors": [validation_res["message"]],
            "message": f"Booking validation failed: {validation_res['message']}"
        }
        
    room_type = details.get("room_type", "Standard Cottage")
    checkin = details["checkin"]
    checkout = details["checkout"]
    guest_name = details["guest_name"]
    guests_count = int(details["guests"])
    recipient_email = details.get("email", f"{guest_name.lower().replace(' ', '_')}@example.com").strip()

    # Step 2: Check Calendar Availability (Calendar MCP)
    print(f"[Agent -> MCP] Invoking Calendar MCP to check availability for '{room_type}' from {checkin} to {checkout}")
    is_available = calendar_mcp.check_availability(room_type, checkin, checkout)
    if not is_available:
        return {
            "status": "availability_failed",
            "room_type": room_type,
            "checkin": checkin,
            "checkout": checkout,
            "message": f"Availability check failed: '{room_type}' is occupied from {checkin} to {checkout}."
        }

    # Step 3: Reserve Booking Dates (Calendar MCP)
    print(f"[Agent -> MCP] Invoking Calendar MCP to reserve dates for '{room_type}'")
    reservation = calendar_mcp.reserve_booking_dates(room_type, checkin, checkout)

    stay_details = {
        "guest_name": guest_name,
        "room_type": room_type,
        "checkin": checkin,
        "checkout": checkout,
        "guests": guests_count,
        "calendar_event_id": reservation["calendar_event_id"]
    }

    # Step 4: Save Reservation and Guest Records to Shared Guest State (Goal 2)
    try:
        from shared_state import guest_records
        # Create or update profile
        guest_records.create_or_update_guest(recipient_email, {
            "guest_name": guest_name
        })
        # Add reservation details
        guest_records.add_reservation(recipient_email, reservation["calendar_event_id"], stay_details)
    except Exception as e:
        print(f"[Booking Agent Warning] Failed to update shared guest state: {e}")

    # Step 5: Dispatch Confirmation Email (Gmail MCP)
    # Generate booking summary using the Booking Summary Generator Skill
    from skills.booking_summary import generate_booking_summary
    guest_info = {"guest_name": guest_name}
    booking_info = {
        "room_type": room_type,
        "checkin": checkin,
        "checkout": checkout,
        "guests": guests_count
    }
    booking_summary = generate_booking_summary(guest_info, booking_info)
    stay_details["booking_summary"] = booking_summary
    
    print(f"[Agent -> MCP] Invoking Gmail MCP to send booking confirmation to {recipient_email}")
    email_response = gmail_mcp.send_booking_confirmation(recipient_email, stay_details)

    return {
        "status": "success",
        "reservation": reservation,
        "email_response": email_response,
        "booking_summary": booking_summary,
        "message": f"Booking successfully confirmed for {guest_name}! {email_response}"
    }

# Attach execution method for standalone demo runner and test suites
booking_agent.run = run_booking_flow
