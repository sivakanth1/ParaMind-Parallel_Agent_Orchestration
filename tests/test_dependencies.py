import pytest
import asyncio
from src.agents import ParallelExecutor
from src.llm_clients import LLMClient

class MockLLMClient:
    """Mock LLM client for testing - doesn't need real API keys"""
    def __init__(self):
        self.calls = []
        
    async def call_llm(self, model, prompt, **kwargs):
        # Record call
        self.calls.append({"model": model, "prompt": prompt})
        # Simulate small delay
        await asyncio.sleep(0.01)
        return {
            "response": f"Result for {prompt[-10:]}", # Return last part of prompt as result
            "model": model,
            "tokens": 10,
            "latency": 0.01,
            "error": None
        }

@pytest.mark.asyncio
async def test_simple_dependency():
    """Test A -> B dependency"""
    client = MockLLMClient()
    executor = ParallelExecutor(client)
    
    subtasks = [
        {"id": 1, "description": "Research Alpha", "model": "m1", "depends_on": []},
        {"id": 2, "description": "Summarize Alpha", "model": "m2", "depends_on": [1]}
    ]
    
    results = await executor.mode_b_execution(subtasks)
    
    assert len(results) == 2
    assert len(client.calls) == 2
    
    # Verify Task 2 prompt contains Task 1 result
    task2_call = next(c for c in client.calls if "Summarize Alpha" in c["prompt"])
    assert "Result for arch Alpha" in task2_call["prompt"] # "arch Alpha" is last 10 chars of Task 1 prompt

@pytest.mark.asyncio
async def test_parallel_then_merge():
    """Test (A, B) -> C dependency"""
    client = MockLLMClient()
    executor = ParallelExecutor(client)
    
    subtasks = [
        {"id": 1, "description": "Task A", "model": "m1", "depends_on": []},
        {"id": 2, "description": "Task B", "model": "m1", "depends_on": []},
        {"id": 3, "description": "Task C", "model": "m1", "depends_on": [1, 2]}
    ]
    
    results = await executor.mode_b_execution(subtasks)
    
    assert len(results) == 3
    
    # Verify Task C prompt contains results from A and B
    task3_call = next(c for c in client.calls if "Task C" in c["prompt"])
    assert "Result for Task A" in task3_call["prompt"]
    assert "Result for Task B" in task3_call["prompt"]

@pytest.mark.asyncio
async def test_circular_dependency():
    """Test A -> B -> A cycle"""
    client = MockLLMClient()
    executor = ParallelExecutor(client)
    
    subtasks = [
        {"id": 1, "description": "Task A", "model": "m1", "depends_on": [2]},
        {"id": 2, "description": "Task B", "model": "m1", "depends_on": [1]}
    ]
    
    # Should return empty list or handle error gracefully (logged error)
    results = await executor.mode_b_execution(subtasks)
    assert len(results) == 0 # Expect failure for circular dep

@pytest.mark.asyncio
async def test_no_dependencies():
    """Test standard parallel execution"""
    client = MockLLMClient()
    executor = ParallelExecutor(client)
    
    subtasks = [
        {"id": 1, "description": "Task A", "model": "m1"}, # Missing depends_on key
        {"id": 2, "description": "Task B", "model": "m1", "depends_on": []}
    ]
    
    results = await executor.mode_b_execution(subtasks)
    assert len(results) == 2
    # Should use standard parallel path (logged as "Mode B: Executing...")
    # But since we updated mode_b_execution to check for ANY depends_on, 
    # and Task 2 has empty list, it might trigger DAG path if we are not careful.
    # Our logic: if any(t.get("depends_on") for t in subtasks):
    # Task 1: None. Task 2: []. Both falsy.
    # So it should use standard parallel path.
