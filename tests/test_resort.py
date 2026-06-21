# tests/test_resort.py
"""
Unit tests for checking the VillageTaste Resort multi-agent routing workflow.
Verifies intent classification and conditional routing behavior offline.
"""

import asyncio
import os
import sys
import unittest
from unittest.mock import MagicMock

# --- ADK 2.0 Library Mocking ---
# To make tests run offline without requiring external package installations,
# we mock the google.adk module in sys.modules.

class MockAgent:
    def __init__(self, name, model, instruction):
        self.name = name
        self.model = model
        self.instruction = instruction

class MockWorkflow:
    def __init__(self, name, edges):
        self.name = name
        self.edges = edges

# Construct mock modules
adk_mock = MagicMock()
adk_mock.Agent = MockAgent
adk_mock.Workflow = MockWorkflow
adk_mock.Context = MagicMock()

workflow_mock = MagicMock()
def mock_node_decorator(*args, **kwargs):
    # Support both @node and @node(rerun_on_resume=True) syntax
    if len(args) == 1 and callable(args[0]):
        return args[0]
    def decorator(func):
        return func
    return decorator
workflow_mock.node = mock_node_decorator

# Apply mocks to sys.modules
sys.modules['google.adk'] = adk_mock
sys.modules['google.adk.workflow'] = workflow_mock

# --- End of Mocking ---

# Ensure the root project directory is in the python path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from workflows.resort_workflow import (
    classify_intent,
    run_booking_agent,
    run_reception_agent,
    run_guide_agent,
    run_scope_check_rejection,
    resort_workflow_controller,
)


class MockContext:
    """
    A minimal mock context simulating the google.adk.Context behavior.
    Bypasses the actual ADK runtime engine to enable fast, offline, and lightweight tests.
    """
    async def run_node(self, node_fn, *args, **kwargs):
        return await node_fn(self, *args, **kwargs)


class TestResortWorkflowRouting(unittest.TestCase):
    
    def setUp(self):
        self.ctx = MockContext()
        self.loop = asyncio.get_event_loop()
        
        import agents.booking
        from agents import ReceptionAgent, GuideAgent
        
        self.original_extract = agents.booking.extract_booking_details
        self.original_flow = agents.booking.run_booking_flow
        self.original_reception = ReceptionAgent.run
        self.original_guide = GuideAgent.run
        
        async def mock_extract(query):
            return {"guest_name": "Bob Smith", "checkin": "2026-08-10", "checkout": "2026-08-15", "guests": 3, "room_type": "Standard Cottage"}
            
        async def mock_flow(details):
            return {
                "status": "success",
                "reservation": {"calendar_event_id": "evt_cal_standard_cottage_1"},
                "message": "Booking successfully confirmed for Bob Smith! [Gmail MCP] Booking confirmation successfully sent."
            }
            
        async def mock_reception(query):
            return "[Reception Agent Response]\nmanage guest check-ins, check-outs"
            
        async def mock_guide(query):
            return "[Guide Agent Response]\npottery workshops"
            
        agents.booking.extract_booking_details = mock_extract
        agents.booking.run_booking_flow = mock_flow
        ReceptionAgent.run = mock_reception
        GuideAgent.run = mock_guide

    def tearDown(self):
        import agents.booking
        from agents import ReceptionAgent, GuideAgent
        
        agents.booking.extract_booking_details = self.original_extract
        agents.booking.run_booking_flow = self.original_flow
        ReceptionAgent.run = self.original_reception
        GuideAgent.run = self.original_guide
        
    def test_classify_intent_booking(self):
        """Verifies that booking-related queries route to the BOOKING category."""
        query = "I'd like to book a deluxe villa next weekend."
        category = self.loop.run_until_complete(classify_intent(self.ctx, query))
        self.assertEqual(category, "BOOKING")
        
    def test_classify_intent_reception(self):
        """Verifies that reception and service queries route to the RECEPTION category."""
        query = "Can we get some fresh towels and submit a complaint about the shower?"
        category = self.loop.run_until_complete(classify_intent(self.ctx, query))
        self.assertEqual(category, "RECEPTION")
        
    def test_classify_intent_guide(self):
        """Verifies that resort info, menus, and activity queries route to the GUIDE category."""
        query = "What organic dishes are on the dining menu today?"
        category = self.loop.run_until_complete(classify_intent(self.ctx, query))
        self.assertEqual(category, "GUIDE")
        
    def test_classify_intent_out_of_scope(self):
        """Verifies that unrelated queries are identified as OUT_OF_SCOPE."""
        query = "Tell me the current stock price of Google."
        category = self.loop.run_until_complete(classify_intent(self.ctx, query))
        self.assertEqual(category, "OUT_OF_SCOPE")

    def test_workflow_executes_booking_agent(self):
        """Verifies workflow routes booking query to booking agent node and returns booking details."""
        query = "I want to reserve a cottage."
        response = self.loop.run_until_complete(resort_workflow_controller(self.ctx, query))
        self.assertIn("[Booking Agent Response]", response)
        self.assertIn("reserve cottages", response)

    def test_workflow_executes_reception_agent(self):
        """Verifies workflow routes checkout queries to reception agent node."""
        query = "I want to request checkout at 11am."
        response = self.loop.run_until_complete(resort_workflow_controller(self.ctx, query))
        self.assertIn("[Reception Agent Response]", response)
        self.assertIn("manage guest check-ins, check-outs", response)

    def test_workflow_executes_guide_agent(self):
        """Verifies workflow routes resort questions to guide agent node."""
        query = "Are there any pottery workshops?"
        response = self.loop.run_until_complete(resort_workflow_controller(self.ctx, query))
        self.assertIn("[Guide Agent Response]", response)
        self.assertIn("pottery workshops", response)

    def test_workflow_performs_rejection(self):
        """Verifies workflow rejects unrelated off-topic queries politely."""
        query = "Who was the first president of the United States?"
        response = self.loop.run_until_complete(resort_workflow_controller(self.ctx, query))
        self.assertIn("[Guide Agent Scope Guard Rejection]", response)
        self.assertIn("unrelated to VillageTaste Resort services", response)


if __name__ == "__main__":
    unittest.main()
