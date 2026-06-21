#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Single-shot end-to-end validation of the Guide Agent pipeline.

Execution flow:
  User Query -> ChromaDB Retriever -> Build Context -> Gemini Generation -> Grounded Response

This script makes EXACTLY ONE Gemini API request and then stops.
All intermediate artefacts (source docs, scores, context, response) are captured
and written to  docs/end_to_end_validation.md.
"""

import sys, os, io, time, textwrap
from pathlib import Path
from datetime import datetime

# Force UTF-8 on stdout to avoid cp1252 encoding errors on Windows
sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")

# ── Bootstrap imports ──────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT_ROOT))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# Mock google.adk so the agent module can be imported offline
from unittest.mock import MagicMock

class _MA:
    def __init__(self, name, model, instruction):
        self.name = name; self.model = model; self.instruction = instruction

_adk = MagicMock(); _adk.Agent = _MA
sys.modules.setdefault("google.adk", _adk)
sys.modules.setdefault("google.adk.workflow", MagicMock())

from rag.retriever import search_resort_knowledge

# ── Configuration ──────────────────────────────────────────────────────────────
QUERY = "What accommodation types are available at VillageTaste Resort?"
OUTPUT_FILE = PROJECT_ROOT / "docs" / "end_to_end_validation.md"

# ── Stage 1: Retrieve chunks ──────────────────────────────────────────────────
print(f"\n{'='*70}")
print(f"[Stage 1] Querying ChromaDB for: '{QUERY}'")
print(f"{'='*70}")

t0 = time.perf_counter()
rag_data = search_resort_knowledge(QUERY)
retrieval_ms = (time.perf_counter() - t0) * 1000
results = rag_data.get("results", [])

print(f"  Retrieved {len(results)} chunks in {retrieval_ms:.0f} ms")
for i, r in enumerate(results, 1):
    print(f"  {i}. Source: {r['source']}  |  L2: {r['score']:.4f}")

# ── Stage 2: Build context ────────────────────────────────────────────────────
context_parts = []
sources = set()
for r in results:
    if r["score"] <= 0.85:
        context_parts.append(r["content"])
        sources.add(r["source"])

context_block = "\n\n".join(context_parts)
sources_str = ", ".join(sorted(sources))

print(f"\n{'='*70}")
print(f"[Stage 2] Context built -- {len(context_parts)} chunks, {len(context_block)} chars")
print(f"  Sources: {sources_str}")
print(f"{'='*70}")

# ── Stage 3: Gemini generation (ONE call) ──────────────────────────────────────
gemini_prompt = (
    "You are the Guide Agent for VillageTaste Resort, a fictional eco-luxury village-themed destination.\n"
    "Your persona is friendly, local-expert, informative, and polite.\n\n"
    "Use the following retrieved context from our resort knowledge base to answer the guest's query.\n"
    "Base your answer strictly on the provided context. If the answer is not present in the context or "
    "cannot be reasonably inferred, admit politely that you do not have that information and direct "
    "them to the reception desk.\n\n"
    "Constraints:\n"
    "- Do not make up schedules, prices, or amenities.\n"
    "- Do not mention external hotels or services outside VillageTaste Resort.\n"
    "- Rely strictly on the grounded facts in the context.\n\n"
    f"Context:\n{context_block}\n\n"
    f"Guest Query: {QUERY}\n\n"
    "Grounded Response:"
)

api_key = os.environ.get("GEMINI_API_KEY")
gemini_response = None
gemini_error = None
gemini_model = "gemini-2.5-flash"
gemini_ms = 0

print(f"\n{'='*70}")
print(f"[Stage 3] Sending ONE request to Gemini ({gemini_model})")
print(f"{'='*70}")

if api_key:
    try:
        from google import genai
        client = genai.Client(api_key=api_key)
        t1 = time.perf_counter()
        resp = client.models.generate_content(model=gemini_model, contents=gemini_prompt)
        gemini_ms = (time.perf_counter() - t1) * 1000
        gemini_response = resp.text.strip()
        print(f"  [OK] Gemini responded in {gemini_ms:.0f} ms")
    except Exception as e:
        gemini_error = str(e)
        print(f"  [FAIL] Gemini call failed: {gemini_error}")
else:
    gemini_error = "GEMINI_API_KEY not set in .env"
    print(f"  [INFO] {gemini_error} -- using offline fallback")
    gemini_response = (
        "[Simulated Grounded Response (No Gemini API Key)]:\n"
        "Here is the relevant information found in the resort knowledge base:\n"
        "---\n"
        f"{context_block}"
    )

# ── Stage 4: Compose final grounded answer ─────────────────────────────────────
if gemini_response:
    final_answer = f"{gemini_response}\n\n(Source: {sources_str})"
    if not gemini_error:
        status = "SUCCESS (Live Gemini)"
        status_icon = "[OK]"
    else:
        status = "SUCCESS (Offline Fallback)"
        status_icon = "[OK]"
else:
    final_answer = "No response generated."
    status = "FAILED"
    status_icon = "[FAIL]"

print(f"\n{'='*70}")
print(f"[Result] {status_icon} {status}")
print(f"{'='*70}")
print(final_answer)

# ── Stage 5: Write docs/end_to_end_validation.md ──────────────────────────────
OUTPUT_FILE.parent.mkdir(parents=True, exist_ok=True)

# Build the chunks detail table
chunks_table = "| # | Source File | L2 Distance | Relevance |\n|---|-----------|-------------|----------|\n"
for i, r in enumerate(results, 1):
    rel = "Strong" if r["score"] <= 0.55 else ("Good" if r["score"] <= 0.75 else "Weak")
    chunks_table += f"| {i} | `{r['source']}` | {r['score']:.4f} | {rel} |\n"

timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
mode_label = "Live Gemini API" if (api_key and not gemini_error) else "Offline Simulation"

md_content = f"""# End-to-End Validation Report

> **Status:** {status}
> **Timestamp:** {timestamp}
> **Mode:** {mode_label}

---

## 1. Test Query

```
{QUERY}
```

## 2. Execution Flow

```
User Query
  -> ChromaDB Retriever  ({retrieval_ms:.0f} ms)
  -> Context Builder      ({len(context_parts)} chunks, {len(context_block)} chars)
  -> Gemini Generation    ({gemini_ms:.0f} ms, model: {gemini_model})
  -> Final Response
```

## 3. Retrieved Source Documents

{chunks_table}

## 4. Context Sent to Gemini

<details>
<summary>Click to expand full context block ({len(context_block)} characters)</summary>

```text
{context_block}
```

</details>

## 5. Gemini Prompt

<details>
<summary>Click to expand full prompt</summary>

```text
{gemini_prompt}
```

</details>

## 6. Final Grounded Response

```
{final_answer}
```

## 7. Validation Summary

| Metric | Value |
|--------|-------|
| Query | `{QUERY}` |
| Chunks Retrieved | {len(results)} |
| Chunks Used in Context | {len(context_parts)} |
| Source Files | {sources_str} |
| Retrieval Latency | {retrieval_ms:.0f} ms |
| Gemini Latency | {gemini_ms:.0f} ms |
| Gemini Model | `{gemini_model}` |
| API Key Present | {"Yes" if api_key else "No"} |
| Gemini Error | {gemini_error or "None"} |
| Overall Result | **{status}** |
"""

OUTPUT_FILE.write_text(md_content, encoding="utf-8")
print(f"\nValidation report saved to: {OUTPUT_FILE.resolve()}")
print("Script complete -- no further Gemini requests will be made.")
