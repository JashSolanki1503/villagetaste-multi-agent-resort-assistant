# mcp/gmail_mcp.py
"""
Simulated Gmail Model Context Protocol (MCP) server integration.
Provides tools to send emails and guest notifications offline.
"""

def send_booking_confirmation(recipient: str, details: dict) -> str:
    """
    Simulates sending a room reservation confirmation email to the guest.
    Only logs the action and details.
    """
    log_msg = f"[Gmail MCP Log] Sending booking confirmation email to: {recipient}"
    print(log_msg)
    print(f"[Gmail MCP Log] Stay details: {details}")
    return f"[Gmail MCP] Booking confirmation successfully sent to {recipient}."

def send_guest_notification(recipient: str, message: str) -> str:
    """
    Simulates sending a general service notification email to the guest.
    Only logs the action.
    """
    log_msg = f"[Gmail MCP Log] Sending general notification to: {recipient}"
    print(log_msg)
    print(f"[Gmail MCP Log] Notification body: '{message}'")
    return f"[Gmail MCP] Notification successfully sent to {recipient}."

def send_complaint_acknowledgement(recipient: str, details: dict) -> str:
    """
    Simulates sending a complaint acknowledgement email to the guest.
    Logs the action and details.
    """
    log_msg = f"[Gmail MCP Log] Sending complaint acknowledgement email to: {recipient}"
    print(log_msg)
    print(f"[Gmail MCP Log] Complaint details: {details}")
    return f"[Gmail MCP] Complaint acknowledgement successfully sent to {recipient}."

def send_checkout_summary(recipient: str, billing_details: dict) -> str:
    """
    Simulates sending a checkout billing summary email to the guest.
    Logs the action and billing details.
    """
    log_msg = f"[Gmail MCP Log] Sending checkout billing summary email to: {recipient}"
    print(log_msg)
    print(f"[Gmail MCP Log] Billing summary details: {billing_details}")
    return f"[Gmail MCP] Checkout summary successfully sent to {recipient}."
