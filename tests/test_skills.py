# tests/test_skills.py
"""
Unit tests for the newly added VillageTaste Resort Agent Skills:
1. Booking Validation Skill
2. Complaint Classification Skill
3. Booking Summary Generator Skill
4. FAQ Category Router Skill
"""

import sys
import unittest
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

from skills.booking_validator import validate_booking
from skills.complaint_classifier import classify_complaint
from skills.booking_summary import generate_booking_summary
from skills.faq_router import route_faq


class TestAgentSkills(unittest.TestCase):

    # 1. Booking Validation Skill Tests
    def test_validator_valid(self):
        details = {
            "guest_name": "Alice Cooper",
            "checkin": "2026-07-10",
            "checkout": "2026-07-15",
            "guests": 2,
            "room_type": "Deluxe Villa"
        }
        res = validate_booking(details)
        self.assertTrue(res["valid"])
        self.assertEqual(res["message"], "Booking validated successfully")

    def test_validator_invalid_room_type(self):
        details = {
            "guest_name": "Alice Cooper",
            "checkin": "2026-07-10",
            "checkout": "2026-07-15",
            "guests": 2,
            "room_type": "Tent"
        }
        res = validate_booking(details)
        self.assertFalse(res["valid"])
        self.assertEqual(res["message"], "Invalid room type")

    def test_validator_checkout_before_checkin(self):
        details = {
            "guest_name": "Alice Cooper",
            "checkin": "2026-07-15",
            "checkout": "2026-07-10",
            "guests": 2,
            "room_type": "Deluxe Villa"
        }
        res = validate_booking(details)
        self.assertFalse(res["valid"])
        self.assertEqual(res["message"], "Check-out date must be after check-in date.")

    def test_validator_invalid_guests(self):
        details = {
            "guest_name": "Alice Cooper",
            "checkin": "2026-07-10",
            "checkout": "2026-07-15",
            "guests": 0,
            "room_type": "Deluxe Villa"
        }
        res = validate_booking(details)
        self.assertFalse(res["valid"])
        self.assertEqual(res["message"], "Number of guests must be greater than 0.")

        details["guests"] = -5
        res = validate_booking(details)
        self.assertFalse(res["valid"])

        details["guests"] = "invalid"
        res = validate_booking(details)
        self.assertFalse(res["valid"])

    def test_validator_invalid_dates(self):
        details = {
            "guest_name": "Alice Cooper",
            "checkin": "2026/07/10",
            "checkout": "2026-07-15",
            "guests": 2,
            "room_type": "Deluxe Villa"
        }
        res = validate_booking(details)
        self.assertFalse(res["valid"])
        self.assertEqual(res["message"], "Invalid check-in date format.")

        details["checkin"] = "2026-07-10"
        details["checkout"] = "2026-07-32"
        res = validate_booking(details)
        self.assertFalse(res["valid"])
        self.assertEqual(res["message"], "Invalid check-out date format.")

    def test_validator_missing_fields(self):
        details = {
            "checkin": "2026-07-10",
            "checkout": "2026-07-15",
            "guests": 2,
            "room_type": "Deluxe Villa"
        }
        res = validate_booking(details)
        self.assertFalse(res["valid"])
        self.assertEqual(res["message"], "Guest name is missing.")

    # 2. Complaint Classification Skill Tests
    def test_complaint_maintenance(self):
        self.assertEqual(classify_complaint("AC not working"), "MAINTENANCE")
        self.assertEqual(classify_complaint("The light in the toilet is broken"), "MAINTENANCE")
        self.assertEqual(classify_complaint("water leak in shower"), "MAINTENANCE")

    def test_complaint_housekeeping(self):
        self.assertEqual(classify_complaint("Room is dirty"), "HOUSEKEEPING")
        self.assertEqual(classify_complaint("we need extra towels and pillows"), "HOUSEKEEPING")
        self.assertEqual(classify_complaint("trash bin is full"), "HOUSEKEEPING")

    def test_complaint_billing(self):
        self.assertEqual(classify_complaint("Wrong charge on invoice"), "BILLING")
        self.assertEqual(classify_complaint("why was I billed $100 extra"), "BILLING")
        self.assertEqual(classify_complaint("request refund on the booking fee"), "BILLING")

    def test_complaint_general(self):
        self.assertEqual(classify_complaint("The weather today is cloudy"), "GENERAL")
        self.assertEqual(classify_complaint("nothing special, just want to talk"), "GENERAL")

    # 3. Booking Summary Generator Skill Tests
    def test_booking_summary_generation(self):
        guest_info = {"guest_name": "John Doe"}
        booking_info = {
            "room_type": "Deluxe Villa",
            "guests": 2,
            "checkin": "2026-08-01",
            "checkout": "2026-08-04"
        }
        summary = generate_booking_summary(guest_info, booking_info)
        expected = (
            "Guest Name: John Doe\n"
            "Accommodation: Deluxe Villa\n"
            "Guests: 2\n"
            "Stay Duration: 3 Nights"
        )
        self.assertEqual(summary, expected)

    # 4. FAQ Category Router Skill Tests
    def test_faq_router_activities(self):
        self.assertEqual(route_faq("What activities are available?"), "Activities")
        self.assertEqual(route_faq("Can I book a pottery workshop?"), "Activities")
        self.assertEqual(route_faq("Is there a guided hiking trail?"), "Activities")

    def test_faq_router_dining(self):
        self.assertEqual(route_faq("What food is served?"), "Dining")
        self.assertEqual(route_faq("Do you have vegan options on the menu?"), "Dining")
        self.assertEqual(route_faq("Is breakfast included in the dining options?"), "Dining")

    def test_faq_router_policies(self):
        self.assertEqual(route_faq("What is the cancellation policy?"), "Policies")
        self.assertEqual(route_faq("Is there a pet fee for deluxe villas?"), "Policies")
        self.assertEqual(route_faq("Do you charge extra for children?"), "Policies")

    def test_faq_router_transportation(self):
        self.assertEqual(route_faq("How do I get to Windsong Airport?"), "Transportation")
        self.assertEqual(route_faq("Is there a shuttle service from the railway station?"), "Transportation")
        self.assertEqual(route_faq("Where can we park our EV?"), "Transportation")

    def test_faq_router_accommodation(self):
        self.assertEqual(route_faq("Does the luxury suite have heating?"), "Accommodation")
        self.assertEqual(route_faq("Is there WiFi in the rooms?"), "Accommodation")


if __name__ == "__main__":
    unittest.main()
