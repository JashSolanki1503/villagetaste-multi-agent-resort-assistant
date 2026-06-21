# skills/faq_router/faq_router.py
"""
FAQ Category Router Skill.
Classifies Guide Agent queries into Activities, Dining, Accommodation, Policies, or Transportation.
"""

def route_faq(query: str) -> str:
    """
    Classifies a user query into one of:
    - Activities
    - Dining
    - Accommodation
    - Policies
    - Transportation
    """
    if not query:
        return "Accommodation"
        
    query_lower = query.lower()
    
    # Keyword definitions mapping to each category
    # 1. Activities: related to recreation, workshops, farm crop harvesting, guided hikes, yoga
    activities_keywords = [
        "pottery", "farm", "hike", "activity", "activities", "workshop", "excursion", 
        "excursions", "yoga", "bonfire", "trail", "trails", "walk", "harvesting", 
        "clay", "handicrafts", "artisan", "zoo", "workshops", "cooking class",
        "outdoor", "indoor", "pool", "swimming"
    ]
    
    # 2. Dining: related to food, menus, ingredients, meals, drinks, diets, restaurant
    dining_keywords = [
        "food", "menu", "breakfast", "lunch", "dinner", "eat", "dining", "chef", 
        "organic", "ingredient", "harvest table", "drink", "beverage", "vegan", 
        "vegetarian", "gluten", "allergy", "allergies", "restaurant", "cook",
        "dishes", "served"
    ]
    
    # 3. Policies: related to bookings, cancellations, check-in rules, pets, smoking, refunds, children
    policies_keywords = [
        "policy", "policies", "cancel", "cancellation", "refund", "refunds", 
        "rules", "pets", "pet", "smoking", "children", "child", "fee", "fees", 
        "billing", "payment", "cards", "cash", "credit card", "refunded", 
        "occupancy", "refunds", "cancel booking"
    ]
    
    # 4. Transportation: related to airport, pickup, shuttle, train, railway, parking, EV, valet
    transportation_keywords = [
        "airport", "train", "railway", "pickup", "shuttle", "transport", 
        "transportation", "station", "taxi", "cab", "driving", "drive", 
        "location", "get to", "parking", "ev", "charging", "valet", 
        "how do i get", "arrive"
    ]
    
    # 5. Accommodation: related to rooms, cottages, villas, suites, AC/heating, room amenities, WiFi
    accommodation_keywords = [
        "cottage", "villa", "suite", "accommodation", "accommodations", "room", 
        "rooms", "bed", "beds", "ac", "heating", "wifi", "internet", "luxury suite",
        "deluxe villa", "standard cottage", "amenities", "amenity", "stay"
    ]

    scores = {
        "Activities": 0,
        "Dining": 0,
        "Policies": 0,
        "Transportation": 0,
        "Accommodation": 0
    }
    
    for kw in activities_keywords:
        if kw in query_lower:
            scores["Activities"] += 1
            
    for kw in dining_keywords:
        if kw in query_lower:
            scores["Dining"] += 1
            
    for kw in policies_keywords:
        if kw in query_lower:
            scores["Policies"] += 1
            
    for kw in transportation_keywords:
        if kw in query_lower:
            scores["Transportation"] += 1
            
    for kw in accommodation_keywords:
        if kw in query_lower:
            scores["Accommodation"] += 1

    max_score = max(scores.values())
    if max_score > 0:
        candidates = [cat for cat, score in scores.items() if score == max_score]
        # Prioritize dining, activities, policies, transportation, then accommodation
        for prio in ["Dining", "Activities", "Policies", "Transportation", "Accommodation"]:
            if prio in candidates:
                return prio
        return candidates[0]
        
    # Heuristic fallback based on substrings
    if "food" in query_lower or "eat" in query_lower or "menu" in query_lower or "dish" in query_lower:
        return "Dining"
    if "pottery" in query_lower or "activities" in query_lower or "workshop" in query_lower:
        return "Activities"
    if "cancel" in query_lower or "pet" in query_lower or "policy" in query_lower:
        return "Policies"
    if "airport" in query_lower or "shuttle" in query_lower or "transport" in query_lower:
        return "Transportation"
        
    return "Accommodation"
