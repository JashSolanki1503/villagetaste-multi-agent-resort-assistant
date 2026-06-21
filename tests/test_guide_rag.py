# tests/test_guide_rag.py
"""
Test script to verify the offline RAG retrieval inside the Guide Agent.
Runs the required test queries and displays responses and retrieval logs.
"""

import asyncio
import sys
from pathlib import Path

# Add project root to path
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.append(str(PROJECT_ROOT))

# Mock google.adk module prior to importing agents (bypassing network/gemini engine dependencies)
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

from agents.guide import guide_agent


async def run_test():
    queries = [
        "What activities are available?",
        "What food is served in the resort?",
        "What are the resort policies?",
        "What is the stock price of Apple?"
    ]

    print("=" * 80)
    print("      VillageTaste Resort - Guide Agent RAG Integration Test Run      ")
    print("=" * 80)

    for query in queries:
        print(f"\n[QUERY] Guest asks: '{query}'")
        # run_guide_agent is attached as a .run attribute on the guide_agent instance
        response = await guide_agent.run(query)
        print("-" * 80)
        print(response)
        print("-" * 80)
        print("\n")


if __name__ == "__main__":
    asyncio.run(run_test())
