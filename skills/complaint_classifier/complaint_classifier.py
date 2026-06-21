# skills/complaint_classifier/complaint_classifier.py
"""
Complaint Classification Skill for Reception Agent.
Categorizes complaint queries into MAINTENANCE, HOUSEKEEPING, BILLING, or GENERAL.
"""

def classify_complaint(complaint_text: str) -> str:
    """
    Classifies a guest complaint into one of the four categories:
    - MAINTENANCE
    - HOUSEKEEPING
    - BILLING
    - GENERAL
    """
    if not complaint_text:
        return "GENERAL"
        
    text_lower = complaint_text.lower()
    
    # 1. Maintenance keywords: related to infrastructure, systems, appliances, plumbing
    maintenance_keywords = [
        "ac", "air condition", "air conditioning", "heater", "heating", "light", 
        "leak", "plumbing", "fix", "repair", "maintenance", "lock", "toilet", 
        "shower", "appliance", "tv", "television", "internet", "wifi", "power", 
        "electricity", "fan", "faucet", "water", "drain", "fridge", "refrigerator",
        "broken", "work order"
    ]
    
    # 2. Housekeeping keywords: related to cleanliness, laundry, room items, restocking
    housekeeping_keywords = [
        "dirty", "clean", "towel", "towels", "pillow", "pillows", "blanket", 
        "blankets", "bed", "sheets", "dust", "trash", "messy", "soap", "shampoo", 
        "smell", "stain", "room service", "linen", "vacuum", "restock", "dirty room"
    ]
    
    # 3. Billing keywords: related to invoicing, fees, costs, pricing, payments, refunds
    billing_keywords = [
        "charge", "invoice", "bill", "payment", "credit card", "refund", "price", 
        "rate", "overcharged", "cost", "fee", "fees", "amount", "charged", 
        "receipt", "billing", "charges", "checkout summary", "extra charge"
    ]
    
    # Check matching keywords
    # If a keyword is matched, we return that category.
    # To handle overlaps, we match in order of specificity.
    if any(k in text_lower for k in maintenance_keywords):
        return "MAINTENANCE"
    elif any(k in text_lower for k in housekeeping_keywords):
        return "HOUSEKEEPING"
    elif any(k in text_lower for k in billing_keywords):
        return "BILLING"
    else:
        return "GENERAL"
