# app/main.py
"""
Entry point for the VillageTaste-Agent local prototype.
Demonstrates the Orchestrator routing to sub-agents (Booking, Reception, Guide)
and handles query simulation offline.
"""

import asyncio
import os
import sys

# Ensure the root project directory is in the python path for importing agents and workflows
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Check if google-adk is available; if not, configure mock modules first to allow importing workflow files offline
try:
    from google.adk import Runner
    from google.adk.sessions import InMemorySessionService
    HAS_ADK = True
except ImportError:
    HAS_ADK = False
    
    from unittest.mock import MagicMock
    
    class MockAgent:
        def __init__(self, name, model, instruction):
            self.name = name
            self.model = model
            self.instruction = instruction

    class MockWorkflow:
        def __init__(self, name, edges):
            self.name = name
            self.edges = edges

    mock_adk = MagicMock()
    mock_adk.Agent = MockAgent
    mock_adk.Workflow = MockWorkflow
    mock_adk.Context = MagicMock()

    mock_workflow_mod = MagicMock()
    def mock_node(*args, **kwargs):
        if len(args) == 1 and callable(args[0]):
            return args[0]
        def decorator(func):
            return func
        return decorator
    mock_workflow_mod.node = mock_node

    sys.modules['google.adk'] = mock_adk
    sys.modules['google.adk.workflow'] = mock_workflow_mod

from workflows import root_agent


async def run_sample_query(query: str):
    """
    Executes a query through the resort workflow, showcasing the orchestrator classification
    and the corresponding sub-agent response.
    """
    print("=" * 70)
    print(f"GUEST QUERY: '{query}'")
    print("=" * 70)
    
    # If the google-adk package is installed locally, we demonstrate how the Runner API is set up.
    if HAS_ADK:
        try:
            print("[ADK Runner] Initializing InMemorySessionService...")
            session_service = InMemorySessionService()
            runner = Runner(
                agent=root_agent,
                app_name="VillageTasteResortAssistant",
                session_service=session_service
            )
            print("[ADK Runner] Invoking workflow nodes...")
            
            # In a live environment with API keys, you would stream the events:
            #
            # from google.genai import types
            # content = types.Content(role="user", parts=[types.Part(text=query)])
            # async for event in runner.run(user_id="guest_1", session_id="session_1", new_message=content):
            #     if event.is_final_response():
            #         print(event.content.parts[0].text)
            
            # For our offline local dry-run, we execute the workflow nodes programmatically
            # using a simulated context to bypass network dependencies:
            await run_prototype_simulation(query)
            
        except Exception as e:
            print(f"[ADK Runner Error] {e}")
            print("[Fallback] Running in standalone offline simulation...")
            await run_prototype_simulation(query)
    else:
        print("[System Info] google-adk library not detected in local environment.")
        print("[System Info] Running in standalone offline simulation...")
        await run_prototype_simulation(query)
    
    print("=" * 70)
    print("\n")


async def run_prototype_simulation(query: str):
    """
    Simulates the ADK execution context locally. This allows running the exact node functions,
    evaluating the routing logic of the controller, and checking output format offline.
    """
    from workflows.resort_workflow import resort_workflow_controller
    
    # A lightweight mock context to stand in for google.adk.Context
    class MockContext:
        async def run_node(self, node_fn, *args, **kwargs):
            # Directly execute the node function
            return await node_fn(self, *args, **kwargs)
            
    ctx = MockContext()
    response = await resort_workflow_controller(ctx, query)
    print(response)


async def main():
    print("*" * 80)
    print("      VillageTaste Resort Multi-Agent Assistant - Local Prototype Demo      ")
    print("*" * 80)
    print("This prototype showcases the routing of various guest questions to specialized agents.\n")
    
    # Set of test cases to trigger every possible route in our workflow
    test_queries = [
        # Trigger Route 1: Booking Agent
        "I'd like to book a standard cottage for 3 nights starting next Friday.",
        
        # Trigger Route 2: Reception Agent
        "Could we get some fresh towels and report a broken light in room 12?",
        
        # Trigger Route 3: Guide Agent (RAG-Ready)
        "What are the dining hours and menu options for tonight at the resort?",
        
        # Trigger Route 4: Out of Scope Guard Rejection
        "Can you help me write code for a website or tell me the stock price of Apple?"
    ]
    
    for query in test_queries:
        await run_sample_query(query)


if __name__ == "__main__":
    asyncio.run(main())
