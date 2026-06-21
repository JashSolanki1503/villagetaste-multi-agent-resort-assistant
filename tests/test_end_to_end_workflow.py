# tests/test_end_to_end_workflow.py
"""
End-to-End integration tests for the VillageTaste Resort multi-agent system.
Demonstrates:
Scenario 1: Guest books a Deluxe Villa (writes to shared state and blocks calendar).
Scenario 2: Same guest submits a maintenance complaint (links to guest record in shared state).
Scenario 3: Guide Agent answers an activity question (queries local RAG database).
"""

import sys
import os
import asyncio
import unittest
from unittest.mock import MagicMock

# --- ADK 2.0 Library Mocking ---
# Mocks the google.adk module in sys.modules to allow running workflow nodes offline

class MockAgent:
    def __init__(self, name, model, instruction):
        self.name = name
        self.model = model
        self.instruction = instruction

class MockWorkflow:
    def __init__(self, name, edges):
        self.name = name
        self.edges = edges

adk_mock = MagicMock()
adk_mock.Agent = MockAgent
adk_mock.Workflow = MockWorkflow
adk_mock.Context = MagicMock()

workflow_mock = MagicMock()
def mock_node_decorator(*args, **kwargs):
    if len(args) == 1 and callable(args[0]):
        return args[0]
    def decorator(func):
        return func
    return decorator
workflow_mock.node = mock_node_decorator

sys.modules['google.adk'] = adk_mock
sys.modules['google.adk.workflow'] = workflow_mock
# --- End of Mocking ---

# Ensure the root project directory is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from workflows.resort_workflow import resort_workflow_controller
from shared_state import guest_records
from mcp import calendar_mcp, gmail_mcp


class MockContext:
    """
    A minimal mock context simulating the google.adk.Context behavior offline.
    """
    async def run_node(self, node_fn, *args, **kwargs):
        return await node_fn(self, *args, **kwargs)


class TestEndToEndWorkflow(unittest.TestCase):

    def setUp(self):
        self.ctx = MockContext()
        self.loop = asyncio.get_event_loop()
        # Reset the database state before each test run
        guest_records.clear_records()

    def tearDown(self):
        # Clean up database file after run
        guest_records.clear_records()

    def test_end_to_end_scenarios(self):
        """
        Executes Scenarios 1, 2, and 3 in sequence.
        """
        guest_email = "jane.doe@example.com"
        guest_name = "Jane Doe"

        # ======================================================================
        # SCENARIO 1: Guest (Jane Doe) books a Deluxe Villa
        # ======================================================================
        booking_query = f"I'd like to book a Deluxe Villa for 3 nights under the name of {guest_name} at {guest_email}."
        
        # Execute the workflow controller
        booking_response = self.loop.run_until_complete(
            resort_workflow_controller(self.ctx, booking_query)
        )
        
        # 1. Verify response details
        self.assertIn("[Booking Agent Response]", booking_response)
        self.assertIn(guest_name, booking_response)
        self.assertIn("Deluxe Villa", booking_response)
        self.assertIn("Reservation confirmed", booking_response)

        # 2. Verify shared guest state update
        guest_state = guest_records.get_guest_by_email(guest_email)
        self.assertIsNotNone(guest_state)
        self.assertEqual(guest_state["profile"]["guest_name"], guest_name)
        self.assertEqual(len(guest_state["reservations"]), 1)
        
        # 3. Verify Calendar Event block registration
        event_id = guest_state["reservations"][0]
        calendar_event = calendar_mcp.view_reservation(event_id)
        self.assertIsNotNone(calendar_event)
        self.assertEqual(calendar_event["room_type"], "Deluxe Villa")
        self.assertEqual(calendar_event["guest_name"], guest_name)
        self.assertEqual(calendar_event["checkin"], "2026-06-27")
        self.assertEqual(calendar_event["checkout"], "2026-06-30")
        self.assertEqual(calendar_event["guests"], 2)

        # ======================================================================
        # SCENARIO 2: Same guest (Jane Doe) submits a maintenance complaint
        # ======================================================================
        complaint_query = f"I want to report a broken light in my villa. My email is {guest_email}."
        
        # Execute the workflow controller
        reception_response = self.loop.run_until_complete(
            resort_workflow_controller(self.ctx, complaint_query)
        )
        
        # 1. Verify response details
        self.assertIn("[Reception Agent Response]", reception_response)
        self.assertIn(guest_name, reception_response)
        self.assertIn(guest_email, reception_response)
        self.assertIn("MAINTENANCE", reception_response)
        self.assertIn("[Gmail MCP] Complaint acknowledgement successfully sent", reception_response)

        # 2. Verify shared guest state linked complaint registration
        guest_state = guest_records.get_guest_by_email(guest_email)
        self.assertEqual(len(guest_state["complaints"]), 1)
        complaint_record = guest_state["complaints"][0]
        self.assertEqual(complaint_record["maintenance_issue"], complaint_query)
        self.assertEqual(complaint_record["status"], "Dispatched")

        # ======================================================================
        # SCENARIO 3: Guide Agent answers an activity question
        # ======================================================================
        guide_query = "Are there any pottery workshops?"
        
        # Execute the workflow controller
        guide_response = self.loop.run_until_complete(
            resort_workflow_controller(self.ctx, guide_query)
        )
        
        # 1. Verify response details
        self.assertIn("[Guide Agent Response]", guide_response)
        self.assertIn("pottery workshops", guide_response)
        self.assertIn("activities/activities.md", guide_response)


if __name__ == "__main__":
    unittest.main()
