import os
import json
import glob
from typing import List, Dict, Optional
from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from src.llm_clients import LLMClient
from src.controller import Controller
from src.agents import ParallelExecutor
from src.aggregator import Aggregator

app = FastAPI(title="ParaMind API", description="API for Parallel Agent Orchestration")

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Initialize Core Components
llm_client = LLMClient()
controller = Controller(llm_client)
executor = ParallelExecutor(llm_client)
aggregator = Aggregator(llm_client)

# Models
class PromptRequest(BaseModel):
    prompt: str

class ExecuteRequest(BaseModel):
    mode: str
    plan: Dict
    prompt: str

# Routes
@app.get("/health")
async def health_check():
    return {"status": "healthy", "system": "ParaMind"}

@app.post("/analyze")
async def analyze_prompt(request: PromptRequest):
    """Analyze prompt and return execution plan"""
    try:
        plan = await controller.analyze_and_plan(request.prompt)
        return plan
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/execute")
async def execute_plan(request: ExecuteRequest):
    """Execute the generated plan"""
    try:
        if request.mode == "A":
            # Mode A: plan["models"] is a list of models
            results = await executor.mode_a_execution(request.prompt, request.plan.get("models", []))
        elif request.mode == "B":
            # Mode B: plan["subtasks"] is a list of tasks
            results = await executor.mode_b_execution(request.plan.get("subtasks", []))
        else:
            raise HTTPException(status_code=400, detail="Invalid mode")
            
        # Aggregate results
        combined_result = await aggregator.summarize(results)
        
        # Calculate Metrics
        # Sequential Baseline: Sum of individual agent latencies
        sequential_baseline = sum(r.get("latency", 0) for r in results)
        
        # Parallel Time: Max of individual agent latencies (approximation)
        parallel_time = max((r.get("latency", 0) for r in results), default=0)
        
        # Speedup
        speedup = sequential_baseline / parallel_time if parallel_time > 0 else 0
        
        return {
            "mode": request.mode,
            "responses": results,
            "final_result": combined_result,
            "metrics": {
                "sequential_time": sequential_baseline,
                "parallel_time": parallel_time,
                "speedup": speedup
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/metrics")
async def get_metrics():
    """Get latest benchmark metrics"""
    try:
        # Find latest json result in benchmarks/results
        list_of_files = glob.glob('benchmarks/results/*.json') 
        if not list_of_files:
            return {"error": "No benchmark data found"}
            
        latest_file = max(list_of_files, key=os.path.getctime)
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
            
        # Calculate summary metrics
        total = len(data)
        success = len([d for d in data if d.get("success_rate", 0) == 100])
        avg_speedup = sum(d.get("speedup", 0) for d in data) / total if total > 0 else 0
        avg_latency = sum(d.get("total_latency", 0) for d in data) / total if total > 0 else 0
        
        return {
            "total_prompts": total,
            "success_rate": (success / total) * 100 if total > 0 else 0,
            "avg_speedup": round(avg_speedup, 2),
            "avg_latency": round(avg_latency, 2),
            "latest_run": os.path.basename(latest_file),
            "details": data # Send full data for table
        }
    except Exception as e:
        return {"error": str(e)}

@app.get("/benchmarks")
async def get_benchmarks():
    """Get detailed benchmark history"""
    try:
        # Find latest json result in benchmarks/results
        list_of_files = glob.glob('benchmarks/results/*.json') 
        if not list_of_files:
            return []
            
        latest_file = max(list_of_files, key=os.path.getctime)
        
        with open(latest_file, 'r') as f:
            data = json.load(f)
            
        return data
    except Exception as e:
        print(f"Error loading benchmarks: {e}")
        return []

# Serve Static Files (CSS, JS, etc.) from /ui directory
# Mount static files BEFORE the root route
from fastapi.responses import FileResponse

@app.get("/style.css")
async def serve_css():
    return FileResponse("ui/style.css")

@app.get("/app.js")
async def serve_js():
    return FileResponse("ui/app.js")

@app.get("/")
async def read_root():
    """Serve the main HTML page"""
    return FileResponse("ui/index.html")
