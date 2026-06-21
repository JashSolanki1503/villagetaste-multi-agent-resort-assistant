# tests/test_skills_integration.py
"""
Integration tests for verifying Agent Skills integration in the VillageTaste Resort System:
1. Booking Agent successfully validates bookings and calls skills.
2. Reception Agent correctly classifies complaints automatically.
3. Guide Agent correctly routes FAQ categories and narrows retrieval.
"""

import sys
import asyncio
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# Add project root to python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Mock google.adk prior to importing agents to run completely offline
try:
    import google.adk
except ImportError:
    class MockAgent:
        def __init__(self, name, model, instruction):
            self.name = name
            self.model = model
            self.instruction = instruction
            
    import google
    mock_adk = MagicMock()
    mock_adk.Agent = MockAgent
    google.adk = mock_adk
    sys.modules['google.adk'] = mock_adk

from agents.booking import run_booking_flow
from agents.reception import run_reception_agent
from agents.guide import run_guide_agent


class TestAgentSkillsIntegration(unittest.TestCase):

    def setUp(self):
        self.loop = asyncio.get_event_loop()

    # 1. Booking Agent Integration Test
    def test_booking_agent_validation_integration(self):
        """Proves Booking Agent successfully validates a booking request."""
        # A valid booking request should proceed and succeed
        valid_details = {
            "guest_name": "Dave Grohl",
            "checkin": "2026-07-15",
            "checkout": "2026-07-20",
            "guests": 2,
            "room_type": "Deluxe Villa",
            "email": "dave@example.com"
        }
        res = self.loop.run_until_complete(run_booking_flow(valid_details))
        self.assertEqual(res["status"], "success")
        self.assertIn("booking_summary", res)
        self.assertIn("Dave Grohl", res["booking_summary"])
        self.assertIn("Stay Duration: 5 Nights", res["booking_summary"])
        
        # An invalid booking request (invalid room type) should be validated and fail
        invalid_details = {
            "guest_name": "Dave Grohl",
            "checkin": "2026-07-15",
            "checkout": "2026-07-20",
            "guests": 2,
            "room_type": "Treehouse",
            "email": "dave@example.com"
        }
        res_fail = self.loop.run_until_complete(run_booking_flow(invalid_details))
        self.assertEqual(res_fail["status"], "validation_failed")
        self.assertIn("Invalid room type", res_fail["errors"][0])

    # 2. Reception Agent Integration Test
    def test_reception_agent_complaint_classification_integration(self):
        """Proves Reception Agent correctly classifies complaints."""
        # A complaint query should be classified as MAINTENANCE
        query_maint = "The AC is not working in my room. My email is guest@example.com"
        res_maint = self.loop.run_until_complete(run_reception_agent(query_maint))
        self.assertIn("MAINTENANCE", res_maint)
        self.assertIn("The complaint has been classified as MAINTENANCE", res_maint)
        
        # A complaint query should be classified as HOUSEKEEPING
        query_hk = "My room is extremely dirty. Email: guest@example.com"
        res_hk = self.loop.run_until_complete(run_reception_agent(query_hk))
        self.assertIn("HOUSEKEEPING", res_hk)
        self.assertIn("The complaint has been classified as HOUSEKEEPING", res_hk)

        # A complaint query should be classified as BILLING
        query_billing = "I noticed a wrong charge on my invoice today. Email: guest@example.com"
        res_billing = self.loop.run_until_complete(run_reception_agent(query_billing))
        self.assertIn("BILLING", res_billing)
        self.assertIn("The complaint has been classified as BILLING", res_billing)

    # 3. Guide Agent Integration Test
    def test_guide_agent_faq_routing_integration(self):
        """Proves Guide Agent correctly routes FAQ categories."""
        # 1. Activities routing and retrieval
        query_act = "What activities are available at the resort?"
        res_act = self.loop.run_until_complete(run_guide_agent(query_act))
        self.assertIn("ACTIVITIES", res_act)
        self.assertIn("Routed Category: ACTIVITIES", res_act)
        
        # 2. Dining routing
        query_dining = "What food is served in the restaurant?"
        res_dining = self.loop.run_until_complete(run_guide_agent(query_dining))
        self.assertIn("DINING", res_dining)
        self.assertIn("Routed Category: DINING", res_dining)

        # 3. Policies routing
        query_policies = "What is the pet policy for deluxe villas?"
        res_policies = self.loop.run_until_complete(run_guide_agent(query_policies))
        self.assertIn("POLICIES", res_policies)
        self.assertIn("Routed Category: POLICIES", res_policies)


if __name__ == "__main__":
    unittest.main()
