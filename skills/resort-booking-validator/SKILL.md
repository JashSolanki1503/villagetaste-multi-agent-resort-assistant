---
name: resort-booking-validator
description: Validates resort room booking requests for guest name, check-in, check-out, and guest count (>0) before processing check-ins or calendar updates.
license: Apache-2.0
metadata:
  author: Antigravity
  version: "1.0"
---

# resort-booking-validator

This skill guides the Booking Agent in performing structural verification checks on incoming guest room reservation requests. 

## Purpose
Ensure all incoming booking requests contain complete and logically consistent information before engaging downstream services (such as calendar availability checks or confirmation email generation).

## Validation Rules
The agent must verify that the request contains the following properties:
1. **Guest Name**: A non-empty string representing the guest's name.
2. **Check-in Date**: A non-empty string representing the arrival date.
3. **Check-out Date**: A non-empty string representing the departure date.
4. **Number of Guests**: An integer greater than 0 representing the guest count.

## Error Handling
If any of the parameters are missing or invalid:
- Do not check the calendar.
- Do not trigger booking confirmation notifications.
- Respond with a clear checklist of missing/invalid fields and politely ask the guest to provide them.

## When to Use This Skill
- Activate this skill immediately upon receiving a reservation query or booking request from the orchestrator.
