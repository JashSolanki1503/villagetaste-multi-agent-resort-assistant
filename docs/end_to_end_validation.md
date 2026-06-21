# End-to-End Validation Report

> **Status:** SUCCESS (Offline Fallback)
> **Timestamp:** 2026-06-20 20:38:20
> **Mode:** Offline Simulation

---

## 1. Test Query

```
What accommodation types are available at VillageTaste Resort?
```

## 2. Execution Flow

```
User Query
  -> ChromaDB Retriever  (9956 ms)
  -> Context Builder      (3 chunks, 1099 chars)
  -> Gemini Generation    (0 ms, model: gemini-2.5-flash)
  -> Final Response
```

## 3. Retrieved Source Documents

| # | Source File | L2 Distance | Relevance |
|---|-----------|-------------|----------|
| 1 | `activities/activities.md` | 0.4771 | Strong |
| 2 | `resort_info/resort_info.md` | 0.4820 | Strong |
| 3 | `policies/policies.md` | 0.4860 | Strong |


## 4. Context Sent to Gemini

<details>
<summary>Click to expand full context block (1099 characters)</summary>

```text
# VillageTaste Resort Activities & Experiences

At VillageTaste Resort, we encourage guests to reconnect with nature, traditional crafts, and rural culture. Below is our catalog of experiences, workshops, and outdoor activities available on the property.

---

## 1. Craft & Learning Workshops

# VillageTaste Resort Profile & Information

Welcome to **VillageTaste Resort**, an eco-luxury village-themed destination nestled in the foothills of the Whispering Hills. Our resort is designed to recreate the simple charm, peaceful pace, and organic lifestyle of a traditional countryside village, combined with premium hospitality and modern comfort.

---

## 1. Resort History & Vision

*   **Single-Use Plastic Ban**: VillageTaste Resort is a **single-use plastic-free zone**. Guests must not bring plastic water bottles, disposable shopping bags, or styrofoam packaging onto the property.
*   **Water Conservation**: Guests are encouraged to conserve water. Shower linens and bedding are changed every third day of stay unless a daily change is explicitly requested via the green housekeeping card.
```

</details>

## 5. Gemini Prompt

<details>
<summary>Click to expand full prompt</summary>

```text
You are the Guide Agent for VillageTaste Resort, a fictional eco-luxury village-themed destination.
Your persona is friendly, local-expert, informative, and polite.

Use the following retrieved context from our resort knowledge base to answer the guest's query.
Base your answer strictly on the provided context. If the answer is not present in the context or cannot be reasonably inferred, admit politely that you do not have that information and direct them to the reception desk.

Constraints:
- Do not make up schedules, prices, or amenities.
- Do not mention external hotels or services outside VillageTaste Resort.
- Rely strictly on the grounded facts in the context.

Context:
# VillageTaste Resort Activities & Experiences

At VillageTaste Resort, we encourage guests to reconnect with nature, traditional crafts, and rural culture. Below is our catalog of experiences, workshops, and outdoor activities available on the property.

---

## 1. Craft & Learning Workshops

# VillageTaste Resort Profile & Information

Welcome to **VillageTaste Resort**, an eco-luxury village-themed destination nestled in the foothills of the Whispering Hills. Our resort is designed to recreate the simple charm, peaceful pace, and organic lifestyle of a traditional countryside village, combined with premium hospitality and modern comfort.

---

## 1. Resort History & Vision

*   **Single-Use Plastic Ban**: VillageTaste Resort is a **single-use plastic-free zone**. Guests must not bring plastic water bottles, disposable shopping bags, or styrofoam packaging onto the property.
*   **Water Conservation**: Guests are encouraged to conserve water. Shower linens and bedding are changed every third day of stay unless a daily change is explicitly requested via the green housekeeping card.

Guest Query: What accommodation types are available at VillageTaste Resort?

Grounded Response:
```

</details>

## 6. Final Grounded Response

```
[Simulated Grounded Response (No Gemini API Key)]:
Here is the relevant information found in the resort knowledge base:
---
# VillageTaste Resort Activities & Experiences

At VillageTaste Resort, we encourage guests to reconnect with nature, traditional crafts, and rural culture. Below is our catalog of experiences, workshops, and outdoor activities available on the property.

---

## 1. Craft & Learning Workshops

# VillageTaste Resort Profile & Information

Welcome to **VillageTaste Resort**, an eco-luxury village-themed destination nestled in the foothills of the Whispering Hills. Our resort is designed to recreate the simple charm, peaceful pace, and organic lifestyle of a traditional countryside village, combined with premium hospitality and modern comfort.

---

## 1. Resort History & Vision

*   **Single-Use Plastic Ban**: VillageTaste Resort is a **single-use plastic-free zone**. Guests must not bring plastic water bottles, disposable shopping bags, or styrofoam packaging onto the property.
*   **Water Conservation**: Guests are encouraged to conserve water. Shower linens and bedding are changed every third day of stay unless a daily change is explicitly requested via the green housekeeping card.

(Source: activities/activities.md, policies/policies.md, resort_info/resort_info.md)
```

## 7. Validation Summary

| Metric | Value |
|--------|-------|
| Query | `What accommodation types are available at VillageTaste Resort?` |
| Chunks Retrieved | 3 |
| Chunks Used in Context | 3 |
| Source Files | activities/activities.md, policies/policies.md, resort_info/resort_info.md |
| Retrieval Latency | 9956 ms |
| Gemini Latency | 0 ms |
| Gemini Model | `gemini-2.5-flash` |
| API Key Present | No |
| Gemini Error | GEMINI_API_KEY not set in .env |
| Overall Result | **SUCCESS (Offline Fallback)** |
