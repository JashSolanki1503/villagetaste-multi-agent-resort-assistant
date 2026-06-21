# workflows/resort_workflow.py
"""
Resort Workflow for the VillageTaste Resort multi-agent system.
Orchestrates request flow between the Orchestrator Agent and specialized sub-agents.
Uses ADK 2.0 dynamic execution via the @node decorator and ctx.run_node().

================================================================================
KAGGLE CAPSTONE ARCHITECTURAL OVERVIEW
================================================================================

1. AGENT ARCHITECTURE
- Orchestrator Agent (orchestrator.py): Classifies guest intents into BOOKING, 
  RECEPTION, GUIDE, or OUT_OF_SCOPE, and dynamically routes requests.
- Booking Agent (booking.py): Extracts parameters, validates check-in inputs, 
  queries calendar availability, and registers reservation receipts.
- Reception Agent (reception.py): Categorizes check-in, check-out, complaints, 
  or room service requests, dispatching emails and maintenance work orders.
- Guide Agent (guide.py): Performs scope guard checks, retrieves vector database 
  context, and uses Gemini to answer resort FAQs consistently with source attribution.

2. MODEL CONTEXT PROTOCOL (MCP) INTEGRATION POINTS
- Google Calendar MCP: Simulated Calendar API tools check availability and reserve blocks.
- Gmail MCP: Simulated Gmail API tools email booking confirmation receipts and guest folios.
- Future Production upgrade: Host separate, standards-compliant JSON-RPC MCP servers 
  running via node or python-mcp-server packages to replace simulated modules.

3. SKILLS USAGE
- resort-booking-validator: Validates parameters like guest headcount, names, and stay dates.
- resort-faq-helper: Controls RAG prompt formatting and formatting constraints for FAQs.

4. FUTURE PRODUCTION UPGRADES
- Live ADK Execution: Connect live ADK agents running on hosted servers via the ADK Runner API.
- Fully Autonomous Nodes: Replace offline regex extraction logic with true LLM tool calling.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add project root to path to ensure robust imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from google.adk import Context, Workflow
from google.adk.workflow import node

# Import the pre-defined agents from the agents package
from agents import OrchestratorAgent, BookingAgent, ReceptionAgent, GuideAgent

# Check for google-genai package
has_genai = False
try:
    from google import genai
    has_genai = True
except ImportError:
    pass

def generate_intent_with_gemini(query: str) -> str:
    """
    Calls Gemini once to classify user intent.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not has_genai or not api_key:
        return None
    try:
        client = genai.Client(api_key=api_key)
        prompt = (
            "Classify the following user query for a resort assistant into exactly one of these 4 categories:\n"
            "- BOOKING: Room reservations, availability checks, cottage/villa booking dates, or booking inquiries.\n"
            "- RECEPTION: Check-in/out procedures, billing/folio inquiries, room maintenance issues, broken appliances, plumbing, room service, complaints, towels, pillows.\n"
            "- GUIDE: Resort facilities layout, schedules (e.g. pottery workshop, organic farming), dining menus, dining hours, activity details, general resort FAQs, rules, pets policies.\n"
            "- OUT_OF_SCOPE: Completely unrelated questions (e.g. stock prices, writing website code, homework, other hotels).\n\n"
            "Return ONLY the category name in uppercase with no additional text or formatting.\n\n"
            f"Query: \"{query}\"\n"
            "Category:"
        )
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        cat = response.text.strip().upper()
        if cat in ["BOOKING", "RECEPTION", "GUIDE", "OUT_OF_SCOPE"]:
            return cat
        return None
    except Exception as e:
        print(f"[Orchestrator Agent] Gemini intent classification failed: {e}")
        return None

def classify_intent_locally(query: str) -> str:
    """
    Local score-based classifier for routing intent when Gemini is offline.
    """
    query_lower = query.lower()
    
    # Initialize scores for each category
    scores = {
        "BOOKING": 0,
        "RECEPTION": 0,
        "GUIDE": 0
    }
    
    # Define distinct keyword patterns
    booking_keywords = ["book", "reserve", "reservation", "availability", "date", "stay", "cottage", "villa", "suite", "room type", "nights"]
    reception_keywords = ["check-in", "check-out", "checkin", "checkout", "check in", "check out", "complaint", "towel", "towels", "maintenance", "repair", "broken", "leak", "service request", "folio", "bill", "invoice", "receipt", "disappointed", "issue", "problem"]
    guide_keywords = ["menu", "food", "eat", "dining", "pottery", "farm", "hike", "activity", "activities", "policy", "policies", "faq", "faqs", "workshop", "excursion", "hours", "breakfast", "lunch", "dinner", "pet", "pets", "smoking", "transport", "payment"]
    
    for kw in booking_keywords:
        if kw in query_lower:
            scores["BOOKING"] += 2 if kw in query_lower.split() else 1
            
    for kw in reception_keywords:
        if kw in query_lower:
            scores["RECEPTION"] += 2 if kw in query_lower.split() else 1
            
    for kw in guide_keywords:
        if kw in query_lower:
            scores["GUIDE"] += 2 if kw in query_lower.split() else 1
            
    max_score = max(scores.values())
    if max_score == 0:
        return "OUT_OF_SCOPE"
        
    best_categories = [k for k, v in scores.items() if v == max_score]
    # Tie breaker: RECEPTION takes priority, then BOOKING, then GUIDE
    if "RECEPTION" in best_categories:
        return "RECEPTION"
    elif "BOOKING" in best_categories:
        return "BOOKING"
    else:
        return "GUIDE"

