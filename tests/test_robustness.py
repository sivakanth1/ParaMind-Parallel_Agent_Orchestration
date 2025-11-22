import pytest
import asyncio
from unittest.mock import MagicMock, AsyncMock, patch
from src.llm_clients import LLMClient
from src.controller import Controller
from src.agents import ParallelExecutor

class MockLLMClient(LLMClient):
    def __init__(self):
        self.call_count = 0
        self.fail_count = 0
        self.should_fail_times = 0
        self.responses = []
        
    async def call_llm(self, model, prompt, **kwargs):
        self.call_count += 1
        
        if self.fail_count < self.should_fail_times:
            self.fail_count += 1
            raise Exception("Simulated API Error")
            
        if self.responses:
            return self.responses.pop(0)
            
        return {
            "response": "Default response",
            "model": model,
            "tokens": 10,
            "latency": 0.1,
            "error": None
        }

@pytest.mark.asyncio
async def test_retry_logic():
    """Test that LLMClient retries on failure"""
    client = LLMClient()
    
    # Mock the Groq client's create method on this specific instance
    mock_create = AsyncMock()
    client.groq_client.chat.completions.create = mock_create
    
    # Make it fail twice then succeed
    mock_create.side_effect = [
        Exception("Fail 1"),
        Exception("Fail 2"),
        MagicMock(choices=[MagicMock(message=MagicMock(content="Success"))], usage=MagicMock(total_tokens=10))
    ]
    
    # Patch wait to avoid delay
    with patch("tenacity.nap.time.sleep"):
        # Disable cache to force calls
        result = await client.call_llm("llama-3.1-8b-instant", "test", use_cache=False)
    
    assert result["response"] == "Success"
    assert mock_create.call_count == 3

@pytest.mark.asyncio
async def test_json_correction():
    """Test that Controller corrects invalid JSON"""
    client = AsyncMock(spec=LLMClient)
    
    # First call returns invalid JSON, second call (correction) returns valid JSON
    client.call_llm.side_effect = [
        {
            "response": "Invalid JSON { mode: 'A' }", # Missing quotes
            "error": None
        },
        {
            "response": '{"mode": "A", "plan": {"models": ["llama-3.1-8b-instant"]}}',
            "error": None
        }
    ]
    
    controller = Controller(client)
    plan = await controller.analyze_and_plan("test prompt")
    
    assert plan["mode"] == "A"
    # Should have called LLM twice (initial + correction)
    assert client.call_llm.call_count == 2

@pytest.mark.asyncio
async def test_dag_partial_failure():
    """Test that DAG execution handles partial failures"""
    client = AsyncMock(spec=LLMClient)
    
    # Mock execution: Task 1 fails, Task 2 succeeds (independent), Task 3 (depends on 1) should be skipped
    async def mock_execute(model, prompt, **kwargs):
        if "Task 1" in prompt:
            return {"response": "", "error": "Task 1 Failed", "id": 1}
        return {"response": "Success", "error": None, "id": 2} # ID will be overwritten by executor loop but that's fine
        
    executor = ParallelExecutor(client)
    executor.execute_agent = AsyncMock(side_effect=mock_execute)
    
    subtasks = [
        {"id": 1, "description": "Task 1", "model": "m1", "depends_on": []},
        {"id": 2, "description": "Task 2", "model": "m1", "depends_on": []},
        {"id": 3, "description": "Task 3", "model": "m1", "depends_on": [1]}
    ]
    
    results = await executor.mode_b_execution_with_deps(subtasks)
    
    results_map = {r["id"]: r for r in results}
    
    assert results_map[1]["error"] == "Task 1 Failed"
    assert results_map[2]["error"] is None
    assert results_map[3]["error"] == "Dependency failed"
    assert results_map[3]["response"] == "Skipped due to failed dependency"
