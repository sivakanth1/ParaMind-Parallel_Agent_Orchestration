import asyncio
from src.llm_clients import LLMClient
from src.aggregator import Aggregator

async def test_aggregator():
    client = LLMClient()
    aggregator = Aggregator(client)
    
    results = [
        {"model": "Model A", "response": "Paris is the capital of France.", "error": None},
        {"model": "Model B", "response": "Paris is a major European city known for the Eiffel Tower.", "error": None}
    ]
    
    print("Testing Summarize...")
    summary = await aggregator.summarize(results)
    print(f"Summary: {summary}")
    
    print("\nTesting Best of N...")
    best = await aggregator.best_of_n(results, "What is Paris?")
    print(f"Best: {best}")

if __name__ == "__main__":
    asyncio.run(test_aggregator())
