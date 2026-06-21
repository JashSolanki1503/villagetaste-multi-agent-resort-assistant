# tests/test_mcp.py
"""
Unit tests for the Booking validation and MCP simulated sub-systems.
Checks validation constraints, simulated calendar conflicts, and booking flows.
"""

import sys
import unittest
from pathlib import Path

# Add project root to python path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Mock google.adk prior to importing agents to run completely offline
try:
    import google.adk
except ImportError:
    from unittest.mock import MagicMock
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

from agents.booking import validate_booking_request, run_booking_flow
from mcp.gmail_mcp import send_booking_confirmation, send_guest_notification
from mcp.calendar_mcp import check_availability, reserve_booking_dates


class TestResortMCPSystem(unittest.TestCase):

    def test_booking_validation_valid(self):
        """Verifies validation passes for complete check-in requests."""
        details = {
            "guest_name": "John Doe",
            "checkin": "2026-08-01",
            "checkout": "2026-08-05",
            "guests": 2,
            "room_type": "Deluxe Villa"
        }
        errors = validate_booking_request(details)
        self.assertEqual(len(errors), 0)

    def test_booking_validation_missing_fields(self):
        """Verifies validation returns correct errors for incomplete requests."""
        details = {
            "guest_name": "",
            "checkin": "",
            "checkout": "2026-08-05",
            "guests": -1
        }
        errors = validate_booking_request(details)
        self.assertIn("Guest name is missing.", errors)
        self.assertIn("Check-in date is missing.", errors)
        self.assertIn("Number of guests must be greater than 0.", errors)

    def test_gmail_mcp_methods(self):
        """Verifies simulated Gmail MCP logging responses."""
        confirm_res = send_booking_confirmation("guest@example.com", {"guest_name": "Alice"})
        self.assertIn("Booking confirmation successfully sent", confirm_res)

        notify_res = send_guest_notification("guest@example.com", "Your room is ready.")
        self.assertIn("Notification successfully sent", notify_res)

    def test_calendar_mcp_availability_checks(self):
        """Verifies availability detection against pre-existing slots."""
        # Standard Cottage is busy on these dates in simulator database
        is_avail_busy = check_availability("Standard Cottage", "2026-07-01", "2026-07-07")
        self.assertFalse(is_avail_busy)

        # Other dates or rooms should return available
        is_avail_free = check_availability("Standard Cottage", "2026-07-08", "2026-07-12")
        self.assertTrue(is_avail_free)

    def test_calendar_mcp_reservation(self):
        """Verifies simulated calendar event block generation."""
        res = reserve_booking_dates("Luxury Suite", "2026-09-01", "2026-09-05")
        self.assertEqual(res["status"], "confirmed")
        self.assertEqual(res["room_type"], "Luxury Suite")
        self.assertTrue(res["calendar_event_id"].startswith("evt_cal_luxury_suite_"))

    def test_run_booking_flow_success(self):
        """Verifies complete validation->check->reserve->dispatch booking agent flow."""
        details = {
            "guest_name": "Bob Smith",
            "checkin": "2026-08-10",
            "checkout": "2026-08-15",
            "guests": 3,
            "room_type": "Luxury Suite",
            "email": "bob@example.com"
        }
        # Run synchronous wrapper since ADK runner handles async nodes
        import asyncio
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(run_booking_flow(details))
        
        self.assertEqual(result["status"], "success")
        self.assertIn("Booking successfully confirmed for Bob Smith", result["message"])

    def test_run_booking_flow_failure_occupied(self):
        """Verifies booking agent handles calendar date conflicts gracefully."""
        details = {
            "guest_name": "Charlie Brown",
            "checkin": "2026-07-01",
            "checkout": "2026-07-07",
            "guests": 1,
            "room_type": "Standard Cottage"
        }
        import asyncio
        loop = asyncio.get_event_loop()
        result = loop.run_until_complete(run_booking_flow(details))
        
        self.assertEqual(result["status"], "availability_failed")
        self.assertIn("Availability check failed", result["message"])


if __name__ == "__main__":
    unittest.main()