# --- 1. Define Node: Classify Intent ---
@node(name="classify_intent")
async def classify_intent(ctx: Context, query: str) -> str:
    """
    Evaluates the guest query to classify its category.
    First tries to classify using Gemini (once), falling back to local scores.
    """
    category = generate_intent_with_gemini(query)
    if not category:
        category = classify_intent_locally(query)
    return category


# --- 2. Define Sub-Agent Execution Nodes ---
@node(name="run_booking_agent")
async def run_booking_agent(ctx: Context, query: str) -> str:
    """
    Executes the Booking Agent workflow:
    Extract Details -> Validate -> Calendar Check -> Reserve -> Send Email Confirmation.
    """
    from agents.booking import extract_booking_details, run_booking_flow
    
    # Extract details
    details = await extract_booking_details(query)
    
    # Run the booking flow
    result = await run_booking_flow(details)
    
    # Format a detailed, step-by-step execution report
    response_lines = [
        "[Booking Agent Response]",
        f"Query processed: '{query}'",
        "Welcome to VillageTaste Resort Booking! I can help you reserve cottages, check rates, and confirm stays.",
        f"Stay Details Extracted: Guest: {details.get('guest_name')}, Dates: {details.get('checkin')} to {details.get('checkout')}, Room: {details.get('room_type')}, Guests: {details.get('guests')}",
        "Step 1 (Validator Skill): Verification successful."
    ]
    
    if result["status"] == "validation_failed":
        response_lines[4] = f"Step 1 (Validator Skill): Failed. Errors: {', '.join(result['errors'])}"
        response_lines.append(f"Result: Booking aborted. {result['message']}")
    elif result["status"] == "availability_failed":
        response_lines.append("Step 2 (Calendar MCP Check): Failed. Requested dates are occupied.")
        response_lines.append(f"Result: Booking aborted. {result['message']}")
    else:
        response_lines.append("Step 2 (Calendar MCP Check): Success. Dates are available.")
        response_lines.append(f"Step 3 (Calendar MCP Reserve): Success. Reservation confirmed (Event ID: {result['reservation']['calendar_event_id']}).")
        response_lines.append("Step 4 (Gmail MCP Confirmation): Success. Confirmation receipt generated.")
        if "booking_summary" in result:
            response_lines.append(f"\nBooking Summary:\n{result['booking_summary']}\n")
        response_lines.append(f"Result: {result['message']}")
        
    return "\n".join(response_lines)


@node(name="run_reception_agent")
async def run_reception_agent(ctx: Context, query: str) -> str:
    """
    Delegates execution to the Reception Agent.
    """
    return await ReceptionAgent.run(query)


@node(name="run_guide_agent")
async def run_guide_agent(ctx: Context, query: str) -> str:
    """
    Delegates execution to the Guide Agent.
    """
    return await GuideAgent.run(query)


@node(name="run_scope_check_rejection")
async def run_scope_check_rejection(ctx: Context, query: str) -> str:
    """
    Triggered when the query is OUT_OF_SCOPE.
    """
    agent_response = (
        f"[Guide Agent Scope Guard Rejection]\n"
        f"Query checked: '{query}'\n"
        "I apologize, but that query is unrelated to VillageTaste Resort services. "
        "I can only help you with room bookings, activities, check-in, dining menus, or other resort amenities. "
        "Please let me know if you would like info on any resort-related services!"
    )
    return agent_response


# --- 3. Define the Dynamic Workflow Node ---
@node(rerun_on_resume=True)
async def resort_workflow_controller(ctx: Context, query: str) -> str:
    """
    Controller node for the resort assistant workflow.
    Classifies intent first, then routes to appropriate sub-agent node.
    """
    category = await ctx.run_node(classify_intent, query)
    
    if category == "BOOKING":
        return await ctx.run_node(run_booking_agent, query)
    elif category == "RECEPTION":
        return await ctx.run_node(run_reception_agent, query)
    elif category == "GUIDE":
        return await ctx.run_node(run_guide_agent, query)
    else:
        return await ctx.run_node(run_scope_check_rejection, query)


# --- 4. Expose the Workflow Agent ---
root_agent = Workflow(
    name="VillageTasteResortWorkflow",
    edges=[
        ("START", resort_workflow_controller)
    ]
)
