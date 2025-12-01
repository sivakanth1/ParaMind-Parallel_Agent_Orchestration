import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from src.controller import Controller
from src.llm_clients import LLMClient

@pytest.fixture
def mock_llm_client():
    client = MagicMock(spec=LLMClient)
    client.call_llm = AsyncMock()
    return client

@pytest.fixture
def controller(mock_llm_client):
    return Controller(mock_llm_client)

@pytest.mark.asyncio
async def test_paris_tour_parallel_planning(controller, mock_llm_client):
    """Test that 'Paris tour' request is decomposed into parallel tasks"""
    
    # Mock LLM response for Paris tour
    mock_response = {
        "mode": "B",
        "reasoning": "Complex task with independent components (Budget, Attractions, Food)",
        "plan": {
            "subtasks": [
                {
                    "id": 1,
                    "description": "Create a detailed budget for a 3-day Paris trip",
                    "model": "llama-3.3-70b-versatile",
                    "depends_on": []
                },
                {
                    "id": 2,
                    "description": "List top attractions for a 3-day Paris itinerary",
                    "model": "llama-3.1-8b-instant",
                    "depends_on": []
                },
                {
                    "id": 3,
                    "description": "Recommend restaurants for a 3-day Paris trip",
                    "model": "llama-3.3-70b-versatile",
                    "depends_on": []
                }
            ]
        }
    }
    
    mock_llm_client.call_llm.return_value = {
        "response": json.dumps(mock_response),
        "error": None
    }
    
    prompt = "Plan a 3-day trip to Paris with budget, attractions, and restaurant recommendations"
    plan = await controller.analyze_and_plan(prompt)
    
    assert plan["mode"] == "B"
    assert len(plan["plan"]["subtasks"]) == 3
    # Verify all tasks are independent (empty depends_on)
    for task in plan["plan"]["subtasks"]:
        assert task["depends_on"] == []

@pytest.mark.asyncio
async def test_serial_dependency_planning(controller, mock_llm_client):
    """Test that 'Research then Summary' request is decomposed into serial tasks"""
    
    mock_response = {
        "mode": "B",
        "reasoning": "Sequential task: Summary depends on Research",
        "plan": {
            "subtasks": [
                {
                    "id": 1,
                    "description": "Research the history of Java programming language",
                    "model": "llama-3.3-70b-versatile",
                    "depends_on": []
                },
                {
                    "id": 2,
                    "description": "Write a summary based on the research",
                    "model": "llama-3.3-70b-versatile",
                    "depends_on": [1]
                }
            ]
        }
    }
    
    mock_llm_client.call_llm.return_value = {
        "response": json.dumps(mock_response),
        "error": None
    }
    
    prompt = "Research the history of Java and then write a summary"
    plan = await controller.analyze_and_plan(prompt)
    
    assert plan["mode"] == "B"
    assert len(plan["plan"]["subtasks"]) == 2
    assert plan["plan"]["subtasks"][0]["id"] == 1
    assert plan["plan"]["subtasks"][1]["id"] == 2
    assert plan["plan"]["subtasks"][1]["depends_on"] == [1]

@pytest.mark.asyncio
async def test_hybrid_planning(controller, mock_llm_client):
    """Test 'Research A and B, then Compare' (Hybrid: Parallel -> Serial)"""
    
    mock_response = {
        "mode": "B",
        "reasoning": "Hybrid task: Parallel research followed by serial comparison",
        "plan": {
            "subtasks": [
                {
                    "id": 1,
                    "description": "Research Python features",
                    "model": "llama-3.1-8b-instant",
                    "depends_on": []
                },
                {
                    "id": 2,
                    "description": "Research JavaScript features",
                    "model": "llama-3.1-8b-instant",
                    "depends_on": []
                },
                {
                    "id": 3,
                    "description": "Compare Python and JavaScript based on research",
                    "model": "llama-3.3-70b-versatile",
                    "depends_on": [1, 2]
                }
            ]
        }
    }
    
    mock_llm_client.call_llm.return_value = {
        "response": json.dumps(mock_response),
        "error": None
    }
    
    prompt = "Research Python and JavaScript, then compare them"
    plan = await controller.analyze_and_plan(prompt)
    
    assert plan["mode"] == "B"
    assert len(plan["plan"]["subtasks"]) == 3
    # Tasks 1 and 2 are independent
    assert plan["plan"]["subtasks"][0]["depends_on"] == []
    assert plan["plan"]["subtasks"][1]["depends_on"] == []
    # Task 3 depends on 1 and 2
    assert set(plan["plan"]["subtasks"][2]["depends_on"]) == {1, 2}
