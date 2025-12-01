import asyncio
import sys
import os

# Add src to path
sys.path.append(os.path.join(os.getcwd(), "src"))

from src.controller import Controller
from src.llm_clients import LLMClient

async def main():
    # Initialize
    client = LLMClient()
    controller = Controller(client)
    
    # Test prompt
    prompt = "Plan a detailed 3-day tour of Paris attractions, including a budget, a list of top museums, and restaurant recommendations."
    
    print(f"Analyzing prompt: {prompt}", flush=True)
    plan = await controller.analyze_and_plan(prompt)
    
    import json
    print(json.dumps(plan, indent=2), flush=True)

if __name__ == "__main__":
    asyncio.run(main())
