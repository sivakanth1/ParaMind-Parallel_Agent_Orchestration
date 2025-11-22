import asyncio
import json
import time
import os
import csv
from datetime import datetime
from typing import List, Dict
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.controller import Controller
from src.agents import ParallelExecutor
from src.llm_clients import LLMClient
from loguru import logger
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Configure logging
logger.remove()
logger.add(sys.stderr, level="INFO")
logger.add("benchmarks/benchmark.log", rotation="1 day")

async def run_benchmark():
    # Load prompts
    with open("benchmarks/prompts.json", "r") as f:
        data = json.load(f)
        prompts = data["prompts"]

    # Initialize system
    client = LLMClient()
    controller = Controller(client)
    executor = ParallelExecutor(client)

    # Prepare results directory
    timestamp = datetime.now().strftime("%Y_%m_%d_%H_%M")
    results_dir = "benchmarks/results"
    os.makedirs(results_dir, exist_ok=True)
    
    results = []
    
    logger.info(f"🚀 Starting benchmark with {len(prompts)} prompts...")

    for i, item in enumerate(prompts):
        logger.info(f"[{i+1}/{len(prompts)}] Running: {item['id']} - {item['prompt'][:50]}...")
        
        start_time = time.time()
        
        try:
            # 1. Controller Plan
            plan_start = time.time()
            plan = await controller.analyze_and_plan(item["prompt"])
            plan_latency = time.time() - plan_start
            
            if not plan:
                logger.error(f"❌ Plan generation failed for {item['id']}")
                continue

            mode = plan["mode"]
            
            # 2. Execution
            exec_start = time.time()
            execution_result = []
            
            if mode == "A":
                execution_result = await executor.mode_a_execution(
                    item["prompt"], 
                    plan["plan"]["models"]
                )
            elif mode == "B":
                subtasks = plan["plan"]["subtasks"]
                # Check for dependencies to decide execution path
                if any(t.get("depends_on") for t in subtasks):
                    execution_result = await executor.mode_b_execution_with_deps(subtasks)
                else:
                    execution_result = await executor.mode_b_execution(subtasks)
            
            exec_latency = time.time() - exec_start
            total_latency = time.time() - start_time
            
            # 3. Metrics Calculation
            
            # Agent stats
            num_agents = len(execution_result)
            failed_agents = len([r for r in execution_result if r.get("error")])
            success_rate = ((num_agents - failed_agents) / num_agents) * 100 if num_agents > 0 else 0
            
            # Token usage (estimate if not provided)
            total_tokens = sum(r.get("tokens", 0) for r in execution_result)
            
            # Sequential Baseline Estimation
            # Sum of individual agent latencies (assuming sequential execution)
            sequential_baseline = sum(r.get("latency", 0) for r in execution_result)
            
            # Speedup
            speedup = sequential_baseline / exec_latency if exec_latency > 0 else 0
            
            # Mode Accuracy
            mode_accuracy = (mode == item["expected_mode"])
            
            # Dependency check
            has_dependencies = False
            if mode == "B":
                subtasks = plan["plan"].get("subtasks", [])
                has_dependencies = any(t.get("depends_on") for t in subtasks)

            # Layers (for Mode B)
            num_layers = 1
            if mode == "B" and has_dependencies:
                # Simple layer estimation or we could expose it from executor
                # For now, we'll assume 1 unless we parse the DAG again, 
                # but let's just track if it was dependent.
                # Actually, let's calculate it properly if we can, but for now 1 or >1 is enough distinction.
                num_layers = "DAG" 
            elif mode == "B":
                num_layers = 1
            else:
                num_layers = 1

            result_entry = {
                "prompt_id": item["id"],
                "category": item["category"],
                "prompt": item["prompt"],
                "mode_detected": mode,
                "mode_expected": item["expected_mode"],
                "mode_accuracy": mode_accuracy,
                "num_agents": num_agents,
                "num_layers": num_layers,
                "has_dependencies": has_dependencies,
                "plan_latency": round(plan_latency, 2),
                "exec_latency": round(exec_latency, 2),
                "total_latency": round(total_latency, 2),
                "sequential_baseline": round(sequential_baseline, 2),
                "speedup": round(speedup, 2),
                "success_rate": success_rate,
                "failed_agents": failed_agents,
                "total_tokens": total_tokens,
                "timestamp": datetime.now().isoformat()
            }
            
            results.append(result_entry)
            logger.success(f"✅ Finished {item['id']} | Mode: {mode} | Speedup: {speedup:.2f}x")
            
        except Exception as e:
            logger.error(f"❌ Error running {item['id']}: {e}")
            results.append({
                "prompt_id": item["id"],
                "error": str(e),
                "timestamp": datetime.now().isoformat()
            })

    # Save Results
    
    # JSON
    json_path = f"{results_dir}/eval_{timestamp}.json"
    with open(json_path, "w") as f:
        json.dump(results, f, indent=2)
        
    # CSV
    csv_path = f"{results_dir}/eval_{timestamp}.csv"
    if results:
        keys = results[0].keys()
        with open(csv_path, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=keys)
            writer.writeheader()
            writer.writerows(results)
            
    logger.info(f"🏁 Benchmark complete. Results saved to {results_dir}")

if __name__ == "__main__":
    asyncio.run(run_benchmark())
