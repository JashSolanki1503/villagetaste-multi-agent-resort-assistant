# agents/reception.py
"""
Reception Agent for the VillageTaste Resort assistant system.
Handles check-in/out guidance, guest complaint routing, customer records, and operational reporting.
Integrates categorization of guest requests and updates shared guest records.
"""

import os
import sys
import re
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path to ensure robust imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from google.adk import Agent
from mcp import gmail_mcp
from shared_state import guest_records

# Check for google-genai package
has_genai = False
try:
    from google import genai
    has_genai = True
except ImportError:
    pass

# Define the Reception Agent
reception_agent = Agent(
    name="ReceptionAgent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Reception Agent for VillageTaste Resort, a fictional village-themed resort. "
        "Your responsibilities include:\n"
        "1. Coordinating guest check-in and check-out instructions and operations.\n"
        "2. Handling and logging guest complaints or specific service requests (e.g., extra towels, maintenance).\n"
        "3. Managing guest database records (e.g., retrieving guest status, preferences, room assignments).\n"
        "4. Generating resort operational reports (daily summaries of occupancy, complaints, resolved requests).\n\n"
        "Active Integrations:\n"
        "- Gmail MCP: Simulates emailing guest folios, feedback surveys, or escalating complaints."
    )
)

def extract_guest_email_and_name(query: str) -> tuple[str, str]:
    """
    Identifies a guest email and name from the query text.
    Queries the shared state registry if needed.
    """
    # 1. Search for email pattern
    email_match = re.search(r'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)', query)
    if email_match:
        email = email_match.group(1).lower().strip().rstrip('.')
        # Look up name in database if possible
        try:
            guest = guest_records.get_guest_by_email(email)
            if guest and guest.get("profile"):
                return email, guest["profile"].get("guest_name", "Valued Guest")
        except Exception:
            pass
        return email, "Valued Guest"
        
    # 2. Look up name in query
    try:
        data = guest_records._load_data()
        for email, guest in data.get("guests", {}).items():
            name = guest.get("profile", {}).get("guest_name", "")
            if name and name.lower() in query.lower():
                return email, name
    except Exception:
        pass
        
    # Fallback default profile
    return "valued_guest@example.com", "Valued Guest"

