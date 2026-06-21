import sys
from pathlib import Path
import os
from dotenv import load_dotenv

# Load environment variables from .env
load_dotenv()

# Add project root to path to ensure robust imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from google.adk import Agent
from rag.retriever import search_resort_knowledge

# Check for google-genai package
has_genai = False
try:
    from google import genai
    has_genai = True
except ImportError:
    pass

# Define the Guide Agent
guide_agent = Agent(
    name="GuideAgent",
    model="gemini-2.5-flash",
    instruction=(
        "You are the Guide Agent for VillageTaste Resort, a fictional village-themed resort. "
        "Your responsibilities include:\n"
        "1. Answering questions about resort facilities, amenities, and design themes.\n"
        "2. Recommending activities and schedules (e.g., pottery, organic farming, guided hikes).\n"
        "3. Sharing information about dining options, menus, and ingredients sourced from our local farms.\n"
        "4. Resolving frequently asked questions (FAQs) regarding transport, services, and payments.\n"
        "5. Guardrails / Scope Checks: Detect queries that are completely unrelated to VillageTaste Resort "
        "(e.g., general world news, math homework, general knowledge, other businesses). "
        "Politely reject these out-of-scope questions and redirect the guest to resort services.\n\n"
        "Maintain an informative, local-expert, and friendly guide persona."
    )
)

def is_in_scope(query: str) -> bool:
    """
    Checks if a query is related to the resort (bookings, reception, dining, activities, policies).
    """
    query_lower = query.lower()
    
    # Common keywords representing all resort-related services (booking, reception, guide)
    resort_keywords = [
        "book", "reserve", "availability", "date", "room", "stay", "cottage", "villa", "suite",
        "check-in", "check-out", "checkin", "checkout", "check in", "check out", "complaint", "towel", 
        "towels", "maintenance", "repair", "broken", "leak", "service", "folio", "bill",
        "menu", "food", "eat", "dining", "breakfast", "lunch", "dinner", "beverage", "dessert",
        "pottery", "farm", "hike", "activity", "activities", "workshop", "excursion",
        "policy", "policies", "faq", "faqs", "resort", "hotel", "village", "taste",
        "transport", "payment", "pet", "smoking"
    ]
    return any(kw in query_lower for kw in resort_keywords)

def generate_answer_with_gemini(query: str, context: str) -> str:
    """
    Sends the user query and retrieved context to Gemini to generate a response.
    """
    api_key = os.environ.get("GEMINI_API_KEY")
    if not has_genai or not api_key:
        return None
        
    try:
        client = genai.Client(api_key=api_key)
        
        prompt = (
            "You are the Guide Agent for VillageTaste Resort, a fictional eco-luxury village-themed destination.\n"
            "Your persona is friendly, local-expert, informative, and polite.\n\n"
            "Use the following retrieved context from our resort knowledge base to answer the guest's query.\n"
            "Base your answer strictly on the provided context. If the answer is not present in the context or "
            "cannot be reasonably inferred, admit politely that you do not have that information and direct "
            "them to the reception desk.\n\n"
            "Constraints:\n"
            "- Do not make up schedules, prices, or amenities.\n"
            "- Do not mention external hotels or services outside VillageTaste Resort.\n"
            "- Rely strictly on the grounded facts in the context.\n\n"
            f"Context:\n{context}\n\n"
            f"Guest Query: {query}\n\n"
            "Grounded Response:"
        )
        
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=prompt
        )
        return response.text
    except Exception as e:
        print(f"[Guide Agent] Gemini generation failed: {e}")
        return None

async def run_guide_agent(query: str) -> str:
    """
    Executes the Guide Agent in RAG mode.
    Validates scope, queries local vector store, builds context,
    sends context + query to Gemini (once per request), and returns the natural language response.
    """
    # 1. Scope Guard Check
    if not is_in_scope(query):
        return (
            "[Guide Agent Scope Guard Rejection]\n"
            f"Query checked: '{query}'\n"
            "I apologize, but that query is unrelated to VillageTaste Resort services. "
            "I can only help you with room bookings, activities, check-in, dining menus, or other resort amenities. "
            "Please let me know if you would like info on any resort-related services!"
        )

    # Use the FAQ Category Router Skill
    from skills.faq_router import route_faq
    faq_category = route_faq(query)

    # 2. Retrieve local RAG knowledge (top-k matching chunks) narrowed by category
    search_results = search_resort_knowledge(query, category=faq_category)
    results = search_results.get("results", [])

    # Detailed logging
    print("\n" + "=" * 60)
    print(f"[Guide Agent RAG Log] User Query: '{query}'")
    print(f"[Guide Agent RAG Log] Routed FAQ Category: '{faq_category}'")
    if results:
        print("[Guide Agent RAG Log] Retrieved Chunks & Similarity Scores:")
        for idx, r in enumerate(results, 1):
            print(f"  {idx}. Source: {r['source']} | Score (L2): {r['score']:.4f}")
    else:
        print("[Guide Agent RAG Log] No relevant documents found.")
    print("=" * 60 + "\n")

    # 3. If no relevant chunks are found
    if not results or results[0]["score"] > 0.85:
        return (
            "[Guide Agent Response]\n"
            f"Query processed: '{query}'\n"
            f"Routed Category: {faq_category.upper()}\n"
            "I apologize, but I could not find that information in the VillageTaste Resort knowledge base. "
            "Please contact our reception desk for further assistance."
        )

    # 4. Build a context string from retrieved content
    context_parts = []
    sources = set()
    for r in results:
        if r["score"] <= 0.85:
            context_parts.append(r["content"])
            sources.add(r["source"])

    joined_context = "\n\n".join(context_parts)
    sources_str = ", ".join(sorted(sources))
    
    # 5. Generate Natural Language Response using Gemini
    gemini_response = generate_answer_with_gemini(query, joined_context)
    
    if gemini_response:
        agent_response = (
            "[Guide Agent Response]\n"
            f"Query processed: '{query}'\n"
            f"Routed Category: {faq_category.upper()}\n\n"
            f"{gemini_response.strip()}\n\n"
            f"(Source: {sources_str})"
        )
    else:
        agent_response = (
            "[Guide Agent Response]\n"
            f"Query processed: '{query}'\n"
            f"Routed Category: {faq_category.upper()}\n"
            "[Simulated Grounded Response (No Gemini API Key)]:\n"
            "Here is the relevant information found in the resort knowledge base:\n"
            f"{joined_context}\n\n"
            f"(Source: {sources_str})"
        )
        
    return agent_response

# Expose the execution helper on the guide_agent instance for easy calling
guide_agent.run = run_guide_agent