def generate_reception_category_with_gemini(query: str) -> str:
    """
    Calls Gemini once to classify request category.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not has_genai or not api_key:
        return None
    try:
        client = genai.Client(api_key=api_key)
        prompt = (
            "Classify this guest request query into exactly one of these 6 categories:\n"
            "- Complaint\n"
            "- Maintenance\n"
            "- Room Service\n"
            "- Check-In\n"
            "- Check-Out\n"
            "- General Inquiry\n\n"
            "Return only the category name, e.g. 'Room Service' or 'Complaint', with no additional text.\n\n"
            f"Query: \"{query}\"\n"
            "Category:"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        cat = response.text.strip()
        valid_cats = ["Complaint", "Maintenance", "Room Service", "Check-In", "Check-Out", "General Inquiry"]
        for valid in valid_cats:
            if valid.lower() in cat.lower():
                return valid
        return "General Inquiry"
    except Exception as e:
        print(f"[Reception Agent] Gemini classification failed: {e}")
        return None

def classify_reception_request_locally(query: str) -> str:
    """
    Heuristics-based local classifier for request categorization.
    """
    query_lower = query.lower()
    if any(k in query_lower for k in ["complaint", "unhappy", "angry", "disappointed", "poor", "bad", "issue", "problem", "dissatisfied", "not working", "dirty", "wrong charge"]):
        return "Complaint"
    elif any(k in query_lower for k in ["broken", "light", "leak", "plumbing", "fix", "repair", "maintenance", "lock", "toilet", "shower", "appliance"]):
        return "Maintenance"
    elif any(k in query_lower for k in ["towel", "towels", "room service", "clean", "pillow", "blanket", "soap", "shampoo", "service", "dinner in room", "lunch in room"]):
        return "Room Service"
    elif any(k in query_lower for k in ["check-in", "checkin", "check in", "arrive", "arrival", "check-in instruction", "checkin rules"]):
        return "Check-In"
    elif any(k in query_lower for k in ["check-out", "checkout", "check out", "leave", "departure", "folio", "bill", "invoice", "receipt"]):
        return "Check-Out"
    else:
        return "General Inquiry"

async def run_reception_agent(query: str) -> str:
    """
    Executes the Reception Agent flow.
    Identifies guest, categorizes request, saves state, triggers Gmail MCP, and returns customized response.
    """
    # 1. Identify guest email and profile
    email, guest_name = extract_guest_email_and_name(query)
    
    # 2. Categorize request (Try Gemini first, then local fallback)
    category = generate_reception_category_with_gemini(query)
    if not category:
        category = classify_reception_request_locally(query)
        
    response_lines = [
        f"[Reception Agent Response]",
        f"Query processed: '{query}'",
        f"Identified Guest: {guest_name} ({email})",
        f"Categorized request: {category.upper()}"
    ]
    
    if category == "Complaint":
        # Classify the complaint using the Complaint Classification Skill
        from skills.complaint_classifier import classify_complaint
        complaint_cat = classify_complaint(query)
        
        # Register in shared state
        guest_records.add_complaint(email, {"complaint": query, "category": complaint_cat, "status": "Logged"})
        # Send acknowledgement via Gmail MCP
        print(f"[Agent -> MCP] Invoking Gmail MCP to send complaint acknowledgement to {email}")
        email_res = gmail_mcp.send_complaint_acknowledgement(email, {"complaint": query, "category": complaint_cat})
        
        response_lines.append(
            "Greetings from Front Desk! We are very sorry to hear about your experience. "
            "I have registered this complaint in your guest file. "
            f"The complaint has been classified as {complaint_cat}. "
            "Our Duty Manager has been alerted and a confirmation receipt has been sent to your email.\n"
            f"{email_res}"
        )
    elif category == "Maintenance":
        # Register in shared state
        guest_records.add_complaint(email, {"maintenance_issue": query, "status": "Dispatched"})
        # Send acknowledgement via Gmail MCP
        print(f"[Agent -> MCP] Invoking Gmail MCP to send maintenance ticket acknowledgement to {email}")
        email_res = gmail_mcp.send_complaint_acknowledgement(email, {"maintenance_issue": query})
        
        response_lines.append(
            "Greetings from Front Desk! We apologize for the inconvenience. "
            "I have registered a maintenance work order in your guest file and dispatched the repair crew. "
            "Confirmation sent to your email.\n"
            f"{email_res}"
        )
    elif category == "Room Service":
        # Register in shared state
        guest_records.add_service_request(email, {"service_request": query, "status": "Pending"})
        
        response_lines.append(
            "Greetings from Front Desk! Housekeeping has been notified of your request. "
            "We are preparing the items and will deliver them to your room shortly. "
            "This request has been added to your guest folio."
        )
    elif category == "Check-In":
        # Update checkin status in shared state
        guest_records.update_checkin_status(email, "Checked In")
        
        response_lines.append(
            "Greetings from Front Desk! Welcome to VillageTaste Resort! "
            "I have successfully updated your check-in status to 'Checked In'. "
            "Please collect your key cards at the desk."
        )
    elif category == "Check-Out":
        # Update checkin status in shared state
        guest_records.update_checkin_status(email, "Checked Out")
        
        billing_details = {
            "room_charges": "$450.00",
            "dining_charges": "$85.00",
            "activity_fees": "$60.00",
            "total_due": "$595.00"
        }
        # Send checkout summary via Gmail MCP
        print(f"[Agent -> MCP] Invoking Gmail MCP to send checkout summary to {email}")
        email_res = gmail_mcp.send_checkout_summary(email, billing_details)
        
        response_lines.append(
            "Greetings from Front Desk! We hope you enjoyed your stay at VillageTaste Resort! "
            "I have successfully updated your status to 'Checked Out'. "
            "Your billing statement has been sent to your email.\n"
            f"{email_res}"
        )
    else:  # General Inquiry
        response_lines.append(
            "Greetings from Front Desk! How can I assist you today? "
            "I can coordinate checking in/out, log maintenance issues, or arrange room services."
        )
        
    return "\n".join(response_lines)

# Expose execution method on the reception_agent instance
reception_agent.run = run_reception_agent
